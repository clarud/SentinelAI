import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import health, jobs, gmail_oauth, gmail_watch

APP_NAME = "SentinelAI API"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
PORT = 8000

app = FastAPI(title=APP_NAME)

if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
async def ping():
    return { "result": "main is active" }


app.include_router(health.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(gmail_oauth.router, prefix="/api", tags=["auth"])
app.include_router(gmail_watch.router, prefix="/api/gmail", tags=["gmail"])
