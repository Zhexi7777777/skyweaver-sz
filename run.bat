@echo off
REM 深圳天气艺术可视化 - 简化运行脚本

echo 启动深圳天气艺术可视化...
E:/skyweaver-sz/.venv/Scripts/python.exe src/main.py %*

if errorlevel 1 (
    echo.
    echo 运行失败，请检查：
    echo 1. Python 环境是否正确配置
    echo 2. 依赖包是否安装完整
    echo 3. 网络连接是否正常
    pause
)