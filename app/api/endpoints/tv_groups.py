from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, database, auth, models
from app.api.endpoints.realtime import notify_frontend
#from models import TvGroup, Counter
#from schemas import TvGroupCreate, TvGroupUpdate, TvGroupResponse, Counter

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Lấy danh sách group (theo xã)
@router.get("/", response_model=List[schemas.TvGroupResponse])
def get_tv_groups_by_tenxa(tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    groups = db.query(models.TvGroup).filter(models.TvGroup.tenxa_id == tenxa_id).all()
    result = []
    for g in groups:
        counters = db.query(models.Counter).filter(models.Counter.id.in_(g.counter_ids)).filter(models.TvGroup.tenxa_id == tenxa_id).all()
        result.append(
            schemas.TvGroupResponse(
                id=g.id,
                name=g.name,
                tenxa_id=g.tenxa_id,
                counter_ids=g.counter_ids,
                counters=counters
            )
        )
    return result


# Tạo group mới
@router.post("/", response_model=schemas.TvGroupResponse)
def create_tv_group(group: schemas.TvGroupCreate, background_tasks: BackgroundTasks, tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    
    existing_group = db.query(models.TvGroup).filter(
        models.TvGroup.tenxa_id == tenxa_id,
        models.TvGroup.name == group.name
    ).first()

    if existing_group:
        raise HTTPException(
            status_code=400,
            detail=f"Tên nhóm '{group.name}' đã tồn tại trong đơn vị này"
        )
        
    db_group = models.TvGroup(
        name=group.name,
        tenxa_id=tenxa_id,
        counter_ids=group.counter_ids
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    background_tasks.add_task(
        notify_frontend, {
            "event": "new_tv_group",
            "group_name": group.name,
            "counter_ids": group.counter_ids,
            "tenxa" : tenxa
        }
    )

    counters = db.query(models.Counter).filter(models.Counter.id.in_(db_group.counter_ids)).filter(models.Counter.tenxa_id == tenxa_id).all()
    return schemas.TvGroupResponse(
        id=db_group.id,
        name=db_group.name,
        tenxa_id=db_group.tenxa_id,
        counter_ids=db_group.counter_ids,
        counters=counters
    )


# Cập nhật group
@router.put("/updates", response_model=schemas.TvGroupResponse)
def update_tv_group(group_name: str, group: schemas.TvGroupUpdate, background_tasks: BackgroundTasks, tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    db_group = db.query(models.TvGroup).filter(models.TvGroup.name == group_name).filter(models.TvGroup.tenxa_id == tenxa_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    db_group.name = group.name
    db_group.tenxa_id = tenxa_id
    db_group.counter_ids = group.counter_ids

    db.commit()
    db.refresh(db_group)
    
    background_tasks.add_task(
        notify_frontend, {
            "event": "update_tv_group",
            "group_name": group.name,
            "counter_ids": group.counter_ids,
            "tenxa" : tenxa
        }
    )

    counters = db.query(models.Counter).filter(models.Counter.id.in_(db_group.counter_ids)).filter(models.Counter.tenxa_id == tenxa_id).all()
    return schemas.TvGroupResponse(
        id=db_group.id,
        name=db_group.name,
        tenxa_id=db_group.tenxa_id,
        counter_ids=db_group.counter_ids,
        counters=counters
    )


# Xóa group
@router.delete("/")
def delete_tv_group(group_name: str, background_tasks: BackgroundTasks, tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    db_group = db.query(models.TvGroup).filter(models.TvGroup.name == group_name).filter(models.TvGroup.tenxa_id == tenxa_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    db.delete(db_group)
    db.commit()
    background_tasks.add_task(
        notify_frontend, {
            "event": "delete_tv_group",
            "group_name": db_group.name,
            "counter_ids": db_group.counter_ids,
            "tenxa" : tenxa
        }
    )
    return {"message": "Deleted successfully"}


# Lấy danh sách quầy theo group
@router.get("/counters", response_model=List[schemas.Counter])
def get_counters_by_group(group_name: str, tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    db_group = db.query(models.TvGroup).filter(
        models.TvGroup.name == group_name, models.TvGroup.tenxa_id == tenxa_id
    ).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    counters = db.query(models.Counter).filter(models.Counter.id.in_(db_group.counter_ids)).filter(models.Counter.tenxa_id == tenxa_id).all()
    return counters
