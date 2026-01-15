from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(scan_router)
app.include_router(user_router)
app.include_router(data_router)

# Serve frontend static files
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
print(f"Looking for frontend at: {frontend_dist}")
print(f"Frontend exists: {os.path.exists(frontend_dist)}")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dist, "index.html"))
    
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Signal Analyzer Backend Running"}
