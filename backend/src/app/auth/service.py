from app.auth.models import AuthIdentity, User
from app.core.enums import AuthProvider
from app.core.exceptions import  AuthError, ServerError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.db.config import DbSession

async def create_user_with_email_identity(
    session : AsyncSession, 
    username : str, 
    email : str,
    password_hash : str,
    ):
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
        
        print("User and auth created")
        
    except IntegrityError as e:
        await session.rollback()    
        raise AuthError(message=str(e),code="EMAIL_ALREADY_EXISTS")
    
    except SQLAlchemyError as e:
        await session.rollback()
        raise ServerError(message=str(e), code="ERROR_CREATING_USER_WITH_EMAIL")
    
    except Exception as e:
        raise Exception(str(e))

async def get_user_by_email(session : DbSession, email : str):
    stmt = select(AuthIdentity).where(AuthIdentity.email == email)
    result = await session.scalar(stmt)
    
    return result
