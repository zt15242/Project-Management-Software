@echo off
setlocal EnableDelayedExpansion

:: 项目管理系统 Windows 部署脚本
:: 使用方法: deploy.bat [start|stop|restart|logs|build|clean|backup|restore]

:: 设置控制台代码页为 UTF-8
chcp 65001 >nul

:: 项目根目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 定义颜色 (Windows CMD 不直接支持 ANSI 颜色，这里用简单的回显)
:: 如果需要颜色，需要第三方工具或 registry hack，这里保持简单

:: 主程序入口
if "%1"=="" goto interactive_menu
if "%1"=="build" goto build
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="status" goto status
if "%1"=="logs" goto logs
if "%1"=="backup" goto backup
if "%1"=="restore" goto restore
if "%1"=="clean" goto clean
if "%1"=="help" goto show_help
if "%1"=="-h" goto show_help
if "%1"=="--help" goto show_help

echo 错误: 未知命令 '%1'
goto show_help

:interactive_menu
    cls
    echo ==========================================
    echo    项目管理系统部署脚本 (Windows)
    echo ==========================================
    echo.
    echo    1. 构建镜像 (build)
    echo    2. 启动服务 (start)
    echo    3. 停止服务 (stop)
    echo    4. 重启服务 (restart)
    echo    5. 查看状态 (status)
    echo    6. 查看日志 (logs)
    echo    7. 备份数据 (backup)
    echo    8. 清理资源 (clean)
    echo    0. 退出
    echo.
    set /p choice="请选择操作 [0-8]: "
    
    if "%choice%"=="1" call :build & pause & goto interactive_menu
    if "%choice%"=="2" call :start & pause & goto interactive_menu
    if "%choice%"=="3" call :stop & pause & goto interactive_menu
    if "%choice%"=="4" call :restart & pause & goto interactive_menu
    if "%choice%"=="5" call :status & pause & goto interactive_menu
    if "%choice%"=="6" call :logs & pause & goto interactive_menu
    if "%choice%"=="7" call :backup & pause & goto interactive_menu
    if "%choice%"=="8" call :clean & pause & goto interactive_menu
    if "%choice%"=="0" exit /b 0
    if "%choice%"=="" goto interactive_menu
    
    echo 无效的选择，请重试
    pause
    goto interactive_menu

:check_requirements
    echo 正在检查系统要求...
    where docker >nul 2>nul
    if %errorlevel% neq 0 (
        echo [错误] Docker 未安装，请先安装 Docker Desktop for Windows
        exit /b 1
    )
    where docker-compose >nul 2>nul
    if %errorlevel% neq 0 (
        :: 尝试检查 docker compose (v2)
        docker compose version >nul 2>nul
        if %errorlevel% neq 0 (
            echo [错误] Docker Compose 未安装
            exit /b 1
        )
    )
    echo [OK] Docker 和 Docker Compose 已安装
    exit /b 0

:check_env_file
    if not exist ".env" (
        if exist ".env.production" (
            echo [警告] .env 文件不存在，复制 .env.production 使用默认配置
            copy ".env.production" ".env" >nul
            echo [OK] 环境配置已加载
        ) else (
            echo [警告] 未找到 .env 或 .env.production 文件
        )
    )
    exit /b 0

:build
    call :check_requirements
    if %errorlevel% neq 0 exit /b %errorlevel%
    call :check_env_file
    
    echo 开始构建 Docker 镜像...
    set DOCKER_BUILDKIT=1
    docker-compose build
    if %errorlevel% neq 0 (
       echo [错误] 构建失败
       exit /b 1
    )
    echo [OK] Docker 镜像构建完成
    goto :eof

:start
    call :check_requirements
    if %errorlevel% neq 0 exit /b %errorlevel%
    call :check_env_file
    
    echo 启动服务...
    :: 创建必要的目录
    if not exist "data\uploads" mkdir "data\uploads"
    if not exist "data\logs" mkdir "data\logs"
    
    docker-compose up -d
    
    echo [OK] 服务启动成功
    echo.
    echo 服务访问地址:
    echo   - 前端: http://localhost:6004
    echo   - 后端 API: http://localhost:6002
    echo   - API 文档: http://localhost:6002/docs
    echo   - MongoDB: External (External Database Specified)
    goto :eof

:stop
    echo 停止服务...
    docker-compose down
    echo [OK] 服务已停止
    goto :eof

:restart
    call :stop
    call :start
    goto :eof

:status
    echo 服务状态:
    docker-compose ps
    goto :eof

:logs
    if "%2"=="" (
        docker-compose logs -f
    ) else (
        docker-compose logs -f %2
    )
    goto :eof

:clean
    echo 清理 Docker 资源...
    set /p confirm="这将删除所有容器、镜像和卷，确定要继续吗？(y/N) "
    if /i "%confirm%"=="y" (
        docker-compose down -v --rmi all
        echo [OK] 资源清理完成
    ) else (
        echo 取消清理操作
    )
    goto :eof

:backup
    echo 备份数据库...
    if not exist "..\backups" mkdir "..\backups"
    
    :: 获取时间戳 (格式: YYYYMMDD_HHMMSS)
    set "d=%date:~0,4%%date:~5,2%%date:~8,2%"
    set "t=%time:~0,2%%time:~3,2%%time:~6,2%"
    :: 处理小时小于10的情况，前面的空格替换为0
    set "t=%t: =0%"
    set "TIMESTAMP=%d%_%t%"
    set "BACKUP_FILE=..\backups\mongodb_backup_%TIMESTAMP%.archive"
    
    echo [警告] 外部 MongoDB 模式下，此脚本不支持自动备份。请手动备份您的本地数据库。
    goto :eof

:restore
    if "%2"=="" (
        echo [错误] 请指定备份文件路径
        echo 用法: deploy.bat restore ^<backup_file^>
        exit /b 1
    )
    if not exist "%2" (
        echo [错误] 备份文件不存在: %2
        exit /b 1
    )
    
    echo 恢复数据库...
    echo [警告] 外部 MongoDB 模式下，此脚本不支持自动恢复。请手动恢复您的本地数据库。
    goto :eof

:show_help
    echo.
    echo 项目管理系统 Windows 部署脚本
    echo.
    echo 用法: deploy.bat [命令] [选项]
    echo.
    echo 命令:
    echo   build       构建 Docker 镜像
    echo   start       启动所有服务
    echo   stop        停止所有服务
    echo   restart     重启所有服务
    echo   status      显示服务状态
    echo   logs        查看日志 (可选: logs ^<service_name^>)
    echo   backup      备份数据库
    echo   restore     恢复数据库 (需要: restore ^<backup_file^>)
    echo   clean       清理所有 Docker 资源
    echo   help        显示此帮助信息
    echo.
    echo 示例:
    echo   deploy.bat build              # 构建镜像
    echo   deploy.bat start              # 启动服务
    echo   deploy.bat logs backend       # 查看后端日志
    echo.
    goto :eof
