from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt, JWTError
import pyotp
import qrcode
import io
import base64

from database import Base, engine, SessionLocal
from models import User
from auth import (
    hash_password,
    verify_password,
    generate_otp_secret,
    verify_totp,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class OTPRequest(BaseModel):
    username: str
    otp_code: str
    biometric_verified: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_qr_code_base64(uri: str):
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"


@app.get("/")
def root():
    return {"message": "MFA Backend is running"}


@app.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        User.username == request.username
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    otp_secret = generate_otp_secret()
    hashed_pw = hash_password(request.password)

    new_user = User(
        username=request.username,
        hashed_password=hashed_pw,
        otp_secret=otp_secret
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    totp_uri = pyotp.totp.TOTP(otp_secret).provisioning_uri(
        name=request.username,
        issuer_name="MFA-Cryptography-Project"
    )

    qr_code = create_qr_code_base64(totp_uri)

    return {
        "message": "User registered successfully",
        "username": request.username,
        "otp_secret": otp_secret,
        "qr_code": qr_code
    }


@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == request.username
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "message": "Password verified. Please enter OTP.",
        "username": user.username,
        "requires_otp": True
    }


@app.post("/verify-otp")
def verify_otp(request: OTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == request.username
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_totp(user.otp_secret, request.otp_code):
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    if not request.biometric_verified:
        raise HTTPException(status_code=401, detail="Biometric verification failed")

    token = create_access_token(
        data={"sub": user.username}
    )

    return {
        "message": "MFA verification successful",
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/dashboard")
def dashboard(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        scheme, token = authorization.split()

        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    return {
        "message": f"Welcome {username}, you accessed a protected dashboard."
    }