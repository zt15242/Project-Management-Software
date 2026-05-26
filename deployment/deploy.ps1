# 项目管理系统 PowerShell 部署脚本
# 使用方法: .\deploy.ps1 [start|stop|restart|logs|build|clean|backup|restore]

param (
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "logs", "build", "status", "clean", "backup", "restore", "help")]
    [string]$Command = "help",

    [Parameter(Position=1)]
    [string]$Target = ""
)

# 设置编码
$OutputEncoding = [System.Text.Encoding]::UTF8

# 获取脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Host-Color {
    param($Message, $Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Check-Requirements {
    Write-Host-Color "检查系统要求..." "Yellow"
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host-Color "错误: Docker 未安装，请先安装 Docker Desktop for Windows" "Red"
        exit 1
    }
    
    $composeVersion = docker compose version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host-Color "错误: Docker Compose 未安装" "Red"
        exit 1
    }
    
    Write-Host-Color "✓ Docker 和 Docker Compose 已安装" "Green"
}

function Check-EnvFile {
    $envPath = Join-Path $SCRIPT_DIR ".env"
    $prodPath = Join-Path $SCRIPT_DIR ".env.production"
    
    if (-not (Test-Path $envPath)) {
        if (Test-Path $prodPath) {
            Write-Host-Color "警告: .env 文件不存在，复制 .env.production 使用默认配置" "Yellow"
            Copy-Item $prodPath $envPath
            Write-Host-Color "✓ 环境配置已加载" "Green"
        } else {
            Write-Host-Color "警告: 未找到 .env 或 .env.production 文件" "Yellow"
        }
    }
}

function Build-Images {
    Check-Requirements
    Check-EnvFile
    Write-Host-Color "开始构建 Docker 镜像..." "Yellow"
    
    $env:DOCKER_BUILDKIT = 1
    Set-Location $SCRIPT_DIR
    docker compose build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host-Color "✓ Docker 镜像构建完成" "Green"
    } else {
        Write-Host-Color "错误: 构建失败" "Red"
        exit 1
    }
}

function Start-Services {
    Check-Requirements
    Check-EnvFile
    Write-Host-Color "启动服务..." "Yellow"
    
    Set-Location $SCRIPT_DIR
    
    # 创建必要的目录
    $dataDirs = @("data/uploads", "data/logs")
    foreach ($dir in $dataDirs) {
        $fullPath = Join-Path $SCRIPT_DIR $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Force -Path $fullPath | Out-Null
        }
    }
    
    docker compose up -d
    
    Write-Host-Color "✓ 服务启动成功" "Green"
    Write-Host-Color "`n服务访问地址:" "Green"
    Write-Host-Color "  - 前端: http://localhost:6004" "Green"
    Write-Host-Color "  - 后端 API: http://localhost:6002" "Green"
    Write-Host-Color "  - API 文档: http://localhost:6002/docs" "Green"
    Write-Host-Color "  - MongoDB: External (External Database Specified)" "Green"
}

function Stop-Services {
    Write-Host-Color "停止服务..." "Yellow"
    Set-Location $SCRIPT_DIR
    docker compose down
    Write-Host-Color "✓ 服务已停止" "Green"
}

function Restart-Services {
    Stop-Services
    Start-Services
}

function View-Logs {
    Set-Location $SCRIPT_DIR
    if ($Target) {
        docker compose logs -f $Target
    } else {
        docker compose logs -f
    }
}

function Show-Status {
    Write-Host-Color "服务状态:" "Yellow"
    Set-Location $SCRIPT_DIR
    docker compose ps
}

function Clean-Resources {
    Write-Host-Color "清理 Docker 资源..." "Yellow"
    $confirm = Read-Host "这将删除所有容器、镜像和卷，确定要继续吗？(y/N)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Set-Location $SCRIPT_DIR
        docker compose down -v --rmi all
        Write-Host-Color "✓ 资源清理完成" "Green"
    } else {
        Write-Host-Color "取消清理操作" "Yellow"
    }
}

function Backup-Data {
    Write-Host-Color "备份数据库..." "Yellow"
    
    $projectRoot = Split-Path $SCRIPT_DIR -Parent
    $backupDir = Join-Path $projectRoot "backups"
    
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir | Out-Null
    }
    
    Write-Host-Color "警告: 外部 MongoDB 模式下，此脚本不支持自动备份。请手动备份您的本地数据库。" "Yellow"
}

function Restore-Data {
    if (-not $Target) {
        Write-Host-Color "错误: 请指定备份文件路径" "Red"
        Write-Host-Color "用法: .\deploy.ps1 restore <backup_file>" "Yellow"
        return
    }
    
    Write-Host-Color "恢复数据库..." "Yellow"
    Write-Host-Color "警告: 外部 MongoDB 模式下，此脚本不支持自动恢复。请手动恢复您的本地数据库。" "Yellow"
}

function Show-Help {
    Write-Host-Color "`n项目管理系统 PowerShell 部署脚本" "Cyan"
    Write-Host "用法: .\deploy.ps1 [命令] [选项]"
    Write-Host "`n命令:"
    Write-Host "  build       构建 Docker 镜像"
    Write-Host "  start       启动所有服务"
    Write-Host "  stop        停止所有服务"
    Write-Host "  restart     重启所有服务"
    Write-Host "  status      显示服务状态"
    Write-Host "  logs        查看日志 (可选: .\deploy.ps1 logs backend)"
    Write-Host "  backup      备份数据库"
    Write-Host "  restore     恢复数据库 (需要: .\deploy.ps1 restore <file>)"
    Write-Host "  clean       清理所有 Docker 资源"
    Write-Host "  help        显示此帮助信息"
    Write-Host "`n示例:"
    Write-Host "  .\deploy.ps1 build"
    Write-Host "  .\deploy.ps1 start"
    Write-Host "  .\deploy.ps1 logs backend"
}

# 主逻辑
switch ($Command) {
    "build"   { Build-Images }
    "start"   { Start-Services }
    "stop"    { Stop-Services }
    "restart" { Restart-Services }
    "status"  { Show-Status }
    "logs"    { View-Logs }
    "backup"  { Backup-Data }
    "restore" { Restore-Data }
    "clean"   { Clean-Resources }
    "help"    { Show-Help }
    default  { Show-Help }
}
