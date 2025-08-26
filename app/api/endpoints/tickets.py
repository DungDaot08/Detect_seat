from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, database, redis_client
from typing import List, Optional
from app.api.endpoints.realtime import notify_frontend
from datetime import datetime, timedelta
from pytz import timezone
from app.utils.jwt_ultils import create_ticket_token, verify_ticket_token


vn_tz = timezone("Asia/Ho_Chi_Minh")


router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close() 

def is_within_allowed_ranges(ranges: list) -> bool:
    if not ranges:
        return True  # không cấu hình thì mặc định luôn cho phép
    
    now = datetime.now(vn_tz).time()
    for r in ranges:
        start = datetime.strptime(r["start"], "%H:%M").time()
        end = datetime.strptime(r["end"], "%H:%M").time()
        if start <= now <= end:
            return True
    return False

@router.post("/", response_model=dict)
def create_ticket(
    ticket: schemas.TicketCreate,
    background_tasks: BackgroundTasks,  
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    footer = crud.get_footer_by_tenxa(db, tenxa_id)

    if footer and not is_within_allowed_ranges(footer.allowed_time_ranges or []):
        raise HTTPException(status_code=403, detail="Ngoài giờ làm việc, không thể tạo vé")
    if not redis_client.acquire_ticket_lock(tenxa_id, ticket.counter_id):
        raise HTTPException(status_code=429, detail="Bạn vừa lấy vé, vui lòng chờ vài giây")

    new_ticket = crud.create_ticket(db, tenxa_id, ticket)
    counter_name = crud.get_counter_name_from_counter_id(db, new_ticket.counter_id, tenxa_id)

    # Tạo JWT token cho QR
    token = create_ticket_token({
        "t": new_ticket.number,
        "x": tenxa_id
        #"ci": new_ticket.counter_id
    })

    background_tasks.add_task(
        notify_frontend, {
            "event": "new_ticket",
            "ticket_number": new_ticket.number,
            "counter_name": counter_name,
            "counter_id": new_ticket.counter_id,
            "tenxa": tenxa,
            "token": token  # nếu cần cho kiosk in luôn QR
        }
    )

    return {
        **new_ticket.__dict__,
        "counter_name": counter_name,
        "token": token
    }
    
@router.get("/waiting", response_model=List[schemas.Ticket])
def get_waiting_tickets(
    counter_id: Optional[int] = Query(None, description="ID của quầy (tùy chọn)"),
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    
    return crud.get_waiting_tickets(db, tenxa_id, counter_id)

@router.get("/called", response_model=List[schemas.Ticket])
def get_called_tickets(
    counter_id: Optional[int] = Query(None, description="ID của quầy (tùy chọn)"),
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    
    return crud.get_called_tickets(db, tenxa_id, counter_id)

@router.get("/done", response_model=List[schemas.Ticket])
def get_done_tickets(
    counter_id: Optional[int] = Query(None, description="ID của quầy (tùy chọn)"),
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    
    return crud.get_done_tickets(db, tenxa_id, counter_id)

@router.put("/update_status", response_model=schemas.Ticket)
def update_ticket_status(ticket_number: int, status_update: schemas.TicketUpdateStatus, tenxa: str = Query(...), db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    
    return crud.update_ticket_status(db, tenxa_id, ticket_number, status_update)

@router.get("/{ticket_number}/feedback", response_model=schemas.TicketFeedbackInfo)
def get_ticket_feedback_info(ticket_number: int, tenxa: str, db: Session = Depends(get_db)):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    ticket = crud.get_ticket(db, tenxa_id, ticket_number)

    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy vé")

    if not ticket.finished_at:
        raise HTTPException(status_code=400, detail="Vé chưa được tiếp đón xong")

    # lấy thời gian timeout từ bảng tenxa
    feedback_timeout = crud.get_feedback_timeout(db, tenxa_id)

    # kiểm tra thời gian còn hạn đánh giá
    deadline = ticket.finished_at + timedelta(minutes=feedback_timeout)
    expired = datetime.now(vn_tz) > deadline

    return {
        "ticket_number": ticket.number,
        "status": ticket.status,
        "finished_at": ticket.finished_at,
        #"can_rate": not expired and (ticket.rating is None or ticket.rating == "satisfied"),
        "can_rate": not expired,
        "rating": ticket.rating,
        "feedback": ticket.feedback
    }


@router.post("/{ticket_number}/feedback", response_model=schemas.Ticket)
def submit_ticket_feedback(
    ticket_number: int,
    feedback_data: schemas.TicketRatingUpdate,
    tenxa: str,
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    feedback_timeout = crud.get_feedback_timeout(db, tenxa_id)

    return crud.update_ticket_rating(db, tenxa_id, ticket_number, feedback_data, feedback_timeout)

@router.post("/feedback", response_model=schemas.Ticket)
def submit_ticket_feedback_new(
    feedback_data: schemas.TicketRatingUpdate,
    token: str = Query(...),  # hoặc trong body
    db: Session = Depends(get_db)
):
    payload = verify_ticket_token(token)
    ticket_number = payload["t"]
    tenxa_id = payload["x"]

    #tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    feedback_timeout = crud.get_feedback_timeout(db, tenxa_id)

    return crud.update_ticket_rating(db, tenxa_id, ticket_number, feedback_data, feedback_timeout)

@router.get("/feedback", response_model=schemas.TicketFeedbackInfo)
def get_ticket_feedback_info_new(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    # Giải mã token để lấy thông tin vé
    payload = verify_ticket_token(token)
    ticket_number = payload["t"]
    tenxa_id = payload["x"]
    #counter_id = payload["ci"]

    #tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    ticket = crud.get_ticket(db, tenxa_id, ticket_number)
    counter_name = crud.get_counter_name_from_counter_id(db, ticket.counter_id, tenxa_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Không tìm thấy vé")

    if not ticket.finished_at:
        raise HTTPException(status_code=400, detail="Vé chưa được tiếp đón xong")

    # lấy thời gian timeout từ bảng tenxa
    feedback_timeout = crud.get_feedback_timeout(db, tenxa_id)

    # kiểm tra thời gian còn hạn đánh giá
    deadline = ticket.finished_at + timedelta(minutes=feedback_timeout)
    expired = datetime.now(vn_tz) > deadline

    return {
        "ticket_number": ticket.number,
        "counter_name": counter_name,
        "status": ticket.status,
        "finished_at": ticket.finished_at,
        "can_rate": not expired,
        "rating": ticket.rating,
        "feedback": ticket.feedback
    }

