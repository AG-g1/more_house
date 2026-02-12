# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from backend.api import occupancy, cashflow

app = FastAPI(
    title="More House API",
    description="Occupancy and Cash Flow Management for More House",
    version="0.1.0"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(occupancy.router, prefix="/api/occupancy", tags=["Occupancy"])
app.include_router(cashflow.router, prefix="/api/cashflow", tags=["Cash Flow"])


@app.get("/")
async def root():
    return {"message": "More House API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8001))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
