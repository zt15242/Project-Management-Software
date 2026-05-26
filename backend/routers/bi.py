from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_database
from models import (
    DataSourceCreate, DataSourceUpdate, DataSourceResponse,
    DataObjectResponse,
    ReportCreate, ReportUpdate, ReportResponse,
    DashboardCreate, DashboardUpdate, DashboardResponse,
    UserResponse, UserRole
)
from auth import get_current_active_user
from bson import ObjectId
from utils import get_beijing_time
from config import settings

router = APIRouter(prefix="/api/bi", tags=["BI商业智能"])


def check_bi_permission(current_user: UserResponse, project: dict):
    """检查BI权限：管理员、项目所有者或项目经理"""
    is_admin = current_user.role == UserRole.ADMIN
    is_owner = current_user.id == project["owner_id"]
    is_pm = current_user.id == project.get("project_manager_id")
    
    if not (is_admin or is_owner or is_pm):
        raise HTTPException(
            status_code=403,
            detail="没有权限，只有管理员、项目所有者或项目经理可以管理BI"
        )


# ==================== 系统配置 ====================

@router.get("/config/datasource-types")
async def get_enabled_datasource_types(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取系统启用的数据源类型"""
    datasource_types = {
        "mysql": {"value": "mysql", "label": "MySQL"},
        "postgresql": {"value": "postgresql", "label": "PostgreSQL"},
        "mongodb": {"value": "mongodb", "label": "MongoDB"},
        "api": {"value": "api", "label": "API接口"},
        "csv": {"value": "csv", "label": "CSV文件"}
    }
    
    # 只返回系统配置中启用的数据源类型
    enabled_types = [
        datasource_types[ds_type] 
        for ds_type in settings.ENABLED_DATASOURCES 
        if ds_type in datasource_types
    ]
    
    return {"enabled_types": enabled_types}


# ==================== 数据源管理 ====================

@router.post("/datasources", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_datasource(
    datasource: DataSourceCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建数据源"""
    db = get_database()
    
    # 检查项目是否存在
    try:
        project = await db.projects.find_one({"_id": ObjectId(datasource.project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限
    check_bi_permission(current_user, project)
    
    # 如果是MongoDB且使用系统配置，自动填充系统配置信息
    config = datasource.config
    if datasource.type == "mongodb" and config.get("use_system") == True:
        # 使用系统MongoDB配置
        config = {
            "use_system": True,
            "url": settings.MONGODB_URL,
            "database": settings.DATABASE_NAME
        }
    
    datasource_dict = {
        "name": datasource.name,
        "project_id": datasource.project_id,
        "type": datasource.type,
        "config": config,
        "description": datasource.description,
        "created_by": current_user.id,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.datasources.insert_one(datasource_dict)
    created = await db.datasources.find_one({"_id": result.inserted_id})
    
    return DataSourceResponse(
        id=str(created["_id"]),
        name=created["name"],
        project_id=created["project_id"],
        type=created["type"],
        config=created["config"],
        description=created.get("description"),
        created_by=created["created_by"],
        created_at=created["created_at"],
        updated_at=created["updated_at"]
    )


@router.get("/datasources", response_model=List[DataSourceResponse])
async def get_datasources(
    project_id: str = None,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取数据源列表"""
    db = get_database()
    
    query = {}
    if project_id:
        query["project_id"] = project_id
    
    datasources = await db.datasources.find(query).to_list(length=None)
    
    return [
        DataSourceResponse(
            id=str(ds["_id"]),
            name=ds["name"],
            project_id=ds["project_id"],
            type=ds["type"],
            config=ds["config"],
            description=ds.get("description"),
            created_by=ds["created_by"],
            created_at=ds["created_at"],
            updated_at=ds["updated_at"]
        )
        for ds in datasources
    ]


@router.get("/datasources/{datasource_id}", response_model=DataSourceResponse)
async def get_datasource(
    datasource_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定数据源"""
    db = get_database()
    
    try:
        datasource = await db.datasources.find_one({"_id": ObjectId(datasource_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的数据源ID")
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    return DataSourceResponse(
        id=str(datasource["_id"]),
        name=datasource["name"],
        project_id=datasource["project_id"],
        type=datasource["type"],
        config=datasource["config"],
        description=datasource.get("description"),
        created_by=datasource["created_by"],
        created_at=datasource["created_at"],
        updated_at=datasource["updated_at"]
    )


@router.put("/datasources/{datasource_id}", response_model=DataSourceResponse)
async def update_datasource(
    datasource_id: str,
    datasource_update: DataSourceUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新数据源"""
    db = get_database()
    
    try:
        datasource = await db.datasources.find_one({"_id": ObjectId(datasource_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的数据源ID")
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(datasource["project_id"])})
    check_bi_permission(current_user, project)
    
    update_data = {k: v for k, v in datasource_update.dict(exclude_unset=True).items() if v is not None}
    
    # 如果更新的是MongoDB类型且使用系统配置，自动填充系统配置信息
    if "config" in update_data and datasource.get("type") == "mongodb":
        config = update_data["config"]
        if config and config.get("use_system") == True:
            update_data["config"] = {
                "use_system": True,
                "url": settings.MONGODB_URL,
                "database": settings.DATABASE_NAME
            }
    
    update_data["updated_at"] = get_beijing_time()
    
    await db.datasources.update_one(
        {"_id": ObjectId(datasource_id)},
        {"$set": update_data}
    )
    
    updated = await db.datasources.find_one({"_id": ObjectId(datasource_id)})
    
    return DataSourceResponse(
        id=str(updated["_id"]),
        name=updated["name"],
        project_id=updated["project_id"],
        type=updated["type"],
        config=updated["config"],
        description=updated.get("description"),
        created_by=updated["created_by"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"]
    )


@router.delete("/datasources/{datasource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datasource(
    datasource_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除数据源"""
    db = get_database()
    
    try:
        datasource = await db.datasources.find_one({"_id": ObjectId(datasource_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的数据源ID")
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(datasource["project_id"])})
    check_bi_permission(current_user, project)
    
    # 检查是否有报表在使用此数据源
    reports_count = await db.reports.count_documents({"datasource_id": datasource_id})
    if reports_count > 0:
        raise HTTPException(status_code=400, detail=f"无法删除，有{reports_count}个报表正在使用此数据源")
    
    await db.datasources.delete_one({"_id": ObjectId(datasource_id)})
    return None


@router.get("/datasources/{datasource_id}/objects", response_model=List[DataObjectResponse])
async def get_datasource_objects(
    datasource_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取数据源中的对象（表/集合）和字段"""
    db = get_database()
    
    try:
        datasource = await db.datasources.find_one({"_id": ObjectId(datasource_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的数据源ID")
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # 根据数据源类型获取对象列表
    if datasource["type"] == "mongodb":
        # 获取MongoDB集合列表和字段
        mongo_db = db.client[datasource["config"].get("database", settings.DATABASE_NAME)]
        collections = await mongo_db.list_collection_names()
        
        objects = []
        for coll_name in collections:
            # 获取一个示例文档来推断字段结构
            sample_doc = await mongo_db[coll_name].find_one()
            fields = []
            if sample_doc:
                for key, value in sample_doc.items():
                    field_type = type(value).__name__
                    fields.append({
                        "name": key,
                        "type": field_type,
                        "label": key
                    })
            
            objects.append(DataObjectResponse(
                name=coll_name,
                type="collection",
                fields=fields
            ))
        
        return objects
    
    # 其他数据源类型返回空列表或实现相应逻辑
    return []


@router.post("/datasources/{datasource_id}/preview")
async def preview_datasource_data(
    datasource_id: str,
    request_data: dict,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """预览数据源数据"""
    db = get_database()
    
    try:
        datasource = await db.datasources.find_one({"_id": ObjectId(datasource_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的数据源ID")
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    object_name = request_data.get("object_name")
    fields = request_data.get("fields", [])
    limit = request_data.get("limit", 20)
    
    if not object_name:
        raise HTTPException(status_code=400, detail="缺少对象名称")
    
    # 根据数据源类型查询数据
    if datasource["type"] == "mongodb":
        # 获取MongoDB数据库
        mongo_db = db.client[datasource["config"].get("database", settings.DATABASE_NAME)]
        collection = mongo_db[object_name]
        
        # 构建投影
        projection = {"_id": 0}  # 默认不返回_id
        if fields:
            for field in fields:
                projection[field] = 1
        
        # 查询数据
        cursor = collection.find({}, projection).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        # 转换ObjectId为字符串
        for doc in documents:
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    doc[key] = str(value)
        
        return {
            "data": documents,
            "total": len(documents)
        }
    
    # 其他数据源类型
    return {"data": [], "total": 0}


# ==================== 报表管理 ====================

@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report: ReportCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建报表"""
    db = get_database()
    
    # 检查项目是否存在
    try:
        project = await db.projects.find_one({"_id": ObjectId(report.project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限
    check_bi_permission(current_user, project)
    
    # 检查数据源是否存在
    try:
        datasource = await db.datasources.find_one({"_id": ObjectId(report.datasource_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的数据源ID")
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    report_dict = {
        "name": report.name,
        "project_id": report.project_id,
        "datasource_id": report.datasource_id,
        "object_name": report.object_name,
        "fields": report.fields,
        "chart_type": report.chart_type,
        "chart_config": report.chart_config,
        "filter_config": report.filter_config,
        "description": report.description,
        "created_by": current_user.id,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.reports.insert_one(report_dict)
    created = await db.reports.find_one({"_id": result.inserted_id})
    
    return ReportResponse(
        id=str(created["_id"]),
        name=created["name"],
        project_id=created["project_id"],
        datasource_id=created["datasource_id"],
        object_name=created["object_name"],
        fields=created["fields"],
        chart_type=created["chart_type"],
        chart_config=created["chart_config"],
        filter_config=created.get("filter_config"),
        description=created.get("description"),
        created_by=created["created_by"],
        created_at=created["created_at"],
        updated_at=created["updated_at"]
    )


@router.get("/reports", response_model=List[ReportResponse])
async def get_reports(
    project_id: str = None,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取报表列表"""
    db = get_database()
    
    query = {}
    if project_id:
        query["project_id"] = project_id
    
    reports = await db.reports.find(query).to_list(length=None)
    
    return [
        ReportResponse(
            id=str(r["_id"]),
            name=r["name"],
            project_id=r["project_id"],
            datasource_id=r["datasource_id"],
            object_name=r.get("object_name", ""),
            fields=r.get("fields", []),
            chart_type=r["chart_type"],
            chart_config=r["chart_config"],
            filter_config=r.get("filter_config"),
            description=r.get("description"),
            created_by=r["created_by"],
            created_at=r["created_at"],
            updated_at=r["updated_at"]
        )
        for r in reports
    ]


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定报表"""
    db = get_database()
    
    try:
        report = await db.reports.find_one({"_id": ObjectId(report_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的报表ID")
    
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    return ReportResponse(
        id=str(report["_id"]),
        name=report["name"],
        project_id=report["project_id"],
        datasource_id=report["datasource_id"],
        object_name=report.get("object_name", ""),
        fields=report.get("fields", []),
        chart_type=report["chart_type"],
        chart_config=report["chart_config"],
        filter_config=report.get("filter_config"),
        description=report.get("description"),
        created_by=report["created_by"],
        created_at=report["created_at"],
        updated_at=report["updated_at"]
    )


@router.post("/reports/{report_id}/execute")
async def execute_report(
    report_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """执行报表查询并返回数据"""
    db = get_database()
    
    try:
        report = await db.reports.find_one({"_id": ObjectId(report_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的报表ID")
    
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    # 这里简化处理，返回模拟数据
    # 实际应用中需要根据数据源类型执行真实的查询
    return {
        "report_id": report_id,
        "data": [
            {"date": "2025-01", "value": 120},
            {"date": "2025-02", "value": 150},
            {"date": "2025-03", "value": 180},
            {"date": "2025-04", "value": 200},
            {"date": "2025-05", "value": 230}
        ],
        "columns": ["date", "value"],
        "total_rows": 5
    }


@router.put("/reports/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    report_update: ReportUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新报表"""
    db = get_database()
    
    try:
        report = await db.reports.find_one({"_id": ObjectId(report_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的报表ID")
    
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(report["project_id"])})
    check_bi_permission(current_user, project)
    
    update_data = {k: v for k, v in report_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = get_beijing_time()
    
    await db.reports.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": update_data}
    )
    
    updated = await db.reports.find_one({"_id": ObjectId(report_id)})
    
    return ReportResponse(
        id=str(updated["_id"]),
        name=updated["name"],
        project_id=updated["project_id"],
        datasource_id=updated["datasource_id"],
        object_name=updated.get("object_name", ""),
        fields=updated.get("fields", []),
        chart_type=updated["chart_type"],
        chart_config=updated["chart_config"],
        filter_config=updated.get("filter_config"),
        description=updated.get("description"),
        created_by=updated["created_by"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"]
    )


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除报表"""
    db = get_database()
    
    try:
        report = await db.reports.find_one({"_id": ObjectId(report_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的报表ID")
    
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(report["project_id"])})
    check_bi_permission(current_user, project)
    
    await db.reports.delete_one({"_id": ObjectId(report_id)})
    return None


# ==================== 仪表板管理 ====================

@router.post("/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard: DashboardCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建仪表板"""
    db = get_database()
    
    # 检查项目是否存在
    try:
        project = await db.projects.find_one({"_id": ObjectId(dashboard.project_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限
    check_bi_permission(current_user, project)
    
    dashboard_dict = {
        "name": dashboard.name,
        "project_id": dashboard.project_id,
        "report_ids": dashboard.report_ids,
        "layout": dashboard.layout,
        "description": dashboard.description,
        "created_by": current_user.id,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    
    result = await db.dashboards.insert_one(dashboard_dict)
    created = await db.dashboards.find_one({"_id": result.inserted_id})
    
    return DashboardResponse(
        id=str(created["_id"]),
        name=created["name"],
        project_id=created["project_id"],
        report_ids=created["report_ids"],
        layout=created["layout"],
        description=created.get("description"),
        created_by=created["created_by"],
        created_at=created["created_at"],
        updated_at=created["updated_at"]
    )


@router.get("/dashboards", response_model=List[DashboardResponse])
async def get_dashboards(
    project_id: str = None,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取仪表板列表"""
    db = get_database()
    
    query = {}
    if project_id:
        query["project_id"] = project_id
    
    dashboards = await db.dashboards.find(query).to_list(length=None)
    
    return [
        DashboardResponse(
            id=str(d["_id"]),
            name=d["name"],
            project_id=d["project_id"],
            report_ids=d["report_ids"],
            layout=d["layout"],
            description=d.get("description"),
            created_by=d["created_by"],
            created_at=d["created_at"],
            updated_at=d["updated_at"]
        )
        for d in dashboards
    ]


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取指定仪表板"""
    db = get_database()
    
    try:
        dashboard = await db.dashboards.find_one({"_id": ObjectId(dashboard_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的仪表板ID")
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="仪表板不存在")
    
    return DashboardResponse(
        id=str(dashboard["_id"]),
        name=dashboard["name"],
        project_id=dashboard["project_id"],
        report_ids=dashboard["report_ids"],
        layout=dashboard["layout"],
        description=dashboard.get("description"),
        created_by=dashboard["created_by"],
        created_at=dashboard["created_at"],
        updated_at=dashboard["updated_at"]
    )


@router.put("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: str,
    dashboard_update: DashboardUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新仪表板"""
    db = get_database()
    
    try:
        dashboard = await db.dashboards.find_one({"_id": ObjectId(dashboard_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的仪表板ID")
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="仪表板不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(dashboard["project_id"])})
    check_bi_permission(current_user, project)
    
    update_data = {k: v for k, v in dashboard_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = get_beijing_time()
    
    await db.dashboards.update_one(
        {"_id": ObjectId(dashboard_id)},
        {"$set": update_data}
    )
    
    updated = await db.dashboards.find_one({"_id": ObjectId(dashboard_id)})
    
    return DashboardResponse(
        id=str(updated["_id"]),
        name=updated["name"],
        project_id=updated["project_id"],
        report_ids=updated["report_ids"],
        layout=updated["layout"],
        description=updated.get("description"),
        created_by=updated["created_by"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"]
    )


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除仪表板"""
    db = get_database()
    
    try:
        dashboard = await db.dashboards.find_one({"_id": ObjectId(dashboard_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的仪表板ID")
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="仪表板不存在")
    
    # 检查权限
    project = await db.projects.find_one({"_id": ObjectId(dashboard["project_id"])})
    check_bi_permission(current_user, project)
    
    await db.dashboards.delete_one({"_id": ObjectId(dashboard_id)})
    return None

