"""
独立的Playwright登录脚本
在单独的进程中运行，避免asyncio事件循环冲突
"""
import sys
import json
import os
import time

# 设置环境变量，强制使用同步模式
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '0'

# Windows平台设置事件循环策略
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from playwright.sync_api import sync_playwright


def auto_login(url: str, username: str, password: str, env_name: str) -> dict:
    """
    自动登录并获取cookies
    """
    try:
        with sync_playwright() as p:
            # 启动无头浏览器
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # 访问登录页面
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 等待页面加载
            time.sleep(2)
            
            # 尝试查找并填写用户名
            username_selectors = [
                'input[name="username"]',
                'input[type="text"]',
                'input[placeholder*="用户名"]',
                'input[placeholder*="账号"]',
                'input[id="username"]',
                'input[id="account"]'
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.fill(selector, username)
                        username_filled = True
                        break
                except:
                    continue
            
            if not username_filled:
                browser.close()
                return {
                    "success": False,
                    "cookies": [],
                    "message": "无法找到用户名输入框"
                }
            
            # 尝试查找并填写密码
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[id="password"]',
                'input[id="passwd"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.fill(selector, password)
                        password_filled = True
                        break
                except:
                    continue
            
            if not password_filled:
                browser.close()
                return {
                    "success": False,
                    "cookies": [],
                    "message": "无法找到密码输入框"
                }
            
            # 查找并点击登录按钮
            login_button_selectors = [
                'button[type="submit"]',
                'button:has-text("登录")',
                'button:has-text("Login")',
                'input[type="submit"]',
                'a:has-text("登录")',
                '.login-button',
                'button.login-button',
                '#login-button'
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.click(selector)
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                browser.close()
                return {
                    "success": False,
                    "cookies": [],
                    "message": "无法找到登录按钮"
                }
            
            # 等待登录完成
            time.sleep(3)
            
            # 检查是否需要选择环境
            try:
                # 查找包含环境名称的元素
                env_selectors = [
                    f'text="{env_name}"',
                    f'div:has-text("{env_name}")',
                    f'button:has-text("{env_name}")',
                    f'a:has-text("{env_name}")',
                    f'[title*="{env_name}"]',
                    f'span:has-text("{env_name}")'
                ]
                
                env_selected = False
                for selector in env_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.click(selector)
                            env_selected = True
                            time.sleep(2)
                            break
                    except:
                        continue
                
                if env_selected:
                    # 等待环境切换完成
                    time.sleep(2)
            except Exception as e:
                # 如果没有环境选择页面，继续执行
                print(f"环境选择检测: {str(e)}", file=sys.stderr)
            
            # 获取所有cookies
            cookies = context.cookies()
            
            # 保存页面截图用于调试
            try:
                # 获取脚本所在目录（backend目录）
                script_dir = os.path.dirname(os.path.abspath(__file__))
                # 创建screenshots文件夹
                screenshots_dir = os.path.join(script_dir, "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                
                screenshot_filename = f"login_screenshot_{int(time.time())}.png"
                screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                page.screenshot(path=screenshot_path)
                print(f"截图已保存: {screenshot_path}", file=sys.stderr)
            except Exception as e:
                print(f"保存截图失败: {str(e)}", file=sys.stderr)
            
            browser.close()
            
            # 转换cookies格式
            cookie_list = [
                {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie.get("path", "/"),
                    "expires": cookie.get("expires"),
                    "httpOnly": cookie.get("httpOnly", False),
                    "secure": cookie.get("secure", False),
                    "sameSite": cookie.get("sameSite")
                }
                for cookie in cookies
            ]
            
            return {
                "success": True,
                "cookies": cookie_list,
                "message": "登录成功"
            }
            
    except Exception as e:
        return {
            "success": False,
            "cookies": [],
            "message": f"登录失败: {str(e)}"
        }


if __name__ == "__main__":
    # 从命令行参数读取配置
    if len(sys.argv) != 5:
        print(json.dumps({
            "success": False,
            "cookies": [],
            "message": "参数错误"
        }))
        sys.exit(1)
    
    url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    env_name = sys.argv[4]
    
    # 执行登录
    result = auto_login(url, username, password, env_name)
    
    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False))
