from fastapi import APIRouter
from pydantic import BaseModel
from app.services.copilot_service import ask_copilot

router = APIRouter(prefix="/chat", tags=["AI Shopping Copilot"])


class ChatRequest(BaseModel):
    question: str
    top_k: int = 3


@router.post("")
def chat(request: ChatRequest):
    """Ask the AI Shopping Copilot a product question — it searches products,
    pulls review insights, and answers grounded in that real data."""
    return ask_copilot(request.question, top_k=request.top_k)
