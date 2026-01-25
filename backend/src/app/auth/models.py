from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Enum, false, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.enums import AuthProvider
import uuid
import datetime 

## AuthIdentity
# - auth_id(PK, Text, default uid)
# - user_id(FK->User.user_id, not null)
# - provider(ENUM : EMAIL, GOOGLE, GITHUB)(not null)
# - email(Text, not null)
# - password_hash(nullable)
# - is_verified(boolean, default false)
# - created_at(not null)
# UNIQUE(provider, email)

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
    user_id : Mapped[UUID] = mapped_column(
        ForeignKey("users.user_id"), 
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