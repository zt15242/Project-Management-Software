"""
测试 LandPPT 模板渲染引擎
"""
import asyncio
import logging
from services.landppt_renderer import generate_pptx_from_template_id
from database import get_database, connect_to_mongo, close_mongo_connection

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_render():
    """测试渲染功能"""
    logger.info("=" * 60)
    logger.info("开始测试 LandPPT 模板渲染引擎")
    logger.info("=" * 60)
    
    try:
        # 连接数据库
        await connect_to_mongo()
        db = get_database()
        
        # 准备测试数据
        slides_data = [
            {
                "title": "项目进展汇报",
                "content": [
                    "完成核心功能开发",
                    "用户增长200%",
                    "营收突破500万",
                    "团队扩展至50人"
                ]
            },
            {
                "title": "核心成果",
                "content": [
                    "技术架构全面升级",
                    "系统性能提升3倍",
                    "用户体验大幅优化",
                    "新增10+核心功能"
                ]
            },
            {
                "title": "市场表现",
                "content": [
                    "月活用户突破100万",
                    "日活用户增长150%",
                    "用户留存率达85%",
                    "NPS评分提升至75"
                ]
            },
            {
                "title": "下一步计划",
                "content": [
                    "扩展海外市场",
                    "产品功能迭代",
                    "团队能力建设",
                    "生态合作伙伴拓展"
                ]
            }
        ]
        
        # 测试不同模板
        test_templates = [
            ("商务", "test_business.pptx"),
            ("科技风", "test_tech.pptx"),
            ("清新风", "test_fresh.pptx")
        ]
        
        for template_id, output_file in test_templates:
            logger.info(f"\n测试模板: {template_id}")
            logger.info(f"输出文件: {output_file}")
            
            try:
                result = await generate_pptx_from_template_id(
                    template_id=template_id,
                    slides_data=slides_data,
                    output_path=f"uploads/ppt/{output_file}",
                    title="项目进展汇报",
                    db=db
                )
                
                logger.info(f"✅ 生成成功: {result}")
                
            except Exception as e:
                logger.error(f"❌ 生成失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # 关闭数据库连接
        await close_mongo_connection()
        
        logger.info("\n" + "=" * 60)
        logger.info("测试完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_render())
    exit(exit_code)
