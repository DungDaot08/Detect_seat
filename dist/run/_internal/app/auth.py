from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas, database

# --- CONFIG ---
SECRET_KEY = "your-secret-key"  # Thay bằng biến môi trường khi production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

# --- PASSWORD HASHING ---
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# --- PASSWORD FUNCTIONS ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- AUTHENTICATE ---
def authenticate_user(db: Session, tenxa_id: int, username: str, password: str) -> Optional[models.User]:
    user = db.query(models.User).filter(models.User.tenxa_id == tenxa_id).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# --- TOKEN HANDLING ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- GET CURRENT USER FROM TOKEN ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực người dùng",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# --- ROLE CHECK ---
def get_current_active_user(user: models.User = Depends(get_current_user)) -> models.User:
    return user

def get_admin_user(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới có quyền")
    return user

def get_leader_user(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "leader":
        raise HTTPException(status_code=403, detail="Chỉ lãnh đạo mới có quyền")
    return user

def get_staff_user(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "officer":
        raise HTTPException(status_code=403, detail="Chỉ cán bộ mới có quyền")
    return user

def check_counter_permission(counter_id: int, user: models.User):
    if user.role in ["admin", "leader"]:
        return
    if user.role == "officer" and user.counter_id == counter_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Không có quyền truy cập quầy này"
    )
