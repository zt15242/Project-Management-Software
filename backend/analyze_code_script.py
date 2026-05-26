"""
独立的代码分析脚本
在单独的进程中运行，避免asyncio事件循环问题
"""
import sys
import json
import os
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient

# 添加父目录到路径以导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from models import DeploymentType
from ai_service import analyze_code_with_ai


def update_progress(db, deployment_id: str, version: int, progress: str, percentage: int = None, task_id: str = None):
    """更新分析进度"""
    update_data = {
        "versions.$.analysis_progress": progress,
        "updated_at": datetime.now()
    }
    if percentage is not None:
        update_data["versions.$.analysis_percentage"] = percentage
    
    db.deployments.update_one(
        {
            "_id": ObjectId(deployment_id),
            "versions.version": version
        },
        {"$set": update_data}
    )
    
    # 同时也更新后台任务状态
    if task_id:
        try:
            task_update = {
                "updated_at": datetime.now(),
                "status": "running"
            }
            if percentage is not None:
                task_update["progress"] = percentage
            if progress:
                task_update["current_step"] = progress
                
            db.background_tasks.update_one(
                {"_id": ObjectId(task_id)},
                {"$set": task_update}
            )
        except Exception as e:
            # 忽略后台任务更新失败，不影响主流程
            print(f"Warning: Failed to update background task: {e}", file=sys.stderr)
            
    print(f"[{deployment_id}:v{version}] 进度: {progress} ({percentage}%)" if percentage else f"[{deployment_id}:v{version}] 进度: {progress}", file=sys.stderr)


