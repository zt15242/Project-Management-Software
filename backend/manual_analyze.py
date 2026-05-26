"""
手动触发分析脚本，用于调试
"""
import sys
from analyze_code_script import analyze_version

if __name__ == "__main__":
    # 测试3的ID
    deployment_id = "6943a99a66ebf6297fbc427d"
    version = 1
    
    # 从数据库获取文件路径
    from pymongo import MongoClient
    from bson import ObjectId
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client['project_management']
    
    deployment = db.deployments.find_one({"_id": ObjectId(deployment_id)})
    if deployment:
        versions = deployment.get("versions", [])
        for v in versions:
            if v["version"] == version:
                file_path = v.get("file_path")
                deployment_type = deployment.get("deployment_type")
                
                print(f"开始分析:")
                print(f"  部署ID: {deployment_id}")
                print(f"  版本: {version}")
                print(f"  文件: {file_path}")
                print(f"  类型: {deployment_type}")
                print("-" * 50)
                
                result = analyze_version(deployment_id, version, file_path, deployment_type)
                print("-" * 50)
                print(f"结果: {result}")
                break
    else:
        print("未找到部署记录")
