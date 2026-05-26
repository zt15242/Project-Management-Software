# Docker部署优化说明

## 问题描述
在Docker重新部署时，`static-ffmpeg`包会尝试从GitHub下载ffmpeg二进制文件：
```
Downloading https://github.com/zackees/ffmpeg_bins/raw/main/v5.0/linux.zip
```
由于网络问题，这个下载过程可能会长时间卡住或失败。

## 解决方案

### 1. 使用系统FFmpeg替代
修改 `deployment/Dockerfile.backend`，在系统包安装阶段添加ffmpeg：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基础工具
    curl \
    wget \
    gnupg \
    ca-certificates \
    # FFmpeg (替代 static_ffmpeg，避免从 GitHub 下载)
    ffmpeg \
    # Selenium 支持
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*
```

### 2. 移除Python包依赖
修改 `backend/requirements.txt`，注释掉static-ffmpeg：

```text
faster-whisper==1.0.3
# static-ffmpeg==2.5  # Docker中使用系统ffmpeg，避免从GitHub下载
OpenCC==1.1.9
```

### 3. 代码兼容性
代码中已有fallback机制（`backend/routers/meetings.py`）：

```python
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except ImportError:
    print("static_ffmpeg not installed, using system ffmpeg")
```

`get_ffmpeg_cmd()`函数会按以下顺序查找ffmpeg：
1. 环境变量中的ffmpeg（系统安装的）
2. static_ffmpeg包中的ffmpeg
3. 默认使用'ffmpeg'命令

## 优势

1. **更快的构建速度**：不需要从GitHub下载文件
2. **更稳定**：使用Debian官方源的ffmpeg，版本稳定
3. **更小的镜像**：系统ffmpeg比static_ffmpeg包更精简
4. **更好的兼容性**：系统包经过充分测试

## 重新部署步骤

```bash
# 1. 进入部署目录
cd deployment

# 2. 停止并删除旧容器
docker-compose down

# 3. 重新构建镜像
docker-compose build --no-cache

# 4. 启动服务
docker-compose up -d

# 5. 查看日志
docker-compose logs -f backend
```

## 验证

部署成功后，可以通过以下方式验证ffmpeg是否正常工作：

```bash
# 进入容器
docker-compose exec backend bash

# 检查ffmpeg版本
ffmpeg -version

# 应该看到类似输出：
# ffmpeg version 5.1.x ...
```

## 注意事项

- 本地开发环境仍然可以使用`static-ffmpeg`包
- Docker环境会自动使用系统ffmpeg
- 两种方式都能正常工作，代码会自动适配
