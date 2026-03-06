from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Integer
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)          # Telegram user_id
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)

    # Onboarding
    gender = Column(String, nullable=True)             # male / female
    age_group = Column(String, nullable=True)          # e.g. "18-20"
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)

    # State
    is_onboarded = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)

    # Stats
    total_chats = Column(Integer, default=0)
    report_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id = Column(BigInteger, nullable=False)
    reported_id = Column(BigInteger, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
