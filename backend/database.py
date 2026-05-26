from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = None
database = None


async def connect_to_mongo():
    global client, database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    print(f"连接到MongoDB数据库: {settings.DATABASE_NAME}")


async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("关闭MongoDB连接")


def get_database():
    return database

