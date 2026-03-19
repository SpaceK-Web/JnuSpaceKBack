import redis.asyncio as aioredis
from app.config import settings

redis_pool: aioredis.Redis = None


async def connect_redis():
    global redis_pool
    redis_pool = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    await redis_pool.ping()
    print("✅ Redis 연결됨")


async def close_redis():
    global redis_pool
    if redis_pool:
        await redis_pool.close()
        print("❌ Redis 연결 종료")


def get_redis() -> aioredis.Redis:
    return redis_pool
