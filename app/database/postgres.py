from contextlib import asynccontextmanager
from typing import Optional
import asyncpg

# 전역 풀 변수
_pool: Optional[asyncpg.Pool] = None


async def init_db(dsn: str):
    global _pool
    if _pool is None:
        pool = asyncpg.create_pool(dsn=dsn) #dsn = "postgresql://postgres:PASSWORD@localhost:5432/DATABASE_NAME"
        await pool
        _pool = pool


async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_connection():
    global _pool
    if _pool is None:
        raise RuntimeError("데이터베이스 풀이 초기화되지 않았습니다. init_db()를 먼저 호출하세요.")

    async with _pool.acquire() as connection:
        yield connection