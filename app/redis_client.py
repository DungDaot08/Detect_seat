import os
import redis
from urllib.parse import urlparse

redis_url = os.getenv("REDIS_URL")
url = urlparse(redis_url)

r = redis.Redis(
    host=url.hostname,
    port=url.port,
    password=url.password,
    ssl=url.scheme == "rediss",
    decode_responses=True
)

def acquire_ticket_lock(tenxa_id: int, counter_id: int, cooldown: int = 2) -> bool:
    """
    Trả về True nếu lock thành công (nghĩa là cho phép tạo vé).
    Trả về False nếu request bị lặp trong cooldown giây.
    """
    key = f"ticket_lock:{tenxa_id}:{counter_id}"
    was_set = r.set(key, "1", ex=cooldown, nx=True)  # nx=True: chỉ set nếu chưa tồn tại
    return was_set is not None
