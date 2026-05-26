"""
OSS对象存储工具函数
支持阿里云OSS和腾讯云COS
配置从MongoDB动态读取
"""
import os
from config import settings
from database import get_database
import logging

logger = logging.getLogger(__name__)


async def get_oss_config():
    """从MongoDB获取OSS配置"""
    db = get_database()
    config = await db.system_config.find_one({"config_type": "oss"})
    return config if config else {}


async def upload_file_to_oss(local_file_path: str, object_name: str = None) -> str:
    """
    上传文件到OSS
    
    Args:
        local_file_path: 本地文件路径
        object_name: OSS中的对象名称,如果为None则使用文件名
    
    Returns:
        文件的公网访问URL
    """
    if not object_name:
        object_name = os.path.basename(local_file_path)
    
    # 从MongoDB获取OSS配置
    oss_config = await get_oss_config()
    provider = oss_config.get("provider")
    
    # 如果没有配置OSS,返回本地服务器URL
    if not provider:
        logger.info("未配置OSS,使用本地服务器URL")
        # 计算相对于uploads目录的路径
        relative_path = os.path.relpath(local_file_path, settings.UPLOAD_DIR)
        return f"{settings.BASE_URL}/uploads/{relative_path.replace(os.sep, '/')}"
    
    try:
        if provider == "aliyun":
            return await upload_to_aliyun_oss(local_file_path, object_name, oss_config)
        elif provider == "tencent":
            return await upload_to_tencent_cos(local_file_path, object_name, oss_config)
        else:
            logger.warning(f"不支持的OSS提供商: {provider}, 使用本地URL")
            relative_path = os.path.relpath(local_file_path, settings.UPLOAD_DIR)
            return f"{settings.BASE_URL}/uploads/{relative_path.replace(os.sep, '/')}"
    except Exception as e:
        logger.error(f"上传到OSS失败: {e}, 降级使用本地URL")
        relative_path = os.path.relpath(local_file_path, settings.UPLOAD_DIR)
        return f"{settings.BASE_URL}/uploads/{relative_path.replace(os.sep, '/')}"


async def upload_to_aliyun_oss(local_file_path: str, object_name: str, oss_config: dict) -> str:
    """上传文件到阿里云OSS"""
    import asyncio
    try:
        import oss2
    except ImportError:
        raise Exception("未安装阿里云OSS SDK, 请运行: pip install oss2")
    
    # 从配置中获取参数
    access_key_id = oss_config.get("access_key_id")
    access_key_secret = oss_config.get("access_key_secret")
    bucket_name = oss_config.get("bucket_name")
    region = oss_config.get("region")
    endpoint = oss_config.get("endpoint")
    
    # 创建认证对象
    auth = oss2.Auth(access_key_id, access_key_secret)
    
    # 创建Bucket对象
    endpoint_url = endpoint or f"https://oss-{region}.aliyuncs.com"
    bucket = oss2.Bucket(auth, endpoint_url, bucket_name)
    
    # 上传文件 (使用线程池执行同步操作)
    logger.info(f"上传文件到阿里云OSS: {object_name}")
    
    def _sync_upload():
        bucket.put_object_from_file(object_name, local_file_path)
    
    await asyncio.to_thread(_sync_upload)
    
    # 生成公网访问URL
    if endpoint:
        # 如果配置了自定义域名
        url = f"{endpoint}/{object_name}"
    else:
        # 使用默认域名
        url = f"https://{bucket_name}.oss-{region}.aliyuncs.com/{object_name}"
    
    logger.info(f"文件上传成功: {url}")
    return url


async def upload_to_tencent_cos(local_file_path: str, object_name: str, oss_config: dict) -> str:
    """上传文件到腾讯云COS"""
    import asyncio
    try:
        from qcloud_cos import CosConfig, CosS3Client
    except ImportError:
        raise Exception("未安装腾讯云COS SDK, 请运行: pip install cos-python-sdk-v5")
    
    # 从配置中获取参数
    access_key_id = oss_config.get("access_key_id")
    access_key_secret = oss_config.get("access_key_secret")
    bucket_name = oss_config.get("bucket_name")
    region = oss_config.get("region")
    endpoint = oss_config.get("endpoint")
    
    # 创建COS配置
    cos_config = CosConfig(
        Region=region,
        SecretId=access_key_id,
        SecretKey=access_key_secret
    )
    client = CosS3Client(cos_config)
    
    # 上传文件 (使用线程池执行同步操作)
    logger.info(f"上传文件到腾讯云COS: {object_name}")
    
    def _sync_upload():
        with open(local_file_path, 'rb') as fp:
            client.put_object(
                Bucket=bucket_name,
                Body=fp,
                Key=object_name
            )
            
    await asyncio.to_thread(_sync_upload)
    
    # 生成公网访问URL
    if endpoint:
        url = f"{endpoint}/{object_name}"
    else:
        url = f"https://{bucket_name}.cos.{region}.myqcloud.com/{object_name}"
    
    logger.info(f"文件上传成功: {url}")
    return url


