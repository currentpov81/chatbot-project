from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.database.models import User
from app.keyboards.onboarding_kb import gender_keyboard
from app.utils.states import OnboardingStates

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_user: User, **kwargs):
    await state.clear()

    if db_user.is_onboarded:
        await message.answer(
            f"👋 Welcome back, <b>{message.from_user.first_name}</b>!\n\n"
            "Use /chat to find a chat partner.\n"
            "Use /help to see all commands."
        )
        return

    await message.answer(
        f"👋 Hey <b>{message.from_user.first_name}</b>, welcome to <b>AnonymChat</b>!\n\n"
        "Chat anonymously with strangers from around the world. 🌍\n\n"
        "<i>No messages are stored. Your identity stays hidden.</i>\n\n"
        "Let's set up your profile first."
    )

    await message.answer(
        "🧑 What's your gender?",
        reply_markup=gender_keyboard()
    )
    await state.set_state(OnboardingStates.waiting_gender)
