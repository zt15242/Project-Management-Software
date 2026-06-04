"""
使用Selenium的登录脚本
Selenium不依赖asyncio，完全避免Windows平台的事件循环问题
"""
import sys
import json
import os
import shutil
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def auto_login(url: str, username: str, password: str, env_name: str) -> dict:
    """
    使用Selenium自动登录并获取cookies
    支持跨平台（Windows/Linux/Mac）
    """
    driver = None
    user_data_dir = tempfile.mkdtemp(prefix="pm_chrome_profile_")
    try:
        # 配置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        
        # Docker/Linux 环境需要额外的参数
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--remote-debugging-port=0')
        
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 创建screenshots文件夹
        screenshots_dir = os.path.join(script_dir, "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # 检查是否有本地ChromeDriver（跨平台支持）
        # 根据系统平台选择合适的驱动名称
        if sys.platform.startswith('win'):
            # Windows
            local_chromedriver_candidates = [
                os.path.join(script_dir, "chromedriver.exe"),
            ]
        else:
            # Linux/Mac
            local_chromedriver_candidates = [
                "/usr/bin/chromedriver",                # Apt install default
                "/usr/local/bin/chromedriver",          # Common manual install
                os.path.join(script_dir, "chromedriver"), # Local binary
            ]
        
        local_chromedriver = None
        for candidate in local_chromedriver_candidates:
            if os.path.exists(candidate):
                local_chromedriver = candidate
                break
        
        if local_chromedriver:
            # 使用本地ChromeDriver
            print(f"✓ 使用本地ChromeDriver: {local_chromedriver}", file=sys.stderr)
            service = Service(executable_path=local_chromedriver)
            
            # Docker环境下可能需要特殊的Service参数
            if not sys.platform.startswith('win'):
                # 确保有执行权限
                try:
                    os.chmod(local_chromedriver, 0o755)
                except:
                    pass
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # 使用webdriver-manager自动下载（推荐方式，支持跨平台）
            print(f"✓ 本地未找到ChromeDriver，尝试使用webdriver-manager", file=sys.stderr)
            try:
                # 尝试指定版本安装，或者让它自动检测
                # 在Docker环境中，最好配合已安装的Chrome版本
                from webdriver_manager.core.os_manager import ChromeType
                
                # 检查系统是否安装了Chromium/Chrome
                if os.path.exists("/usr/bin/chromium") or os.path.exists("/usr/bin/chromium-browser"):
                    print("检测到系统Chromium，配置webdriver-manager使用它", file=sys.stderr)
                    # 显式指定浏览器路径有助于webdriver-manager找到正确的驱动
                    chrome_options.binary_location = "/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else "/usr/bin/chromium-browser"
                    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
                else:
                    service = Service(ChromeDriverManager().install())
                
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"webdriver-manager初始化失败: {e}", file=sys.stderr)
                # 最后的尝试：直接初始化，期望PATH中有chromedriver
                driver = webdriver.Chrome(options=chrome_options)
        
        driver.set_page_load_timeout(30)
        
        # 访问登录页面
        driver.get(url)
        print(f"已访问URL: {url}", file=sys.stderr)
        time.sleep(3)  # 增加等待时间
        
        # 打印页面标题
        print(f"页面标题: {driver.title}", file=sys.stderr)
        
        # 尝试查找并填写用户名
        username_selectors = [
            (By.ID, "username"),
            (By.NAME, "username"),
            (By.XPATH, "//input[@placeholder='手机号/邮箱']"),
            (By.XPATH, "//input[@placeholder='Please enter your mobile number or email']"),  # English support (Exact match from screenshot)
            (By.XPATH, "//input[@placeholder='Mobile/Email']"),
            (By.XPATH, "//input[@type='text' and contains(@class, 'el-input')]"),
            (By.XPATH, "//input[@type='text']"),
            (By.CSS_SELECTOR, "input[type='text']"),
        ]
        
        username_filled = False
        for by, selector in username_selectors:
            try:
                elements = driver.find_elements(by, selector)
                print(f"尝试用户名选择器 {by}='{selector}': 找到 {len(elements)} 个元素", file=sys.stderr)
                for element in elements:
                    if element.is_displayed():
                        element.clear()
                        element.send_keys(username)
                        username_filled = True
                        print(f"成功填写用户名", file=sys.stderr)
                        break
                if username_filled:
                    break
            except Exception as e:
                print(f"用户名选择器失败: {str(e)}", file=sys.stderr)
                continue
        
        if not username_filled:
            raise Exception("无法找到用户名输入框")
        
        time.sleep(1)
        
        # 尝试查找并填写密码
        password_selectors = [
            (By.ID, "password"),
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.XPATH, "//input[@placeholder='密码']"),
            (By.XPATH, "//input[@placeholder='Password']"),  # English support
            (By.XPATH, "//input[@type='password']"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]
        
        password_filled = False
        for by, selector in password_selectors:
            try:
                elements = driver.find_elements(by, selector)
                print(f"尝试密码选择器 {by}='{selector}': 找到 {len(elements)} 个元素", file=sys.stderr)
                for element in elements:
                    if element.is_displayed():
                        element.clear()
                        element.send_keys(password)
                        password_filled = True
                        print(f"成功填写密码", file=sys.stderr)
                        break
                if password_filled:
                    break
            except Exception as e:
                print(f"密码选择器失败: {str(e)}", file=sys.stderr)
                continue
        
        if not password_filled:
            raise Exception("无法找到密码输入框")
        
        time.sleep(1)
        
        # 查找并点击登录按钮
        login_button_selectors = [
            (By.XPATH, "//button[contains(text(), '登录') or contains(text(), '登 录')]"),
            (By.XPATH, "//button[normalize-space()='Log In']"),  # English support (Exact match from screenshot)
            (By.XPATH, "//div[normalize-space()='Log In']"),     # Sometimes it's a div
            (By.XPATH, "//span[normalize-space()='Log In']"),    # Sometimes it's a span
            (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(@class, 'el-button--primary')]"),
            (By.XPATH, "//a[contains(text(), '登录')]"),
            (By.XPATH, "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]"),  # English support
            (By.CSS_SELECTOR, "button.el-button--primary"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CLASS_NAME, "login-button"),
        ]
        
        login_clicked = False
        for by, selector in login_button_selectors:
            try:
                elements = driver.find_elements(by, selector)
                print(f"尝试登录按钮选择器 {by}='{selector}': 找到 {len(elements)} 个元素", file=sys.stderr)
                for element in elements:
                    if element.is_displayed():
                        print(f"找到可见的登录按钮，文本: {element.text}", file=sys.stderr)
                        element.click()
                        login_clicked = True
                        print(f"成功点击登录按钮", file=sys.stderr)
                        break
                if login_clicked:
                    break
            except Exception as e:
                print(f"登录按钮选择器失败: {str(e)}", file=sys.stderr)
                continue
        
        if not login_clicked:
            raise Exception("无法找到登录按钮")
        
        # 等待登录完成
        time.sleep(3)
        
        # 检查是否需要选择环境
        try:
            env_selectors = [
                (By.XPATH, f"//div[contains(text(), '{env_name}')]"),
                (By.XPATH, f"//button[contains(text(), '{env_name}')]"),
                (By.XPATH, f"//a[contains(text(), '{env_name}')]"),
                (By.XPATH, f"//span[contains(text(), '{env_name}')]"),
                (By.XPATH, f"//*[@title='{env_name}']")
            ]
            
            env_selected = False
            for by, selector in env_selectors:
                try:
                    element = driver.find_element(by, selector)
                    if element.is_displayed():
                        element.click()
                        env_selected = True
                        time.sleep(2)
                        break
                except:
                    continue
            
            if env_selected:
                time.sleep(2)
        except Exception as e:
            print(f"环境选择检测: {str(e)}", file=sys.stderr)
        
        # === 新增：访问更多页面以获取完整cookie ===
        print("访问更多页面以获取完整cookie...", file=sys.stderr)
        try:
            # 获取当前URL
            current_url = driver.current_url
            print(f"当前URL: {current_url}", file=sys.stderr)
            
            # 尝试访问首页
            base_url = url.split('/login')[0] if '/login' in url else url.rstrip('/')
            
            # 访问首页
            home_url = f"{base_url}/home"
            print(f"访问首页: {home_url}", file=sys.stderr)
            driver.get(home_url)
            time.sleep(5)  # 增加等待时间
            
            # 保存首页截图
            try:
                home_screenshot = f"home_screenshot_{int(time.time())}.png"
                home_screenshot_path = os.path.join(screenshots_dir, home_screenshot)
                driver.save_screenshot(home_screenshot_path)
                print(f"首页截图已保存: {home_screenshot_path}", file=sys.stderr)
                print(f"当前页面标题: {driver.title}", file=sys.stderr)
                print(f"当前页面URL: {driver.current_url}", file=sys.stderr)
            except Exception as e:
                print(f"保存首页截图失败: {str(e)}", file=sys.stderr)
            
            # 执行一些JavaScript以触发cookie设置
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 0);")
            except:
                pass
            
            # 尝试访问一些常见的页面
            pages_to_visit = [
                "/bff/neoweb#/entityGrid/account?objectApiKey=account"
            ]
            
            for page in pages_to_visit:
                try:
                    page_url = f"{base_url}{page}"
                    print(f"访问页面: {page_url}", file=sys.stderr)
                    driver.get(page_url)
                    time.sleep(2)
                    
                    # 打印当前cookie数量
                    current_cookies = driver.get_cookies()
                    print(f"  当前cookie数量: {len(current_cookies)}", file=sys.stderr)
                except Exception as e:
                    print(f"  访问 {page} 失败: {str(e)}", file=sys.stderr)
            
            print("已访问额外页面", file=sys.stderr)
        except Exception as e:
            print(f"访问额外页面失败（继续）: {str(e)}", file=sys.stderr)
        # === 新增结束 ===
        
        # 获取所有cookies（包括JavaScript设置的）
        print("获取所有cookies（包括JavaScript设置的）...", file=sys.stderr)
        
        # 方法1：使用Selenium的get_cookies()（只能获取HTTP cookie）
        selenium_cookies = driver.get_cookies()
        print(f"Selenium获取到 {len(selenium_cookies)} 个HTTP cookie", file=sys.stderr)
        
        # 方法2：使用JavaScript的document.cookie（可以获取所有cookie）
        try:
            js_cookie_string = driver.execute_script("return document.cookie")
            print(f"JavaScript获取到的cookie字符串: {js_cookie_string[:200]}...", file=sys.stderr)
            
            # 解析cookie字符串
            js_cookies = []
            if js_cookie_string:
                for cookie_pair in js_cookie_string.split('; '):
                    if '=' in cookie_pair:
                        name, value = cookie_pair.split('=', 1)
                        js_cookies.append({
                            'name': name,
                            'value': value
                        })
            
            print(f"JavaScript解析出 {len(js_cookies)} 个cookie", file=sys.stderr)
            
            # 合并两种方式获取的cookie
            # 使用字典去重，优先使用Selenium获取的完整cookie信息
            cookie_dict = {}
            
            # 先添加Selenium获取的cookie（有完整信息）
            for cookie in selenium_cookies:
                cookie_dict[cookie['name']] = cookie
            
            # 再添加JavaScript获取的cookie（只有name和value）
            for js_cookie in js_cookies:
                if js_cookie['name'] not in cookie_dict:
                    # 补充默认信息
                    cookie_dict[js_cookie['name']] = {
                        'name': js_cookie['name'],
                        'value': js_cookie['value'],
                        'domain': '.xiaoshouyi.com',
                        'path': '/',
                        'expires': None,
                        'httpOnly': False,
                        'secure': False,
                        'sameSite': 'Lax'
                    }
            
            cookies = list(cookie_dict.values())
            print(f"最终合并得到 {len(cookies)} 个cookie", file=sys.stderr)
            
        except Exception as e:
            print(f"使用JavaScript获取cookie失败，使用Selenium结果: {str(e)}", file=sys.stderr)
            cookies = selenium_cookies
        
        # 打印所有cookie名称
        cookie_names = [c['name'] for c in cookies]
        print(f"Cookie名称: {cookie_names}", file=sys.stderr)
        
        # 保存截图
        try:
            screenshot_filename = f"login_screenshot_{int(time.time())}.png"
            screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
            driver.save_screenshot(screenshot_path)
            print(f"截图已保存: {screenshot_path}", file=sys.stderr)
        except Exception as e:
            print(f"保存截图失败: {str(e)}", file=sys.stderr)
        
        # 转换cookies格式
        cookie_list = [
            {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie.get("path", "/"),
                "expires": cookie.get("expiry"),
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
        # 尝试保存错误截图
        if driver:
            try:
                # 确保screenshots文件夹存在
                script_dir = os.path.dirname(os.path.abspath(__file__))
                screenshots_dir = os.path.join(script_dir, "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                
                screenshot_filename = f"login_error_{int(time.time())}.png"
                screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                driver.save_screenshot(screenshot_path)
                print(f"错误截图已保存: {screenshot_path}", file=sys.stderr)
            except:
                pass
        
        return {
            "success": False,
            "cookies": [],
            "message": f"登录失败: {str(e)}"
        }
    
    finally:
        if driver:
            driver.quit()
        shutil.rmtree(user_data_dir, ignore_errors=True)


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
