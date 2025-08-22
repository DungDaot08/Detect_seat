from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, database, auth, models
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
def get_tv_groups(tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    groups = db.query(models.TvGroup).filter(models.TvGroup.tenxa_id == tenxa_id).all()
    result = []
    for g in groups:
        counters = db.query(models.Counter).filter(models.Counter.id.in_(g.counter_ids)).all()
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
def create_tv_group(group: schemas.TvGroupCreate, tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    db_group = models.TvGroup(
        name=group.name,
        tenxa_id=tenxa_id,
        counter_ids=group.counter_ids
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    counters = db.query(models.Counter).filter(models.Counter.id.in_(db_group.counter_ids)).all()
    return schemas.TvGroupResponse(
        id=db_group.id,
        name=db_group.name,
        tenxa_id=db_group.tenxa_id,
        counter_ids=db_group.counter_ids,
        counters=counters
    )


# Cập nhật group
@router.put("/updates", response_model=schemas.TvGroupResponse)
def update_tv_group(group_name: str, group: schemas.TvGroupUpdate, tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    db_group = db.query(models.TvGroup).filter(models.TvGroup.name == group_name).filter(models.TvGroup.tenxa_id == tenxa_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    db_group.name = group.name
    db_group.tenxa_id = tenxa_id
    db_group.counter_ids = group.counter_ids

    db.commit()
    db.refresh(db_group)

    counters = db.query(models.Counter).filter(models.Counter.id.in_(db_group.counter_ids)).all()
    return schemas.TvGroupResponse(
        id=db_group.id,
        name=db_group.name,
        tenxa_id=db_group.tenxa_id,
        counter_ids=db_group.counter_ids,
        counters=counters
    )


# Xóa group
@router.delete("/")
def delete_tv_group(group_name: str, tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    db_group = db.query(models.TvGroup).filter(models.TvGroup.name == group_name).filter(models.TvGroup.tenxa_id == tenxa_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    db.delete(db_group)
    db.commit()
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

    counters = db.query(models.Counter).filter(models.Counter.id.in_(db_group.counter_ids)).all()
    return counters
