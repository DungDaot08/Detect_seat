from fastapi import FastAPI, Query, Depends, APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models import Ticket, SeatLog, Seat  # assuming these are your SQLAlchemy models
from sqlalchemy import func, and_, or_
from app import crud, schemas, database
from collections import defaultdict
from datetime import datetime, timedelta, time
import pytz

#app = FastAPI()
router = APIRouter()
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==== SCHEMAS ====

class TicketsPerCounter(BaseModel):
    counter_id: int
    total_tickets: int

class AttendedTickets(BaseModel):
    counter_id: int
    attended_tickets: int

class AverageHandlingTime(BaseModel):
    counter_id: int
    avg_handling_time_seconds: float

class AbsenceTime(BaseModel):
    counter_id: int
    total_absence_seconds: float

class WorkingTimeCheck(BaseModel):
    counter_id: int
    is_late: bool
    first_checkin: Optional[datetime]
    
class AfkDuration(BaseModel):
    counter_id: int
    total_absent_minutes: float

class AverageWaitingTime(BaseModel):
    counter_id: int
    avg_waiting_time_seconds: float


# ==== UTILS ====

def get_date_range(start: Optional[date], end: Optional[date]):
    today = date.today()
    if not start:
        start = today
    if not end:
        end = today
    return start, end


# ==== ENDPOINTS ====

