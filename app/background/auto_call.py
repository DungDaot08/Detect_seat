from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Counter, Seat, Ticket
from app.database import SessionLocal

def check_and_call_next():
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        counters = db.query(Counter).all()

        for counter in counters:
            seats = counter.seats
            if not seats or len(seats) < 2:
                continue

            officer_seat = next((s for s in seats if s.type == 'officer'), None)
            client_seat = next((s for s in seats if s.type == 'client'), None)

            if officer_seat is None or client_seat is None:
                continue

            if not officer_seat.status:
                print(f"⚠️ Không có cán bộ ngồi tại quầy {counter.name}")
                continue

            if officer_seat.status and not client_seat.status:
                next_ticket = (
                    db.query(Ticket)
                    .filter(
                        Ticket.status == "waiting",
                        Ticket.counter_id == counter.id
                    )
                    .order_by(Ticket.created_at)
                    .first()
                )

                if next_ticket:
                    print(f"🎯 Gọi vé {next_ticket.number} tại quầy {counter.name}")
                    next_ticket.status = "called"
                    db.commit()

    except Exception as e:
        print(f"❌ Lỗi khi auto-call: {e}")
    finally:
        db.close()
