# ============================================================
# 自动部署脚本 - Windows Server 版本
# 用途: Git pull -> 备份 -> 重新构建 -> 健康检查 -> 失败回滚
# ============================================================

param(
    [string]$ProjectRoot = "D:\Project_Package_20260304_1520",
    [string]$Branch = "main",
    [int]$BackendPort = 6002,
    [int]$FrontendPort = 6004,
    [int]$HealthCheckTimeout = 60,
    [switch]$SkipBackup = $false,
    [switch]$SkipFrontendBuild = $false
)

# 错误时停止
$ErrorActionPreference = "Stop"

# ============== 配置 ==============
$DeploymentDir = Join-Path $ProjectRoot "deployment"
$BackupRoot = Join-Path $ProjectRoot "..\_deploy_backups"
$LogDir = Join-Path $ProjectRoot "..\_deploy_logs"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "deploy_$Timestamp.log"

# ============== 工具函数 ==============
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $LogMessage = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage -Encoding UTF8
}

function Test-HealthCheck {
    param([string]$Url, [int]$TimeoutSeconds = 60)
    $StartTime = Get-Date
    while (((Get-Date) - $StartTime).TotalSeconds -lt $TimeoutSeconds) {
        try {
            $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ($Response.StatusCode -eq 200) {
                return $true
            }
        } catch {
            Start-Sleep -Seconds 3
        }
    }
    return $false
}

function Invoke-CommandWithLog {
    param([string]$Command, [string]$WorkDir = $PWD)
    Write-Log "执行: $Command (工作目录: $WorkDir)"
    Push-Location $WorkDir
    $OldErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $Output = Invoke-Expression $Command 2>&1
        $Output | ForEach-Object { Write-Log "  $_" }
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
            throw "命令执行失败，退出码: $LASTEXITCODE"
        }
        return $Output
    } finally {
        $ErrorActionPreference = $OldErrorAction
        Pop-Location
    }
}

function Save-LocalEnvFiles {
    param([string]$Root, [string]$BackupDir)
    $EnvBackupDir = Join-Path $BackupDir "env_files"
    New-Item -ItemType Directory -Path $EnvBackupDir -Force | Out-Null

    foreach ($RelativePath in @("backend\.env", "deployment\.env", "deployment\docker-compose.override.yml")) {
        $Source = Join-Path $Root $RelativePath
        if (Test-Path $Source) {
            $Target = Join-Path $EnvBackupDir ($RelativePath -replace '[\\/]', '__')
            Copy-Item $Source $Target -Force
            Write-Log "  已保护本地配置: $RelativePath"
        }
    }
    return $EnvBackupDir
}

function Restore-LocalEnvFiles {
    param([string]$Root, [string]$EnvBackupDir)
    if (-not $EnvBackupDir -or -not (Test-Path $EnvBackupDir)) {
        return
    }

    $Map = @{
        "backend__.env" = "backend\.env"
        "deployment__.env" = "deployment\.env"
        "deployment__docker-compose.override.yml" = "deployment\docker-compose.override.yml"
    }

    foreach ($Item in $Map.GetEnumerator()) {
        $Source = Join-Path $EnvBackupDir $Item.Key
        if (Test-Path $Source) {
            $Target = Join-Path $Root $Item.Value
            Copy-Item $Source $Target -Force
            Write-Log "  已恢复本地配置: $($Item.Value)"
        }
    }
}

# ============== 准备工作 ==============
# 创建必要目录
foreach ($Dir in @($BackupRoot, $LogDir)) {
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
    }
}

Write-Log "============================================================"
Write-Log "开始部署 - 项目目录: $ProjectRoot"
Write-Log "============================================================"

# 检查项目目录
if (-not (Test-Path $ProjectRoot)) {
    Write-Log "项目目录不存在: $ProjectRoot" "ERROR"
    exit 1
}

# 检查是否为 git 仓库
if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
    Write-Log "不是 git 仓库，请先运行 migrate-to-git.ps1 进行迁移" "ERROR"
    exit 1
}

# 检查 docker
try {
    $null = docker --version
} catch {
    Write-Log "Docker 未安装或未运行" "ERROR"
    exit 1
}

# ============== 1. 记录当前版本 ==============
Push-Location $ProjectRoot
try {
    $CurrentCommit = git rev-parse HEAD
    $CurrentBranch = git rev-parse --abbrev-ref HEAD
    Write-Log "当前分支: $CurrentBranch"
    Write-Log "当前提交: $CurrentCommit"
} finally {
    Pop-Location
}

