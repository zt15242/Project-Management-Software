from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import os
import zipfile
import difflib

from database import get_database
from auth import get_current_active_user
from ai_service import analyze_code_with_ai
from models import (
    CodeDeploymentCreate, CodeDeploymentUpdate, CodeDeploymentResponse,
    VersionInfo, VersionResponse, VersionUpload,
    DeploymentType, DeploymentStatus, RiskLevel, AIAnalysisResult,
    DeploymentReview, UserRole, UserResponse
)
from background_task_manager import BackgroundTaskManager

router = APIRouter(prefix="/api/deployments", tags=["代码发布"])


# 后台异步分析函数（完全独立运行，不受HTTP连接影响）
async def analyze_version_async(
    deployment_id: str,
    version: int,
    file_path: str,
    deployment_type: DeploymentType
):
    """后台异步执行AI分析（完全隔离，带超时保护和进度跟踪）"""
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    from config import settings
    
    # 创建独立的数据库连接（避免共享连接池问题）
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    async def update_progress(progress: str, percentage: int = None):
        """更新分析进度"""
        update_data = {
            "versions.$.analysis_progress": progress,
            "updated_at": datetime.now()
        }
        if percentage is not None:
            update_data["versions.$.analysis_percentage"] = percentage
        
        await db.deployments.update_one(
            {
                "_id": ObjectId(deployment_id),
                "versions.version": version
            },
            {"$set": update_data}
        )
        print(f"[{deployment_id}:v{version}] 进度: {progress} ({percentage}%)" if percentage else f"[{deployment_id}:v{version}] 进度: {progress}")
    
    try:
        print(f"[{deployment_id}:v{version}] 开始分析版本...")
        await update_progress("初始化分析", 0)
        
        # 获取上一个版本的文件路径（用于对比）
        await update_progress("加载版本信息", 10)
        deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
        prev_version_file = None
        
        if deployment and len(deployment.get("versions", [])) > 1:
            # 找到上一个版本
            versions = sorted(deployment["versions"], key=lambda x: x["version"])
            for v in reversed(versions):
                if v["version"] < version and v.get("file_path"):
                    prev_version_file = v["file_path"]
                    break
        
        # 执行AI分析（带超时控制）
        await update_progress("正在分析代码", 20)
        
        ai_analysis = await asyncio.wait_for(
            analyze_code_with_ai(
                file_path,
                deployment_type,
                str(version),
                str(version - 1) if version > 1 else None
            ),
            timeout=600  # 10分钟总超时
        )
        
        await update_progress("分析完成，保存结果", 90)
        print(f"[{deployment_id}:v{version}] 分析完成，更新数据库...")
        
        # 更新分析结果
        await db.deployments.update_one(
            {
                "_id": ObjectId(deployment_id),
                "versions.version": version
            },
            {
                "$set": {
                    "versions.$.status": DeploymentStatus.ANALYSIS_COMPLETED.value,
                    "versions.$.ai_analysis": ai_analysis.dict(),
                    "updated_at": datetime.now()
                },
                "$unset": {
                    "versions.$.analysis_progress": "",
                    "versions.$.analysis_percentage": ""
                }
            }
        )
        
        print(f"[{deployment_id}:v{version}] 分析结果已保存")
        
    except asyncio.TimeoutError:
        print(f"[{deployment_id}:v{version}] AI分析超时（超过10分钟）")
        try:
            await db.deployments.update_one(
                {
                    "_id": ObjectId(deployment_id),
                    "versions.version": version
                },
                {
                    "$set": {
                        "versions.$.status": DeploymentStatus.PENDING.value,
                        "versions.$.analysis_progress": "分析超时，请重试",
                        "updated_at": datetime.now()
                    },
                    "$unset": {
                        "versions.$.analysis_percentage": ""
                    }
                }
            )
        except Exception as update_error:
            print(f"[{deployment_id}:v{version}] 更新超时状态失败: {str(update_error)}")
            
    except Exception as e:
        error_msg = str(e)
        print(f"[{deployment_id}:v{version}] AI分析失败: {error_msg}")
        import traceback
        traceback.print_exc()
        
        # 即使分析失败，也更新状态
        try:
            await db.deployments.update_one(
                {
                    "_id": ObjectId(deployment_id),
                    "versions.version": version
                },
                {
                    "$set": {
                        "versions.$.status": DeploymentStatus.PENDING.value,
                        "versions.$.analysis_progress": f"分析失败: {error_msg[:100]}",
                        "updated_at": datetime.now()
                    },
                    "$unset": {
                        "versions.$.analysis_percentage": ""
                    }
                }
            )
        except Exception as update_error:
            print(f"[{deployment_id}:v{version}] 更新失败状态出错: {str(update_error)}")
    
    finally:
        # 关闭独立的数据库连接
        client.close()


