import os
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# WebAuthn Passkeys Library
from webauthn import generate_registration_options
from webauthn.helpers.structs import PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity

# 1. Create APIRouter instance
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# 2. Database Setup (SQLite)
DATABASE_URL = "sqlite:///./wasaa_app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

RP_ID = "localhost"
RP_NAME = "waSaa Lifestyle"

# 3. Database Models
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String(10), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    current_challenge = Column(String(255), nullable=True)

class PasskeyDB(Base):
    __tablename__ = "passkeys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credential_id = Column(Text, nullable=False, unique=True)
    public_key = Column(Text, nullable=False)
    sign_count = Column(Integer, default=0)

# Create tables on startup
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 4. Request Schemas
class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Verify2FARequest(BaseModel):
    email: EmailStr
    code: str

# ============================================================================
# Live Email Delivery Engine Configuration (Fixed SMTP setup)
# ============================================================================
SMTP_SERVER = "smtp.gmail.com"  # 👈 Fixed typo: changed from "://gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "naomi.teko@strathmore.edu"  
SENDER_PASSWORD = "icoe jtqo dmam zmph"  # 👈 Cleaned trailing workspace spaces

def send_2fa_email(recipient_email: str, code: str):
    msg = MIMEMultipart()
    msg['From'] = f"waSaa lifestyle <{SENDER_EMAIL}>"
    msg['To'] = recipient_email
    msg['Subject'] = f"{code} is your waSaa verification code"

    body = f"""
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; padding: 20px; max-width: 500px; border: 1px solid #e8e8e8; border-radius: 12px;">
        <h2 style="color: #ff003b; margin-bottom: 4px;">waSaa lifestyle</h2>
        <p style="color: #666666; font-size: 14px; margin-bottom: 24px;">Security Verification Code</p>
        <p style="font-size: 16px; color: #111111;">Your 2FA verification code is:</p>
        <div style="background: #fff0f3; border: 1px solid #ffccd5; padding: 16px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <span style="color: #ff003b; font-size: 32px; font-weight: 800; letter-spacing: 6px; display: inline-block;">{code}</span>
        </div>
        <p style="color: #666666; font-size: 13px;">This verification code is valid for 10 minutes. If you did not request this code, please ignore this email safely.</p>
    </div>
    """
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Secure 2FA code successfully dispatched to inbox: {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to dispatch email via SMTP connection engine: {e}")

# 5. Auth Endpoints
@auth_router.post("/signup")
def signup(req: SignupRequest, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == req.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Account with this email already exists.")

    hashed_pwd = pwd_context.hash(req.password)
    otp = f"{random.randint(1000, 9999)}"

    new_user = UserDB(
        full_name=req.full_name,
        email=req.email,
        hashed_password=hashed_pwd,
        is_verified=False,
        otp_code=otp,
        otp_expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(new_user)
    db.commit()

    bg_tasks.add_task(send_2fa_email, recipient_email=req.email, code=otp)

    return {
        "status": "success",
        "message": f"Account created. 2FA verification code sent to {req.email}"
    }

@auth_router.post("/login")
def login(req: LoginRequest, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == req.email).first()
    if not user or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    otp = f"{random.randint(1000, 9999)}"
    user.otp_code = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.commit()

    bg_tasks.add_task(send_2fa_email, recipient_email=req.email, code=otp)

    return {
        "status": "success",
        "message": f"2FA code sent to {req.email}"
    }

@auth_router.post("/verify-2fa")
def verify_2fa(req: Verify2FARequest, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == req.email).first()
    if not user or user.otp_code != req.code:
        raise HTTPException(status_code=400, detail="Invalid or expired 2FA code.")

    user.is_verified = True
    user.otp_code = None
    db.commit()

    return {
        "status": "success",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email
        }
    }

@auth_router.get("/passkey/register-options")
def passkey_register_options(email: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=str(user.id).encode(),
        user_name=user.email,
        user_display_name=user.full_name,
    )

    user.current_challenge = options.challenge
    db.commit()

    return options
