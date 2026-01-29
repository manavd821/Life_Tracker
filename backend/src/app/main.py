from fastapi import FastAPI
from app.auth.router import router as auth_router
from app.core.register_handlers import register_execption_hander

def create_app() -> FastAPI:
    app = FastAPI()
    
    app.include_router(
        router=auth_router, 
        prefix="/api/v1/auth", 
        tags=["auth"]
    )
    register_execption_hander(app)
    
    return app

app = create_app()   
@app.get('/')
def home():
    return {'msg' : 'Hi'}