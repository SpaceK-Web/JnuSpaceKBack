import aiomysql
from app.config import settings

conn: aiomysql.Connection
cursor: aiomysql.Cursor

async def connect_mysql(loop):
    global conn, cursor
    conn = await aiomysql.connect(
        host="127.0.0.1", port="3306",
        user="root", password="",
        db="spacek", autocommit=False,
        loop=loop
    )
    cursor = await conn.cursor()

async def close_mysql(conn):
    global cursor
    await cursor.close()
    conn.close()

async def get_conn() -> aiomysql.Connection:
    return conn

async def get_cursor() -> aiomysql.Cursor:
    return cursor