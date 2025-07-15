# app/api/endpoints/procedures.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, database

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.Procedure])
def list_procedures(search: str = "", db: Session = Depends(get_db)):
    return crud.get_procedures(db, search)

@router.get("/search-extended", response_model=List[schemas.ProcedureSearchResponse])
def search_procedures_with_counters(search: str = "", db: Session = Depends(get_db)):
    return crud.get_procedures_with_counters(db, search)
