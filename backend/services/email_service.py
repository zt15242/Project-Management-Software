import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timedelta
import random
import string
from typing import Optional
from database import get_database
from models import EmailConfigResponse, EmailVerify
from utils import get_beijing_time

class EmailService:
    @staticmethod
    async def get_config():
        db = get_database()
        config = await db.email_config.find_one({"is_enabled": True})
        return config

    @staticmethod
    def send_email(config_dict, to_email, subject, content):
        try:
            smtp_server = config_dict["smtp_server"]
            smtp_port = config_dict["smtp_port"]
            smtp_user = config_dict["smtp_user"]
            smtp_password = config_dict["smtp_password"]
            sender_email = config_dict["sender_email"]
            use_tls = config_dict.get("use_tls", True)

            msg = MIMEText(content, 'html', 'utf-8')
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')

            if use_tls:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
            
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, [to_email], msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"发送邮件失败: {str(e)}")
            return False

    @staticmethod
    async def generate_and_send_code(email: str, purpose: str = "register"):
        config = await EmailService.get_config()
        if not config:
            return False, "未配置邮局服务"
        
        # 生成6位数字验证码
        code = ''.join(random.choices(string.digits, k=6))
        
        # 存储到MongoDB
        db = get_database()
        expires_at = get_beijing_time() + timedelta(minutes=10)
        
        await db.email_verifications.insert_one({
            "email": email,
            "code": code,
            "purpose": purpose,
            "created_at": get_beijing_time(),
            "expires_at": expires_at
        })
        
        subject = "验证码 - 项目管理系统"
        content = f"""
        <div style="padding: 20px; background-color: #f8fafc; font-family: sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h2 style="color: #1e293b; margin-bottom: 24px;">验证您的身份</h2>
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">您好，</p>
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">您正在进行账号注册，您的验证码为：</p>
                <div style="background-color: #f1f5f9; padding: 20px; text-align: center; border-radius: 8px; margin: 30px 0;">
                    <span style="font-size: 32px; font-weight: 800; color: #7c4dff; letter-spacing: 8px;">{code}</span>
                </div>
                <p style="color: #94a3b8; font-size: 14px;">该验证码将在 10 分钟后过期。如果这不是您本人的操作，请忽略此邮件。</p>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                <p style="color: #94a3b8; font-size: 12px; text-align: center;">项目管理系统 - 智能办公专家</p>
            </div>
        </div>
        """
        
        success = EmailService.send_email(config, email, subject, content)
        if success:
            return True, "验证码已发送"
        else:
            return False, "发送验证码失败，请检查邮局配置"

    @staticmethod
    async def verify_code(email: str, code: str, purpose: str = "register"):
        db = get_database()
        now = get_beijing_time()
        
        # 查找最新的有效验证码
        verification = await db.email_verifications.find_one({
            "email": email,
            "code": code,
            "purpose": purpose,
            "expires_at": {"$gt": now}
        }, sort=[("created_at", -1)])
        
        if verification:
            # 验证成功后删除（或标记已使用）
            await db.email_verifications.delete_one({"_id": verification["_id"]})
            return True
        return False
