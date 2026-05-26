
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import io

# 模拟环境设置
os.environ["DATABASE_NAME"] = "project_management"
MONGODB_URL = "mongodb://localhost:27017"

async def diagnostic():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client["project_management"]
    
    # 获取这个特定的文档
    doc_id = "6978571473db5065ee253329" # 从URL中提取的ID部分，虽然URL里路径不同，但我们查库
    # 实际上URL里的ID是知识库文档ID对应的存储路径
    # URL 路径: knowledge/6978571473db5065ee253329/5eb45dbd...docx
    # 这里 6978571473db5065ee253329 应该是项目ID或者知识库ID
    
    doc = await db.knowledge.find_one({"file_path": {"$regex": "5eb45dbd-86fd-4a27-8d23-5433aa95fff0"}})
    
    if not doc:
        print("未找到该文档记录")
        return

    print(f"找到文档: {doc['title']}")
    print(f"存储类型: {doc.get('storage_type')}")
    print(f"OSS Key: {doc.get('oss_key')}")
    print(f"内容字段预览: {str(doc.get('content'))[:100]}")
    
    # 检查OSS配置
    config = await db.system_config.find_one({"config_type": "oss"})
    print(f"OSS配置状态: {'已配置' if config else '未配置'}")
    if config:
        print(f"提供商: {config.get('provider')}")

if __name__ == "__main__":
    asyncio.run(diagnostic())
