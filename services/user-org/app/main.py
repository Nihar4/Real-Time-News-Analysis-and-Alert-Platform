from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth as auth_router, queries as queries_router, health as health_router
from .kafka_producer import producer
from .db import ensure_password_column

app = FastAPI(title="NewsInsight - User Service (S6)")

# CORS (adjust origins for your frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # Ensure password column present (safe no-op if already there)
    await ensure_password_column()
    # Start Kafka producer
    await producer.start()

@app.on_event("shutdown")
async def on_shutdown():
    await producer.stop()

app.include_router(health_router.router)
app.include_router(auth_router.router)
app.include_router(queries_router.router)
