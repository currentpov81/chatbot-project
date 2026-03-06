import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.queries import increment_chat_count, create_report, get_user
from app.services import matcher
from app.keyboards.chat_kb import chat_actions_keyboard, report_reasons_keyboard
from app.utils.states import ChatStates
from app.config import settings

router = Router()


# ── /chat command ──────────────────────────────────────────────────────────

@router.message(Command("chat"))
async def cmd_chat(message: Message, state: FSMContext, db_user: User, **kwargs):
    if not db_user.is_onboarded:
        await message.answer("⚠️ Please complete your profile first. Send /start")
        return

    current_state = await state.get_state()

    # Already in chat — don't restart
    if current_state == ChatStates.in_chat:
        await message.answer("💬 You're already in a chat. Use /next or /stop.")
        return

    await _start_matching(message, state, message.bot)


async def _start_matching(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id

    # Try immediate match first
    partner_id = await matcher.find_match(user_id)

    if partner_id:
        await _connect_users(bot, user_id, partner_id, state)
        return

    # No match — add to queue and wait
    await matcher.add_to_queue(user_id)
    await state.set_state(ChatStates.searching)

    wait_msg = await message.answer(
        "🔍 <b>Looking for a chat partner...</b>\n\n"
        "<i>This usually takes a few seconds.</i>\n\n"
        "Send /stop to cancel."
    )
    await state.update_data(wait_msg_id=wait_msg.message_id)

    # Background polling for match (up to MATCH_TIMEOUT seconds)
    asyncio.create_task(_poll_for_match(bot, user_id, state, message.chat.id))


async def _poll_for_match(bot: Bot, user_id: int, state: FSMContext, chat_id: int):
    """Poll Redis every 1s until match found or timeout."""
    for _ in range(settings.MATCH_TIMEOUT):
        await asyncio.sleep(1)

        current_state = await state.get_state()
        if current_state != ChatStates.searching:
            return  # User cancelled or something changed

        partner_id = await matcher.get_partner(user_id)
        if partner_id:
            # Partner was matched by another worker
            await _notify_connected(bot, user_id, partner_id, state, chat_id)
            return

        # Try to match again
        partner_id = await matcher.find_match(user_id)
        if partner_id:
            await _connect_users_by_id(bot, user_id, partner_id, state, chat_id)
            return

    # Timeout
    await matcher.remove_from_queue(user_id)
    await state.clear()
    try:
        await bot.send_message(
            chat_id,
            "😔 <b>No partner found.</b>\n\n"
            "The queue is currently empty. Try again in a moment with /chat"
        )
    except Exception:
        pass


async def _connect_users(bot: Bot, user_id: int, partner_id: int, state: FSMContext):
    """Match just happened — notify both users."""
    await state.set_state(ChatStates.in_chat)

    # Get partner state context (different FSM state for partner)
    from aiogram.fsm.storage.base import StorageKey
    storage = state.storage
    bot_id = bot.id

    partner_key = StorageKey(bot_id=bot_id, chat_id=partner_id, user_id=partner_id)
    partner_state = FSMContext(storage=storage, key=partner_key)
    await partner_state.set_state(ChatStates.in_chat)

    msg = (
        "✅ <b>Partner found!</b>\n\n"
        "💬 You can send: text, photos, stickers, voice, video\n\n"
        "Use /next for a new partner • /stop to end"
    )

    await bot.send_message(user_id, msg, reply_markup=chat_actions_keyboard())
    await bot.send_message(partner_id, msg, reply_markup=chat_actions_keyboard())


async def _connect_users_by_id(bot: Bot, user_id: int, partner_id: int, state: FSMContext, chat_id: int):
    await _connect_users(bot, user_id, partner_id, state)


async def _notify_connected(bot: Bot, user_id: int, partner_id: int, state: FSMContext, chat_id: int):
    await state.set_state(ChatStates.in_chat)
    await bot.send_message(
        chat_id,
        "✅ <b>Partner found!</b>\n\n"
        "💬 You can send: text, photos, stickers, voice, video\n\n"
        "Use /next for a new partner • /stop to end",
        reply_markup=chat_actions_keyboard()
    )


# ── Message relay ─────────────────────────────────────────────────────────

@router.message(ChatStates.in_chat)
async def relay_message(message: Message, **kwargs):
    """Forward all message types to the chat partner."""
    user_id = message.from_user.id
    partner_id = await matcher.get_partner(user_id)

    if not partner_id:
        await message.answer("⚠️ Your chat has ended. Use /chat to find a new partner.")
        return

    bot: Bot = message.bot

    try:
        if message.text:
            await bot.send_message(partner_id, message.text)
        elif message.photo:
            await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
        elif message.sticker:
            await bot.send_sticker(partner_id, message.sticker.file_id)
        elif message.voice:
            await bot.send_voice(partner_id, message.voice.file_id)
        elif message.video_note:
            await bot.send_video_note(partner_id, message.video_note.file_id)
        elif message.video:
            await bot.send_video(partner_id, message.video.file_id, caption=message.caption)
        elif message.document:
            await bot.send_document(partner_id, message.document.file_id, caption=message.caption)
        elif message.animation:
            await bot.send_animation(partner_id, message.animation.file_id)
        elif message.audio:
            await bot.send_audio(partner_id, message.audio.file_id, caption=message.caption)
    except Exception:
        # Partner may have blocked the bot
        await _handle_partner_gone(message, user_id, partner_id)


async def _handle_partner_gone(message: Message, user_id: int, partner_id: int):
    await matcher.end_chat(user_id)
    await message.answer(
        "😔 Your partner has left the chat.\n\nUse /chat to find a new partner."
    )


# ── /next command ─────────────────────────────────────────────────────────

@router.message(Command("next"))
@router.callback_query(F.data == "chat:next")
async def cmd_next(event, state: FSMContext, session: AsyncSession, db_user: User, **kwargs):
    user_id = event.from_user.id

    partner_id = await matcher.end_chat(user_id)

    if partner_id:
        await increment_chat_count(session, user_id)
        await increment_chat_count(session, partner_id)
        try:
            await event.bot.send_message(
                partner_id,
                "👋 Your partner left the chat.\n\nUse /chat to find a new partner."
            )
        except Exception:
            pass

    if isinstance(event, CallbackQuery):
        await event.answer()
        msg = event.message
    else:
        msg = event

    await msg.answer("🔄 Finding a new partner...")
    await _start_matching(msg, state, event.bot)


# ── /stop command ─────────────────────────────────────────────────────────

@router.message(Command("stop"))
@router.callback_query(F.data == "chat:stop")
async def cmd_stop(event, state: FSMContext, session: AsyncSession, **kwargs):
    user_id = event.from_user.id

    partner_id = await matcher.end_chat(user_id)
    await matcher.remove_from_queue(user_id)
    await state.clear()

    if partner_id:
        await increment_chat_count(session, user_id)
        await increment_chat_count(session, partner_id)
        try:
            await event.bot.send_message(
                partner_id,
                "👋 Your partner left the chat.\n\nUse /chat to find a new partner."
            )
        except Exception:
            pass

    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer("🛑 Chat ended. Use /chat to start a new one.")
    else:
        await event.answer("🛑 Chat ended. Use /chat to start a new one.")


# ── Report ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "chat:report")
async def cb_report_start(callback: CallbackQuery, state: FSMContext, **kwargs):
    partner_id = await matcher.get_partner(callback.from_user.id)
    if not partner_id:
        await callback.answer("No active chat to report.", show_alert=True)
        return

    await state.update_data(report_target=partner_id)
    await state.set_state(ChatStates.reporting)
    await callback.message.answer(
        "🚩 <b>Report user</b>\n\nSelect a reason:",
        reply_markup=report_reasons_keyboard()
    )
    await callback.answer()


@router.callback_query(ChatStates.reporting, F.data.startswith("report:"))
async def cb_report_reason(callback: CallbackQuery, state: FSMContext, session: AsyncSession, **kwargs):
    reason = callback.data.split(":")[1]

    if reason == "cancel":
        await state.set_state(ChatStates.in_chat)
        await callback.message.edit_text("Report cancelled.")
        await callback.answer()
        return

    data = await state.get_data()
    reported_id = data.get("report_target")

    if reported_id:
        await create_report(session, callback.from_user.id, reported_id, reason)

    await state.set_state(ChatStates.in_chat)
    await callback.message.edit_text("✅ Report submitted. Thank you for keeping this community safe.")
    await callback.answer()
