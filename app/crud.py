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
vn_tz = timezone("Asia/Ho_Chi_Minh")

def get_tenxa_id_from_slug(db: Session, slug: str) -> Optional[int]:
    tenxa = db.query(models.Tenxa).filter(models.Tenxa.slug == slug).first()
    return tenxa.id if tenxa else None

def get_slug_from_tenxa_id(db: Session, tenxa_id: int) ->Optional[str]:
    tenxa = db.query(models.Tenxa).filter(models.Tenxa.id == tenxa_id).first()
    return tenxa.slug if tenxa else None

def get_user_by_username(db: Session, tenxa_id: int, username: str):
    return db.query(models.User).filter(models.User.tenxa_id == tenxa_id).filter(models.User.username == username).first()

def create_user(db: Session,tenxa_id: int, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        tenxa_id=tenxa_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session,tenxa_id: int, username: str, password: str):
    user = get_user_by_username(db, tenxa_id, username)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return None
    return user
def get_procedures(db: Session, tenxa_id: int, search: str = "") -> List[models.Procedure]:
    if not search:
        return db.query(models.Procedure).filter(models.Procedure.tenxa_id == tenxa_id).all()

    all_procedures = db.query(models.Procedure).filter(models.Procedure.tenxa_id == tenxa_id).all()
    results = []

    for proc in all_procedures:
        score = fuzz.partial_ratio(search.lower(), proc.name.lower())
        if score > 60:  # ngưỡng độ tương đồng (có thể điều chỉnh)
            results.append((score, proc))

    # Sắp xếp theo độ giống giảm dần
    results.sort(reverse=True, key=lambda x: x[0])
    return [proc for _, proc in results]

