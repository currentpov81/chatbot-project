from sqlalchemy.ext.asyncio import AsyncSession
from app.database.queries import get_user, update_user, get_or_create_user
from app.database.models import User


async def get_or_register(session: AsyncSession, user_id: int, username: str = None, first_name: str = None) -> tuple[User, bool]:
    return await get_or_create_user(
        session,
        user_id=user_id,
        username=username,
        first_name=first_name
    )


async def complete_onboarding(session: AsyncSession, user_id: int, gender: str, age_group: str, country: str, city: str):
    await update_user(
        session,
        user_id,
        gender=gender,
        age_group=age_group,
        country=country,
        city=city,
        is_onboarded=True
    )


async def is_banned(session: AsyncSession, user_id: int) -> bool:
    user = await get_user(session, user_id)
    return user.is_banned if user else False


async def is_onboarded(session: AsyncSession, user_id: int) -> bool:
    user = await get_user(session, user_id)
    return user.is_onboarded if user else False
