"""检查v3版本的文件路径"""
from pymongo import MongoClient
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017/")
db = client["project_management"]

dep = db.deployments.find_one({"_id": ObjectId("690303969aed41e6bd0b4234")})
if dep:
    for v in dep.get("versions", []):
        if v["version"] == 3:
            print(f"v3文件路径: {v.get('file_path', 'N/A')}")
            import os
            if v.get('file_path'):
                print(f"文件存在: {os.path.exists(v['file_path'])}")
                print(f"绝对路径: {os.path.abspath(v['file_path'])}")
            break

client.close()
