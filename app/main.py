from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.config import CORS_ORIGINS
from app.routers.v1 import router as v1_router

app = FastAPI(title="HR Software API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


app.add_middleware(
    CORSMiddleware,                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
