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
import pytz

router = APIRouter()

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
