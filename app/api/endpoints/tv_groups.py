from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, database, auth, models
from models import TvGroup, Counter
from schemas import TvGroupCreate, TvGroupUpdate, TvGroupResponse, Counter

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Lấy danh sách group (theo xã)
@router.get("/", response_model=List[TvGroupResponse])
def get_tv_groups(tenxa_id: int = Query(...), db: Session = Depends(get_db)):
    groups = db.query(TvGroup).filter(TvGroup.tenxa_id == tenxa_id).all()
    result = []
    for g in groups:
        counters = db.query(Counter).filter(Counter.id.in_(g.counter_ids)).all()
        result.append(
            TvGroupResponse(
                id=g.id,
                name=g.name,
                tenxa_id=g.tenxa_id,
                counter_ids=g.counter_ids,
                counters=counters
            )
        )
    return result


# Tạo group mới
@router.post("/", response_model=TvGroupResponse)
def create_tv_group(group: TvGroupCreate, db: Session = Depends(get_db)):
    db_group = TvGroup(
        name=group.name,
        tenxa_id=group.tenxa_id,
        counter_ids=group.counter_ids
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    counters = db.query(Counter).filter(Counter.id.in_(db_group.counter_ids)).all()
    return TvGroupResponse(
        id=db_group.id,
        name=db_group.name,
        tenxa_id=db_group.tenxa_id,
        counter_ids=db_group.counter_ids,
        counters=counters
    )


# Cập nhật group
@router.put("/{group_id}", response_model=TvGroupResponse)
def update_tv_group(group_id: int, group: TvGroupUpdate, db: Session = Depends(get_db)):
    db_group = db.query(TvGroup).filter(TvGroup.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    db_group.name = group.name
    db_group.tenxa_id = group.tenxa_id
    db_group.counter_ids = group.counter_ids

    db.commit()
    db.refresh(db_group)

    counters = db.query(Counter).filter(Counter.id.in_(db_group.counter_ids)).all()
    return TvGroupResponse(
        id=db_group.id,
        name=db_group.name,
        tenxa_id=db_group.tenxa_id,
        counter_ids=db_group.counter_ids,
        counters=counters
    )


# Xóa group
@router.delete("/{group_id}")
def delete_tv_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(TvGroup).filter(TvGroup.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    db.delete(db_group)
    db.commit()
    return {"message": "Deleted successfully"}


# Lấy danh sách quầy theo group
@router.get("/{group_id}/counters", response_model=List[Counter])
def get_counters_by_group(group_id: int, tenxa_id: int = Query(...), db: Session = Depends(get_db)):
    db_group = db.query(TvGroup).filter(
        TvGroup.id == group_id, TvGroup.tenxa_id == tenxa_id
    ).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    counters = db.query(Counter).filter(Counter.id.in_(db_group.counter_ids)).all()
    return counters
