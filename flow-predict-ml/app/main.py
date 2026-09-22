"""
ClaimFlow AI Service - Stage 1

Stage 1 scope: serve the trained claim-risk model over HTTP so it can be
deployed on Render and later called from the Node/Express backend.

    uvicorn app.main:app --reload          # local dev
    uvicorn app.main:app --host 0.0.0.0 --port $PORT   # Render
"""

# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Import/Init Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_prediction import router as prediction_router
from app.api.routes_investigation import router as investigation_router
from app.ml import predict as predict_module

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("claimflow.main")



# ════════════════════════════════════════════════════════════════════════════════════════════════
#                                       Main function Statements
# ════════════════════════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        predict_module.load_model()
        meta = predict_module.get_metadata()
        logger.info(
            "Model loaded: version=%s trained_rows=%s",
            meta.get("model_version"),
            meta.get("training_rows"),
        )
    except Exception as exc:  # noqa: BLE001
        # The service should still start (health checks must pass on Render),
        # but /predict will return 503 until a model is present.
        logger.error("Could not load model at startup: %s", exc)
    yield


app = FastAPI(
    title="ClaimFlow AI Service",
    description=(
        "Internal risk-assessment service for the ClaimFlow claim "
        "investigation platform. Produces model-generated risk/investigation "
        "probabilities -- not fraud determinations. Human investigators make "
        "the final decision."
    ),
    version="0.2.0-stage2",
    lifespan=lifespan,
)

# CORS: Stage 1 is called only from the Node backend (server-to-server), but
# CORS is left open during local development. Tighten ALLOWED_ORIGINS on
# Render once the Node backend's URL is known.
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. The AI service logged the details."},
    )


@app.get("/")
def root():
    return {
        "service": "ClaimFlow AI Service",
        "stage": 1,
        "status": "ok",
        "model_loaded": predict_module.is_loaded(),
    }


@app.get("/health")
def health():
    """Used by Render's health check."""
    meta = predict_module.get_metadata()
    return {
        "status": "healthy" if predict_module.is_loaded() else "degraded",
        "model_loaded": predict_module.is_loaded(),
        "model_version": meta.get("model_version"),
    }


app.include_router(prediction_router, prefix="/api")
app.include_router(investigation_router , prefix="/api")