# 创建代码发布申请（包）
@router.post("/", response_model=CodeDeploymentResponse)
async def create_deployment(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    project_id: str = Form(...),
    deployment_type: DeploymentType = Form(...),
    environment_id: Optional[str] = Form(None),
    package_path: Optional[str] = Form(None),
    remote_package_id: Optional[str] = Form(None),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建代码发布申请（包），不上传文件，只创建容器"""
    
    db = get_database()
    
    # 验证项目是否存在
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 如果指定了环境配置，验证环境是否存在且属于该项目
    if environment_id:
        environment = await db.environments.find_one({
            "_id": ObjectId(environment_id),
            "project_id": project_id
        })
        if not environment:
            raise HTTPException(status_code=404, detail="环境配置不存在或不属于该项目")
    
    # 检查同名包是否存在
    existing = await db.deployments.find_one({
        "title": title,
        "project_id": project_id,
        "deployment_type": deployment_type.value
    })
    if existing:
        raise HTTPException(status_code=400, detail="同名包已存在")
    
    # 如果提供了环境配置和包路径，自动匹配或创建远程包
    if environment_id and package_path and deployment_type == DeploymentType.LOGIC_CODE:
        import httpx
        
        try:
            # 获取环境配置
            environment = await db.environments.find_one({"_id": ObjectId(environment_id)})
            if environment:
                cookies = environment.get("cookies", [])
                if cookies:
                    cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
                    base_url = environment['url'].rstrip('/')
                    
                    # 获取包列表
                    list_url = f"{base_url}/rest/metadata/v2.0/dx/logic/packages"
                    params = {"type": 0, "pageNo": 1, "pageSize": 100}
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.get(list_url, params=params, cookies=cookie_dict, timeout=30.0)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("code") == "200":
                                packages = data.get("data", {}).get("records", {}).get("codePackageList", [])
                                
                                # 查找匹配的包
                                matched_package = None
                                for pkg in packages:
                                    if pkg.get("packageTitle") == package_path:
                                        matched_package = pkg
                                        break
                                
                                if matched_package:
                                    # 找到匹配的包
                                    remote_package_id = str(matched_package.get("id"))
                                    print(f"[INFO] 匹配到现有包: {package_path}, ID: {remote_package_id}")
                                else:
                                    # 创建新包
                                    create_url = f"{base_url}/rest/metadata/v2.0/dx/logic/packages/"
                                    create_data = {
                                        "name": title,
                                        "packageName": package_path,
                                        "type": 0
                                    }
                                    
                                    create_response = await client.post(
                                        create_url,
                                        json=create_data,
                                        cookies=cookie_dict,
                                        timeout=30.0
                                    )
                                    
                                    if create_response.status_code == 200:
                                        create_result = create_response.json()
                                        if create_result.get("code") == "200":
                                            # 重新获取包列表找到新创建的包
                                            response2 = await client.get(list_url, params=params, cookies=cookie_dict, timeout=30.0)
                                            data2 = response2.json()
                                            packages2 = data2.get("data", {}).get("records", {}).get("codePackageList", [])
                                            
                                            for pkg in packages2:
                                                if pkg.get("packageTitle") == package_path:
                                                    remote_package_id = str(pkg.get("id"))
                                                    print(f"[INFO] 创建新包: {package_path}, ID: {remote_package_id}")
                                                    break
        except Exception as e:
            print(f"[WARN] 自动匹配或创建远程包失败: {str(e)}")
            # 不抛出异常，允许继续创建本地包
    
    # 创建部署记录
    deployment_data = {
        "title": title,
        "description": description,
        "project_id": project_id,
        "deployment_type": deployment_type.value,
        "current_version": 0,  # 初始版本号为0
        "versions": [],  # 版本列表为空
        "environment_id": environment_id,
        "package_path": package_path,
        "remote_package_id": remote_package_id,
        "created_by": current_user.id,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    result = await db.deployments.insert_one(deployment_data)
    deployment_id = str(result.inserted_id)
    
    return CodeDeploymentResponse(
        id=deployment_id,
        title=title,
        description=description,
        project_id=project_id,
        deployment_type=deployment_type,
        current_version=0,
        versions=[],
        environment_id=environment_id,
        package_path=package_path,
        remote_package_id=remote_package_id,
        created_by=current_user.id,
        created_at=deployment_data["created_at"],
        updated_at=deployment_data["updated_at"]
    )


# 上传新版本
@router.post("/{deployment_id}/versions", response_model=VersionResponse)
async def upload_version(
    deployment_id: str,
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """为指定的包上传新版本"""
    
    db = get_database()
    
    # 验证文件类型
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="只支持上传zip文件")
    
    # 获取部署记录
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 验证项目是否存在
    project = await db.projects.find_one({"_id": ObjectId(deployment["project_id"])})
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 计算新版本号（当前版本号 + 1）
    new_version = deployment.get("current_version", 0) + 1
    
    # 创建上传目录
    upload_dir = os.path.join("uploads", "deployments", deployment["project_id"], deployment_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{deployment['deployment_type']}_v{new_version}_{timestamp}.zip"
    file_path = os.path.join(upload_dir, safe_filename)
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            file_size = len(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    # 创建版本信息
    version_info = {
        "version": new_version,
        "description": description,
        "status": DeploymentStatus.ANALYZING.value,
        "file_path": file_path,
        "file_size": file_size,
        "uploaded_by": current_user.id,
        "uploaded_at": datetime.now()
    }
    
    # 更新部署记录：添加新版本并更新当前版本号
    await db.deployments.update_one(
        {"_id": ObjectId(deployment_id)},
        {
            "$push": {"versions": version_info},
            "$set": {
                "current_version": new_version,
                "updated_at": datetime.now()
            }
        }
    )
    
    # 启动后台任务进行AI分析（使用subprocess独立进程）
    import subprocess
    import sys
    
    # 获取脚本路径
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analyze_code_script.py")
    
    print(f"[DEBUG] 准备启动分析进程")
    print(f"[DEBUG] 脚本路径: {script_path}")
    print(f"[DEBUG] 文件存在: {os.path.exists(script_path)}")
    
    
    # 创建后台任务
    bg_manager = BackgroundTaskManager(db)
    task_name = f"代码分析: {deployment['title']} v{new_version}"
    task_id = await bg_manager.create_task(
        task_type="code_analysis",
        task_name=task_name,
        created_by=current_user.id,
        related_id=deployment_id
    )
    
    # 构建命令
    cmd = [
        sys.executable,
        script_path,
        deployment_id,
        str(new_version),
        file_path,
        deployment["deployment_type"],
        str(task_id) if task_id else ""
    ]
    
    print(f"[DEBUG] 命令: {' '.join(cmd)}")
    
    try:
        # 创建日志文件
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"analysis_{deployment_id}_v{new_version}.log")
        
        print(f"[DEBUG] 日志文件: {log_file}")
        
        # 在后台启动分析进程（输出到日志文件）
        with open(log_file, 'w', encoding='utf-8') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,  # 合并stderr到stdout
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
        print(f"[DEBUG] 分析进程已启动，PID: {process.pid}")
        print(f"[DEBUG] 查看日志: {log_file}")
    except Exception as e:
        print(f"[ERROR] 启动分析进程失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return VersionResponse(
        deployment_id=deployment_id,
        deployment_title=deployment["title"],
        version=new_version,
        description=description,
        status=DeploymentStatus.ANALYZING,
        file_path=file_path,
        file_size=file_size,
        uploaded_by=current_user.id,
        uploaded_at=version_info["uploaded_at"]
    )


# 获取代码发布列表
@router.get("/", response_model=List[CodeDeploymentResponse])
async def get_deployments(
    project_id: Optional[str] = None,
    deployment_type: Optional[DeploymentType] = None,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取代码发布申请列表"""
    
    db = get_database()
    
    query = {}
    
    if project_id:
        query["project_id"] = project_id
    
    if deployment_type:
        query["deployment_type"] = deployment_type.value
    
    deployments = await db.deployments.find(query).sort("created_at", -1).to_list(100)
    
    result = []
    for deployment in deployments:
        # 处理旧数据结构兼容
        versions_list = deployment.get("versions", [])
        
        # 如果是旧数据结构（没有versions字段），转换为新结构
        if not versions_list and "file_path" in deployment:
            # 旧数据：将整个deployment作为版本1
            version_info = {
                "version": 1,
                "description": deployment.get("description"),
                "status": deployment.get("status", DeploymentStatus.PENDING.value),
                "file_path": deployment.get("file_path"),
                "file_size": deployment.get("file_size"),
                "uploaded_by": deployment.get("created_by"),
                "uploaded_at": deployment.get("created_at"),
                "ai_analysis": deployment.get("ai_analysis"),
                "review": deployment.get("review"),
                "deployed_at": deployment.get("deployed_at")
            }
            versions_list = [version_info]
        
        # 转换版本信息
        versions = []
        for v in versions_list:
            versions.append(VersionInfo(**v))
        
        deployment_dict = {
            "id": str(deployment["_id"]),
            "title": deployment.get("title") or deployment.get("package_name", "未命名包"),
            "description": deployment.get("description"),
            "project_id": deployment["project_id"],
            "deployment_type": DeploymentType(deployment["deployment_type"]),
            "current_version": deployment.get("current_version", len(versions)),
            "versions": versions,
            "environment_id": deployment.get("environment_id"),
            "package_path": deployment.get("package_path"),
            "remote_package_id": deployment.get("remote_package_id"),
            "created_by": deployment["created_by"],
            "created_at": deployment["created_at"],
            "updated_at": deployment.get("updated_at", deployment["created_at"])
        }
        
        result.append(CodeDeploymentResponse(**deployment_dict))
    
    return result


# 获取代码发布详情
@router.get("/{deployment_id}", response_model=CodeDeploymentResponse)
async def get_deployment(
    deployment_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取代码发布申请详情（包含所有版本）"""
    
    db = get_database()
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 处理旧数据结构兼容
    versions_list = deployment.get("versions", [])
    
    # 如果是旧数据结构，转换为新结构
    if not versions_list and "file_path" in deployment:
        version_info = {
            "version": 1,
            "description": deployment.get("description"),
            "status": deployment.get("status", DeploymentStatus.PENDING.value),
            "file_path": deployment.get("file_path"),
            "file_size": deployment.get("file_size"),
            "uploaded_by": deployment.get("created_by"),
            "uploaded_at": deployment.get("created_at"),
            "ai_analysis": deployment.get("ai_analysis"),
            "review": deployment.get("review"),
            "deployed_at": deployment.get("deployed_at")
        }
        versions_list = [version_info]
    
    # 转换版本信息
    versions = []
    for v in versions_list:
        versions.append(VersionInfo(**v))
    
    deployment_dict = {
        "id": str(deployment["_id"]),
        "title": deployment.get("title") or deployment.get("package_name", "未命名包"),
        "description": deployment.get("description"),
        "project_id": deployment["project_id"],
        "deployment_type": DeploymentType(deployment["deployment_type"]),
        "current_version": deployment.get("current_version", len(versions)),
        "versions": versions,
        "environment_id": deployment.get("environment_id"),
        "package_path": deployment.get("package_path"),
        "remote_package_id": deployment.get("remote_package_id"),
        "created_by": deployment["created_by"],
        "created_at": deployment["created_at"],
        "updated_at": deployment.get("updated_at", deployment["created_at"])
    }
    
    return CodeDeploymentResponse(**deployment_dict)


# 获取特定版本详情
@router.get("/{deployment_id}/versions/{version}", response_model=VersionResponse)
async def get_version(
    deployment_id: str,
    version: int,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取特定版本的详情"""
    
    db = get_database()
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 查找指定版本
    version_info = None
    for v in deployment.get("versions", []):
        if v["version"] == version:
            version_info = v
            break
    
    if not version_info:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return VersionResponse(
        deployment_id=deployment_id,
        deployment_title=deployment.get("title", "未命名包"),
        **version_info
    )


# 更新发布申请基本信息
@router.put("/{deployment_id}", response_model=CodeDeploymentResponse)
async def update_deployment(
    deployment_id: str,
    update_data: CodeDeploymentUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新代码发布申请的基本信息（标题、描述）"""
    
    db = get_database()
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 只有创建者、项目经理或管理员可以更新
    if (deployment["created_by"] != current_user.id and
        current_user.role not in [UserRole.PROJECT_MANAGER.value, UserRole.ADMIN.value]):
        raise HTTPException(status_code=403, detail="没有权限更新此发布申请")
    
    # 构建更新数据
    update_fields = {}
    if update_data.title is not None:
        update_fields["title"] = update_data.title
    if update_data.description is not None:
        update_fields["description"] = update_data.description
    
    if update_fields:
        update_fields["updated_at"] = datetime.now()
        await db.deployments.update_one(
            {"_id": ObjectId(deployment_id)},
            {"$set": update_fields}
        )
    
    # 返回更新后的数据
    return await get_deployment(deployment_id, current_user)


# 审核特定版本
@router.post("/{deployment_id}/versions/{version}/review")
async def review_version(
    deployment_id: str,
    version: int,
    action: str = Form(...),  # approved 或 rejected
    comment: Optional[str] = Form(None),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """项目经理审核特定版本"""
    
    db = get_database()
    
    # 验证权限（只有项目经理和管理员可以审核）
    if current_user.role not in [UserRole.PROJECT_MANAGER.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="没有权限审核发布申请")
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 验证项目权限
    project = await db.projects.find_one({"_id": ObjectId(deployment["project_id"])})
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查是否是项目经理或管理员
    if (current_user.role != UserRole.ADMIN.value and 
        str(project.get("project_manager_id")) != current_user.id):
        raise HTTPException(status_code=403, detail="只有项目经理或管理员可以审核")
    
    if action not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="审核操作必须是 approved 或 rejected")
    
    # 创建审核记录
    review = DeploymentReview(
        reviewer_id=current_user.id,
        reviewer_name=current_user.full_name,
        action=action,
        comment=comment,
        reviewed_at=datetime.now()
    )
    
    # 更新状态
    new_status = DeploymentStatus.APPROVED.value if action == "approved" else DeploymentStatus.REJECTED.value
    
    await db.deployments.update_one(
        {
            "_id": ObjectId(deployment_id),
            "versions.version": version
        },
        {
            "$set": {
                "versions.$.status": new_status,
                "versions.$.review": review.dict(),
                "updated_at": datetime.now()
            }
        }
    )
    
    return {"message": f"审核完成，状态已更新为 {new_status}", "review": review.dict()}


# 部署特定版本
@router.post("/{deployment_id}/versions/{version}/deploy")
async def deploy_version(
    deployment_id: str,
    version: int,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """部署特定版本（仅项目经理和管理员）"""
    
    db = get_database()
    
    # 验证权限
    if current_user.role not in [UserRole.PROJECT_MANAGER.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="没有权限部署代码")
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 查找指定版本
    version_info = None
    for v in deployment.get("versions", []):
        if v["version"] == version:
            version_info = v
            break
    
    if not version_info:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    if version_info["status"] != DeploymentStatus.APPROVED.value:
        raise HTTPException(status_code=400, detail="只有审核通过的版本才能部署")
    
    # 验证项目权限
    project = await db.projects.find_one({"_id": ObjectId(deployment["project_id"])})
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if (current_user.role != UserRole.ADMIN.value and 
        str(project.get("project_manager_id")) != current_user.id):
        raise HTTPException(status_code=403, detail="只有项目经理或管理员可以部署")
    
    # 更新状态为部署中
    await db.deployments.update_one(
        {
            "_id": ObjectId(deployment_id),
            "versions.version": version
        },
        {
            "$set": {
                "versions.$.status": DeploymentStatus.DEPLOYING.value,
                "updated_at": datetime.now()
            }
        }
    )
    
    # 执行部署操作 - 上传到远程平台
    try:
        # 检查是否配置了环境和包路径
        if deployment.get("environment_id") and deployment.get("package_path"):
            # 获取环境配置
            environment = await db.environments.find_one({"_id": ObjectId(deployment["environment_id"])})
            
            if environment:
                cookies = environment.get("cookies", [])
                if cookies:
                    import httpx
                    
                    cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
                    base_url = environment['url'].rstrip('/')
                    
                    # 上传到远程包
                    upload_url = f"{base_url}/rest/metadata/v2.0/dx/logic/packages/actions/upload"
                    params = {"packageName": deployment["package_path"]}
                    
                    # 读取zip文件
                    file_path = version_info.get("file_path")
                    if not file_path or not os.path.exists(file_path):
                        raise HTTPException(status_code=400, detail="代码文件不存在")
                    
                    print(f"[DEPLOY] 开始上传包到远程平台: {upload_url}")
                    print(f"[DEPLOY] 包路径: {deployment['package_path']}")
                    print(f"[DEPLOY] 文件: {file_path}")
                    
                    # 第一次尝试上传（不带force参数）
                    with open(file_path, 'rb') as f:
                        files = {'file': (os.path.basename(file_path), f, 'application/zip')}
                        
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                upload_url,
                                params=params,
                                files=files,
                                cookies=cookie_dict,
                                timeout=60.0
                            )
                            
                            print(f"[DEPLOY] 响应状态码: {response.status_code}")
                            print(f"[DEPLOY] 响应内容: {response.text}")
                            
                            if response.status_code == 200:
                                result = response.json()
                                
                                # 检查是否返回 code 290052（存在已部署的类，需要强制覆盖）
                                if result.get("code") == "290052":
                                    print(f"[DEPLOY] 检测到已部署的类，准备强制覆盖上传")
                                    
                                    # 打印冲突信息
                                    data = result.get("data", {})
                                    records = data.get("records", {})
                                    batch_jobs = records.get("batchJob", [])
                                    future_tasks = records.get("futureTask", [])
                                    
                                    if batch_jobs:
                                        print(f"[DEPLOY] 冲突的 BatchJob: {len(batch_jobs)} 个")
                                        for job in batch_jobs[:3]:  # 只打印前3个
                                            print(f"  - {job.get('className', 'Unknown')}")
                                    
                                    if future_tasks:
                                        print(f"[DEPLOY] 冲突的 FutureTask: {len(future_tasks)} 个")
                                    
                                    # 重新上传，带 force=true 参数
                                    params_with_force = {**params, "force": "true"}
                                    
                                    with open(file_path, 'rb') as f2:
                                        files2 = {'file': (os.path.basename(file_path), f2, 'application/zip')}
                                        
                                        print(f"[DEPLOY] 使用 force=true 重新上传")
                                        response2 = await client.post(
                                            upload_url,
                                            params=params_with_force,
                                            files=files2,
                                            cookies=cookie_dict,
                                            timeout=60.0
                                        )
                                        
                                        print(f"[DEPLOY] 强制上传响应状态码: {response2.status_code}")
                                        print(f"[DEPLOY] 强制上传响应内容: {response2.text}")
                                        
                                        if response2.status_code == 200:
                                            result = response2.json()
                                        else:
                                            print(f"[DEPLOY] 强制上传 HTTP 错误: {response2.status_code}")
                                            raise HTTPException(status_code=400, detail=f"强制上传失败: HTTP {response2.status_code}")
                                
                                # 检查最终结果
                                if result.get("code") == "200":
                                    print(f"[DEPLOY] 远程部署成功")
                                    
                                    # 更新状态为已部署,并保存远程接口响应
                                    await db.deployments.update_one(
                                        {
                                            "_id": ObjectId(deployment_id),
                                            "versions.version": version
                                        },
                                        {
                                            "$set": {
                                                "versions.$.status": DeploymentStatus.DEPLOYED.value,
                                                "versions.$.deployed_at": datetime.now(),
                                                "versions.$.deployment_response": result,
                                                "updated_at": datetime.now()
                                            }
                                        }
                                    )
                                else:
                                    # 部署失败
                                    error_msg = result.get('msg', '未知错误')
                                    error_code = result.get('code', 'Unknown')
                                    print(f"[DEPLOY] 远程API返回错误 (code: {error_code}): {error_msg}")
                                    
                                    await db.deployments.update_one(
                                        {
                                            "_id": ObjectId(deployment_id),
                                            "versions.version": version
                                        },
                                        {
                                            "$set": {
                                                "versions.$.status": DeploymentStatus.FAILED.value,
                                                "updated_at": datetime.now()
                                            }
                                        }
                                    )
                                    raise HTTPException(status_code=400, detail=f"远程部署失败 (code: {error_code}): {error_msg}")
                            else:
                                print(f"[DEPLOY] HTTP错误: {response.status_code}")
                                raise HTTPException(status_code=400, detail=f"远程部署失败: HTTP {response.status_code}")
                                
                else:
                    print(f"[WARN] 环境未登录，无法自动上传")
                    raise HTTPException(status_code=400, detail="环境未登录，请先在环境配置中登录")
            else:
                print(f"[WARN] 环境配置不存在")
                raise HTTPException(status_code=400, detail="关联的环境配置不存在")
        else:
            print(f"[WARN] 未配置环境或包路径")
            
            # 如果是纯手动管理，也可以标记为已部署
            await db.deployments.update_one(
                {
                    "_id": ObjectId(deployment_id),
                    "versions.version": version
                },
                {
                    "$set": {
                        "versions.$.status": DeploymentStatus.DEPLOYED.value,
                        "versions.$.deployed_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                }
            )
            
    except Exception as e:
        print(f"[ERROR] 部署过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 更新状态为失败
        await db.deployments.update_one(
            {
                "_id": ObjectId(deployment_id),
                "versions.version": version
            },
            {
                "$set": {
                    "versions.$.status": DeploymentStatus.FAILED.value,
                    "updated_at": datetime.now()
                }
            }
        )
        raise HTTPException(status_code=500, detail=f"部署失败: {str(e)}")
    
    return {"message": "部署成功"}


# 获取版本文件列表
@router.get("/{deployment_id}/versions/{version}/files")
async def get_version_files(
    deployment_id: str,
    version: int,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取版本代码包中的文件列表"""
    
    db = get_database()
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 查找指定版本
    version_info = None
    for v in deployment.get("versions", []):
        if v["version"] == version:
            version_info = v
            break
    
    if not version_info:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    file_path = version_info.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="代码包文件不存在")
    
    try:
        files = []
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if not file_info.is_dir():
                    files.append({
                        "path": file_info.filename,
                        "size": file_info.file_size,
                        "last_modified": datetime(*file_info.date_time).isoformat()
                    })
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取代码包失败: {str(e)}")


# 获取版本文件内容
@router.get("/{deployment_id}/versions/{version}/files/content")
async def get_version_file_content(
    deployment_id: str,
    version: int,
    path: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取版本代码包中指定文件的内容"""
    
    db = get_database()
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 查找指定版本
    version_info = None
    for v in deployment.get("versions", []):
        if v["version"] == version:
            version_info = v
            break
    
    if not version_info:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    file_path = version_info.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="代码包文件不存在")
    
    try:
        content = ""
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # 检查文件是否存在
            if path not in zip_ref.namelist():
                raise HTTPException(status_code=404, detail="文件在代码包中不存在")
            
            with zip_ref.open(path) as f:
                # 尝试以UTF-8读取
                try:
                    content = f.read().decode('utf-8')
                except UnicodeDecodeError:
                    # 尝试其他编码
                    try:
                        content = f.read().decode('gbk')
                    except:
                        content = f"无法读取文件内容（非文本文件或编码不支持）"
        
        return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件内容失败: {str(e)}")


# AI重新审核特定版本
@router.post("/{deployment_id}/versions/{version}/reanalyze")
async def reanalyze_version(
    deployment_id: str,
    version: int,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """AI重新审核特定版本"""
    
    db = get_database()
    
    # 验证权限（项目经理和管理员可以重新审核）
    if current_user.role not in [UserRole.PROJECT_MANAGER.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="没有权限重新审核发布申请")
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 查找指定版本
    version_info = None
    for v in deployment.get("versions", []):
        if v["version"] == version:
            version_info = v
            break
    
    if not version_info:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 验证项目权限
    project = await db.projects.find_one({"_id": ObjectId(deployment["project_id"])})
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if (current_user.role != UserRole.ADMIN.value and 
        str(project.get("project_manager_id")) != current_user.id):
        raise HTTPException(status_code=403, detail="只有项目经理或管理员可以重新审核")
    
    # 检查文件是否存在
    if not version_info.get("file_path") or not os.path.exists(version_info["file_path"]):
        raise HTTPException(status_code=400, detail="代码文件不存在，无法重新分析")
    
    # 更新状态为分析中，并清除旧的分析结果
    await db.deployments.update_one(
        {
            "_id": ObjectId(deployment_id),
            "versions.version": version
        },
        {
            "$set": {
                "versions.$.status": DeploymentStatus.ANALYZING.value,
                "updated_at": datetime.now()
            },
            "$unset": {
                "versions.$.ai_analysis": ""
            }
        }
    )
    
    # 启动后台任务进行AI分析（使用subprocess独立进程）
    import subprocess
    import sys
    
    # 获取脚本路径
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analyze_code_script.py")
    
    # 构建命令
    cmd = [
        sys.executable,
        script_path,
        deployment_id,
        str(version),
        version_info["file_path"],
        deployment["deployment_type"]
    ]
    
    # 创建日志文件
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"reanalysis_{deployment_id}_v{version}.log")
    
    print(f"[DEBUG] 重新分析日志文件: {log_file}")
    
    # 在后台启动分析进程（输出到日志文件）
    with open(log_file, 'w', encoding='utf-8') as f:
        subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
    
    print(f"[DEBUG] 重新分析进程已启动")
    print(f"[DEBUG] 查看日志: {log_file}")
    
    return {"message": "已启动AI重新审核，请稍后刷新查看结果"}


# 版本对比
@router.get("/{deployment_id}/versions/{version1}/compare/{version2}")
async def compare_versions(
    deployment_id: str,
    version1: int,
    version2: int,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """对比两个版本的差异"""
    
    db = get_database()
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 查找两个版本
    v1_info = None
    v2_info = None
    
    for v in deployment.get("versions", []):
        if v["version"] == version1:
            v1_info = v
        if v["version"] == version2:
            v2_info = v
    
    if not v1_info or not v2_info:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 提取两个版本的代码文件
    file1_path = v1_info.get("file_path")
    file2_path = v2_info.get("file_path")
    
    if not file1_path or not file2_path or not os.path.exists(file1_path) or not os.path.exists(file2_path):
        raise HTTPException(status_code=400, detail="代码文件不存在")
    
    # 解压并对比文件
    try:
        extract1 = file1_path.replace('.zip', '_compare1')
        extract2 = file2_path.replace('.zip', '_compare2')
        
        os.makedirs(extract1, exist_ok=True)
        os.makedirs(extract2, exist_ok=True)
        
        with zipfile.ZipFile(file1_path, 'r') as zf:
            zf.extractall(extract1)
        with zipfile.ZipFile(file2_path, 'r') as zf:
            zf.extractall(extract2)
        
        # 收集文件列表
        files1 = set()
        files2 = set()
        
        for root, dirs, files in os.walk(extract1):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), extract1)
                files1.add(rel_path)
        
        for root, dirs, files in os.walk(extract2):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), extract2)
                files2.add(rel_path)
        
        # 对比文件
        file_diffs = []
        
        # 新增文件
        for file in files1 - files2:
            file_diffs.append({
                "file": file,
                "status": "added",
                "message": "新增文件"
            })
        
        # 删除文件
        for file in files2 - files1:
            file_diffs.append({
                "file": file,
                "status": "deleted",
                "message": "删除文件"
            })
        
        # 修改文件
        for file in files1 & files2:
            file1_full = os.path.join(extract1, file)
            file2_full = os.path.join(extract2, file)
            
            try:
                with open(file1_full, 'r', encoding='utf-8', errors='ignore') as f1, \
                     open(file2_full, 'r', encoding='utf-8', errors='ignore') as f2:
                    content1 = f1.readlines()
                    content2 = f2.readlines()
                    
                    # 生成diff
                    diff = list(difflib.unified_diff(
                        content2, content1,
                        fromfile=f"v{version2}/{file}",
                        tofile=f"v{version1}/{file}",
                        lineterm=''
                    ))
                    
                    if diff:
                        file_diffs.append({
                            "file": file,
                            "status": "modified",
                            "message": f"修改了 {len([l for l in diff if l.startswith('+') or l.startswith('-')])} 行",
                            "diff": '\n'.join(diff),
                            "additions": len([l for l in diff if l.startswith('+') and not l.startswith('+++')]),
                            "deletions": len([l for l in diff if l.startswith('-') and not l.startswith('---')])
                        })
            except Exception as e:
                print(f"对比文件 {file} 失败: {str(e)}")
        
        # 清理临时文件
        import shutil
        shutil.rmtree(extract1)
        shutil.rmtree(extract2)
        
        return {
            "version1": {
                "version": version1,
                "uploaded_at": v1_info["uploaded_at"]
            },
            "version2": {
                "version": version2,
                "uploaded_at": v2_info["uploaded_at"]
            },
            "file_diffs": file_diffs,
            "summary": {
                "total_files": len(file_diffs),
                "added": len([f for f in file_diffs if f["status"] == "added"]),
                "deleted": len([f for f in file_diffs if f["status"] == "deleted"]),
                "modified": len([f for f in file_diffs if f["status"] == "modified"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"版本对比失败: {str(e)}")


# 删除代码发布申请
@router.delete("/{deployment_id}")
async def delete_deployment(
    deployment_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除代码发布申请（包括所有版本）"""
    
    db = get_database()
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 只有创建者、项目经理或管理员可以删除
    if (deployment["created_by"] != current_user.id and
        current_user.role not in [UserRole.PROJECT_MANAGER.value, UserRole.ADMIN.value]):
        raise HTTPException(status_code=403, detail="没有权限删除此发布申请")
    
    # 删除所有版本的文件
    for version in deployment.get("versions", []):
        if version.get("file_path") and os.path.exists(version["file_path"]):
            try:
                os.remove(version["file_path"])
            except Exception as e:
                print(f"删除文件失败: {str(e)}")
    
    # 删除旧数据结构的文件
    if deployment.get("file_path") and os.path.exists(deployment["file_path"]):
        try:
            os.remove(deployment["file_path"])
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
    
    # 删除记录
    await db.deployments.delete_one({"_id": ObjectId(deployment_id)})
    
    return {"message": "发布申请已删除"}


# 删除特定版本
@router.delete("/{deployment_id}/versions/{version}")
async def delete_version(
    deployment_id: str,
    version: int,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除特定版本"""
    
    db = get_database()
    
    deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    
    if not deployment:
        raise HTTPException(status_code=404, detail="发布申请不存在")
    
    # 只有创建者、项目经理或管理员可以删除
    if (deployment["created_by"] != current_user.id and
        current_user.role not in [UserRole.PROJECT_MANAGER.value, UserRole.ADMIN.value]):
        raise HTTPException(status_code=403, detail="没有权限删除此版本")
    
    # 查找版本
    version_info = None
    for v in deployment.get("versions", []):
        if v["version"] == version:
            version_info = v
            break
    
    if not version_info:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 删除文件
    if version_info.get("file_path") and os.path.exists(version_info["file_path"]):
        try:
            os.remove(version_info["file_path"])
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
    
    # 从数组中移除版本
    await db.deployments.update_one(
        {"_id": ObjectId(deployment_id)},
        {
            "$pull": {"versions": {"version": version}},
            "$set": {"updated_at": datetime.now()}
        }
    )
    
    # 如果删除的是最新版本，需要更新current_version
    if version == deployment.get("current_version"):
        updated_deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
        remaining_versions = updated_deployment.get("versions", [])
        if remaining_versions:
            max_version = max(v["version"] for v in remaining_versions)
            await db.deployments.update_one(
                {"_id": ObjectId(deployment_id)},
                {"$set": {"current_version": max_version}}
            )
        else:
            await db.deployments.update_one(
                {"_id": ObjectId(deployment_id)},
                {"$set": {"current_version": 0}}
            )
    
    return {"message": "版本已删除"}


# 获取远程包列表
@router.get("/remote-packages/{environment_id}")
async def get_remote_packages(
    environment_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """从远程平台获取包列表"""
    import httpx
    
    db = get_database()
    
    # 获取环境配置
    environment = await db.environments.find_one({"_id": ObjectId(environment_id)})
    if not environment:
        raise HTTPException(status_code=404, detail="环境配置不存在")
    
    # 检查是否有有效的cookies
    cookies = environment.get("cookies", [])
    if not cookies:
        raise HTTPException(status_code=400, detail="环境未登录，请先登录获取cookie")
    
    # 构建cookie字典
    cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
    
    # 调试：打印cookie信息
    print(f"[DEBUG] 环境ID: {environment_id}")
    print(f"[DEBUG] 环境名称: {environment.get('name')}")
    print(f"[DEBUG] Cookie数量: {len(cookies)}")
    print(f"[DEBUG] Cookie名称: {list(cookie_dict.keys())}")
    print(f"[DEBUG] Cookie详情:")
    for name, value in cookie_dict.items():
        print(f"  {name}: {value[:50]}..." if len(value) > 50 else f"  {name}: {value}")
    
    # 请求远程API（确保URL没有双斜杠）
    base_url = environment['url'].rstrip('/')
    url = f"{base_url}/rest/metadata/v2.0/dx/logic/packages"
    params = {"type": 0, "pageNo": 1, "pageSize": 100}
    
    print(f"[DEBUG] 请求URL: {url}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, cookies=cookie_dict, timeout=30.0)
            
            # 检查401错误（cookie过期）
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401, 
                    detail="Cookie已过期或无效，请重新登录环境获取最新cookie"
                )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "200":
                raise HTTPException(status_code=400, detail=f"远程API返回错误: {data.get('msg')}")
            
            # 提取包列表
            packages = data.get("data", {}).get("records", {}).get("codePackageList", [])
            
            # 格式化返回数据
            result = []
            for pkg in packages:
                result.append({
                    "id": str(pkg.get("id")),
                    "packageTitle": pkg.get("packageTitle"),
                    "codePackageName": pkg.get("codePackageName"),
                    "version": pkg.get("version"),
                    "createdAt": pkg.get("createdAt"),
                    "updatedAt": pkg.get("updatedAt")
                })
            
            return {"packages": result}
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Cookie已过期或无效，请重新登录环境获取最新cookie"
            )
        raise HTTPException(status_code=500, detail=f"请求远程API失败: {str(e)}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"请求远程API失败: {str(e)}")


# 匹配或创建远程包
@router.post("/match-or-create-package/{environment_id}")
async def match_or_create_package(
    environment_id: str,
    package_path: str = Form(...),
    package_name: str = Form(...),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """匹配远程包或创建新包"""
    import httpx
    
    db = get_database()
    
    # 获取环境配置
    environment = await db.environments.find_one({"_id": ObjectId(environment_id)})
    if not environment:
        raise HTTPException(status_code=404, detail="环境配置不存在")
    
    # 检查是否有有效的cookies
    cookies = environment.get("cookies", [])
    if not cookies:
        raise HTTPException(status_code=400, detail="环境未登录，请先登录获取cookie")
    
    # 构建cookie字典
    cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
    
    try:
        async with httpx.AsyncClient() as client:
            # 1. 先获取所有包（确保URL没有双斜杠）
            base_url = environment['url'].rstrip('/')
            list_url = f"{base_url}/rest/metadata/v2.0/dx/logic/packages"
            params = {"type": 0, "pageNo": 1, "pageSize": 100}
            
            response = await client.get(list_url, params=params, cookies=cookie_dict, timeout=30.0)
            
            # 检查401错误（cookie过期）
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Cookie已过期或无效，请重新登录环境获取最新cookie"
                )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "200":
                raise HTTPException(status_code=400, detail=f"获取包列表失败: {data.get('msg')}")
            
            # 2. 查找匹配的包
            packages = data.get("data", {}).get("records", {}).get("codePackageList", [])
            matched_package = None
            
            for pkg in packages:
                if pkg.get("packageTitle") == package_path:
                    matched_package = pkg
                    break
            
            # 3. 如果找到匹配的包，返回包ID
            if matched_package:
                return {
                    "matched": True,
                    "package_id": str(matched_package.get("id")),
                    "package_title": matched_package.get("packageTitle"),
                    "package_name": matched_package.get("codePackageName")
                }
            
            # 4. 如果没有找到，创建新包
            create_url = f"{base_url}/rest/metadata/v2.0/dx/logic/packages/"
            create_data = {
                "name": package_name,
                "packageName": package_path,
                "type": 0
            }
            
            create_response = await client.post(
                create_url,
                json=create_data,
                cookies=cookie_dict,
                timeout=30.0
            )
            
            # 检查401错误
            if create_response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Cookie已过期或无效，请重新登录环境获取最新cookie"
                )
            
            create_response.raise_for_status()
            create_result = create_response.json()
            
            if create_result.get("code") != "200":
                raise HTTPException(status_code=400, detail=f"创建包失败: {create_result.get('msg')}")
            
            # 创建成功后，再次获取包列表找到新创建的包ID
            response2 = await client.get(list_url, params=params, cookies=cookie_dict, timeout=30.0)
            data2 = response2.json()
            packages2 = data2.get("data", {}).get("records", {}).get("codePackageList", [])
            
            new_package = None
            for pkg in packages2:
                if pkg.get("packageTitle") == package_path:
                    new_package = pkg
                    break
            
            if new_package:
                return {
                    "matched": False,
                    "created": True,
                    "package_id": str(new_package.get("id")),
                    "package_title": new_package.get("packageTitle"),
                    "package_name": new_package.get("codePackageName")
                }
            else:
                raise HTTPException(status_code=500, detail="创建包成功但无法获取包ID")
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Cookie已过期或无效，请重新登录环境获取最新cookie"
            )
        raise HTTPException(status_code=500, detail=f"请求远程API失败: {str(e)}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"请求远程API失败: {str(e)}")
