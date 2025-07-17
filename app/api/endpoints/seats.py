from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import pytz
from app import models, schemas, database
from app.utils.auto_call_loop import reset_events

vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.Seat])
def list_seats(db: Session = Depends(get_db)):
    return db.query(models.Seat).all()


@router.put("/{seat_id}", response_model=schemas.Seat)
def update_seat(seat_id: int, seat_update: schemas.SeatUpdate, db: Session = Depends(get_db)):
    seat = db.query(models.Seat).filter(models.Seat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")
    
    old_status = seat.status
    new_status = seat_update.status
    
    # Nếu cập nhật sang trạng thái trống (False), lưu lại thời điểm
    if seat_update.status is False and seat.status is True:
        seat.last_empty_time = datetime.now(vn_tz)

    seat.status = seat_update.status
    
    log = models.SeatLog(
        seat_id=seat_id,
        old_status=old_status,
        new_status=new_status,
        timestamp=datetime.now(vn_tz)
    )
    db.add(log)
    db.commit()
    db.refresh(seat)
    if old_status != new_status:
        event = reset_events.get(seat.counter_id)
        if event:
            print(f"♻️ Reset auto-call cho quầy {seat.counter_id}")
            event.set()

    return seat

@router.get("/{seat_id}", response_model=schemas.Seat)
def get_seat(seat_id: int, db: Session = Depends(get_db)):
    seat = db.query(models.Seat).filter(models.Seat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")
    return seat

@router.get("/counter/{counter_id}", response_model=List[schemas.Seat])
def get_client_seats_by_counter(counter_id: int, db: Session = Depends(get_db)):
    seats = db.query(models.Seat).filter(
        models.Seat.counter_id == counter_id,
        models.Seat.type == "client"
    ).all()

    if not seats:
        raise HTTPException(status_code=404, detail="No client-type seats found for this counter")

    return seats