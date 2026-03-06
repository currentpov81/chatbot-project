from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def chat_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏭ Next", callback_data="chat:next"),
            InlineKeyboardButton(text="🛑 Stop", callback_data="chat:stop"),
        ],
        [
            InlineKeyboardButton(text="🚩 Report", callback_data="chat:report"),
        ]
    ])


def report_reasons_keyboard() -> InlineKeyboardMarkup:
    reasons = ["Spam", "Abuse", "Inappropriate content", "Scam", "Other"]
    rows = [[InlineKeyboardButton(text=r, callback_data=f"report:{r}")] for r in reasons]
    rows.append([InlineKeyboardButton(text="❌ Cancel", callback_data="report:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
