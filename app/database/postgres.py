import json
from typing import Optional

import asyncpg

from app.config import settings

_pool: Optional[asyncpg.Pool] = None


def _parse_host_port(host_str: str) -> tuple[str, int]:
    if ":" in host_str:
        host, port = host_str.rsplit(":", 1)
        return host, int(port)
    return host_str, 5432


async def _init_connection(conn: asyncpg.Connection):
    """풀 내 모든 커넥션에 json/jsonb 코덱 등록 — Python 객체로 자동 변환."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
        format="text",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
        format="text",
    )


async def init_db():
    global _pool
    if _pool is None:
        host, port = _parse_host_port(settings.POSTGRES_HOST)
        _pool = await asyncpg.create_pool(
            host=host,
            port=port,
            user=settings.POSTGRES_USERNAME,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DATABASE,
            ssl=False,
            init=_init_connection,
        )
    await _create_tables()


async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def _create_tables():
    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          SERIAL PRIMARY KEY,
                user_id     TEXT NOT NULL,
                conversation TEXT NOT NULL,
                metadata    JSONB NOT NULL DEFAULT '{}',
                timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS extracted_entries (
                id              SERIAL PRIMARY KEY,
                user_id         TEXT NOT NULL,
                conversation_id INTEGER REFERENCES conversations(id),
                entries         JSONB NOT NULL DEFAULT '[]',
                date            TEXT NOT NULL,
                timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS daily_records (
                id          SERIAL PRIMARY KEY,
                user_id     TEXT NOT NULL,
                date        TEXT NOT NULL,
                entries     JSONB NOT NULL DEFAULT '[]',
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (user_id, date)
            );

            CREATE INDEX IF NOT EXISTS idx_conv_user      ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_entries_user   ON extracted_entries(user_id, date);
            CREATE INDEX IF NOT EXISTS idx_daily_user_date ON daily_records(user_id, date);
        """)


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB 풀이 초기화되지 않았습니다. init_db()를 먼저 호출하세요.")
    return _pool
