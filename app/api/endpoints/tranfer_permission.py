from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app import models, schemas, crud
from app.auth import get_db

router = APIRouter()

# A. Lấy danh sách phân quyền
@router.get("/transfer-permissions", response_model=List[schemas.TransferPermissionOut])
def get_transfer_permissions(tenxa: str, db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    permissions = (
        db.query(models.TransferPermission)
        .filter(models.TransferPermission.tenxa_id == tenxa_id)
        .all()
    )

    result = []
    for p in permissions:
        target_names = [
            c.name
            for c in db.query(models.Counter)
            .filter(models.Counter.id.in_(p.target_counter_ids))
            .all()
        ]
        result.append(
            schemas.TransferPermissionOut(
                id=p.id,
                source_counter_id=p.source_counter_id,
                source_counter_name=p.source_counter.name if p.source_counter else None,
                target_counter_ids=p.target_counter_ids,
                target_counter_names=target_names,
                enabled=p.enabled,
                created_at=p.created_at,
                updated_at=p.updated_at,
                tenxa=tenxa,
            )
        )
    return result

# B. Tạo/Cập nhật phân quyền
@router.post("/transfer-permissions")
def upsert_transfer_permission(
    data: schemas.TransferPermissionCreate,
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, data.tenxa)

    permission = (
        db.query(models.TransferPermission)
        .filter(
            models.TransferPermission.tenxa_id == tenxa_id,
            models.TransferPermission.source_counter_id == data.source_counter_id
        )
        .first()
    )

    if permission:
        permission.target_counter_ids = data.target_counter_ids
        permission.enabled = data.enabled
        permission.updated_at = datetime.utcnow()
    else:
        permission = models.TransferPermission(
            tenxa_id=tenxa_id,
            source_counter_id=data.source_counter_id,
            target_counter_ids=data.target_counter_ids,
            enabled=data.enabled,
        )
        db.add(permission)

    db.commit()
    db.refresh(permission)

    return {
        "success": True,
        "message": f"Đã cập nhật quyền chuyển vé cho Quầy {data.source_counter_id}",
        "permission": permission
    }

# C. Kiểm tra quyền cho một quầy cụ thể
@router.get("/transfer-permissions/{counter_id}", response_model=schemas.TransferPermissionCheck)
def check_transfer_permission(counter_id: int, tenxa: str, db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)

    permission = (
        db.query(models.TransferPermission)
        .filter(
            models.TransferPermission.tenxa_id == tenxa_id,
            models.TransferPermission.source_counter_id == counter_id,
            models.TransferPermission.enabled == True
        )
        .first()
    )

    if not permission:
        return {"has_permission": False, "permission": None, "available_targets": []}

    available_targets = []
    for target_id in permission.target_counter_ids:
        counter = db.query(models.Counter).filter(
            models.Counter.tenxa_id == tenxa_id,
            models.Counter.id == target_id
        ).first()
        if counter:
            queue_length = (
                db.query(models.Ticket)
                .filter(
                    models.Ticket.tenxa_id == tenxa_id,
                    models.Ticket.counter_id == target_id,
                    models.Ticket.status == "waiting"
                )
                .count()
            )
            available_targets.append({
                "counter_id": target_id,
                "counter_name": counter.name,
                "current_queue_length": queue_length
            })

    return {
        "has_permission": True,
        "permission": permission,
        "available_targets": available_targets
    }

# D. Xóa phân quyền
@router.delete("/transfer-permissions/{permission_id}")
def delete_transfer_permission(permission_id: int, tenxa: str, db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    permission = db.query(models.TransferPermission).filter(models.TransferPermission.id == permission_id).filter(models.TransferPermission.tenxa_id == tenxa_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    source_counter_name = permission.source_counter.name if permission.source_counter else None

    db.delete(permission)
    db.commit()

    return {
        "success": True,
        "message": f"Đã xóa quyền chuyển vé cho {source_counter_name or 'Counter'}"
    }
