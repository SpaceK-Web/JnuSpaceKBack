import redis.asyncio as aioredis
from app.config import settings

redis_pool: aioredis.Redis = None
_redis_available: bool = False


async def connect_redis():
    """Redis 연결 (선택사항 - 없으면 메모리 버퍼 사용)"""
    global redis_pool, _redis_available
    try:
        redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_pool.ping()
        _redis_available = True
        print("✅ Redis 연결됨")
    except Exception as e:
        print(f"⚠️ Redis 연결 실패 (메모리 버퍼 사용): {e}")
        _redis_available = False


async def close_redis():
    global redis_pool
    if redis_pool:
        await redis_pool.close()
        print("❌ Redis 연결 종료")


def get_redis() -> aioredis.Redis:
    return redis_pool


def is_redis_available() -> bool:
    """Redis 사용 가능 여부"""
    return _redis_available
