# ============================================================
# GitHub Webhook 接收器 - Windows Server 版本
# 用途: 监听 GitHub Webhook，自动触发部署脚本
# ============================================================

param(
    [int]$Port = 9000,
    [string]$Secret = "",
    [string]$DeployScript = "D:\Project_Package_20260304_1520\deployment\deploy.ps1",
    [string]$AllowedBranch = "main"
)

$ErrorActionPreference = "Continue"

Write-Host "============================================================"
Write-Host "GitHub Webhook 接收器启动中..."
Write-Host "  监听端口: $Port"
Write-Host "  部署脚本: $DeployScript"
Write-Host "  允许分支: $AllowedBranch"
Write-Host "  Secret: $(if ($Secret) { '已配置' } else { '未配置（不验证签名）' })"
Write-Host "============================================================`n"

# 检查部署脚本是否存在
if (-not (Test-Path $DeployScript)) {
    Write-Host "[ERROR] 部署脚本不存在: $DeployScript" -ForegroundColor Red
    exit 1
}

# 创建 HTTP 监听器
$Listener = New-Object System.Net.HttpListener
$Listener.Prefixes.Add("http://+:$Port/webhook/")
$Listener.Prefixes.Add("http://+:$Port/")

try {
    $Listener.Start()
    Write-Host "[INFO] 监听器已启动: http://localhost:$Port/webhook/" -ForegroundColor Green
    Write-Host "[INFO] 等待 GitHub Webhook 请求...`n"
} catch {
    Write-Host "[ERROR] 启动失败: $_" -ForegroundColor Red
    Write-Host "[提示] 请以管理员身份运行，或先执行:" -ForegroundColor Yellow
    Write-Host "  netsh http add urlacl url=http://+:$Port/ user=Everyone" -ForegroundColor Yellow
    exit 1
}

# 验证 GitHub 签名
function Test-GitHubSignature {
    param(
        [string]$Payload,
        [string]$Signature,
        [string]$Secret
    )
    
    if (-not $Secret) {
        return $true  # 未配置 Secret，跳过验证
    }
    
    if (-not $Signature) {
        return $false
    }
    
    # 移除 "sha256=" 前缀
    $Signature = $Signature -replace '^sha256=', ''
    
    # 计算 HMAC-SHA256
    $hmac = New-Object System.Security.Cryptography.HMACSHA256
    $hmac.Key = [Text.Encoding]::UTF8.GetBytes($Secret)
    $hash = $hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($Payload))
    $expectedSignature = [BitConverter]::ToString($hash).Replace('-', '').ToLower()
    
    return $Signature -eq $expectedSignature
}

