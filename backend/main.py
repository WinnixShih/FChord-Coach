from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import infer
from app.routers.infer import gnn_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    gnn_service.load()
    yield


app = FastAPI(title="FChord Coach API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(infer.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
