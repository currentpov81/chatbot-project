from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Male", callback_data="gender:male"),
            InlineKeyboardButton(text="👩 Female", callback_data="gender:female"),
        ]
    ])


def age_keyboard() -> InlineKeyboardMarkup:
    ages = ["18-20", "20-23", "23-25", "25-30", "30-40", "40+"]
    rows = [[InlineKeyboardButton(text=a, callback_data=f"age:{a}")] for a in ages]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def country_keyboard() -> InlineKeyboardMarkup:
    """Top countries — extend as needed or use a dynamic list."""
    countries = [
        ("🇮🇳 India", "India"),
        ("🇺🇸 USA", "USA"),
        ("🇧🇷 Brazil", "Brazil"),
        ("🇷🇺 Russia", "Russia"),
        ("🇵🇰 Pakistan", "Pakistan"),
        ("🇧🇩 Bangladesh", "Bangladesh"),
        ("🇳🇬 Nigeria", "Nigeria"),
        ("🇮🇩 Indonesia", "Indonesia"),
        ("🇹🇷 Turkey", "Turkey"),
        ("🌍 Other", "Other"),
    ]
    rows = [[InlineKeyboardButton(text=name, callback_data=f"country:{code}")] for name, code in countries]
    return InlineKeyboardMarkup(inline_keyboard=rows)
