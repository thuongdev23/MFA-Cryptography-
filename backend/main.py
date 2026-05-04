from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt, JWTError
import pyotp
import qrcode
import io
import base64
import time

from database import Base, engine, SessionLocal
from models import User, MFAFactor, LoginAttempt
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
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class OTPRequest(BaseModel):
    email: str
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
    existing_user = db.query(User).filter(User.email == request.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    otp_secret = generate_otp_secret()
    password_hash = hash_password(request.password)

    new_user = User(
        email=request.email,
        password_hash=password_hash
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    totp_factor = MFAFactor(
        user_id=new_user.id,
        factor_type="totp",
        secret=otp_secret,
        is_verified=True
    )

    biometric_factor = MFAFactor(
        user_id=new_user.id,
        factor_type="biometric",
        is_verified=False
    )

    db.add(totp_factor)
    db.add(biometric_factor)
    db.commit()

    totp_uri = pyotp.totp.TOTP(otp_secret).provisioning_uri(
        name=request.email,
        issuer_name="MFA-Cryptography-Project"
    )

    qr_code = create_qr_code_base64(totp_uri)

    return {
        "message": "User registered successfully",
        "email": request.email,
        "qr_code": qr_code
    }


@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    start_time = time.time()  
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        db.add(LoginAttempt(email=request.email, success=False))
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    db.add(LoginAttempt(email=request.email, success=True))
    db.commit()

    totp_factor = db.query(MFAFactor).filter(
        MFAFactor.user_id == user.id,
        MFAFactor.factor_type == "totp"
    ).first()

    totp_uri = pyotp.totp.TOTP(totp_factor.secret).provisioning_uri(
        name=user.email,
        issuer_name="MFA-Cryptography-Project"
    )

    qr_code = create_qr_code_base64(totp_uri)

    end_time = time.time()   

    execution_time = (end_time - start_time) * 1000 
    print(f"Login time: {execution_time:.2f} ms")

    return {
        "message": "Password verified. Please enter OTP.",
        "email": user.email,
        "requires_otp": True,
        "qr_code": qr_code
    }

@app.post("/verify-otp")
def verify_otp(request: OTPRequest, db: Session = Depends(get_db)):
    start_time = time.time()

    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    totp_factor = db.query(MFAFactor).filter(
        MFAFactor.user_id == user.id,
        MFAFactor.factor_type == "totp"
    ).first()

    if not totp_factor:
        raise HTTPException(status_code=404, detail="TOTP factor not found")

    if not verify_totp(totp_factor.secret, request.otp_code):
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    if not request.biometric_verified:
        raise HTTPException(status_code=401, detail="Biometric verification failed")

    jwt_start = time.time()

    token = create_access_token(
        data={"sub": user.email}
    )

    jwt_end = time.time()
    jwt_time = (jwt_end - jwt_start) * 1000
    print(f"JWT generation time: {jwt_time:.2f} ms")

    end_time = time.time()
    execution_time = (end_time - start_time) * 1000
    print(f"OTP verification time: {execution_time:.2f} ms")

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