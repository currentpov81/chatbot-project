from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.services.matcher import get_queue_length

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message, **kwargs):
    await message.answer(
        "📖 <b>Commands</b>\n\n"
        "/chat — Find a random chat partner\n"
        "/next — Skip to a new partner\n"
        "/stop — End current chat\n"
        "/profile — View your profile\n"
        "/help — Show this message\n\n"
        "<i>All conversations are anonymous. No messages are stored.</i>"
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message, db_user: User, **kwargs):
    if not db_user.is_onboarded:
        await message.answer("⚠️ No profile yet. Send /start to create one.")
        return

    gender_emoji = "👨" if db_user.gender == "male" else "👩"
    location = db_user.country or "Unknown"
    if db_user.city:
        location = f"{db_user.city}, {db_user.country}"

    await message.answer(
        f"👤 <b>Your Profile</b>\n\n"
        f"{gender_emoji} Gender: <b>{'Male' if db_user.gender == 'male' else 'Female'}</b>\n"
        f"📅 Age: <b>{db_user.age_group or 'N/A'}</b>\n"
        f"📍 Location: <b>{location}</b>\n"
        f"💬 Total chats: <b>{db_user.total_chats}</b>"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message, **kwargs):
    queue_len = await get_queue_length()
    await message.answer(
        f"📊 <b>Live Stats</b>\n\n"
        f"👥 Users in queue: <b>{queue_len}</b>"
    )
