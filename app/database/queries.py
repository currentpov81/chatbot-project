from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.database.models import User, Report


async def get_or_create_user(session: AsyncSession, user_id: int, **kwargs) -> tuple[User, bool]:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        # Update last seen
        user.last_seen = datetime.now(timezone.utc)
        if kwargs.get("username"):
            user.username = kwargs["username"]
        await session.commit()
        return user, False
    user = User(id=user_id, **kwargs)
    session.add(user)
    await session.commit()
    return user, True


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user(session: AsyncSession, user_id: int, **kwargs):
    await session.execute(
        update(User).where(User.id == user_id).values(**kwargs)
    )
    await session.commit()


async def increment_chat_count(session: AsyncSession, user_id: int):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.total_chats += 1
        await session.commit()


async def create_report(session: AsyncSession, reporter_id: int, reported_id: int, reason: str = None):
    report = Report(reporter_id=reporter_id, reported_id=reported_id, reason=reason)
    session.add(report)

    # Increment report count on reported user
    result = await session.execute(select(User).where(User.id == reported_id))
    user = result.scalar_one_or_none()
    if user:
        user.report_count += 1
        # Auto-ban at threshold
        if user.report_count >= 10:
            user.is_banned = True

    await session.commit()
