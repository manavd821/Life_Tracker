from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
## AuthIdentity
# - auth_id(PK, Text, default uid)
# - user_id(FK->User.user_id, not null)
# - provider(ENUM : EMAIL, GOOGLE, GITHUB)
# - email(Text, not null)
# - password_hash(nullable)
# - is_verified(boolean, default false)
# - created_at(not null)
# UNIQUE(provider, email)

class AuthIdentity(Base):
    __tablename__ = "auth_identity"
    
    auth_id : Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True, 
        default=uuid.uuid4,
    )
    user_id : Mapped[UUID] = mapped_column(
        ForeignKey("user.user_id"), 
        nullable=False,
    )
    
    user : Mapped["User"] = relationship(back_populates="auth_identities")