"""
初始化 LandPPT 模板
运行此脚本将从 temp_landppt/template_examples 导入所有专业模板到 MongoDB
"""
import asyncio
import logging
from database import get_database
from services.landppt_template_importer import import_landppt_templates

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始导入 LandPPT 专业模板")
    logger.info("=" * 60)
    
    try:
        # 获取数据库连接
        from database import connect_to_mongo
        await connect_to_mongo()
        
        db = get_database()
        
        # 导入模板（force_reimport=True 强制重新导入）
        imported_ids = await import_landppt_templates(db, force_reimport=True)
        
        logger.info("=" * 60)
        logger.info(f"✅ 成功导入 {len(imported_ids)} 个模板")
        logger.info("=" * 60)
        
        # 显示导入的模板列表
        logger.info("\n导入的模板列表:")
        for i, template_id in enumerate(imported_ids, 1):
            template = await db.ppt_templates.find_one({"template_id": template_id})
            if template:
                is_default = " [默认]" if template.get("is_default") else ""
                tags = ", ".join(template.get("tags", []))
                logger.info(f"  {i}. {template['template_name']}{is_default}")
                logger.info(f"     ID: {template_id}")
                logger.info(f"     标签: {tags}")
                logger.info(f"     描述: {template.get('description', '无')[:50]}...")
                logger.info("")
        
        # 关闭数据库连接
        from database import close_mongo_connection
        await close_mongo_connection()
        
    except Exception as e:
        logger.error(f"❌ 导入失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
