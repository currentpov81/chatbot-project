"""
Matching Service
================
Redis data structures used:
  - waiting_queue          → LIST of user_ids waiting for match (FIFO)
  - active_chat:{uid}      → STRING partner_id (TTL = 24h)
  - queue_joined:{uid}     → STRING timestamp (TTL = 35s, for timeout cleanup)

Matching is O(1) — just LPOP from the queue.
Supports 1M+ users with horizontal scaling (all workers share Redis).
"""

import time
from app.cache.redis_client import get_redis

QUEUE_KEY = "waiting_queue"
ACTIVE_CHAT_PREFIX = "active_chat:"
QUEUE_JOINED_PREFIX = "queue_joined:"
ACTIVE_CHAT_TTL = 86400   # 24 hours
QUEUE_JOINED_TTL = 35     # slightly more than MATCH_TIMEOUT


async def add_to_queue(user_id: int):
    """Add user to the waiting queue."""
    redis = await get_redis()
    # Remove if already in queue (prevent duplicates)
    await redis.lrem(QUEUE_KEY, 0, str(user_id))
    await redis.rpush(QUEUE_KEY, str(user_id))
    await redis.setex(f"{QUEUE_JOINED_PREFIX}{user_id}", QUEUE_JOINED_TTL, str(time.time()))


async def remove_from_queue(user_id: int):
    """Remove user from waiting queue."""
    redis = await get_redis()
    await redis.lrem(QUEUE_KEY, 0, str(user_id))
    await redis.delete(f"{QUEUE_JOINED_PREFIX}{user_id}")


async def find_match(user_id: int) -> int | None:
    """
    Try to match user_id with someone from the queue.
    Returns partner_id if matched, None otherwise.
    """
    redis = await get_redis()

    while True:
        # Pop first person from queue
        candidate = await redis.lpop(QUEUE_KEY)
        if candidate is None:
            return None  # Queue empty

        candidate_id = int(candidate)

        # Don't match with yourself
        if candidate_id == user_id:
            await redis.rpush(QUEUE_KEY, str(user_id))
            return None

        # Check candidate is still alive (not timed out)
        joined = await redis.get(f"{QUEUE_JOINED_PREFIX}{candidate_id}")
        if joined is None:
            # Candidate timed out, skip them
            continue

        # Valid match found — create session
        await redis.delete(f"{QUEUE_JOINED_PREFIX}{candidate_id}")
        await set_active_chat(user_id, candidate_id)
        return candidate_id


async def set_active_chat(user_id: int, partner_id: int):
    """Store bidirectional active chat mapping."""
    redis = await get_redis()
    await redis.setex(f"{ACTIVE_CHAT_PREFIX}{user_id}", ACTIVE_CHAT_TTL, str(partner_id))
    await redis.setex(f"{ACTIVE_CHAT_PREFIX}{partner_id}", ACTIVE_CHAT_TTL, str(user_id))


async def get_partner(user_id: int) -> int | None:
    """Get current chat partner of user."""
    redis = await get_redis()
    val = await redis.get(f"{ACTIVE_CHAT_PREFIX}{user_id}")
    return int(val) if val else None


async def end_chat(user_id: int) -> int | None:
    """End chat for both users. Returns partner_id if there was one."""
    redis = await get_redis()
    partner_id = await get_partner(user_id)
    await redis.delete(f"{ACTIVE_CHAT_PREFIX}{user_id}")
    if partner_id:
        await redis.delete(f"{ACTIVE_CHAT_PREFIX}{partner_id}")
    return partner_id


async def is_in_queue(user_id: int) -> bool:
    redis = await get_redis()
    return await redis.exists(f"{QUEUE_JOINED_PREFIX}{user_id}") > 0


async def get_queue_length() -> int:
    redis = await get_redis()
    return await redis.llen(QUEUE_KEY)
