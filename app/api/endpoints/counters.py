from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, database, schemas
from app.models import Counter, User
from app.schemas import CounterPauseCreate, CounterPauseLog
from app.auth import get_db, get_current_user, check_counter_permission
from typing import Optional

router = APIRouter()

@router.post("/{counter_id}/call-next", response_model=Optional[schemas.CalledTicket])
def call_next_manually(
    counter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_counter_permission(counter_id, current_user)

    ticket = crud.call_next_ticket(db, counter_id)
    if ticket:
        return schemas.CalledTicket(
            number=ticket.number,
            counter_name=ticket.counter.name
        )
    raise HTTPException(status_code=404, detail="Không còn vé để gọi.")

@router.post("/{counter_id}/pause", response_model=CounterPauseLog)
def pause_counter(
    counter_id: int,
    data: CounterPauseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_counter_permission(counter_id, current_user)

    counter = db.query(Counter).filter(Counter.id == counter_id).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    return crud.pause_counter(db, counter_id, data.reason)

@router.put("/{counter_id}/resume", response_model=schemas.Counter)
def resume_counter_route(
    counter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_counter_permission(counter_id, current_user)

    counter = crud.resume_counter(db, counter_id=counter_id)
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    return counter


