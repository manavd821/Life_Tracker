from app.auth.models import AuthIdentity, User
from app.core.enums import AuthProvider
from app.core.exceptions import DomainError, ServerError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

async def create_user_with_email_identity(
    session : AsyncSession, 
    username : str, 
    email : str,
    password_hash : str,
    ) :
    try:
        user = User(username = username)
        
        auth = AuthIdentity(
            user = user,
            provider = AuthProvider.EMAIL,
            email = email,
            password_hash = password_hash,
        )
        session.add(user)
        session.add(auth)
        await session.commit()
        
        return user, auth
        
    except IntegrityError:
        await session.rollback() 
           
        raise DomainError(
            message="Email already exists",
            code="EMAIL_ALREADY_EXISTS"
        )
    
    except SQLAlchemyError as e:
        await session.rollback()
        
        raise ServerError(
            message="Failed to create user via email", 
            code="USER_CREATION_VIA_EMAIL_FAILED"
        )
    
    except Exception as e:
        await session.rollback()
        
        raise Exception(str(e))

async def get_user_by_email(session : AsyncSession, email : str) -> AuthIdentity | None:
    
    try:
        stmt = select(AuthIdentity).where(AuthIdentity.email == email)
        result = await session.scalar(stmt)        
        return result
    
    except SQLAlchemyError:
        raise ServerError(
            message="Error fetching user by email",
            code="ERROR_FETCHING_USER_BY_EMAIL",
        )
    except Exception as e:
        raise Exception(str(e))
    
async def update_password_hash(
    session : AsyncSession, 
    user : AuthIdentity, 
    new_hash : str
    ) -> AuthIdentity | None:
    
    try:
        user.password_hash = new_hash
        await session.commit()
        
        return user
    
    except SQLAlchemyError:
        await session.rollback()
        
        raise ServerError(
            message="Error fetching user by email",
            code="ERROR_FETCHING_USER_BY_EMAIL",
        )
        
    except Exception as e:
        await session.rollback()
        
        raise Exception(str(e))