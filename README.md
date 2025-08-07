Yêu cầu hệ thống:
- Python 3.10
- PostgreSQL
- pip

Cài thư viện:
pip install -r requirements.txt

Sửa database url theo database cần dùng:
    DATABASE_URL=postgresql://username:password@localhost/dbname

Chạy server:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Giao diện tài liệu các API hiện có: http://localhost:8000/docs