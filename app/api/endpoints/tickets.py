from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app import crud, schemas, database
from typing import List, Optional
from app.api.endpoints.realtime import notify_frontend

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Ticket)
def create_ticket(
    ticket: schemas.TicketCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = Depends()
):
    new_ticket = crud.create_ticket(db, ticket)

    background_tasks.add_task(
        notify_frontend, {
            "event": "ticket_called",
            "ticket_number": new_ticket.number,
            "counter_name": f"Quầy {new_ticket.counter_id}"
        }
    )

    return new_ticket

@router.get("/waiting", response_model=List[schemas.Ticket])
def get_waiting_tickets(
    counter_id: Optional[int] = Query(None, description="ID của quầy (tùy chọn)"),
    db: Session = Depends(get_db)
):
    return crud.get_waiting_tickets(db, counter_id)

@router.put("/{ticket_id}/status", response_model=schemas.Ticket)
def update_ticket_status(ticket_id: int, status_update: schemas.TicketUpdateStatus, db: Session = Depends(get_db)):
    return crud.update_ticket_status(db, ticket_id, status_update)
