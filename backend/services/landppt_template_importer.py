"""
LandPPT 模板导入器
从 LandPPT 的 template_examples 目录导入专业模板到 MongoDB
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from utils import get_beijing_time

logger = logging.getLogger(__name__)


class LandPPTTemplateImporter:
    """LandPPT 模板导入器"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.ppt_templates
    
    def get_template_examples_path(self) -> Optional[Path]:
        """获取 template_examples 目录路径"""
        # 从项目根目录查找
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "temp_landppt" / "template_examples"
        
        if not template_path.exists():
            logger.warning(f"Template examples directory not found at: {template_path}")
            return None
        
        return template_path
    
    def load_template_from_json(self, json_file_path: Path) -> Optional[Dict[str, Any]]:
        """从 JSON 文件加载模板数据"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # 移除导出信息
            if 'export_info' in template_data:
                del template_data['export_info']
            
            # 验证必要字段
            if 'template_name' not in template_data or 'html_template' not in template_data:
                logger.error(f"Invalid template JSON file: {json_file_path}")
                return None
            
            # 生成 template_id（使用文件名）
            template_id = json_file_path.stem  # 如：商务.json -> 商务
            
            # 转换为 MongoDB 文档格式
            mongo_doc = {
                "template_id": template_id,
                "template_name": template_data.get('template_name', template_id),
                "description": template_data.get('description', ''),
                "html_template": template_data.get('html_template', ''),
                "tags": template_data.get('tags', []),
                "is_default": template_data.get('is_default', False),
                "is_active": True,
                "is_builtin": True,  # 标记为内置模板
                "source": "landppt",  # 来源标记
                "created_by": "system",
                "created_at": get_beijing_time(),
                "updated_at": get_beijing_time()
            }
            
            return mongo_doc
            
        except Exception as e:
            logger.error(f"Error loading template from {json_file_path}: {e}")
            return None
    
    async def import_all_templates(self, force_reimport: bool = False) -> List[str]:
        """导入所有模板
        
        Args:
            force_reimport: 如果为 True，则重新导入已存在的模板
            
        Returns:
            导入的模板 ID 列表
        """
        template_path = self.get_template_examples_path()
        if not template_path:
            logger.warning("Template examples directory not found, skipping import")
            return []
        
        imported_ids = []
        
        try:
            # 获取所有 JSON 文件
            json_files = list(template_path.glob("*.json"))
            logger.info(f"Found {len(json_files)} template files in {template_path}")
            
            for json_file in json_files:
                logger.info(f"Processing template file: {json_file.name}")
                
                # 加载模板数据
                template_doc = self.load_template_from_json(json_file)
                if not template_doc:
                    continue
                
                # 检查模板是否已存在
                existing = await self.collection.find_one({
                    "template_id": template_doc["template_id"]
                })
                
                if existing and not force_reimport:
                    logger.info(f"Template '{template_doc['template_name']}' already exists, skipping")
                    imported_ids.append(template_doc["template_id"])
                    continue
                
                # 插入或更新模板
                try:
                    if existing:
                        # 更新现有模板
                        await self.collection.update_one(
                            {"template_id": template_doc["template_id"]},
                            {"$set": template_doc}
                        )
                        logger.info(f"Updated template '{template_doc['template_name']}'")
                    else:
                        # 插入新模板
                        await self.collection.insert_one(template_doc)
                        logger.info(f"Imported template '{template_doc['template_name']}'")
                    
                    imported_ids.append(template_doc["template_id"])
                    
                except Exception as e:
                    logger.error(f"Failed to import template '{template_doc['template_name']}': {e}")
                    continue
            
            logger.info(f"Successfully imported {len(imported_ids)} templates")
            
            # 确保有一个默认模板
            await self._ensure_default_template(imported_ids)
            
            return imported_ids
            
        except Exception as e:
            logger.error(f"Error importing templates: {e}")
            return imported_ids
    
    async def _ensure_default_template(self, imported_ids: List[str]):
        """确保有一个默认模板"""
        # 检查是否已有默认模板
        default_template = await self.collection.find_one({"is_default": True})
        
        if not default_template and imported_ids:
            # 设置"商务"为默认模板，如果不存在则设置第一个
            default_id = "商务" if "商务" in imported_ids else imported_ids[0]
            
            await self.collection.update_one(
                {"template_id": default_id},
                {"$set": {"is_default": True}}
            )
            logger.info(f"Set template '{default_id}' as default template")
    
    async def get_all_templates(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """获取所有模板"""
        query = {"is_active": True} if active_only else {}
        
        cursor = self.collection.find(query)
        templates = await cursor.to_list(length=None)
        
        # 转换 _id 为字符串
        for template in templates:
            template["id"] = str(template["_id"])
            del template["_id"]
        
        return templates
    
    async def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """根据 template_id 获取模板"""
        template = await self.collection.find_one({"template_id": template_id})
        
        if template:
            template["id"] = str(template["_id"])
            del template["_id"]
        
        return template
    
    async def get_default_template(self) -> Optional[Dict[str, Any]]:
        """获取默认模板"""
        template = await self.collection.find_one({"is_default": True})
        
        if template:
            template["id"] = str(template["_id"])
            del template["_id"]
        
        return template
    
    async def create_indexes(self):
        """创建索引"""
        await self.collection.create_index("template_id", unique=True)
        await self.collection.create_index("template_name")
        await self.collection.create_index("tags")
        await self.collection.create_index("is_default")
        logger.info("Created indexes for ppt_templates collection")


async def import_landppt_templates(db: AsyncIOMotorDatabase, force_reimport: bool = False):
    """导入 LandPPT 模板的便捷函数"""
    importer = LandPPTTemplateImporter(db)
    
    # 创建索引
    await importer.create_indexes()
    
    # 导入模板
    imported_ids = await importer.import_all_templates(force_reimport)
    
    return imported_ids


if __name__ == "__main__":
    import asyncio
    from database import get_database
    
    async def main():
        db = get_database()
        imported_ids = await import_landppt_templates(db, force_reimport=True)
        print(f"Imported {len(imported_ids)} templates: {imported_ids}")
    
    asyncio.run(main())