def analyze_version(deployment_id: str, version: int, file_path: str, deployment_type: str, task_id: str = None):
    """
    分析代码版本
    """
    sync_client = None
    try:
        # 连接同步数据库（用于进度更新）
        from pymongo import MongoClient
        sync_client = MongoClient(settings.MONGODB_URL)
        sync_db = sync_client[settings.DATABASE_NAME]
        
        print(f"[{deployment_id}:v{version}] 开始分析版本...", file=sys.stderr)
        update_progress(sync_db, deployment_id, version, "初始化分析", 0, task_id)
        
        # 获取上一个版本的文件路径（用于对比）
        update_progress(sync_db, deployment_id, version, "加载版本信息", 10, task_id)
        deployment = sync_db.deployments.find_one({"_id": ObjectId(deployment_id)})
        prev_version_file = None
        
        if deployment and len(deployment.get("versions", [])) > 1:
            # 找到上一个版本
            versions = sorted(deployment["versions"], key=lambda x: x["version"])
            for v in reversed(versions):
                if v["version"] < version and v.get("file_path"):
                    prev_version_file = v["file_path"]
                    break
        
        # 执行AI分析
        update_progress(sync_db, deployment_id, version, "正在分析代码", 20, task_id)
        
        # 创建独立的事件循环和异步数据库连接
        import asyncio
        from motor.motor_asyncio import AsyncIOMotorClient
        
        # Windows平台设置事件循环策略
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 创建异步数据库连接
        async_client = AsyncIOMotorClient(settings.MONGODB_URL)
        async_db = async_client[settings.DATABASE_NAME]
        
        # 临时设置全局数据库连接（供ai_service使用）
        import database
        database.database = async_db  # 设置正确的变量名
        
        try:
            ai_analysis = loop.run_until_complete(
                analyze_code_with_ai(
                    file_path,
                    DeploymentType(deployment_type),
                    str(version),
                    str(version - 1) if version > 1 else None
                )
            )
        finally:
            loop.close()
            async_client.close()
            database.database = None  # 恢复为None
        
        update_progress(sync_db, deployment_id, version, "分析完成，保存结果", 90, task_id)
        print(f"[{deployment_id}:v{version}] 分析完成，更新数据库...", file=sys.stderr)
        
        # 更新分析结果
        sync_db.deployments.update_one(
            {
                "_id": ObjectId(deployment_id),
                "versions.version": version
            },
            {
                "$set": {
                    "versions.$.status": "analysis_completed",
                    "versions.$.ai_analysis": ai_analysis.dict(),
                    "updated_at": datetime.now()
                },
                "$unset": {
                    "versions.$.analysis_progress": "",
                    "versions.$.analysis_percentage": ""
                }
            }
        )
        
        # 更新后台任务为完成状态
        if task_id:
            try:
                sync_db.background_tasks.update_one(
                    {"_id": ObjectId(task_id)},
                    {
                        "$set": {
                            "status": "completed",
                            "progress": 100,
                            "completed_at": datetime.now(),
                            "updated_at": datetime.now()
                        }
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to complete background task: {e}", file=sys.stderr)
        
        print(f"[{deployment_id}:v{version}] 分析结果已保存", file=sys.stderr)
        
        # 如果评分≥85分，自动上传到远程包
        # 用于通知的部署响应信息
        deployment_response_result = None
        
        # 如果评分≥85分，自动上传到远程包
        if ai_analysis.code_quality_score >= 85:
            print(f"[{deployment_id}:v{version}] 评分{ai_analysis.code_quality_score}≥85，开始自动上传到远程包...", file=sys.stderr)
            
            try:
                # 获取部署信息
                deployment = sync_db.deployments.find_one({"_id": ObjectId(deployment_id)})
                
                if deployment and deployment.get("environment_id") and deployment.get("package_path"):
                    # 获取环境配置
                    environment = sync_db.environments.find_one({"_id": ObjectId(deployment["environment_id"])})
                    
                    if environment:
                        import requests
                        
                        cookies = environment.get("cookies", [])
                        if cookies:
                            cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
                            base_url = environment['url'].rstrip('/')
                            
                            # 上传到远程包
                            upload_url = f"{base_url}/rest/metadata/v2.0/dx/logic/packages/actions/upload"
                            params = {"packageName": deployment["package_path"]}
                            
                            # 读取zip文件
                            with open(file_path, 'rb') as f:
                                files = {'file': (os.path.basename(file_path), f, 'application/zip')}
                                
                                # 使用requests同步请求
                                import requests
                                response = requests.post(
                                    upload_url,
                                    params=params,
                                    files=files,
                                    cookies=cookie_dict,
                                    timeout=60.0
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    deployment_response_result = result
                                    
                                    if result.get("code") == "200":
                                        print(f"[{deployment_id}:v{version}] 自动上传成功！", file=sys.stderr)
                                        
                                        # 更新状态为已部署,并保存远程接口响应
                                        sync_db.deployments.update_one(
                                            {
                                                "_id": ObjectId(deployment_id),
                                                "versions.version": version
                                            },
                                            {
                                                "$set": {
                                                    "versions.$.status": "deployed",
                                                    "versions.$.deployed_at": datetime.now(),
                                                    "versions.$.deployment_response": result,  # 保存远程接口返回的完整响应
                                                    "updated_at": datetime.now()
                                                }
                                            }
                                        )
                                    else:
                                        print(f"[{deployment_id}:v{version}] 远程API返回错误: {result.get('msg')}", file=sys.stderr)
                                else:
                                    print(f"[{deployment_id}:v{version}] 上传失败，HTTP {response.status_code}", file=sys.stderr)
                                    deployment_response_result = {"code": str(response.status_code), "msg": f"HTTP Error: {response.text}", "data": None}
                        else:
                            print(f"[{deployment_id}:v{version}] 环境未登录，跳过自动上传", file=sys.stderr)
                            deployment_response_result = {"code": "401", "msg": "Environment not logged in", "data": None}
                    else:
                        print(f"[{deployment_id}:v{version}] 环境配置不存在，跳过自动上传", file=sys.stderr)
                        deployment_response_result = {"code": "404", "msg": "Environment config not found", "data": None}
                else:
                    print(f"[{deployment_id}:v{version}] 未配置环境或包路径，跳过自动上传", file=sys.stderr)
                    deployment_response_result = {"code": "400", "msg": "Missing environment or package path", "data": None}
                    
            except Exception as upload_error:
                print(f"[{deployment_id}:v{version}] 自动上传失败: {str(upload_error)}", file=sys.stderr)
                import traceback
                traceback.print_exc()
                deployment_response_result = {"code": "500", "msg": f"Upload exception: {str(upload_error)}", "data": None}
        else:
            print(f"[{deployment_id}:v{version}] 评分{ai_analysis.code_quality_score}<85，需要审批后手动上传", file=sys.stderr)
            deployment_response_result = {
                "code": "400",
                "msg": f"AI Code Quality Score ({ai_analysis.code_quality_score}) is below threshold (85). Auto-deployment skipped.",
                "data": None
            }
            
        # 发送通知 (无论评分高低都发送)
        try:
            # 重新获取最新的deployment信息确保数据准确
            deployment = sync_db.deployments.find_one({"_id": ObjectId(deployment_id)})
            
            # 获取相关人员ID
            submitter_id = deployment.get("created_by")
            
            project = sync_db.projects.find_one({"_id": ObjectId(deployment["project_id"])})
            reviewer_id = None
            if project:
                reviewer_id = project.get("project_manager_id")
            
            # 确定接收人
            recipients = set()
            if submitter_id: recipients.add(submitter_id)
            
            # 只有当评分低于85分时，才通知审批人(项目经理)
            notification_type = "deployment_audit_info"
            title = "代码发布AI审核结果"
            
            if ai_analysis.code_quality_score < 85:
                 if reviewer_id: 
                     recipients.add(reviewer_id)
                 notification_type = "deployment_audit_warning"
                 title = "代码发布AI审核预警(低分)"
            
            # 构造消息内容
            suggestions_text = "\n".join([f"- {s}" for s in ai_analysis.suggestions[:5]]) # 只取前5条建议
            if len(ai_analysis.suggestions) > 5:
                suggestions_text += f"\n... (还有{len(ai_analysis.suggestions)-5}条)"
            
            deployment_resp_str = json.dumps(deployment_response_result, ensure_ascii=False, indent=2) if deployment_response_result else "无部署响应"
            
            message = (
                f"代码发布申请【{deployment.get('title', '未命名')}】v{version} AI评分: {ai_analysis.code_quality_score}分。\n\n"
                f"【改进建议】\n{suggestions_text}\n\n"
                f"【部署响应】\n{deployment_resp_str}"
            )
            
            # 发送通知
            notifications = []
            for uid in recipients:
                notifications.append({
                    "user_id": uid,
                    "title": title,
                    "message": message,
                    "type": notification_type,
                    "related_id": deployment_id,
                    "project_id": deployment.get("project_id"),
                    "is_read": False,
                    "created_at": datetime.now()
                })
            
            if notifications:
                sync_db.notifications.insert_many(notifications)
                print(f"[{deployment_id}:v{version}] 已向 {len(recipients)} 位用户发送审核结果通知", file=sys.stderr)
                
        except Exception as notify_error:
            print(f"[{deployment_id}:v{version}] 发送通知失败: {str(notify_error)}", file=sys.stderr)
            import traceback
            traceback.print_exc()
        
        return {
            "success": True,
            "message": "分析完成"
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"[{deployment_id}:v{version}] AI分析失败: {error_msg}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        
        # 即使分析失败，也更新状态
        if sync_client:
            try:
                sync_db = sync_client[DATABASE_NAME]
                sync_db.deployments.update_one(
                    {
                        "_id": ObjectId(deployment_id),
                        "versions.version": version
                    },
                    {
                        "$set": {
                            "versions.$.status": "pending",
                            "versions.$.analysis_progress": f"分析失败: {error_msg[:100]}",
                            "updated_at": datetime.now()
                        },
                        "$unset": {
                            "versions.$.analysis_percentage": ""
                        }
                    }
                )
                
                # 更新后台任务为失败状态
                if task_id:
                    sync_db.background_tasks.update_one(
                        {"_id": ObjectId(task_id)},
                        {
                            "$set": {
                                "status": "failed",
                                "error_message": error_msg,
                                "completed_at": datetime.now(),
                                "updated_at": datetime.now()
                            }
                        }
                    )
            except Exception as update_error:
                print(f"[{deployment_id}:v{version}] 更新失败状态错误: {str(update_error)}", file=sys.stderr)
        
        return {
            "success": False,
            "message": f"分析失败: {error_msg}"
        }
    
    finally:
        if sync_client:
            sync_client.close()


if __name__ == "__main__":
    # 从命令行参数读取配置
    # 从命令行参数读取配置
    if len(sys.argv) < 5:
        print(json.dumps({
            "success": False,
            "message": "参数错误：需要 deployment_id version file_path deployment_type [task_id]"
        }))
        sys.exit(1)
    
    deployment_id = sys.argv[1]
    version = int(sys.argv[2])
    file_path = sys.argv[3]
    deployment_type = sys.argv[4]
    task_id = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else None
    
    # 执行分析
    result = analyze_version(deployment_id, version, file_path, deployment_type, task_id)
    
    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False))