async def delete_file_from_oss(object_name: str) -> bool:
    """
    从OSS删除文件
    
    Args:
        object_name: OSS中的对象名称
    
    Returns:
        bool: 是否删除成功
    """
    # 从MongoDB获取OSS配置
    oss_config = await get_oss_config()
    provider = oss_config.get("provider")
    
    if not provider:
        logger.info("未配置OSS, 跳过远程删除")
        return False
        
    try:
        if provider == "aliyun":
            return await delete_from_aliyun_oss(object_name, oss_config)
        elif provider == "tencent":
            return await delete_from_tencent_cos(object_name, oss_config)
        else:
            return False
    except Exception as e:
        logger.error(f"从OSS删除文件失败: {e}")
        return False


async def delete_from_aliyun_oss(object_name: str, oss_config: dict) -> bool:
    """从阿里云OSS删除文件"""
    import asyncio
    try:
        import oss2
    except ImportError:
        logger.error("未安装阿里云OSS SDK")
        return False
    
    # 从配置中获取参数
    access_key_id = oss_config.get("access_key_id")
    access_key_secret = oss_config.get("access_key_secret")
    bucket_name = oss_config.get("bucket_name")
    region = oss_config.get("region")
    endpoint = oss_config.get("endpoint")
    
    # 创建认证对象
    auth = oss2.Auth(access_key_id, access_key_secret)
    
    # 创建Bucket对象
    endpoint_url = endpoint or f"https://oss-{region}.aliyuncs.com"
    bucket = oss2.Bucket(auth, endpoint_url, bucket_name)
    
    # 删除文件
    logger.info(f"从阿里云OSS删除文件: {object_name}")
    
    def _sync_delete():
        bucket.delete_object(object_name)
    
    await asyncio.to_thread(_sync_delete)
    return True


async def delete_from_tencent_cos(object_name: str, oss_config: dict) -> bool:
    """从腾讯云COS删除文件"""
    import asyncio
    try:
        from qcloud_cos import CosConfig, CosS3Client
    except ImportError:
        logger.error("未安装腾讯云COS SDK")
        return False
    
    # 从配置中获取参数
    access_key_id = oss_config.get("access_key_id")
    access_key_secret = oss_config.get("access_key_secret")
    bucket_name = oss_config.get("bucket_name")
    region = oss_config.get("region")
    
    # 创建COS配置
    cos_config = CosConfig(
        Region=region,
        SecretId=access_key_id,
        SecretKey=access_key_secret
    )
    client = CosS3Client(cos_config)
    
    # 删除文件
    logger.info(f"从腾讯云COS删除文件: {object_name}")
    
    def _sync_delete():
        client.delete_object(
            Bucket=bucket_name,
            Key=object_name
        )
            
    await asyncio.to_thread(_sync_delete)
    return True


async def download_file_from_oss(object_name: str) -> bytes:
    """
    从OSS下载文件内容为字节流
    """
    oss_config = await get_oss_config()
    provider = oss_config.get("provider")
    
    if not provider:
        raise Exception("未配置OSS, 无法下载")
        
    try:
        if provider == "aliyun":
            return await download_from_aliyun_oss(object_name, oss_config)
        elif provider == "tencent":
            return await download_from_tencent_cos(object_name, oss_config)
        else:
            raise Exception(f"不支持的OSS提供商: {provider}")
    except Exception as e:
        logger.error(f"从OSS下载文件失败: {e}")
        raise e


async def download_from_aliyun_oss(object_name: str, oss_config: dict) -> bytes:
    """从阿里云OSS下载文件"""
    import asyncio
    import oss2
    
    auth = oss2.Auth(oss_config.get("access_key_id"), oss_config.get("access_key_secret"))
    endpoint = oss_config.get("endpoint") or f"https://oss-{oss_config.get('region')}.aliyuncs.com"
    bucket = oss2.Bucket(auth, endpoint, oss_config.get("bucket_name"))
    
    def _sync_download():
        return bucket.get_object(object_name).read()
    
    return await asyncio.to_thread(_sync_download)


async def download_from_tencent_cos(object_name: str, oss_config: dict) -> bytes:
    """从腾讯云COS下载文件"""
    import asyncio
    from qcloud_cos import CosConfig, CosS3Client
    
    cos_config = CosConfig(
        Region=oss_config.get("region"),
        SecretId=oss_config.get("access_key_id"),
        SecretKey=oss_config.get("access_key_secret")
    )
    client = CosS3Client(cos_config)
    
    def _sync_download():
        response = client.get_object(
            Bucket=oss_config.get("bucket_name"),
            Key=object_name
        )
        return response['Body'].get_stream().read()
            
    return await asyncio.to_thread(_sync_download)
