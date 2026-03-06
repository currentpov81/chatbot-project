from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.database.connection import AsyncSessionLocal
from app.database.queries import get_or_create_user


class RegisterMiddleware(BaseMiddleware):
    """
    Ensures every user is registered in DB before handler runs.
    Injects `session` and `db_user` into handler data.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        async with AsyncSessionLocal() as session:
            data["session"] = session
            if user:
                db_user, _ = await get_or_create_user(
                    session,
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                )
                data["db_user"] = db_user

                # Block banned users
                if db_user.is_banned:
                    if isinstance(event, Message):
                        await event.answer("🚫 You are banned from this service.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("🚫 You are banned.", show_alert=True)
                    return

            result = await handler(event, data)
        return result