# ============== 2. 备份 ==============
$BackupDir = $null
$EnvBackupDir = $null
if (-not $SkipBackup) {
    Write-Log "------------------------------------------------------------"
    Write-Log "[1/6] 备份当前版本"
    Write-Log "------------------------------------------------------------"

    $BackupDir = Join-Path $BackupRoot "backup_$Timestamp"
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    $EnvBackupDir = Save-LocalEnvFiles -Root $ProjectRoot -BackupDir $BackupDir

    # 备份提交哈希（用于回滚）
    $CurrentCommit | Out-File -FilePath (Join-Path $BackupDir "commit.txt") -Encoding UTF8

    # 备份 docker 镜像 tag（保留当前镜像作为 backup tag）
    Write-Log "标记当前 Docker 镜像为 backup..."
    try {
        docker tag deployment-backend:latest "deployment-backend:backup_$Timestamp" 2>&1 | Out-Null
        docker tag deployment-frontend:latest "deployment-frontend:backup_$Timestamp" 2>&1 | Out-Null
        Write-Log "  镜像备份完成: backup_$Timestamp"
    } catch {
        Write-Log "  镜像备份失败（首次部署可忽略）: $_" "WARN"
    }

    Write-Log "跳过 MongoDB 备份"

    Write-Log "备份位置: $BackupDir"
} else {
    Write-Log "[1/6] 跳过备份" "WARN"
}

# ============== 3. 拉取最新代码 ==============
Write-Log "------------------------------------------------------------"
Write-Log "[2/6] 拉取最新代码"
Write-Log "------------------------------------------------------------"

Push-Location $ProjectRoot
try {
    Invoke-CommandWithLog "git fetch --all"
    Invoke-CommandWithLog "git reset --hard origin/$Branch"
    Restore-LocalEnvFiles -Root $ProjectRoot -EnvBackupDir $EnvBackupDir

    $NewCommit = git rev-parse HEAD
    $VersionFile = Join-Path $ProjectRoot "backend\VERSION"
    $NewVersion = if (Test-Path $VersionFile) { (Get-Content $VersionFile -Raw).Trim() } else { "v1.0.0" }
    $env:APP_COMMIT = $NewCommit
    $env:APP_VERSION = $NewVersion
    Write-Log "最新提交: $NewCommit"
    Write-Log "最新版本: $NewVersion"

    if ($CurrentCommit -eq $NewCommit) {
        Write-Log "代码无更新，跳过部署"
        exit 0
    }

    # 显示变更摘要
    $ChangedFiles = git diff --name-only $CurrentCommit $NewCommit
    Write-Log "变更文件数: $($ChangedFiles.Count)"
    $ChangedFiles | Select-Object -First 20 | ForEach-Object { Write-Log "  - $_" }
    if ($ChangedFiles.Count -gt 20) {
        Write-Log "  ... 还有 $($ChangedFiles.Count - 20) 个文件"
    }

    # 检查关键配置变更
    $CriticalChanges = @()
    if ($ChangedFiles -match "deployment[/\\]docker-compose\.yml") {
        $CriticalChanges += "docker-compose.yml"
    }
    if ($ChangedFiles -match "deployment[/\\]Dockerfile") {
        $CriticalChanges += "Dockerfile"
    }
    if ($ChangedFiles -match "backend[/\\]requirements\.txt") {
        $CriticalChanges += "requirements.txt（后端依赖）"
    }
    if ($ChangedFiles -match "frontend[/\\]package\.json") {
        $CriticalChanges += "package.json（前端依赖）"
    }
    if ($CriticalChanges.Count -gt 0) {
        Write-Log "检测到关键配置变更: $($CriticalChanges -join ', ')" "WARN"
    }
} finally {
    Pop-Location
}

# ============== 4. 判断是否需要重建镜像 ==============
$NeedRebuildBackend = $false
$NeedRebuildFrontend = $false

if ($ChangedFiles -match "backend[/\\]requirements\.txt|deployment[/\\]Dockerfile\.backend") {
    $NeedRebuildBackend = $true
}
# 后端代码是 bind mount，改 .py 文件不需要重建，但需要重启容器
$BackendCodeChanged = $ChangedFiles -match "backend[/\\].*\.py"

if ($ChangedFiles -match "frontend[/\\]") {
    $NeedRebuildFrontend = $true
}

if ($SkipFrontendBuild) {
    $NeedRebuildFrontend = $false
    Write-Log "跳过前端构建（参数指定）"
}

