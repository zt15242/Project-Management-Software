# ============================================================
# 一次性迁移脚本 - 从旧部署迁移到 Git 部署
# 用途: 将现有的非 Git 部署迁移到 Git 管理的部署
# ============================================================

param(
    [string]$OldDir = "D:\Project_Package_20260304_1520",
    [string]$NewDir = "D:\project-git",
    [string]$GitRepo = "https://github.com/zt15242/Project-Management-Software.git",
    [string]$Branch = "main",
    [switch]$TestMode = $false  # 测试模式：使用不同端口，不停止旧服务
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "迁移到 Git 部署" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  旧目录: $OldDir"
Write-Host "  新目录: $NewDir"
Write-Host "  Git 仓库: $GitRepo"
Write-Host "  分支: $Branch"
Write-Host "  测试模式: $(if ($TestMode) { '是（并行测试）' } else { '否（完全迁移）' })"
Write-Host ""

# ============== 1. 检查旧目录 ==============
Write-Host "[1/8] 检查旧部署..." -ForegroundColor Yellow

if (-not (Test-Path $OldDir)) {
    Write-Host "  旧目录不存在: $OldDir" -ForegroundColor Red
    exit 1
}

$OldDeploymentDir = Join-Path $OldDir "deployment"
if (-not (Test-Path $OldDeploymentDir)) {
    Write-Host "  旧部署目录不存在: $OldDeploymentDir" -ForegroundColor Red
    exit 1
}

Write-Host "  旧目录存在: $OldDir" -ForegroundColor Green

# 检查关键文件
$KeyFiles = @(
    "backend\.env",
    "deployment\docker-compose.yml"
)

$MissingFiles = @()
foreach ($File in $KeyFiles) {
    $FilePath = Join-Path $OldDir $File
    if (-not (Test-Path $FilePath)) {
        $MissingFiles += $File
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host "  缺少关键文件:" -ForegroundColor Red
    $MissingFiles | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "  关键文件检查通过" -ForegroundColor Green

# ============== 2. 备份旧部署 ==============
Write-Host "`n[2/8] 备份旧部署..." -ForegroundColor Yellow

$BackupDir = "$OldDir`_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "  备份到: $BackupDir"

try {
    # 只备份关键配置和数据，不备份代码
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    
    # 备份 .env 文件
    if (Test-Path "$OldDir\backend\.env") {
        Copy-Item "$OldDir\backend\.env" "$BackupDir\.env" -Force
        Write-Host "  已备份: backend\.env" -ForegroundColor Green
    }
    
    # 备份 docker-compose.override.yml（如果存在）
    if (Test-Path "$OldDir\deployment\docker-compose.override.yml") {
        Copy-Item "$OldDir\deployment\docker-compose.override.yml" "$BackupDir\docker-compose.override.yml" -Force
        Write-Host "  已备份: docker-compose.override.yml" -ForegroundColor Green
    }
    
    # 备份 MongoDB（如果容器存在）
    $MongoContainer = docker ps -a --filter "name=mongo-1" --format "{{.Names}}" 2>$null
    if ($MongoContainer -eq "mongo-1") {
        Write-Host "  备份 MongoDB 数据..."
        $MongoBackupDir = Join-Path $BackupDir "mongodb"
        New-Item -ItemType Directory -Path $MongoBackupDir -Force | Out-Null
        docker exec mongo-1 mongodump --out /tmp/backup_migrate 2>&1 | Out-Null
        docker cp "mongo-1:/tmp/backup_migrate" "$MongoBackupDir" 2>&1 | Out-Null
        docker exec mongo-1 rm -rf /tmp/backup_migrate 2>&1 | Out-Null
        Write-Host "  MongoDB 备份完成" -ForegroundColor Green
    }
    
    Write-Host "  备份完成" -ForegroundColor Green
} catch {
    Write-Host "  备份失败: $_" -ForegroundColor Red
    exit 1
}

# ============== 3. 克隆 Git 仓库 ==============
Write-Host "`n[3/8] 克隆 Git 仓库..." -ForegroundColor Yellow

if (Test-Path $NewDir) {
    Write-Host "  新目录已存在: $NewDir" -ForegroundColor Yellow
    $Confirm = Read-Host "  是否删除并重新克隆? (y/N)"
    if ($Confirm -eq 'y' -or $Confirm -eq 'Y') {
        Remove-Item $NewDir -Recurse -Force
    } else {
        Write-Host "  取消迁移" -ForegroundColor Red
        exit 1
    }
}

try {
    git clone -b $Branch $GitRepo $NewDir
    Write-Host "  克隆完成" -ForegroundColor Green
} catch {
    Write-Host "  克隆失败: $_" -ForegroundColor Red
    exit 1
}

# ============== 4. 复制配置文件 ==============
Write-Host "`n[4/8] 复制配置文件..." -ForegroundColor Yellow

# 复制 .env
if (Test-Path "$OldDir\backend\.env") {
    Copy-Item "$OldDir\backend\.env" "$NewDir\backend\.env" -Force
    Write-Host "  已复制: backend\.env" -ForegroundColor Green
}

# 复制 docker-compose.override.yml
if (Test-Path "$OldDir\deployment\docker-compose.override.yml") {
    Copy-Item "$OldDir\deployment\docker-compose.override.yml" "$NewDir\deployment\docker-compose.override.yml" -Force
    Write-Host "  已复制: docker-compose.override.yml" -ForegroundColor Green
} elseif ($TestMode) {
    # 测试模式：创建一个使用不同端口的 override 文件
    Write-Host "  测试模式：创建临时端口配置（6012/6014）" -ForegroundColor Yellow
    $OverrideContent = @"
version: '3.8'

services:
  backend:
    ports:
      - "6012:8000"
  
  frontend:
    ports:
      - "6014:80"
"@
    $OverrideContent | Out-File -FilePath "$NewDir\deployment\docker-compose.override.yml" -Encoding UTF8
    Write-Host "  已创建: docker-compose.override.yml (测试端口)" -ForegroundColor Green
}

# ============== 5. 创建数据目录 ==============
Write-Host "`n[5/8] 创建数据目录..." -ForegroundColor Yellow

$DataDirs = @(
    "$NewDir\deployment\data\uploads",
    "$NewDir\deployment\data\logs"
)

foreach ($Dir in $DataDirs) {
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        Write-Host "  已创建: $Dir" -ForegroundColor Green
    }
}

# 如果旧部署有 uploads 数据，复制过来
$OldUploadsDir = "$OldDir\deployment\data\uploads"
if (Test-Path $OldUploadsDir) {
    Write-Host "  复制 uploads 数据..."
    Copy-Item "$OldUploadsDir\*" "$NewDir\deployment\data\uploads\" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  uploads 数据复制完成" -ForegroundColor Green
}

# ============== 6. 构建镜像 ==============
Write-Host "`n[6/8] 构建 Docker 镜像..." -ForegroundColor Yellow

Push-Location "$NewDir\deployment"
try {
    docker-compose build
    Write-Host "  镜像构建完成" -ForegroundColor Green
} catch {
    Write-Host "  镜像构建失败: $_" -ForegroundColor Red
    Pop-Location
    exit 1
} finally {
    Pop-Location
}

# ============== 7. 启动新服务 ==============
Write-Host "`n[7/8] 启动新服务..." -ForegroundColor Yellow

if (-not $TestMode) {
    # 完全迁移模式：停止旧服务
    Write-Host "  停止旧服务..."
    Push-Location $OldDeploymentDir
    try {
        docker-compose down
        Write-Host "  旧服务已停止" -ForegroundColor Green
    } catch {
        Write-Host "  停止旧服务失败: $_" -ForegroundColor Yellow
    } finally {
        Pop-Location
    }
}

# 启动新服务
Push-Location "$NewDir\deployment"
try {
    docker-compose up -d
    Write-Host "  新服务已启动" -ForegroundColor Green
} catch {
    Write-Host "  启动新服务失败: $_" -ForegroundColor Red
    Pop-Location
    exit 1
} finally {
    Pop-Location
}

# ============== 8. 健康检查 ==============
Write-Host "`n[8/8] 健康检查..." -ForegroundColor Yellow

Start-Sleep -Seconds 10

$BackendPort = if ($TestMode) { 6012 } else { 6002 }
$FrontendPort = if ($TestMode) { 6014 } else { 6004 }

$BackendHealthy = $false
$FrontendHealthy = $false

# 检查后端
Write-Host "  检查后端 http://localhost:$BackendPort/health ..."
for ($i = 0; $i -lt 20; $i++) {
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:$BackendPort/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($Response.StatusCode -eq 200) {
            $BackendHealthy = $true
            Write-Host "  后端健康 ✓" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 3
    }
}

if (-not $BackendHealthy) {
    Write-Host "  后端不健康 ✗" -ForegroundColor Red
}

# 检查前端
Write-Host "  检查前端 http://localhost:$FrontendPort ..."
for ($i = 0; $i -lt 10; $i++) {
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:$FrontendPort" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($Response.StatusCode -eq 200) {
            $FrontendHealthy = $true
            Write-Host "  前端健康 ✓" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 3
    }
}

if (-not $FrontendHealthy) {
    Write-Host "  前端不健康 ✗" -ForegroundColor Red
}

# ============== 结果 ==============
Write-Host "`n============================================================" -ForegroundColor Cyan
if ($BackendHealthy -and $FrontendHealthy) {
    Write-Host "迁移成功！" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "新部署信息:" -ForegroundColor Yellow
    Write-Host "  项目目录: $NewDir"
    Write-Host "  后端地址: http://localhost:$BackendPort"
    Write-Host "  前端地址: http://localhost:$FrontendPort"
    Write-Host "  备份位置: $BackupDir"
    Write-Host ""
    
    if ($TestMode) {
        Write-Host "测试模式提示:" -ForegroundColor Yellow
        Write-Host "  1. 新服务运行在端口 6012/6014"
        Write-Host "  2. 旧服务仍在运行（6002/6004）"
        Write-Host "  3. 测试通过后，运行以下命令完成迁移:"
        Write-Host "     .\migrate-to-git.ps1 -OldDir '$OldDir' -NewDir '$NewDir'"
        Write-Host ""
    } else {
        Write-Host "下一步:" -ForegroundColor Yellow
        Write-Host "  1. 验证服务功能正常"
        Write-Host "  2. 配置自动部署:"
        Write-Host "     cd $NewDir\deployment"
        Write-Host "     .\webhook-server.ps1 -Port 9000 -DeployScript '$NewDir\deployment\deploy.ps1'"
        Write-Host "  3. 配置 GitHub Webhook:"
        Write-Host "     URL: http://your-server-ip:9000/webhook"
        Write-Host "     Content type: application/json"
        Write-Host "     Events: Just the push event"
        Write-Host ""
    }
} else {
    Write-Host "迁移失败！" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "  1. Docker 容器日志: docker-compose logs"
    Write-Host "  2. 配置文件是否正确"
    Write-Host "  3. 端口是否被占用"
    Write-Host ""
    Write-Host "回滚方法:" -ForegroundColor Yellow
    if ($TestMode) {
        Write-Host "  cd $NewDir\deployment"
        Write-Host "  docker-compose down"
    } else {
        Write-Host "  cd $OldDeploymentDir"
        Write-Host "  docker-compose up -d"
    }
    Write-Host ""
    exit 1
}