# 主循环
while ($Listener.IsListening) {
    try {
        # 等待请求（阻塞）
        $Context = $Listener.GetContext()
        $Request = $Context.Request
        $Response = $Context.Response
        
        $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $ClientIP = $Request.RemoteEndPoint.Address
        
        Write-Host "[$Timestamp] 收到请求: $($Request.HttpMethod) $($Request.Url.PathAndQuery) from $ClientIP"
        
        # 读取请求体
        $Reader = New-Object System.IO.StreamReader($Request.InputStream, $Request.ContentEncoding)
        $Body = $Reader.ReadToEnd()
        $Reader.Close()
        
        # 健康检查端点
        if ($Request.Url.AbsolutePath -eq "/" -or $Request.Url.AbsolutePath -eq "/health") {
            $ResponseText = @{
                status = "running"
                timestamp = $Timestamp
                port = $Port
            } | ConvertTo-Json
            
            $Buffer = [Text.Encoding]::UTF8.GetBytes($ResponseText)
            $Response.ContentType = "application/json"
            $Response.ContentLength64 = $Buffer.Length
            $Response.StatusCode = 200
            $Response.OutputStream.Write($Buffer, 0, $Buffer.Length)
            $Response.Close()
            
            Write-Host "  -> 200 OK (健康检查)" -ForegroundColor Green
            continue
        }
        
        # Webhook 端点
        if ($Request.Url.AbsolutePath -ne "/webhook") {
            $Response.StatusCode = 404
            $Response.Close()
            Write-Host "  -> 404 Not Found" -ForegroundColor Yellow
            continue
        }
        
        # 只接受 POST 请求
        if ($Request.HttpMethod -ne "POST") {
            $Response.StatusCode = 405
            $Response.Close()
            Write-Host "  -> 405 Method Not Allowed" -ForegroundColor Yellow
            continue
        }
        
        # 验证签名
        $Signature = $Request.Headers["X-Hub-Signature-256"]
        if (-not (Test-GitHubSignature -Payload $Body -Signature $Signature -Secret $Secret)) {
            $Response.StatusCode = 403
            $Response.Close()
            Write-Host "  -> 403 Forbidden (签名验证失败)" -ForegroundColor Red
            continue
        }
        
        # 解析 JSON
        try {
            $Payload = $Body | ConvertFrom-Json
        } catch {
            $Response.StatusCode = 400
            $Response.Close()
            Write-Host "  -> 400 Bad Request (JSON 解析失败)" -ForegroundColor Red
            continue
        }
        
        # 检查事件类型
        $Event = $Request.Headers["X-GitHub-Event"]
        Write-Host "  事件类型: $Event"
        
        # 只处理 push 事件
        if ($Event -ne "push") {
            $ResponseText = @{ message = "忽略非 push 事件: $Event" } | ConvertTo-Json
            $Buffer = [Text.Encoding]::UTF8.GetBytes($ResponseText)
            $Response.ContentType = "application/json"
            $Response.ContentLength64 = $Buffer.Length
            $Response.StatusCode = 200
            $Response.OutputStream.Write($Buffer, 0, $Buffer.Length)
            $Response.Close()
            
            Write-Host "  -> 200 OK (忽略事件)" -ForegroundColor Yellow
            continue
        }
        
        # 检查分支
        $Ref = $Payload.ref
        $Branch = $Ref -replace '^refs/heads/', ''
        Write-Host "  分支: $Branch"
        
        if ($Branch -ne $AllowedBranch) {
            $ResponseText = @{ message = "忽略非 $AllowedBranch 分支: $Branch" } | ConvertTo-Json
            $Buffer = [Text.Encoding]::UTF8.GetBytes($ResponseText)
            $Response.ContentType = "application/json"
            $Response.ContentLength64 = $Buffer.Length
            $Response.StatusCode = 200
            $Response.OutputStream.Write($Buffer, 0, $Buffer.Length)
            $Response.Close()
            
            Write-Host "  -> 200 OK (忽略分支)" -ForegroundColor Yellow
            continue
        }
        
        # 提取提交信息
        $Commits = $Payload.commits
        $CommitCount = $Commits.Count
        $Pusher = $Payload.pusher.name
        
        Write-Host "  推送者: $Pusher"
        Write-Host "  提交数: $CommitCount"
        if ($CommitCount -gt 0) {
            $LatestCommit = $Commits[-1]
            Write-Host "  最新提交: $($LatestCommit.id.Substring(0,7)) - $($LatestCommit.message)"
        }
        
        # 返回响应（立即返回，不等待部署完成）
        $ResponseText = @{
            message = "部署任务已启动"
            branch = $Branch
            commits = $CommitCount
        } | ConvertTo-Json
        
        $Buffer = [Text.Encoding]::UTF8.GetBytes($ResponseText)
        $Response.ContentType = "application/json"
        $Response.ContentLength64 = $Buffer.Length
        $Response.StatusCode = 202  # Accepted
        $Response.OutputStream.Write($Buffer, 0, $Buffer.Length)
        $Response.Close()
        
        Write-Host "  -> 202 Accepted (部署任务已启动)" -ForegroundColor Green
        
        # 在后台启动部署脚本
        Write-Host "`n[DEPLOY] 启动部署脚本..." -ForegroundColor Cyan
        $DeployJob = Start-Job -ScriptBlock {
            param($Script, $Branch)
            & $Script -Branch $Branch
        } -ArgumentList $DeployScript, $Branch
        
        Write-Host "[DEPLOY] 部署任务 ID: $($DeployJob.Id)" -ForegroundColor Cyan
        Write-Host "[DEPLOY] 可使用 'Receive-Job $($DeployJob.Id)' 查看输出`n" -ForegroundColor Cyan
        
    } catch {
        Write-Host "[ERROR] 处理请求时出错: $_" -ForegroundColor Red
        try {
            $Response.StatusCode = 500
            $Response.Close()
        } catch {}
    }
}

# 清理
$Listener.Stop()
$Listener.Close()
Write-Host "`n[INFO] Webhook 接收器已停止"
