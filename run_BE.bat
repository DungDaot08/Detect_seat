@echo off
REM chạy python.exe trong cùng thư mục với file .bat
"%~dp0python.exe" "%~dp0fastapi_backend.pyz" %*
