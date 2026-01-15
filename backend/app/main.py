from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.user_routes import router as user_router
from app.routes.data_routes import router as data_router
from app.routes.scan_routes import router as scan_router

app = FastAPI(
    title="Signal Analyzer API",
    description="Backend API for Wi-Fi & Bluetooth signal scanning",
    version="1.0.0",
)

# ✅ CORS FIX (IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://wbz-6.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(scan_router)
app.include_router(user_router)
app.include_router(data_router)


@app.get("/")
async def root():
    return {"message": "Signal Analyzer Backend Running"}
