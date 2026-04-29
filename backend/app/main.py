from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from backend.app.api.v1.predictions import router as predictions_router
from backend.app.api.stocks import router as stocks_router
from backend.app.api.news import router as news_router
from backend.app.api.sentiment import router as sentiment_router
from backend.app.api.trends import router as trends_router
from backend.app.api.prediction import router as simple_prediction_router


def _load_env_file() -> None:
    """Load a local .env file into process environment (dev convenience).

    This keeps secrets out of code while making `uvicorn --reload` usable
    without requiring shell exports.
    """

    root_env_path = Path(__file__).resolve().parents[2] / ".env"
    backend_env_path = Path(__file__).resolve().parents[2] / "backend" / ".env"
    env_paths = [p for p in (root_env_path, backend_env_path) if p.exists()]
    if not env_paths:
        return

    try:
        for env_path in env_paths:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continuedeactivate

                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                key = k.strip()
                val = v.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        # Never crash app startup because of a malformed local env file
        return


_load_env_file()

app = FastAPI(
    title="Advanced Stock Analysis and Risk Prediction System",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "stock-analysis-api"}

# Register routers
app.include_router(predictions_router)
app.include_router(stocks_router)
app.include_router(news_router)
app.include_router(sentiment_router)
app.include_router(trends_router)
app.include_router(simple_prediction_router)
