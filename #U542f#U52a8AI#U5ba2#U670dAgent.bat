@echo off
chcp 65001 >nul
title 跨境电商 AI 客服 Agent

echo ========================================
echo       跨境电商 AI 客服 Agent
echo ========================================
echo.

REM ============================================================
REM 1. 进入项目目录
REM ============================================================

cd /d "C:\Users\Administrator\Desktop\03_工程文件\跨境电商_AI客服Agent_前后端对齐修正版"

echo [1/3] 检查 Docker...

REM ============================================================
REM 2. 检查 Docker 是否已经启动
REM ============================================================

docker info >nul 2>&1

if errorlevel 1 (
    echo Docker Desktop 尚未启动。
    echo 正在启动 Docker Desktop...
    echo.

    start "" "C:\Users\Administrator\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe"

    echo 等待 Docker Desktop 启动...

:WAIT_DOCKER
    timeout /t 3 /nobreak >nul

    docker info >nul 2>&1

    if errorlevel 1 (
        echo Docker 还没有准备好，继续等待...
        goto WAIT_DOCKER
    )
)

echo Docker 已准备完成！
echo.

REM ============================================================
REM 3. 启动 Redis
REM ============================================================

echo [2/3] 启动 Redis...

docker start agent-redis >nul 2>&1

if errorlevel 1 (
    echo Redis 启动失败！
    echo 请检查 Docker 中是否存在 agent-redis 容器。
    pause
    exit /b
)

echo Redis 已启动！
echo.

REM ============================================================
REM 4. 启动 FastAPI
REM ============================================================

echo [3/3] 启动 FastAPI...
echo.

python -m uvicorn app.main:app --reload

echo.
echo FastAPI 已停止。
pause