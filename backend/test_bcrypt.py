"""测试 bcrypt 是否正常工作"""
try:
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # 测试密码加密
    password = "test123"
    hashed = pwd_context.hash(password)
    print("✅ 密码加密成功:", hashed)
    
    # 测试密码验证
    result = pwd_context.verify(password, hashed)
    print("✅ 密码验证成功:", result)
    
    print("\n✅ bcrypt 工作正常！")
    
except Exception as e:
    print("❌ bcrypt 错误:")
    print(type(e).__name__, ":", str(e))
    print("\n建议运行: pip install --upgrade bcrypt passlib")

