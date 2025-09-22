# app/api/endpoints/footer.py

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app import crud, schemas, database, models
from app.api.endpoints.realtime import notify_frontend

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=schemas.FooterResponse)
def get_config(tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    if not tenxa_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy xã")

    footer = crud.get_footer_by_tenxa(db, tenxa_id)
    if not footer:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu footer cho xã này")

    return schemas.FooterResponse(
        tenxa=tenxa,
        work_time=footer.work_time,
        hotline=footer.hotline,
        header= footer.header,
        allowed_time_ranges= footer.allowed_time_ranges
    )

@router.post("/", response_model=schemas.FooterResponse)
def update_config(data: schemas.FooterCreate, background_tasks: BackgroundTasks, tenxa: str = Query(...),  db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    if not tenxa_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy xã")

    footer = crud.upsert_footer(db, tenxa_id, data.work_time, data.hotline, data.header, data.allowed_time_ranges)
    
    background_tasks.add_task(
        notify_frontend,
        {
            "event": "update_config",
            "tenxa": tenxa,
        }
    )

    return schemas.FooterResponse(
        tenxa=tenxa,
        work_time=footer.work_time,
        hotline=footer.hotline,
        header= footer.header,
        allowed_time_ranges= footer.allowed_time_ranges
    )

@router.put("/qr_rating", response_model=schemas.TenXaConfigResponse)
def update_QR_raing_config(
    config_data: schemas.TenXaConfigUpdate,
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    tenxa_obj = crud.update_tenxa_config(db, tenxa_id, config_data)
    if not tenxa_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị")
    return tenxa_obj


@router.get("/qr_rating", response_model=schemas.TenXaConfigResponse)
def get_QR_rating_config(tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    tenxa_obj = db.query(models.Tenxa).filter(models.Tenxa.id == tenxa_id).first()
    if not tenxa_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị")
    return tenxa_obj


@router.get("/tenxa_config", response_model=schemas.AccountConfigResponse)
def get_tenxa_config(tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    tenxa_record = db.query(models.Tenxa).filter(models.Tenxa.id == tenxa_id).first()
    if not tenxa_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị")
    return tenxa_record


@router.put("/tenxa_config", response_model=schemas.AccountConfigResponse)
def update_tenxa_config(
    data: schemas.AccountConfigUpdateRequest,
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    tenxa_record = db.query(models.Tenxa).filter(models.Tenxa.id == tenxa_id).first()
    if not tenxa_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị")

    tenxa_record.postfix = data.postfix
    # ⚠️ nếu password cần hash thì dùng:
    # tenxa_record.password = auth.hash_password(data.password)
    tenxa_record.password = data.password

    db.commit()
    db.refresh(tenxa_record)
    return tenxa_record