def create_ticket_old(db: Session, tenxa_id: int, ticket: schemas.TicketCreate) -> models.Ticket:
    today = datetime.now(timezone("Asia/Ho_Chi_Minh")).date()

    start_of_day = datetime.combine(today, time.min)  # 00:00:00
    end_of_day = datetime.combine(today, time.max)    # 23:59:59.999999

    latest = (
        db.query(models.Ticket)
        .filter(models.Ticket.tenxa_id == tenxa_id)
        #.filter(models.Ticket.counter_id == ticket.counter_id)
        .filter(models.Ticket.created_at >= start_of_day)
        .filter(models.Ticket.created_at <= end_of_day)
        .order_by(models.Ticket.number.desc())
        .first()
    )

    next_number = 1 if not latest else latest.number + 1

    db_ticket = models.Ticket(
        number=next_number,
        counter_id=ticket.counter_id,
        tenxa_id=tenxa_id
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

from datetime import datetime, time, timedelta
from pytz import timezone

def create_ticket(db: Session, tenxa_id: int, ticket: schemas.TicketCreate) -> models.Ticket:
    now = datetime.now(timezone("Asia/Ho_Chi_Minh"))

    if tenxa_id == 0:
        # Reset vé lúc 17:30 hôm nay
        reset_time = datetime.combine(now.date(), time(17, 30, 0), tzinfo=timezone("Asia/Ho_Chi_Minh"))

        if now < reset_time:
            # Nếu chưa đến 17:30, thì lấy mốc reset từ hôm qua
            start_of_range = reset_time - timedelta(days=1)
            end_of_range = reset_time
        else:
            # Nếu sau 17:30, thì lấy từ 17:30 hôm nay đến 17:30 ngày mai
            start_of_range = reset_time
            end_of_range = reset_time + timedelta(days=1)
    else:
        # Xã khác: reset từ 00:00 đến 23:59 cùng ngày
        today = now.date()
        start_of_range = datetime.combine(today, time.min, tzinfo=timezone("Asia/Ho_Chi_Minh"))
        end_of_range = datetime.combine(today, time.max, tzinfo=timezone("Asia/Ho_Chi_Minh"))

    # Tìm vé mới nhất trong khoảng thời gian áp dụng
    latest = (
        db.query(models.Ticket)
        .filter(models.Ticket.tenxa_id == tenxa_id)
        .filter(models.Ticket.created_at >= start_of_range)
        .filter(models.Ticket.created_at <= end_of_range)
        .order_by(models.Ticket.number.desc())
        .first()
    )

    next_number = 1 if not latest else latest.number + 1

    db_ticket = models.Ticket(
        number=next_number,
        counter_id=ticket.counter_id,
        tenxa_id=tenxa_id
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def get_waiting_tickets(db: Session, tenxa_id: int, counter_id: Optional[int] = None):
    #vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    today = datetime.now(vn_tz).date()

    start_of_day = datetime.combine(today, time.min, tzinfo=vn_tz)
    end_of_day = datetime.combine(today, time.max, tzinfo=vn_tz)

    query = db.query(models.Ticket).filter(
        models.Ticket.status == "waiting",
        models.Ticket.created_at >= start_of_day,
        models.Ticket.created_at <= end_of_day
    ).filter(models.Ticket.tenxa_id == tenxa_id)

    if counter_id is not None:
        query = query.filter(models.Ticket.counter_id == counter_id)

    return query.order_by(models.Ticket.created_at.asc()).all()

def get_called_tickets(db: Session, tenxa_id: int, counter_id: Optional[int] = None):
    #vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    today = datetime.now(vn_tz).date()

    start_of_day = datetime.combine(today, time.min, tzinfo=vn_tz)
    end_of_day = datetime.combine(today, time.max, tzinfo=vn_tz)

    query = db.query(models.Ticket).filter(
        models.Ticket.status == "called",
        models.Ticket.created_at >= start_of_day,
        models.Ticket.created_at <= end_of_day
    ).filter(models.Ticket.tenxa_id == tenxa_id)

    if counter_id is not None:
        query = query.filter(models.Ticket.counter_id == counter_id)

    return query.order_by(models.Ticket.created_at.asc()).all()
def get_procedures_with_counters1(db: Session, tenxa_id: int, search: str = "") -> List[dict]:
    procedures = db.query(models.Procedure).filter(models.Procedure.tenxa_id == tenxa_id).all()

    results = []

    for proc in procedures:
        # Tính điểm fuzzy so khớp tên thủ tục
        score = fuzz.partial_ratio(search.lower(), proc.name.lower()) if search else 100

        if score >= 80:
            # Tìm các quầy phục vụ thủ tục này thông qua bảng trung gian CounterField
            counter_ids = (
                db.query(models.CounterField.counter_id)
                .filter(models.CounterField.tenxa_id == tenxa_id)
                .filter(models.CounterField.field_id == proc.field_id)
                .distinct()
                .all()
            )
            # Lấy thông tin quầy
            counters = db.query(models.Counter).filter(models.Counter.tenxa_id == tenxa_id).filter(models.Counter.id.in_([c[0] for c in counter_ids])).all()

            results.append({
                "id": proc.id,
                "name": proc.name,
                "field_id": proc.field_id,
                "score": score,
                "counters": [{"id": c.id, "name": c.name} for c in counters]
            })

    # Sắp xếp kết quả theo độ giống giảm dần
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]

def get_procedures_with_counters(db: Session, tenxa_id: int, search: str = "") -> List[dict]:
    procedures = db.query(models.Procedure).filter(models.Procedure.tenxa_id == tenxa_id).all()

    # Tạo danh sách field_id từ procedures để truy 1 lần CounterField
    field_ids = list(set([p.field_id for p in procedures]))
    
    # Truy vấn tất cả CounterField liên quan
    counterfield_map = db.query(models.CounterField).filter(
        models.CounterField.tenxa_id == tenxa_id,
        models.CounterField.field_id.in_(field_ids)
    ).all()
    
    # Tạo mapping từ field_id -> set(counter_id)
    field_to_counters = {}
    for cf in counterfield_map:
        field_to_counters.setdefault(cf.field_id, set()).add(cf.counter_id)
    
    # Lấy tất cả counter_id cần dùng
    all_counter_ids = {cid for cids in field_to_counters.values() for cid in cids}
    counters = db.query(models.Counter).filter(
        models.Counter.tenxa_id == tenxa_id,
        models.Counter.id.in_(all_counter_ids)
    ).all()
    counter_dict = {c.id: {"id": c.id, "name": c.name} for c in counters}

    results = []

    for proc in procedures:
        score = fuzz.token_set_ratio(search.lower(), proc.name.lower()) if search else 100
        if score >= 10:
            counter_ids = field_to_counters.get(proc.field_id, [])
            matched_counters = [counter_dict[cid] for cid in counter_ids if cid in counter_dict]

            results.append({
                "id": proc.id,
                "name": proc.name,
                "field_id": proc.field_id,
                "score": score,
                "counters": matched_counters
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]

def call_next_ticket(db: Session, tenxa_id: int, counter_id: int) -> Optional[Ticket]:
    # Kiểm tra xem quầy có tồn tại không
    now = datetime.now(vn_tz)
    today = now.date()
    start_of_day = datetime.combine(today, time.min, tzinfo=vn_tz)
    end_of_day = datetime.combine(today, time.max, tzinfo=vn_tz)
    counter = db.query(Counter).filter(Counter.id == counter_id).filter(Counter.tenxa_id == tenxa_id).first()
    if not counter:
        return None
    if counter.status != "active":
        return None 
    
    current_ticket = (
        db.query(Ticket)
        .filter(Ticket.tenxa_id == tenxa_id)
        .filter(Ticket.counter_id == counter_id)
        .filter(Ticket.status == "called")
        .order_by(Ticket.created_at)
        .first()
    )
    if current_ticket:
        current_ticket.status = "done"
        current_ticket.finished_at = now
        db.commit()

    # Lấy vé tiếp theo theo quầy đó (giả định: theo thứ tự created_at)
    next_ticket = (
        db.query(Ticket)
        .filter(Ticket.tenxa_id == tenxa_id)
        .filter(Ticket.counter_id == counter_id)
        .filter(Ticket.status == "waiting")
        .filter(Ticket.created_at >= start_of_day)
        .filter(Ticket.created_at <= end_of_day)
        .order_by(Ticket.created_at)
        .first()
    )

    if next_ticket:
        next_ticket.status = "called"
        next_ticket.called_at = now
        db.commit()
        return next_ticket

    return None

def update_ticket_status_old(db: Session, tenxa_id: int, ticket_number: int, status_update: schemas.TicketUpdateStatus):
    ticket = db.query(models.Ticket).filter(models.Ticket.tenxa_id == tenxa_id).filter(models.Ticket.number == ticket_number).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status_update.status
    db.commit()
    db.refresh(ticket)
    return ticket

def update_ticket_status(
    db: Session,
    tenxa_id: int,
    ticket_number: int,
    status_update: schemas.TicketUpdateStatus
):
    ticket = db.query(models.Ticket).filter(
        models.Ticket.tenxa_id == tenxa_id,
        models.Ticket.number == ticket_number
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # ✅ Kiểm tra ngày tạo vé có phải hôm nay không (theo múi giờ VN)
    now = datetime.now(vn_tz)
    if ticket.created_at.astimezone(vn_tz).date() != now.date():
        raise HTTPException(status_code=400, detail="Chỉ được cập nhật vé tạo trong ngày hôm nay")

    # ✅ Cập nhật trạng thái
    ticket.status = status_update.status

    # ✅ Nếu trạng thái là "done", cập nhật thời điểm hoàn tất
    if status_update.status.lower() == "done":
        ticket.finished_at = now

    db.commit()
    db.refresh(ticket)
    return ticket

def pause_counter(db: Session, tenxa_id: int, counter_id: int, reason: str):
    now = datetime.now(vn_tz)  # hoặc datetime.now(vn_tz) nếu dùng múi giờ

    # ✅ Ghi log với thời gian bắt đầu
    log = models.CounterPauseLog(
        counter_id=counter_id,
        reason=reason,
        start_time=now,
        tenxa_id=tenxa_id
    )
    db.add(log)

    # ✅ Cập nhật trạng thái counter
    counter = db.query(models.Counter).filter(models.Counter.tenxa_id == tenxa_id).filter(models.Counter.id == counter_id).first()
    if counter:
        counter.status = "paused"
        counter.reason = reason
        

    db.commit()
    db.refresh(log)
    return log

def resume_counter(db: Session, tenxa_id: int, counter_id: int):
    now = datetime.now(vn_tz)

    counter = db.query(models.Counter).filter(models.Counter.tenxa_id == tenxa_id).filter(models.Counter.id == counter_id).first()
    if not counter:
        return None

    # ✅ Tìm log pause gần nhất CHƯA có end_time
    last_log = (
        db.query(models.CounterPauseLog)
        .filter(
            models.CounterPauseLog.counter_id == counter_id,
            models.CounterPauseLog.end_time == None
        )
        .filter(models.CounterPauseLog.tenxa_id == tenxa_id)
        .order_by(models.CounterPauseLog.start_time.desc())
        .first()
    )

    if last_log:
        last_log.end_time = now

    # ✅ Cập nhật trạng thái quầy
    counter.status = "active"
    counter.reason = None

    db.commit()
    db.refresh(counter)
    return counter

def get_user_by_username(db: Session, tenxa_id: int, username: str):
    return db.query(models.User).filter(models.User.tenxa_id == tenxa_id).filter(models.User.username == username).first()

def create_user(db: Session, tenxa_id: int, user: schemas.UserCreate):
    hashed_password = auth.hash_password(user.password)
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password,
        full_name=user.full_name, 
        role=user.role,
        tenxa_id=tenxa_id,
        counter_id=user.counter_id if user.role == "officer" else None)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, tenxa_id: int, username: str, password: str):
    user = get_user_by_username(db, tenxa_id, username)
    if not user:
        return None
    if not auth.verify_password(password, user.hashed_password):
        return None
    return user

def get_footer_by_tenxa(db: Session, tenxa_id: int):
    return db.query(models.Footer).filter(models.Footer.tenxa_id == tenxa_id).first()

def upsert_footer(db: Session, tenxa_id: int, work_time: str, hotline: str):
    footer = db.query(models.Footer).filter(models.Footer.tenxa_id == tenxa_id).first()
    if footer:
        footer.work_time = work_time
        footer.hotline = hotline
    else:
        footer = models.Footer(tenxa_id=tenxa_id, work_time=work_time, hotline=hotline)
        db.add(footer)
    db.commit()
    db.refresh(footer)
    return footer