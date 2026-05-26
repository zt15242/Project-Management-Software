"""
环境配置自动刷新服务
每2小时自动刷新所有环境的登录状态，防止cookie失效
"""
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import sys
import os
import json
import subprocess


class EnvironmentRefreshService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_client = None
        self.db = None
        
    async def init_db(self):
        """初始化数据库连接"""
        if not self.db_client:
            self.db_client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.db_client[settings.DATABASE_NAME]
    
    async def auto_login_environment(self, url: str, username: str, password: str, env_name: str) -> dict:
        """
        通过subprocess调用独立的Selenium脚本进行登录
        """
        try:
            # 获取selenium_login.py脚本路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            script_path = os.path.join(parent_dir, "selenium_login.py")
            
            if not os.path.exists(script_path):
                return {
                    "success": False,
                    "cookies": [],
                    "message": f"登录脚本不存在: {script_path}"
                }
            
            # 构建命令
            cmd = [
                sys.executable,
                script_path,
                url,
                username,
                password,
                env_name
            ]
            
            # 在线程池中执行
            loop = asyncio.get_event_loop()
            
            def run_subprocess():
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        timeout=60,
                    )
                    
                    stdout = result.stdout.decode('utf-8', errors='ignore')
                    stderr = result.stderr.decode('utf-8', errors='ignore')
                    
                    if result.returncode == 0:
                        try:
                            return json.loads(stdout)
                        except json.JSONDecodeError as e:
                            return {
                                "success": False,
                                "cookies": [],
                                "message": f"解析登录结果失败: {str(e)}"
                            }
                    else:
                        return {
                            "success": False,
                            "cookies": [],
                            "message": f"登录脚本执行失败: {stderr[:500]}"
                        }
                except subprocess.TimeoutExpired:
                    return {
                        "success": False,
                        "cookies": [],
                        "message": "登录超时（60秒）"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "cookies": [],
                        "message": f"执行登录失败: {str(e)}"
                    }
            
            result = await loop.run_in_executor(None, run_subprocess)
            return result
            
        except Exception as e:
            return {
                "success": False,
                "cookies": [],
                "message": f"登录失败: {str(e)}"
            }
    
    async def refresh_environment_login(self, environment: dict):
        """刷新单个环境的登录状态"""
        from bson import ObjectId
        from utils import get_beijing_time
        
        env_id = str(environment["_id"])
        env_name = environment.get("name", "未命名环境")
        
        try:
            print(f"[环境刷新] 开始刷新环境: {env_name} (ID: {env_id})")
            
            # 执行自动登录
            result = await self.auto_login_environment(
                url=environment["url"],
                username=environment["username"],
                password=environment["password"],
                env_name=env_name
            )
            
            # 更新环境配置
            update_data = {
                "last_login_at": get_beijing_time(),
                "last_login_status": "success" if result["success"] else "failed",
                "updated_at": get_beijing_time()
            }
            
            if result["success"]:
                update_data["cookies"] = result["cookies"]
                print(f"[环境刷新] ✓ 环境 {env_name} 登录成功，已更新 {len(result['cookies'])} 个 cookie")
            else:
                print(f"[环境刷新] ✗ 环境 {env_name} 登录失败: {result.get('message', '未知错误')}")
            
            await self.db.environments.update_one(
                {"_id": ObjectId(env_id)},
                {"$set": update_data}
            )
            
        except Exception as e:
            print(f"[环境刷新] ✗ 刷新环境 {env_name} 时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def refresh_all_environments(self):
        """刷新所有激活的环境配置"""
        try:
            await self.init_db()
            
            print(f"\n{'='*60}")
            print(f"[环境刷新] 开始定时刷新任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # 查询所有激活的环境配置
            environments = await self.db.environments.find({
                "is_active": True
            }).to_list(length=None)
            
            if not environments:
                print("[环境刷新] 没有需要刷新的环境配置")
                return
            
            print(f"[环境刷新] 找到 {len(environments)} 个激活的环境配置")
            
            # 并发刷新所有环境（限制并发数为3，避免过多Selenium实例）
            max_concurrent = 3
            for i in range(0, len(environments), max_concurrent):
                batch = environments[i:i + max_concurrent]
                tasks = [self.refresh_environment_login(env) for env in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            print(f"[环境刷新] 定时刷新任务完成")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"[环境刷新] 定时任务执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """启动定时任务"""
        # 添加定时任务：每2小时执行一次
        self.scheduler.add_job(
            self.refresh_all_environments,
            trigger=IntervalTrigger(hours=2),
            id='refresh_environments',
            name='刷新环境登录状态',
            replace_existing=True,
            max_instances=1  # 同时只允许一个实例运行
        )
        
        # 启动调度器
        self.scheduler.start()
        print(f"[环境刷新] 定时任务已启动，每2小时自动刷新一次环境登录状态")
    
    def stop(self):
        """停止定时任务"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("[环境刷新] 定时任务已停止")
        
        if self.db_client:
            self.db_client.close()


# 全局单例
_refresh_service = None


def get_refresh_service() -> EnvironmentRefreshService:
    """获取环境刷新服务单例"""
    global _refresh_service
    if _refresh_service is None:
        _refresh_service = EnvironmentRefreshService()
    return _refresh_service
