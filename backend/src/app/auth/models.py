from tkinter import CASCADE
from typing import List
from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Enum, false, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.enums import AuthProvider
import uuid
import datetime 

## User
# - user_id(PK, Text, default uid)
# - username(TEXT, not null)

## AuthIdentity
# - auth_id(PK, Text, default uid)
# - user_id(FK->User.user_id, not null)
# - provider(ENUM : EMAIL, GOOGLE, GITHUB)(not null)
# - email(Text, not null)
# - password_hash(nullable)
# - is_verified(boolean, default false)
# - created_at(not null)
# UNIQUE(provider, email)

class User(Base):
    
    __tablename__ = "users"
    
    user_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True, 
        default=uuid.uuid4,
    )
    username : Mapped[str] = mapped_column(nullable=False)
    
    auth_identities : Mapped[List["AuthIdentity"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan",
    )
    
    refresh_tokens : Mapped[List["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
class AuthIdentity(Base):
    __tablename__ = "auth_identity"
    __table_args__ = (
        UniqueConstraint("provider", "email", name="auth_identity_unique_contraint"),
    )
    
    auth_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True, 
        default=uuid.uuid4,
    )
    user_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False,
    )
    provider : Mapped[AuthProvider] = mapped_column(
        Enum(
            AuthProvider,
            name = "provider",
            native_enum = True,
            create_type = True,
        ),
        nullable=False,
    )
    email : Mapped[str] = mapped_column(nullable=False)
    password_hash : Mapped[str] = mapped_column(nullable=True)
    is_verified : Mapped[bool] = mapped_column(
        nullable=False, 
        server_default=false()
        )
    created_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    user : Mapped["User"] = relationship(back_populates="auth_identities")
  
  ## RefreshToken

# - token_id(PK, Text, default uid)
# - user_id(FK->User.user_id)
# - hashed_refresh_token(Text, unique ,not null)
# - session_id(not null)
# - created_at(not null)
# - expires_at(not null)
# - rotated_at(nullable)
# - revoked_at(nullable)
# - ip_address (nullable)
# - user_agent (nullable)
  
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "session_id", name="refresh_tokens_unique_constraint"),
    )
    
    token_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hashed_refresh_token : Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )
    session_id : Mapped[str] = mapped_column(nullable=False)
    created_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    rotated_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at : Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    ip_address : Mapped[str] = mapped_column(nullable=True)
    user_agent : Mapped[str] = mapped_column(nullable=True)
    
    user : Mapped["User"] = relationship(back_populates="refresh_tokens")