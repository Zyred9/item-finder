@echo off
chcp 65001 >nul
echo ========================================
echo   寻物记后端服务启动
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)
echo ✅ Python 环境正常

echo.
echo [2/2] 启动 FastAPI 服务...
echo 服务地址：http://localhost:8000
echo API 文档：http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python main.py

pause
