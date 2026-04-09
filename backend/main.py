from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import infer
from app.routers.infer import gnn_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    gnn_service.load()
    yield


app = FastAPI(title="FChord Coach API", lifespan=lifespan)
app.include_router(infer.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
