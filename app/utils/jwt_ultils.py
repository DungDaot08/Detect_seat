# utils/jwt_utils.py
import jwt
import time
from typing import Dict

SECRET_KEY = "key"  # nên đặt trong config/env
ALGORITHM = "HS256"
EXPIRE_SECONDS = 60 * 30  # 30 phút

def create_ticket_token(data: Dict, expire_seconds: int = EXPIRE_SECONDS):
    to_encode = data.copy()
    now = int(time.time())
    to_encode.update({
        #"iat": now,
        "exp": now + expire_seconds,
        #"nonce": str(now)  # hoặc uuid4() để tránh reuse
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_ticket_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
