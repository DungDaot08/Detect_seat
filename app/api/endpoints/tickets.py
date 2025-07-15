from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import crud, schemas, database
from typing import List  # ✅ thêm dòng này

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Ticket)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    return crud.create_ticket(db, ticket)