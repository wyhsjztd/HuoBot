@echo off
title 藿藿 环境安装
echo ========================================
echo    🦊 藿藿 环境安装
echo ========================================
echo.
echo 正在安装依赖包，请稍候...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
echo.
echo ========================================
echo    ✅ 安装完成！双击 启动藿藿.bat 开始
echo ========================================
pause
