from pathlib import Path
from fastapi import FastAPI
from .router import auth, water_logs, energy_logs, general
from .config import settings
from fastapi.middleware.cors import CORSMiddleware

BASE_PATH = Path(__file__).resolve().parent

app = FastAPI(title="Personal Resource Tracker API")

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )


# Include routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(water_logs.router, prefix="/water-logs", tags=["Water Logs"])
app.include_router(energy_logs.router, prefix="/energy-logs", tags=["Energy Logs"])
app.include_router(general.router, prefix="/general", tags=["General Logs"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug")