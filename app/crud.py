from sqlalchemy.orm import Session
from app import models
from typing import List, Optional
from rapidfuzz import fuzz
from datetime import datetime, time
from sqlalchemy import extract
from app.models import Procedure, Counter, CounterField, Ticket
from app import models, schemas, auth
from passlib.context import CryptContext
from fastapi import HTTPException
from pytz import timezone

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return None
    return user
def get_procedures(db: Session, search: str = "") -> List[models.Procedure]:
    if not search:
        return db.query(models.Procedure).all()

    all_procedures = db.query(models.Procedure).all()
    results = []

    for proc in all_procedures:
        score = fuzz.partial_ratio(search.lower(), proc.name.lower())
        if score > 60:  # ngưỡng độ tương đồng (có thể điều chỉnh)
            results.append((score, proc))

    # Sắp xếp theo độ giống giảm dần
    results.sort(reverse=True, key=lambda x: x[0])
    return [proc for _, proc in results]

def create_ticket(db: Session, ticket: schemas.TicketCreate) -> models.Ticket:
    today = datetime.now(timezone("Asia/Ho_Chi_Minh")).date()

    start_of_day = datetime.combine(today, time.min)  # 00:00:00
    end_of_day = datetime.combine(today, time.max)    # 23:59:59.999999

    latest = (
        db.query(models.Ticket)
        .filter(models.Ticket.counter_id == ticket.counter_id)
        .filter(models.Ticket.created_at >= start_of_day)
        .filter(models.Ticket.created_at <= end_of_day)
        .order_by(models.Ticket.number.desc())
        .first()
    )

    next_number = 1 if not latest else latest.number + 1

    db_ticket = models.Ticket(
        number=next_number,
        counter_id=ticket.counter_id
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def get_waiting_tickets(db: Session, counter_id: Optional[int] = None):
    query = db.query(models.Ticket).filter(models.Ticket.status == "waiting")
    if counter_id is not None:
        query = query.filter(models.Ticket.counter_id == counter_id)
    return query.order_by(models.Ticket.created_at.asc()).all()
def get_procedures_with_counters(db: Session, search: str = "") -> List[dict]:
    procedures = db.query(models.Procedure).all()

    results = []

    for proc in procedures:
        # Tính điểm fuzzy so khớp tên thủ tục
        score = fuzz.partial_ratio(search.lower(), proc.name.lower()) if search else 100

        if score >= 80:
            # Tìm các quầy phục vụ thủ tục này thông qua bảng trung gian CounterField
            counter_ids = (
                db.query(models.CounterField.counter_id)
                .filter(models.CounterField.field_id == proc.field_id)
                .distinct()
                .all()
            )
            # Lấy thông tin quầy
            counters = db.query(models.Counter).filter(models.Counter.id.in_([c[0] for c in counter_ids])).all()

            results.append({
                "id": proc.id,
                "name": proc.name,
                "field_id": proc.field_id,
                "score": score,
                "counters": [{"id": c.id, "name": c.name} for c in counters]
            })

    # Sắp xếp kết quả theo độ giống giảm dần
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

def call_next_ticket(db: Session, counter_id: int) -> Optional[Ticket]:
    # Kiểm tra xem quầy có tồn tại không
    counter = db.query(Counter).filter(Counter.id == counter_id).first()
    if not counter:
        return None

    # Lấy vé tiếp theo theo quầy đó (giả định: theo thứ tự created_at)
    next_ticket = (
        db.query(Ticket)
        .filter(Ticket.counter_id == counter_id)
        .filter(Ticket.status == "waiting")
        .order_by(Ticket.created_at)
        .first()
    )

    if next_ticket:
        next_ticket.status = "called"
        db.commit()
        db.commit()
        return next_ticket

    return None

def update_ticket_status(db: Session, ticket_id: int, status_update: schemas.TicketUpdateStatus):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status_update.status
    db.commit()
    db.refresh(ticket)
    return ticket

def pause_counter(db: Session, counter_id: int, reason: str):
    # ✅ Ghi log
    log = models.CounterPauseLog(counter_id=counter_id, reason=reason)
    db.add(log)

    # ✅ Cập nhật trạng thái counter
    counter = db.query(models.Counter).filter(models.Counter.id == counter_id).first()
    if counter:
        counter.status = "paused"

    db.commit()
    db.refresh(log)
    return log

def resume_counter(db: Session, counter_id: int):
    counter = db.query(models.Counter).filter(models.Counter.id == counter_id).first()
    if not counter:
        return None
    counter.status = "active"
    counter.pause_reason = None
    db.commit()
    db.refresh(counter)
    return counter

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.hash_password(user.password)
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password, 
        role=user.role,
        counter_id=user.counter_id if user.role == "staff" else None)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not auth.verify_password(password, user.hashed_password):
        return None
    return user