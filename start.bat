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

cd /d "D:\AI_Project\9.22\ecommerce-ai-agent"

if errorlevel 1 (
    echo [错误] 无法进入项目目录！
    pause
    exit /b 1
)

echo [1/3] 项目目录检查完成
echo.

REM ============================================================
REM 2. 检查 Docker
REM ============================================================

echo [2/3] 检查 Docker...

docker info >nul 2>&1

if errorlevel 1 (
    echo.
    echo [错误] Docker Desktop 没有启动。
    echo 请先手动打开 Docker Desktop，等待它完全启动后再运行本文件。
    echo.
    pause
    exit /b 1
)

echo Docker 已正常运行。
echo.

REM ============================================================
REM 3. 启动 Redis
REM ============================================================

echo 启动 Redis...

docker start agent-redis

if errorlevel 1 (
    echo.
    echo [错误] Redis 启动失败。
    echo 请检查 Docker 中是否存在 agent-redis 容器。
    echo.
    pause
    exit /b 1
)

echo Redis 已启动。
echo.

REM ============================================================
REM 4. 检查当前项目自己的 Python
REM ============================================================

set "PYTHON_EXE=D:\AI_Project\9.22\ecommerce-ai-agent\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo.
    echo [错误] 项目虚拟环境不存在：
    echo %PYTHON_EXE%
    echo.
    pause
    exit /b 1
)

echo 使用项目 Python：
echo %PYTHON_EXE%
echo.

REM ============================================================
REM 5. 启动 FastAPI
REM ============================================================

echo [3/3] 启动 FastAPI...
echo.
echo Swagger:
echo http://127.0.0.1:8000/docs
echo.
echo ========================================
echo       FastAPI 正在运行
echo ========================================
echo.

"%PYTHON_EXE%" -m uvicorn app.main:app --reload

echo.
echo ========================================
echo       FastAPI 已停止
echo ========================================
pause