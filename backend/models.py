from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    phone_number = Column(String(20))
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

    mfa_factors = relationship("MFAFactor", back_populates="user")


class MFAFactor(Base):
    __tablename__ = "mfa_factors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    factor_type = Column(String(20), nullable=False)
    secret = Column(Text)
    phone_number = Column(String(20))
    public_key = Column(Text)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="mfa_factors")


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255))
    success = Column(Boolean)
    ip_address = Column(String(45))
    created_at = Column(DateTime, server_default=func.now())


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    jwt_id = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_mfa_completed = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())