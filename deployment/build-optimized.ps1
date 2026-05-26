# Docker 构建脚本 - 优化版
# 用于解决网络超时问题

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Docker 镜像构建脚本 (优化版)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设置错误处理
$ErrorActionPreference = "Stop"

# 获取脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

Write-Host "当前工作目录: $SCRIPT_DIR" -ForegroundColor Green
Write-Host ""

# 询问用户是否清理旧镜像
Write-Host "是否清理旧的 Docker 镜像和缓存? (y/n)" -ForegroundColor Yellow
$cleanup = Read-Host "输入选择"

if ($cleanup -eq "y" -or $cleanup -eq "Y") {
    Write-Host ""
    Write-Host "[步骤 1] 停止并删除容器..." -ForegroundColor Cyan
    docker-compose down
    
    Write-Host ""
    Write-Host "[步骤 2] 清理 Docker 系统..." -ForegroundColor Cyan
    Write-Host "注意: 这将删除所有未使用的镜像、容器和卷" -ForegroundColor Yellow
    docker system prune -a --volumes -f
    
    Write-Host ""
    Write-Host "✓ 清理完成" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  选择构建选项" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. 仅构建后端 (Backend)" -ForegroundColor White
Write-Host "2. 仅构建前端 (Frontend)" -ForegroundColor White
Write-Host "3. 构建全部服务" -ForegroundColor White
Write-Host "4. 构建并启动全部服务" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请选择 (1-4)"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  开始构建" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启用 BuildKit 以获得更好的构建性能
$env:DOCKER_BUILDKIT = 1
$env:COMPOSE_DOCKER_CLI_BUILD = 1

# 记录开始时间
$startTime = Get-Date

try {
    switch ($choice) {
        "1" {
            Write-Host "[构建] 后端服务..." -ForegroundColor Cyan
            docker-compose build --no-cache backend
            Write-Host ""
            Write-Host "✓ 后端构建完成" -ForegroundColor Green
        }
        "2" {
            Write-Host "[构建] 前端服务..." -ForegroundColor Cyan
            docker-compose build --no-cache frontend
            Write-Host ""
            Write-Host "✓ 前端构建完成" -ForegroundColor Green
        }
        "3" {
            Write-Host "[构建] 全部服务..." -ForegroundColor Cyan
            docker-compose build --no-cache
            Write-Host ""
            Write-Host "✓ 全部服务构建完成" -ForegroundColor Green
        }
        "4" {
            Write-Host "[构建] 全部服务..." -ForegroundColor Cyan
            docker-compose build --no-cache
            Write-Host ""
            Write-Host "✓ 构建完成" -ForegroundColor Green
            Write-Host ""
            Write-Host "[启动] 启动服务..." -ForegroundColor Cyan
            docker-compose up -d
            Write-Host ""
            Write-Host "✓ 服务已启动" -ForegroundColor Green
        }
        default {
            Write-Host "无效的选择,退出" -ForegroundColor Red
            exit 1
        }
    }
    
    # 计算耗时
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  构建完成" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "总耗时: $($duration.ToString('hh\:mm\:ss'))" -ForegroundColor Green
    Write-Host ""
    
    # 显示容器状态
    Write-Host "当前容器状态:" -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host "提示:" -ForegroundColor Yellow
    Write-Host "- 查看日志: docker-compose logs -f [service_name]" -ForegroundColor White
    Write-Host "- 停止服务: docker-compose down" -ForegroundColor White
    Write-Host "- 重启服务: docker-compose restart" -ForegroundColor White
    
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  构建失败" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "错误信息: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "故障排查建议:" -ForegroundColor Yellow
    Write-Host "1. 检查网络连接是否稳定" -ForegroundColor White
    Write-Host "2. 查看完整日志: docker-compose build backend 2>&1 | Tee-Object build.log" -ForegroundColor White
    Write-Host "3. 尝试切换镜像源(修改 .env 文件中的 PYPI_MIRROR)" -ForegroundColor White
    Write-Host "4. 参考文档: deployment/DOCKER_BUILD_TIMEOUT_FIX.md" -ForegroundColor White
    Write-Host ""
    exit 1
}
