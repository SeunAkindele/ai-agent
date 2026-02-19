from fastapi import FastAPI
from app.api.v1.routes_chat import router as chat_router

app = FastAPI(title="Gateway API", version="0.1.0")

app.include_router(chat_router, prefix="/v1")

@app.get("/")
def root():
    return {"service": "gateway-api", "status": "running"}
