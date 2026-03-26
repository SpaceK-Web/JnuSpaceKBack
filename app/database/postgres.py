import asyncpg
from app.config import settings

conn: asyncpg.Connection

async def connect_postgres():
    global conn
    conn = await asyncpg.connect(user=settings.POSTGRES_USERNAME, password=settings.POSTGRES_PASSWORD, database=settings.POSTGRES_DATABASE, host=settings.POSTGRES_HOST)
    print(f"✅ Postgres 연결됨: {settings.POSTGRES_DATABASE}")


async def close_postgres():
    global conn
    if conn is not None:
        await conn.close()
        print("❌ Postgres 연결 종료")


def get_connection():
    return conn
