from app.core.setting import settings
from fastapi import FastAPI
from app.core.logging import setup_logging
import logging

# load all envs and secrets
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)
logger.info("Applicaton starting", extra={"env" : settings.app_env})


def create_app() -> FastAPI:
    
    from app.auth.router import router as auth_router
    from app.core.utils import (
        add_all_middlewares,
        register_exception_handlers,
    )
    app = FastAPI()
    
    add_all_middlewares(app)
    register_exception_handlers(app)
    
    app.include_router(
        router=auth_router, 
        prefix="/api/v1/auth", 
        tags=["auth"]
    )
    
    return app

app = create_app()   

@app.get('/')
def home():
    return {'msg' : 'Hi'}