from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Counter, Seat, Ticket
from app.database import SessionLocal

def check_and_call_next():
    db: Session = SessionLocal()
    now = datetime.utcnow()

    counters = db.query(Counter).all()

    for counter in counters:
        seats = counter.seats
        if not seats or len(seats) < 2:
            continue

        # Phân loại ghế
        officer_seat = next((s for s in seats if s.type == 'officer'), None)
        client_seat = next((s for s in seats if s.type == 'client'), None)

        if officer_seat is None or client_seat is None:
            continue  # Quầy chưa có đủ ghế

        # Kiểm tra trạng thái từng ghế
        officer_occupied = officer_seat.occupied
        client_occupied = client_seat.occupied

        # Nếu cán bộ không ngồi → cảnh báo
        if not officer_occupied:
            print(f"⚠️ Không có cán bộ ngồi tại quầy {counter.name}")
            continue

        # Nếu cán bộ đang ngồi & ghế khách trống → gọi vé tiếp theo
        if officer_occupied and not client_occupied:
            next_ticket = (
                db.query(Ticket)
                .join(Ticket.procedure)
                .filter(counter.fields.contains(Ticket.procedure.field))
                .order_by(Ticket.created_at)
                .first()
            )
            if next_ticket:
                print(f"🎯 Gọi vé {next_ticket.number} tại quầy {counter.name}")
                db.delete(next_ticket)  # hoặc đánh dấu đã gọi nếu có trạng thái
                db.commit()

    db.close()
