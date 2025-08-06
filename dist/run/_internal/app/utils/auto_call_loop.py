import asyncio
from datetime import datetime
import pytz
from app.background.auto_call import check_and_call_next_for_counter

vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")

# Dict lưu reset_event cho từng quầy
reset_events: dict[int, asyncio.Event] = {}

async def auto_call_loop_for_counter(counter_id: int, tenxa_id: int):
    #event = reset_events.setdefault(counter_id, tenxa_id, asyncio.Event())
    event = reset_events.setdefault((counter_id, tenxa_id), asyncio.Event())

    while True:
        try:
            # Chờ 60 giây hoặc bị reset
            await asyncio.wait_for(event.wait(), timeout=60)
            event.clear()

            # Nếu là reset thủ công → không làm gì, chỉ reset thời gian
            continue  # bỏ qua gọi check lần này

        except asyncio.TimeoutError:
            # Timeout bình thường sau 60s → mới gọi check
            try:
                print(f"⏱️ [Quầy {counter_id}] xã {tenxa_id} Auto-call tick lúc {datetime.now(vn_tz).strftime('%Y-%m-%d %H:%M:%S')}")
                await check_and_call_next_for_counter(counter_id, tenxa_id)
            except Exception as e:
                print(f"[auto_call_loop {counter_id}] Lỗi khi gọi: {e}")

        except Exception as e:
            print(f"[auto_call_loop {counter_id}] Lỗi khác: {e}")
