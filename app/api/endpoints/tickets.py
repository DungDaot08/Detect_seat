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
    background_tasks: BackgroundTasks,  
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)

    # Gán tenant_id vào ticket
    new_ticket = crud.create_ticket(db, tenxa_id, ticket)

    background_tasks.add_task(
        notify_frontend, {
            "event": "new_ticket",
            "ticket_number": new_ticket.number,
            "counter_id": new_ticket.counter_id,
            "tenxa" : tenxa
        }
    )

    return new_ticket

@router.get("/waiting", response_model=List[schemas.Ticket])
def get_waiting_tickets(
    counter_id: Optional[int] = Query(None, description="ID của quầy (tùy chọn)"),
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    
    return crud.get_waiting_tickets(db, tenxa_id, counter_id)

@router.get("/called", response_model=List[schemas.Ticket])
def get_called_tickets(
    counter_id: Optional[int] = Query(None, description="ID của quầy (tùy chọn)"),
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    
    return crud.get_called_tickets(db, tenxa_id, counter_id)

@router.put("/update_status", response_model=schemas.Ticket)
def update_ticket_status(ticket_number: int, status_update: schemas.TicketUpdateStatus, tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    
    return crud.update_ticket_status(db, tenxa_id, ticket_number, status_update)
