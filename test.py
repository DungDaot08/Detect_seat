from passlib.context import CryptContext

# Tạo context với thuật toán bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

if __name__ == "__main__":
    plain_text = input("Nhập mật khẩu: ")
    hashed = get_password_hash(plain_text)
    print(f"Mật khẩu đã được băm:\n{hashed}")
