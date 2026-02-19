# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from backend.api import occupancy, cashflow, sync, activity

app = FastAPI(
    title="More House API",
    description="Occupancy and Cash Flow Management for More House",
    version="0.1.0",
    root_path=os.getenv("ROOT_PATH", ""),
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(occupancy.router, prefix="/api/occupancy", tags=["Occupancy"])
app.include_router(cashflow.router, prefix="/api/cashflow", tags=["Cash Flow"])
app.include_router(sync.router, prefix="/api/sync", tags=["Sync"])
app.include_router(activity.router, prefix="/api/activity", tags=["Activity"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


# Serve frontend static files in production
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    # Mount static assets directory — this MUST come last (after all API routes)
    # Using a catch-all route instead of app.mount to avoid routing conflicts
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend SPA - all non-API routes return index.html."""
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8002))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
