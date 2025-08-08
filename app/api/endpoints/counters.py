from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app import crud, database, schemas, models
from app.models import Counter, User
from app.schemas import CounterPauseCreate, CounterPauseLog
from app.auth import get_db, get_current_user, check_counter_permission
from typing import Optional, List
from app.api.endpoints.realtime import notify_frontend
from app.utils.auto_call_loop import reset_events
from datetime import datetime
from sqlalchemy import func
import pytz

router = APIRouter()

@router.post("/{counter_id}/call-next/old", response_model=Optional[schemas.CalledTicket])
def call_next_manually(
    counter_id: int,
    background_tasks: BackgroundTasks,
    tenxa: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    check_counter_permission(counter_id, current_user)

    ticket = crud.call_next_ticket(db, tenxa_id, counter_id)
    counter = db.query(Counter).filter(
    Counter.id == ticket.counter_id,
    Counter.tenxa_id == tenxa_id
    ).first()
    if ticket:
        # ✅ Gửi sự kiện WebSocket qua background task
        vn_time = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).isoformat()
        background_tasks.add_task(
            notify_frontend,
            {
                "event": "ticket_called",
                "ticket_number": ticket.number,
                "counter_name": counter.name,
                "tenxa": tenxa,
                "timestamp": vn_time
            }
        )
        event = reset_events.get((counter_id, tenxa_id))
        if event:
            print(f"♻️ Reset auto-call cho quầy {counter_id} xã {tenxa_id}")
            event.set()


        return schemas.CalledTicket(
            number=ticket.number,
            counter_name=ticket.counter.name,
            tenxa=tenxa
        )

    raise HTTPException(status_code=404, detail="Không còn vé để gọi.")

@router.post("/{counter_id}/pause", response_model=CounterPauseLog)
def pause_counter(
    counter_id: int,
    data: CounterPauseCreate,
    tenxa: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    check_counter_permission(counter_id, current_user)

    counter = db.query(Counter).filter(Counter.tenxa_id == tenxa_id).filter(Counter.id == counter_id).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    return crud.pause_counter(db, tenxa_id, counter_id, data.reason)

@router.put("/{counter_id}/resume", response_model=schemas.Counter)
def resume_counter_route(
    counter_id: int,
    tenxa: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    check_counter_permission(counter_id, current_user)

    counter = crud.resume_counter(db, tenxa_id, counter_id=counter_id)
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    return counter

@router.get("/", response_model=List[schemas.Counter])
def get_all_counters(tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    counters = db.query(models.Counter).filter(Counter.tenxa_id == tenxa_id).order_by(models.Counter.id).all()
    return counters

@router.get("/{counter_id}", response_model=schemas.Counter)
def get_counter_by_id(counter_id: int,tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    counter = db.query(models.Counter).filter(Counter.tenxa_id == tenxa_id).filter(models.Counter.id == counter_id).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    return counter

@router.post("/{counter_id}/call-next", response_model=Optional[schemas.CalledTicket])
def call_next_manually(
    counter_id: int,
    background_tasks: BackgroundTasks,
    tenxa: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    check_counter_permission(counter_id, current_user)

    ticket = crud.call_next_ticket(db, tenxa_id, counter_id)

    # Dù có vé hay không, vẫn lấy thông tin quầy để gửi WebSocket
    counter = db.query(Counter).filter(
        Counter.id == counter_id,
        Counter.tenxa_id == tenxa_id
    ).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Không tìm thấy quầy.")

    vn_time = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).isoformat()

    # Gửi sự kiện WebSocket với ticket_number có thể là None
    background_tasks.add_task(
        notify_frontend,
        {
            "event": "ticket_called",
            "ticket_number": ticket.number if ticket else None,
            "counter_name": counter.name,
            "tenxa": tenxa,
            "timestamp": vn_time
        }
    )

    if ticket:
        # Nếu có vé thì reset auto-call và trả về kết quả
        event = reset_events.get((counter_id, tenxa_id))
        if event:
            print(f"♻️ Reset auto-call cho quầy {counter_id} xã {tenxa_id}")
            event.set()

        return schemas.CalledTicket(
            number=ticket.number,
            counter_name=counter.name,
            tenxa=tenxa
        )

    # Không có vé, vẫn gửi sự kiện và trả 204
    return None

@router.post("/upsert-counter", response_model=schemas.Counter)
def upsert_counter(
    tenxa: str,
    data: schemas.CounterUpsertRequest,
    db: Session = Depends(get_db)
):
    # Tìm quầy theo ID
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    counter = db.query(models.Counter).filter(models.Counter.id == data.counter_id).filter(models.Counter.tenxa_id == tenxa_id).first()

    if counter:
        # Nếu đã tồn tại → Cập nhật tên và xã
        counter.name = data.name
    else:
        # Nếu chưa tồn tại → Tạo mới
        max_code = db.query(func.max(models.Counter.code)).scalar() or 0
        counter = models.Counter(
            id=data.counter_id,
            tenxa_id=tenxa_id,
            name=data.name,

            code=max_code + 1
        )
        db.add(counter)

    db.commit()
    db.refresh(counter)
    return counter

@router.delete("/delete-counter")
def delete_counter(
    tenxa: str,
    counter_id: int,
    db: Session = Depends(get_db)
):
    # Lấy tenxa_id
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)

    # Tìm counter theo ID và tenxa_id
    counter = (
        db.query(models.Counter)
        .filter(models.Counter.id == counter_id)
        .filter(models.Counter.tenxa_id == tenxa_id)
        .first()
    )

    if not counter:
        raise HTTPException(status_code=404, detail="Counter không tồn tại")
    db.query(models.CounterPauseLog).filter(
        models.CounterPauseLog.counter_id == counter_id,
        models.CounterPauseLog.tenxa_id == tenxa_id
    ).delete(synchronize_session=False)
    
    seat_ids = db.query(models.Seat.id).filter(
        models.Seat.counter_id == counter_id,
        models.Seat.tenxa_id == tenxa_id
    ).all()
    seat_ids = [s.id for s in seat_ids]

    if seat_ids:
        # Xóa SeatLog trước
        db.query(models.SeatLog).filter(
            models.SeatLog.seat_id.in_(seat_ids),
            models.SeatLog.tenxa_id == tenxa_id
        ).delete(synchronize_session=False)

        # Xóa Seat
        db.query(models.Seat).filter(
            models.Seat.id.in_(seat_ids)
        ).delete(synchronize_session=False)
    
    db.query(models.CounterField).filter(
        models.CounterField.counter_id == counter_id,
        models.CounterField.tenxa_id == tenxa_id
    ).delete(synchronize_session=False)
    
    db.query(models.User).filter(
        models.User.counter_id == counter_id,
        models.User.tenxa_id == tenxa_id
    ).delete(synchronize_session=False)
    
    db.query(models.Ticket).filter(
        models.Ticket.counter_id == counter_id,
        models.Ticket.tenxa_id == tenxa_id
    ).delete(synchronize_session=False)
    db.commit
    # Xóa counter
    db.delete(counter)
    db.commit()

    return {"message": "Xóa counter thành công", "counter_id": counter_id}