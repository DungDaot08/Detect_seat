from fastapi import FastAPI
from app.api.endpoints import procedures, tickets, seats, counters, users
from app.database import engine, Base
from fastapi_utils.tasks import repeat_every
from app.background.auto_call import check_and_call_next

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kiosk API",
              root_path="/app")

app.include_router(procedures.router, prefix="/procedures", tags=["Procedures"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
app.include_router(seats.router, prefix="/seats", tags=["Seats"])
app.include_router(counters.router, prefix="/counters", tags=["Counters"])
app.include_router(users.router, prefix="/auths", tags=["Authentication"])
@app.on_event("startup")
@repeat_every(seconds=1)
def auto_call_tickets():
    check_and_call_next()
    