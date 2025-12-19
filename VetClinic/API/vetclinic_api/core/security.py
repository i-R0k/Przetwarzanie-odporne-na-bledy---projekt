import jwt
import datetime
import pyotp
import qrcode
import os
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jwt import encode 
import secrets
from vetclinic_api.models.users import Client, Doctor, Consultant

# Ustawienia do JWT
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(plain_password: str) -> str:
    pw_bytes = plain_password.encode("utf-8")
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]
        plain_password = pw_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str):
    # Przeszukujemy wszystkie tabele, aż znajdziemy użytkownika o danym emailu
    user = db.query(Client).filter(Client.email == email).first()
    if user:
        return user
    user = db.query(Doctor).filter(Doctor.email == email).first()
    if user:
        return user
    user = db.query(Consultant).filter(Consultant.email == email).first()
    if user:
        return user
    return None

def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta

    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_totp_secret() -> str:
    """Generuje 16-znakowy secret TOTP."""
    return pyotp.random_base32()

def get_totp_provisioning_uri(email: str, secret: str, issuer: str = "VetClinic") -> str:
    """Generuje URI, które można przekazać do Google Authenticator."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)

def generate_qr_code(uri: str, filename: str = "qrcode.png") -> None:
    """Generuje i zapisuje QR kod na podstawie URI."""
    img = qrcode.make(uri)
    img.save(filename)
