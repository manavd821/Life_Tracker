from fastapi import FastAPI
from app.core.setting import load_settings
from app.core.logging import setup_logging
import logging

# load all envs and secrets
settings = load_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)
logger.info("Applicaton starting", extra={"env" : settings.app_env})


def create_app() -> FastAPI:
    
    from app.auth.router import router as auth_router
    from app.core.utils import (
        register_execption_handler,
        add_all_middlewares,
    )
    
    app = FastAPI()
    
    add_all_middlewares(app)
    
    app.include_router(
        router=auth_router, 
        prefix="/api/v1/auth", 
        tags=["auth"]
    )
    register_execption_handler(app)
    
    return app

app = create_app()   

@app.get('/')
def home():
    return {'msg' : 'Hi'}