from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.states import OnboardingStates
from app.keyboards.onboarding_kb import age_keyboard, country_keyboard
from app.services.user_service import complete_onboarding

router = Router()


# ── Step 1: Gender ──────────────────────────────────────────────────────────

@router.callback_query(OnboardingStates.waiting_gender, F.data.startswith("gender:"))
async def cb_gender(callback: CallbackQuery, state: FSMContext, **kwargs):
    gender = callback.data.split(":")[1]
    await state.update_data(gender=gender)
    await callback.message.edit_text(
        f"Got it — {'👨 Male' if gender == 'male' else '👩 Female'}.\n\n"
        "📅 What's your age group?",
        reply_markup=age_keyboard()
    )
    await state.set_state(OnboardingStates.waiting_age)
    await callback.answer()


# ── Step 2: Age ─────────────────────────────────────────────────────────────

@router.callback_query(OnboardingStates.waiting_age, F.data.startswith("age:"))
async def cb_age(callback: CallbackQuery, state: FSMContext, **kwargs):
    age_group = callback.data.split(":")[1]
    await state.update_data(age_group=age_group)
    await callback.message.edit_text(
        f"Age group: <b>{age_group}</b> ✅\n\n"
        "🌍 Select your country:",
        reply_markup=country_keyboard()
    )
    await state.set_state(OnboardingStates.waiting_country)
    await callback.answer()


# ── Step 3: Country ──────────────────────────────────────────────────────────

@router.callback_query(OnboardingStates.waiting_country, F.data.startswith("country:"))
async def cb_country(callback: CallbackQuery, state: FSMContext, **kwargs):
    country = callback.data.split(":")[1]
    await state.update_data(country=country)
    await callback.message.edit_text(
        f"Country: <b>{country}</b> ✅\n\n"
        "🏙 What city are you from?\n\n"
        "<i>Type your city name, or send <b>Skip</b> to skip.</i>"
    )
    await state.set_state(OnboardingStates.waiting_city)
    await callback.answer()


# ── Step 4: City ─────────────────────────────────────────────────────────────

@router.message(OnboardingStates.waiting_city)
async def msg_city(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    city_input = message.text.strip()
    city = None if city_input.lower() in ("skip", "/skip") else city_input[:50]

    data = await state.get_data()

    await complete_onboarding(
        session,
        user_id=message.from_user.id,
        gender=data["gender"],
        age_group=data["age_group"],
        country=data["country"],
        city=city,
    )

    await state.clear()

    location_str = data["country"]
    if city:
        location_str = f"{city}, {data['country']}"

    await message.answer(
        f"✅ <b>Profile created!</b>\n\n"
        f"📍 {location_str}\n"
        f"👤 {data['age_group']} • {'Male' if data['gender'] == 'male' else 'Female'}\n\n"
        "You're all set! Use /chat to find a chat partner 🎉"
    )
