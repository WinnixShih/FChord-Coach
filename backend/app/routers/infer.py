from fastapi import APIRouter
from pydantic import BaseModel
from app.services.gnn_service import GNNService
from app.services.vlm_service import VLMService

router = APIRouter()
gnn_service = GNNService()
vlm_service = VLMService()


class Landmark(BaseModel):
    x: float
    y: float
    z: float


class InferRequest(BaseModel):
    landmarks: list[Landmark]  # 21 joints from MediaPipe


class InferResponse(BaseModel):
    error_type: str
    confidence: float
    suggestion: str


@router.post("/infer", response_model=InferResponse)
async def infer(request: InferRequest):
    error_type, confidence = gnn_service.classify(request.landmarks)
    suggestion = await vlm_service.suggest(error_type, request.landmarks)
    return InferResponse(
        error_type=error_type,
        confidence=confidence,
        suggestion=suggestion,
    )