# ============== 5. 构建镜像 ==============
Write-Log "------------------------------------------------------------"
Write-Log "[3/6] 构建镜像"
Write-Log "------------------------------------------------------------"

Push-Location $DeploymentDir
try {
    if ($NeedRebuildBackend) {
        Write-Log "重新构建后端镜像（依赖有变更）..."
        Invoke-CommandWithLog "docker-compose build backend"
    } else {
        Write-Log "后端镜像无需重建（代码通过 bind mount 挂载）"
    }

    if ($NeedRebuildFrontend) {
        Write-Log "重新构建前端镜像..."
        Invoke-CommandWithLog "docker-compose build frontend"
    } else {
        Write-Log "前端无变更，跳过构建"
    }
} finally {
    Pop-Location
}

# ============== 6. 重启容器 ==============
Write-Log "------------------------------------------------------------"
Write-Log "[4/6] 重启容器"
Write-Log "------------------------------------------------------------"

Push-Location $DeploymentDir
try {
    if ($NeedRebuildFrontend -or $NeedRebuildBackend) {
        # 完整重启
        Invoke-CommandWithLog "docker-compose up -d"
    } elseif ($BackendCodeChanged) {
        # 后端代码变更，只重启后端容器（让 Python 重新加载）
        Write-Log "重启后端容器以加载新代码..."
        Invoke-CommandWithLog "docker-compose restart backend"
    } else {
        Write-Log "无需重启容器"
    }
} finally {
    Pop-Location
}

# ============== 7. 健康检查 ==============
Write-Log "------------------------------------------------------------"
Write-Log "[5/6] 健康检查"
Write-Log "------------------------------------------------------------"

Start-Sleep -Seconds 5  # 等待服务启动

$BackendHealthy = $false
$FrontendHealthy = $false

Write-Log "检查后端 http://localhost:$BackendPort/health ..."
$BackendHealthy = Test-HealthCheck -Url "http://localhost:$BackendPort/health" -TimeoutSeconds $HealthCheckTimeout
if ($BackendHealthy) {
    Write-Log "  后端健康"
} else {
    Write-Log "  后端不健康！" "ERROR"
}

Write-Log "检查前端 http://localhost:$FrontendPort ..."
$FrontendHealthy = Test-HealthCheck -Url "http://localhost:$FrontendPort" -TimeoutSeconds 30
if ($FrontendHealthy) {
    Write-Log "  前端健康"
} else {
    Write-Log "  前端不健康！" "ERROR"
}

# ============== 8. 部署结果处理 ==============
Write-Log "------------------------------------------------------------"
Write-Log "[6/6] 部署结果"
Write-Log "------------------------------------------------------------"

if ($BackendHealthy -and $FrontendHealthy) {
    Write-Log "============================================================"
    Write-Log "部署成功！"
    Write-Log "  分支: $Branch"
    Write-Log "  从: $CurrentCommit"
    Write-Log "  到: $NewCommit"
    Write-Log "============================================================"

    # 清理超过 30 天的备份
    Write-Log "清理过期备份（保留最近 30 天）..."
    Get-ChildItem $BackupRoot -Directory -Filter "backup_*" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        ForEach-Object {
            Write-Log "  删除: $($_.Name)"
            Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }

    # 清理无标签的镜像
    docker image prune -f 2>&1 | Out-Null

    exit 0
} else {
    Write-Log "============================================================" "ERROR"
    Write-Log "健康检查失败，开始自动回滚..." "ERROR"
    Write-Log "============================================================" "ERROR"

    # 回滚 git
    Push-Location $ProjectRoot
    try {
        Invoke-CommandWithLog "git reset --hard $CurrentCommit"
    } finally {
        Pop-Location
    }

    # 回滚镜像
    if ($BackupDir) {
        try {
            docker tag "deployment-backend:backup_$Timestamp" "deployment-backend:latest" 2>&1 | Out-Null
            docker tag "deployment-frontend:backup_$Timestamp" "deployment-frontend:latest" 2>&1 | Out-Null
            Write-Log "镜像已回滚"
        } catch {
            Write-Log "镜像回滚失败: $_" "WARN"
        }
    }

    # 重启容器
    Push-Location $DeploymentDir
    try {
        Invoke-CommandWithLog "docker-compose up -d"
    } finally {
        Pop-Location
    }

    Write-Log "已回滚到提交: $CurrentCommit" "ERROR"
    Write-Log "请检查日志: $LogFile" "ERROR"
    exit 1
}

