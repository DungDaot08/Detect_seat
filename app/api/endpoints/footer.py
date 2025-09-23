# app/api/endpoints/footer.py

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app import crud, schemas, database, models, auth
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
    tenxa_record = db.query(models.Tenxa).filter(models.Tenxa.id == tenxa_id).first()

    return schemas.FooterResponse(
        tenxa=tenxa,
        work_time=footer.work_time,
        hotline=footer.hotline,
        header= footer.header,
        allowed_time_ranges= footer.allowed_time_ranges,
        postfix=tenxa_record.postfix,
        password=tenxa_record.password
    )

@router.post("/old", response_model=schemas.FooterResponse)
def update_config_old(data: schemas.FooterCreate, background_tasks: BackgroundTasks, tenxa: str = Query(...),  db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    if not tenxa_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy xã")

    footer = crud.upsert_footer(db, tenxa_id, data.work_time, data.hotline, data.header, data.allowed_time_ranges)
    tenxa_record = db.query(models.Tenxa).filter(models.Tenxa.id == tenxa_id).first()
    if not tenxa_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị")

    tenxa_record.postfix = data.postfix
    # ⚠️ nếu password cần hash thì dùng:
    # tenxa_record.password = auth.hash_password(data.password)
    tenxa_record.password = data.password

    db.commit()
    db.refresh(tenxa_record)
    
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
        allowed_time_ranges= footer.allowed_time_ranges,
        postfix=tenxa_record.postfix,
        password=tenxa_record.password
    )
    
@router.post("/", response_model=schemas.FooterResponse)
def update_config(
    data: schemas.FooterCreate, 
    background_tasks: BackgroundTasks, 
    tenxa: str = Query(...),  
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    if not tenxa_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy xã")

    footer = crud.upsert_footer(
        db, tenxa_id, data.work_time, data.hotline, data.header, data.allowed_time_ranges
    )

    tenxa_record = db.query(models.Tenxa).filter(models.Tenxa.id == tenxa_id).first()
    if not tenxa_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị")

    try:
        # Cập nhật postfix & password trong Tenxa
        tenxa_record.postfix = data.postfix

        # Hash password mới
        hashed_password = auth.hash_password(data.password)
        tenxa_record.password = data.password  # ⚠️ Lưu plain-text nếu bạn muốn (không khuyến nghị)
        
        # Update tất cả user officer thuộc tenxa
        users = db.query(models.User).filter(models.User.tenxa_id == tenxa_id, models.User.role == "officer").all()
        for user in users:
            if user.counter_id:  # chỉ officer có counter_id
                user.username = f"quay{user.counter_id}.{data.postfix}"
                user.full_name = f"quay{user.counter_id}{data.postfix}"
                user.hashed_password = hashed_password

        db.commit()
        db.refresh(tenxa_record)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi update postfix/password: {e}")

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
        header=footer.header,
        allowed_time_ranges=footer.allowed_time_ranges,
        postfix=tenxa_record.postfix,
        password=tenxa_record.password
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

