@echo off

:: Chạy backend ở cửa sổ mới
cd /d "C:\Users\CNCN\OneDrive\Desktop\Backend\Detect_seat"
"C:\Users\CNCN\AppData\Local\Programs\Python\Python39\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
