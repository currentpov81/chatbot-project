from aiogram.fsm.state import StatesGroup, State


class OnboardingStates(StatesGroup):
    waiting_gender = State()
    waiting_age = State()
    waiting_country = State()
    waiting_city = State()


class ChatStates(StatesGroup):
    searching = State()
    in_chat = State()
    reporting = State()
