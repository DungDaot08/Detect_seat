from fastapi import FastAPI
from app.api.endpoints import procedures, tickets, seats, counters, users, realtime
from app.database import engine, Base
from fastapi_utils.tasks import repeat_every
from app.background.auto_call import check_and_call_next
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kiosk API",
              root_path="/app")
origins = [
    "https://laysotudong.netlify.app",  # domain frontend
    # Bạn có thể thêm localhost nếu test local:
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    #allow_origins=origins,              # Chỉ cho phép domain frontend
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],                # Cho phép tất cả method (GET, POST,...)
    allow_headers=["*"],                # Cho phép tất cả headers
)
app.include_router(procedures.router, prefix="/procedures", tags=["Procedures"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
app.include_router(seats.router, prefix="/seats", tags=["Seats"])
app.include_router(counters.router, prefix="/counters", tags=["Counters"])
app.include_router(users.router, prefix="/auths", tags=["Authentication"])
app.include_router(realtime.router)
@app.on_event("startup")
@repeat_every(seconds=60)
def auto_call_tickets():
    check_and_call_next()
    