# ============================================================
# 回滚脚本 - 回滚到指定版本
# 用途: 当部署出现问题时,快速回滚到之前的版本
# ============================================================

param(
    [string]$ProjectRoot = "D:\Project_Package_20260304_1520",
    [string]$Commit = "",          # 要回滚到的 commit hash
    [string]$BackupTimestamp = "", # 要回滚到的备份时间戳(如 20260526_140000)
    [switch]$List = $false         # 列出可用的备份/提交
)

$ErrorActionPreference = "Stop"

$DeploymentDir = Join-Path $ProjectRoot "deployment"
$BackupRoot = Join-Path $ProjectRoot "..\_deploy_backups"

# ============== 列出可用版本 ==============
if ($List) {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "可用的回滚版本" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    
    Write-Host "`n[Git 提交历史] (最近 10 个)" -ForegroundColor Yellow
    Push-Location $ProjectRoot
    try {
        git log --oneline -10
    } finally {
        Pop-Location
    }
    
    Write-Host "`n[Docker 镜像备份]" -ForegroundColor Yellow
    docker images | Select-String -Pattern "deployment-(backend|frontend):backup_"
    
    Write-Host "`n[文件备份]" -ForegroundColor Yellow
    if (Test-Path $BackupRoot) {
        Get-ChildItem $BackupRoot -Directory -Filter "backup_*" |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 10 |
            ForEach-Object {
                $CommitFile = Join-Path $_.FullName "commit.txt"
                $CommitHash = if (Test-Path $CommitFile) { Get-Content $CommitFile } else { "(无)" }
                Write-Host "  $($_.Name) - commit: $CommitHash"
            }
    } else {
        Write-Host "  (无备份)"
    }
    
    Write-Host "`n用法:" -ForegroundColor Yellow
    Write-Host "  按 commit 回滚:    .\rollback.ps1 -Commit abc1234"
    Write-Host "  按备份时间回滚:    .\rollback.ps1 -BackupTimestamp 20260526_140000"
    exit 0
}

# ============== 参数检查 ==============
if (-not $Commit -and -not $BackupTimestamp) {
    Write-Host "请指定回滚目标:" -ForegroundColor Yellow
    Write-Host "  按 commit 回滚:    .\rollback.ps1 -Commit abc1234"
    Write-Host "  按备份时间回滚:    .\rollback.ps1 -BackupTimestamp 20260526_140000"
    Write-Host "  查看可用版本:      .\rollback.ps1 -List"
    exit 1
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "开始回滚" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# ============== Git 回滚 ==============
if ($Commit) {
    Write-Host "`n[1/3] 回滚 Git 代码到 commit: $Commit" -ForegroundColor Yellow
    
    Push-Location $ProjectRoot
    try {
        # 验证 commit 是否存在
        $null = git cat-file -e "$Commit^{commit}" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Commit 不存在: $Commit" -ForegroundColor Red
            exit 1
        }
        
        git reset --hard $Commit
        Write-Host "  Git 回滚完成" -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

# ============== Docker 镜像回滚 ==============
if ($BackupTimestamp) {
    Write-Host "`n[1/3] 回滚 Docker 镜像到备份: $BackupTimestamp" -ForegroundColor Yellow
    
    $BackendBackupTag = "deployment-backend:backup_$BackupTimestamp"
    $FrontendBackupTag = "deployment-frontend:backup_$BackupTimestamp"
    
    # 检查备份镜像是否存在
    $BackendExists = docker image inspect $BackendBackupTag 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  备份镜像不存在: $BackendBackupTag" -ForegroundColor Red
        exit 1
    }
    
    # 标记备份镜像为 latest
    docker tag $BackendBackupTag "deployment-backend:latest"
    docker tag $FrontendBackupTag "deployment-frontend:latest"
    Write-Host "  镜像回滚完成" -ForegroundColor Green
    
    # 同时回滚 git 到对应的 commit(如果备份目录存在)
    $BackupDir = Join-Path $BackupRoot "backup_$BackupTimestamp"
    $CommitFile = Join-Path $BackupDir "commit.txt"
    if (Test-Path $CommitFile) {
        $BackupCommit = Get-Content $CommitFile
        Write-Host "  从备份恢复 git commit: $BackupCommit"
        Push-Location $ProjectRoot
        try {
            git reset --hard $BackupCommit
        } finally {
            Pop-Location
        }
    }
}

# ============== 重启容器 ==============
Write-Host "`n[2/3] 重启容器..." -ForegroundColor Yellow

Push-Location $DeploymentDir
try {
    docker-compose down
    docker-compose up -d
    Write-Host "  容器已重启" -ForegroundColor Green
} finally {
    Pop-Location
}

# ============== 健康检查 ==============
Write-Host "`n[3/3] 健康检查..." -ForegroundColor Yellow

Start-Sleep -Seconds 10

$BackendHealthy = $false
for ($i = 0; $i -lt 20; $i++) {
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:6002/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($Response.StatusCode -eq 200) {
            $BackendHealthy = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 3
    }
}

if ($BackendHealthy) {
    Write-Host "  后端健康 ✓" -ForegroundColor Green
    Write-Host "`n============================================================" -ForegroundColor Green
    Write-Host "回滚成功!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Host "  后端不健康 ✗" -ForegroundColor Red
    Write-Host "`n============================================================" -ForegroundColor Red
    Write-Host "回滚失败,请检查容器日志" -ForegroundColor Red
    Write-Host "  docker-compose logs backend" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Red
    exit 1
}

