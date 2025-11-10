import asyncio
from datetime import datetime, time
from app.database import SessionLocal
from app.models import Counter, Ticket, Seat
from app.api.endpoints.realtime import notify_frontend
from app import crud
import pytz

vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")

async def check_and_call_next_for_counter(counter_id: int, tenxa_id: int):
    db = SessionLocal()
    try:
        now = datetime.now(vn_tz)
        today = now.date()
        start_of_day = datetime.combine(today, time.min, tzinfo=vn_tz)
        end_of_day = datetime.combine(today, time.max, tzinfo=vn_tz)

        counter = db.query(Counter).filter(Counter.tenxa_id == tenxa_id).filter(Counter.id == counter_id).first()
        if not counter:
            print(f"❌ Không tìm thấy quầy với ID {counter_id}")
            return
        if counter.status != "active":
            return  

        #seats = counter.seats
        seats = db.query(Seat).filter(
            Seat.counter_id == counter_id,
            Seat.tenxa_id == tenxa_id
)           .all()

        if not seats or len(seats) < 2:
            return

        officer_seat = next((s for s in seats if s.type == 'officer'), None)
        client_seat = next((s for s in seats if s.type == 'client'), None)

        if officer_seat is None or client_seat is None:
            return
        
        if officer_seat.tenxa_id != tenxa_id or client_seat.tenxa_id != tenxa_id:
            print(f"❌ Seat không thuộc xã {tenxa_id}")
            return

        if not officer_seat.status:
            print(f"⚠️ Không có cán bộ ngồi tại quầy {counter.name} xã {tenxa_id}")
            return

        if officer_seat.status and not client_seat.status:
            # 👉 Đánh dấu vé đang "called" (nếu có) thành "done"
            current_ticket = (
                db.query(Ticket)
                .filter(
                    Ticket.status == "called",
                    Ticket.counter_id == counter.id,
                    Ticket.tenxa_id == tenxa_id
                )
                .order_by(Ticket.called_at.desc())  # Ưu tiên mới nhất nếu có nhiều
                .first()
            )
            if current_ticket:
                current_ticket.status = "done"
                current_ticket.finished_at = now  # nếu có field thời gian kết thúc
                db.commit()

            # 👉 Gọi vé tiếp theo
            next_ticket = (
                db.query(Ticket)
                .filter(
                    Ticket.status == "waiting",
                    Ticket.counter_id == counter.id,
                    Ticket.tenxa_id == tenxa_id
                )
                .filter(Ticket.created_at >= start_of_day)
                .filter(Ticket.created_at <= end_of_day)
                .order_by(Ticket.created_at)
                .first()
            )

            if next_ticket:
                tenxa = crud.get_slug_from_tenxa_id(db, tenxa_id)
                print(f"🎯 Gọi vé {next_ticket.number} tại quầy {counter.name} xã {tenxa}")
                next_ticket.status = "called"
                next_ticket.called_at = now  # nếu có field thời gian gọi
                db.commit()

                vn_time = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).isoformat()
                await notify_frontend({
                    "event": "ticket_called",
                    "ticket_number": next_ticket.number,
                    "counter_name": counter.name,
                    "tenxa": tenxa,
                    "timestamp": vn_time
                })

    except Exception as e:
        print(f"❌ Lỗi khi auto-call cho quầy {counter_id}: {e}")
    finally:
        db.close()
