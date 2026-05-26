import sys
import os
import subprocess
import shutil

print("--- 开始诊断 FFmpeg ---")

try:
    import static_ffmpeg
    print(f"static_ffmpeg 模块位置: {os.path.dirname(static_ffmpeg.__file__)}")
    
    # 执行 add_paths
    static_ffmpeg.add_paths()
    print("已执行 static_ffmpeg.add_paths()")
except ImportError:
    print("错误: static_ffmpeg 未安装")

# 检查 shutil.which
ffmpeg_path = shutil.which("ffmpeg")
print(f"shutil.which('ffmpeg') 结果: {ffmpeg_path}")

# 如果找不到，尝试手动查找
if not ffmpeg_path:
    print("尝试手动在 static_ffmpeg 目录查找...")
    try:
        package_dir = os.path.dirname(static_ffmpeg.__file__)
        if sys.platform == 'win32':
            candidates = [
                os.path.join(package_dir, 'bin', 'ffmpeg.exe'),
                os.path.join(package_dir, 'bin', 'win32', 'ffmpeg.exe'), # 有时候会有子目录
            ]
        else:
            candidates = [os.path.join(package_dir, 'bin', 'ffmpeg')]
            
        for p in candidates:
            print(f"检查路径: {p}")
            if os.path.exists(p):
                print(f"找到文件: {p}")
                ffmpeg_path = p
                break
    except:
        pass

if ffmpeg_path:
    print(f"最终使用的 FFmpeg 路径: {ffmpeg_path}")
    print("尝试运行 ffmpeg -version ...")
    try:
        result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("成功运行! 版本信息头:")
            print(result.stdout.split('\n')[0])
        else:
            print(f"运行失败，返回码: {result.returncode}")
            print("stderr:", result.stderr)
    except Exception as e:
        print(f"运行异常: {e}")
else:
    print("彻底未找到 ffmpeg 可执行文件。")

print("--- 诊断结束 ---")
