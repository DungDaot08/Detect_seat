from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from contextlib import asynccontextmanager

from app.api.endpoints import procedures, tickets, seats, counters, users, realtime
from app.database import engine, Base
from app.background.auto_call import check_and_call_next

# ✅ Khởi tạo DB
Base.metadata.create_all(bind=engine)

# ✅ Khai báo lifespan thay cho on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    @repeat_every(seconds=60)
    async def auto_call_tickets():
        await check_and_call_next()

    # Gọi ngay khi khởi động
    await auto_call_tickets()

    yield  # FastAPI sẽ chạy app từ đây trở đi

    # (Tuỳ chọn) Cleanup khi shutdown (if needed)


# ✅ Tạo app chính
app = FastAPI(
    title="Kiosk API",
    root_path="/app",
    lifespan=lifespan  # 🔄 Dùng lifecycle mới
)

# ✅ CORS config
origins = [
    "https://laysotudong.netlify.app",  # domain frontend
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # (*) Trong production bạn nên dùng: allow_origins=origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Khai báo routers
app.include_router(procedures.router, prefix="/procedures", tags=["Procedures"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
app.include_router(seats.router, prefix="/seats", tags=["Seats"])
app.include_router(counters.router, prefix="/counters", tags=["Counters"])
app.include_router(users.router, prefix="/auths", tags=["Authentication"])
app.include_router(realtime.router)