@router.get("/tickets-per-counter", response_model=List[TicketsPerCounter])
def tickets_per_counter(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    tenxa: str = Query(...),
    db: Session = Depends(get_db),
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    print("start_date:", start_date, "end_date:", end_date)
    start, end = get_date_range(start_date, end_date)

    result = (
        db.query(Ticket.counter_id, func.count().label("total_tickets"))
        .filter(func.date(Ticket.created_at) >= start, func.date(Ticket.created_at) <= end)
        .filter(Ticket.tenxa_id == tenxa_id)
        .group_by(Ticket.counter_id)
        .all()
    )

    items = [
        TicketsPerCounter(counter_id=row[0], total_tickets=row[1])
        for row in result
    ]

    # ✅ Tính tổng tất cả vé
    total = sum(row[1] for row in result)
    #items.append(TicketsPerCounter(counter_id="Tổng", total_tickets=total))

    return items


@router.get("/attended-tickets", response_model=List[AttendedTickets])
def attended_tickets(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    tenxa: str = Query(...),
    db: Session = Depends(get_db),
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    start, end = get_date_range(start_date, end_date)

    result = (
        db.query(Ticket.counter_id, func.count().label("attended_tickets"))
        .filter(
            Ticket.called_at.isnot(None),
            Ticket.finished_at.isnot(None),
            func.date(Ticket.created_at) >= start,
            func.date(Ticket.created_at) <= end,
        )
        .filter(Ticket.tenxa_id == tenxa_id)
        .group_by(Ticket.counter_id)
        .all()
    )

    items = [
        AttendedTickets(counter_id=row[0], attended_tickets=row[1])
        for row in result
    ]

    # ✅ Thêm dòng tổng
    total = sum(row[1] for row in result)
    #items.append(AttendedTickets(counter_id="Tổng", attended_tickets=total))

    return items



@router.get("/average-handling-time", response_model=List[AverageHandlingTime])
def average_handling_time(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    tenxa: str = Query(...),
    db: Session = Depends(get_db),
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    start, end = get_date_range(start_date, end_date)
    result = (
        db.query(
            Ticket.counter_id,
            func.avg(func.extract("epoch", Ticket.finished_at - Ticket.called_at)).label("avg_handling_time_minutes")
        )
        .filter(Ticket.tenxa_id == tenxa_id)
        .filter(
            Ticket.called_at.isnot(None),
            Ticket.finished_at.isnot(None),
            func.date(Ticket.created_at) >= start,
            func.date(Ticket.created_at) <= end,
        )
        .group_by(Ticket.counter_id)
        .all()
    )

    return [
        AverageHandlingTime(counter_id=row[0], avg_handling_time_seconds=row[1])
        for row in result
    ]


@router.get("/working-time-check", response_model=List[WorkingTimeCheck])
def working_time_check(
    date_check: Optional[date] = Query(None),
    tenxa: str = Query(...),
    db: Session = Depends(get_db),
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    date_check = date_check or date.today()
    result = []

    sub = (
        db.query(
            Seat.counter_id,
            func.min(SeatLog.timestamp).label("first_checkin")
        )
        .join(Seat, Seat.id == SeatLog.seat_id)
        .filter(SeatLog.tenxa_id == tenxa_id)
        .filter(
            SeatLog.new_status == True,  # Có mặt
            func.date(SeatLog.timestamp) == date_check
        )
        .group_by(Seat.counter_id)
        .all()
    )

    for counter_id, first_checkin in sub:
        is_late = first_checkin.time() > datetime.strptime("07:30:00", "%H:%M:%S").time()
        result.append(
            WorkingTimeCheck(
                counter_id=counter_id,
                is_late=is_late,
                first_checkin=first_checkin
            )
        )

    return result

@router.get("/afk-duration", response_model=List[AfkDuration])
def afk_duration(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    tenxa: str = Query(...),
    db: Session = Depends(get_db),
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)

    start_date, end_date = get_date_range(start_date, end_date)
    total_afk_per_counter = defaultdict(float)

    seat_logs = (
        db.query(SeatLog)
        .join(Seat, SeatLog.seat_id == Seat.id)
        .filter(SeatLog.tenxa_id == tenxa_id)
        .filter(
            func.date(SeatLog.timestamp) >= start_date,
            func.date(SeatLog.timestamp) <= end_date,
            SeatLog.new_status.in_([True, False])  # 0: vắng mặt, 1: có mặt
        )
        .order_by(SeatLog.seat_id, SeatLog.timestamp)
        .all()
    )

    from itertools import groupby
    grouped_by_seat = groupby(seat_logs, key=lambda log: log.seat_id)

    for seat_id, logs in grouped_by_seat:
        logs = list(logs)
        counter_id = logs[0].seat.counter_id
        prev_status = None
        prev_time = None

        for log in logs:
            current_time = log.timestamp
            current_status = log.new_status

            if prev_status is False and current_status is True:
                afk_start = prev_time
                afk_end = current_time

                tz = afk_start.tzinfo or pytz.timezone("Asia/Ho_Chi_Minh")

                working_start = tz.localize(datetime.combine(afk_start.date(), time(7, 30))) if afk_start.tzinfo is None else datetime.combine(afk_start.date(), time(7, 30)).replace(tzinfo=tz)
                working_end = tz.localize(datetime.combine(afk_end.date(), time(17, 30))) if afk_end.tzinfo is None else datetime.combine(afk_end.date(), time(17, 30)).replace(tzinfo=tz)

                effective_start = max(afk_start, working_start)
                effective_end = min(afk_end, working_end)

                if effective_start < effective_end:
                    duration = (effective_end - effective_start).total_seconds()
                    total_afk_per_counter[counter_id] += duration / 60  # convert to minutes

            prev_status = current_status
            prev_time = current_time

    return [
        AfkDuration(counter_id=k, total_absent_minutes=v)
        for k, v in total_afk_per_counter.items()
    ]

@router.get("/average-waiting-time", response_model=List[AverageWaitingTime])
def average_waiting_time(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    tenxa: str = Query(...),
    db: Session = Depends(get_db),
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    start, end = get_date_range(start_date, end_date)

    result = (
        db.query(
            Ticket.counter_id,
            func.avg(func.extract("epoch", Ticket.called_at - Ticket.created_at)).label("avg_waiting_time_minutes")
        )
        .filter(
            Ticket.created_at.isnot(None),
            Ticket.called_at.isnot(None),
            func.date(Ticket.created_at) >= start,
            func.date(Ticket.created_at) <= end,
        )
        .filter(Ticket.tenxa_id == tenxa_id)
        .group_by(Ticket.counter_id)
        .all()
    )

    return [
        AverageWaitingTime(counter_id=row[0], avg_waiting_time_seconds=row[1])
        for row in result
    ]
