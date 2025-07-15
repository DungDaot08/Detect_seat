from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

raw_password = "admin123"  # ← thay bằng mật khẩu thật bạn muốn tạo
hashed = pwd_context.hash(raw_password)
print(f"Hashed password:\n{hashed}")
