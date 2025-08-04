from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from contextlib import asynccontextmanager
import asyncio
from app.api.endpoints import procedures, tickets, seats, counters, users, realtime, text_to_speech, stats, footer
from app.database import engine, Base, SessionLocal
#from app.background.auto_call import check_and_call_next
from app.models import Counter, Tenxa
from app.utils.auto_call_loop import auto_call_loop_for_counter

# ✅ Khởi tạo DB
Base.metadata.create_all(bind=engine)

# ✅ Khai báo lifespan thay cho on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        # 🔍 Truy vấn tất cả counter_id từ database
        counter_info = db.query(Counter.id, Counter.tenxa_id).join(Tenxa, Counter.tenxa_id == Tenxa.id).filter(Tenxa.auto_call == True).all()
    finally:
        db.close()
    tasks = [asyncio.create_task(auto_call_loop_for_counter(counter_id, tenxa_id)) for counter_id, tenxa_id in counter_info]

    yield

    for task in tasks:
        task.cancel()

# ✅ Khởi tạo FastAPI với lifecycle
app = FastAPI(lifespan=lifespan)


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
app.include_router(text_to_speech.router, prefix="/tts", tags=["Text_to_speech"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(footer.router, prefix="/footers", tags=["Footer"])
app.include_router(realtime.router)
