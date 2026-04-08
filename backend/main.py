from fastapi import FastAPI
from app.routers import infer

app = FastAPI(title="FChord Coach API")

app.include_router(infer.router)


@app.get("/health")
def health():
    return {"status": "ok"}
