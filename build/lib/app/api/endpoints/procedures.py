# app/api/endpoints/procedures.py
from fastapi import APIRouter, Depends, Query
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
def list_procedures(search: str = "", tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    return crud.get_procedures(db, tenxa_id, search)

@router.get("/search-extended", response_model=List[schemas.ProcedureSearchResponse])
def search_procedures_with_counters(search: str = "", tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    return crud.get_procedures_with_counters(db, tenxa_id, search)
