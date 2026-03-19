from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient = None
db = None


async def connect_mongodb():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    print(f"✅ MongoDB 연결됨: {settings.MONGODB_DB_NAME}")


async def close_mongodb():
    global client
    if client:
        client.close()
        print("❌ MongoDB 연결 종료")


def get_db():
    return db
