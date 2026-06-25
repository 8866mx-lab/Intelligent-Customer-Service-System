@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动原型预览服务...
echo.
echo 浏览器将打开: http://127.0.0.1:8766/
echo 关闭本窗口即可停止服务。
echo.
start "" "http://127.0.0.1:8766/"
"C:\Users\DELLPC\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\python.exe" -m http.server 8766 --bind 127.0.0.1
