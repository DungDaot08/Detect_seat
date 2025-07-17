import asyncio
from datetime import datetime
import pytz
from app.background.auto_call import check_and_call_next

reset_event = asyncio.Event()

async def auto_call_loop():
    while True:
        try:
            # ⏱️ Chờ 60 giây hoặc bị reset
            await asyncio.wait_for(reset_event.wait(), timeout=60)
            reset_event.clear()
        except asyncio.TimeoutError:
            # Timeout bình thường sau 60s -> mới chạy check
            try:
                vn_time = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))
                print(f"⏱️ Auto-call tick lúc {vn_time.strftime('%Y-%m-%d %H:%M:%S')}")
                await check_and_call_next()
            except Exception as e:
                print(f"[auto_call_loop] Lỗi: {e}")
        except Exception as e:
            print(f"[auto_call_loop] Lỗi khi chờ: {e}")
