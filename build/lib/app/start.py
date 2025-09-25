# app/start.py
import uvicorn

def main():
    # app.main:app = trong file app/main.py có biến "app = FastAPI()"
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()
