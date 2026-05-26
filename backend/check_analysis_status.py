"""
快速检查代码分析状态的脚本
"""
from pymongo import MongoClient
from bson import ObjectId
import sys

# 连接数据库
client = MongoClient("mongodb://localhost:27017/")
db = client["project_management"]

# 获取所有部署记录
deployments = db.deployments.find().sort("created_at", -1).limit(5)

print("最近5个部署记录的状态：\n")
print("=" * 100)

for dep in deployments:
    print(f"\n包名称: {dep.get('title', 'N/A')}")
    print(f"ID: {dep['_id']}")
    print(f"类型: {dep.get('deployment_type', 'N/A')}")
    print(f"当前版本: {dep.get('current_version', 0)}")
    
    versions = dep.get('versions', [])
    if versions:
        print(f"\n版本列表 ({len(versions)}个):")
        for v in versions:
            print(f"  - v{v['version']}: {v.get('status', 'N/A')}")
            if v.get('analysis_progress'):
                print(f"    进度: {v['analysis_progress']}")
            if v.get('analysis_percentage') is not None:
                print(f"    百分比: {v['analysis_percentage']}%")
            if v.get('ai_analysis'):
                print(f"    AI分析: 已完成")
    else:
        print("  无版本")
    
    print("-" * 100)

client.close()
