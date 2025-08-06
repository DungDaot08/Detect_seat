# app/api/endpoints/footer.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app import crud, schemas, database

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=schemas.FooterResponse)
def get_footer(tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    if not tenxa_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy xã")

    footer = crud.get_footer_by_tenxa(db, tenxa_id)
    if not footer:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu footer cho xã này")

    return schemas.FooterResponse(
        tenxa=tenxa,
        work_time=footer.work_time,
        hotline=footer.hotline
    )

@router.post("/", response_model=schemas.FooterResponse)
def update_footer(data: schemas.FooterCreate, tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    if not tenxa_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy xã")

    footer = crud.upsert_footer(db, tenxa_id, data.work_time, data.hotline)

    return schemas.FooterResponse(
        tenxa=tenxa,
        work_time=footer.work_time,
        hotline=footer.hotline
    )
