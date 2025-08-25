# utils/jwt_utils.py
import jwt
import time
from typing import Dict

SECRET_KEY = "key"  # nên đặt trong config/env
ALGORITHM = "HS256"
EXPIRE_SECONDS = 60 * 30  # 30 phút

def create_ticket_token1(data: Dict, expire_seconds: int = EXPIRE_SECONDS):
    to_encode = data.copy()
    now = int(time.time())
    to_encode.update({
        #"iat": now,
        "exp": now + expire_seconds,
        #"nonce": str(now)  # hoặc uuid4() để tránh reuse
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_ticket_token1(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

from itsdangerous import URLSafeTimedSerializer

SECRET_KEY = "key"
s = URLSafeTimedSerializer(SECRET_KEY)

# Tạo token
def create_ticket_token3(data: dict) -> str:
    return s.dumps(data)

# Verify token
def verify_ticket_token3(token: str, max_age: int = 1800) -> dict:
    return s.loads(token, max_age=max_age)

import base64
import json

def create_ticket_token(payload: dict) -> str:
    data = json.dumps(payload, separators=(",", ":"))  # JSON rút gọn
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")

def verify_ticket_token(token: str) -> dict:
    padded = token + "=" * (-len(token) % 4)  # thêm padding nếu thiếu
    data = base64.urlsafe_b64decode(padded.encode()).decode()
    return json.loads(data)


