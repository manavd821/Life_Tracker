from ast import List
import uuid
from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
## User
# - user_id(PK, Text, default uid)
# - username(TEXT, not null)

class User(Base):
    
    __tablename__ = "user"
    
    user_id : Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True, 
        default=uuid.uuid4,
    )
    username : Mapped[str] = mapped_column(nullable=False)
    
    auth_identities : Mapped[List["AuthIdentity"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan",
    )