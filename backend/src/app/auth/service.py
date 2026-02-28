import datetime
import uuid
from app.auth.models import (
    AuthIdentity, 
    User,
    RefreshToken,
)
from app.core.enums import AuthProvider
from app.core.exceptions import DomainError, ServerError
from app.core.setting import settings
from sqlalchemy import select, update, func
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
            is_verified = True,
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
            message=f"Failed to create user via email: {str(e)}", 
            code="USER_CREATION_VIA_EMAIL_FAILED"
        )
    
    except Exception as e:
        await session.rollback()
        
        raise Exception(str(e))

async def rotate_and_insert_new_refresh_token(
    session : AsyncSession, 
    user_id : uuid.UUID,
    session_id : str,
    new_refresh_token_hash : str,
    user_agent : str,
    db_refresh_token : RefreshToken | None= None, 
    rotate : bool = True,
    ) -> RefreshToken | None:
    # - Insert new refresh token row
    try:
        now = datetime.datetime.now(datetime.UTC)
        # - set rotated_at = now() in old token if rotation is involved
        if rotate and db_refresh_token:
            db_refresh_token.rotated_at = now

        new_refresh_token_db = RefreshToken(
            user_id = user_id,
            hashed_refresh_token = new_refresh_token_hash,
            session_id = session_id,
            expires_at = now + datetime.timedelta(minutes=settings.refresh_token_expires_minutes),
            user_agent = user_agent,
        )
        
        session.add(new_refresh_token_db)
        await session.commit()
        
        return new_refresh_token_db
    except SQLAlchemyError as e:
        await session.rollback()
        await session.refresh(db_refresh_token)
        raise ServerError(
            message=f"Failed to insert new refresh token : {str(e)}",
            code="NEW_REFRESH_TOKEN_INSERTION_FAILED",
        )
    except Exception:
        await session.rollback()
        await session.refresh(db_refresh_token)
        raise
    
async def get_user_by_email(session : AsyncSession, email : str) -> AuthIdentity | None:
    
    try:
        stmt = select(AuthIdentity).where(AuthIdentity.email == email)
        result = await session.scalar(stmt)    
        return result
    
    except SQLAlchemyError as e:
        raise ServerError(
            message=f"Failed to retrieve user from the database: {str(e)}",
            code="USER_FETCH_FAILED",
        )
    except Exception as e:
        raise Exception(str(e))
    
async def get_refresh_token_data_by_hashed_token(session : AsyncSession, hashed_token : str) -> RefreshToken | None:
    
    try:
        stmt = select(RefreshToken).where(RefreshToken.hashed_refresh_token == hashed_token)
        result = await session.scalar(stmt)
        return result
    
    except SQLAlchemyError as e:
        raise ServerError(
            message=f"Failed to retrieve refresh token from the database : {str(e)}",
            code="REFRESH_TOKEN_FETCH_FAILED",
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
    
    except SQLAlchemyError as e:
        await session.rollback()
        await session.refresh(user)
        
        raise ServerError(
            message=f"Failed to update hash password: {str(e)}",
            code="HASH_PASSWORD_UPDATE_FAILED",
        )
        
    except Exception as e:
        await session.rollback()
        await session.refresh(user)
        
        raise Exception(str(e))

async def revoke_all_auth_session(session : AsyncSession, user_id : uuid.UUID) -> uuid.UUID | None:
    """
    revoked all session of the user using user_id
    """
    try:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked_at=func.now())
            )
        
        await session.execute(stmt)
        await session.commit()
        
        return user_id
    except SQLAlchemyError as e:
        await session.rollback()
        
        raise ServerError(
            message=f"Failed to revoke user's all sessions due to an internal error: {str(e)}",
            code="SESSION_REVOCATION_FAILED",
        )
    except Exception:
        await session.rollback()
        raise
    
async def revoke_auth_session_by_token_object(session : AsyncSession, refresh_token_db : RefreshToken):
    try:
        refresh_token_db.revoked_at = datetime.datetime.now(datetime.UTC)
        await session.commit()
        
    except SQLAlchemyError as e:
        await session.rollback()
        
        raise ServerError(
            message=f"Failed to revoke user sessions due to an internal error: {str(e)}",
            code="SESSION_REVOCATION_FAILED",
        )
    except Exception:
        await session.rollback()
        raise
    