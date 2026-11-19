"""
DOOM AI — Image / Video generation
Uses best models from the Elite / Pro Max pools.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from openrouter import call_model
from router import doom_wrap

router = APIRouter()

# Best image models from the list
IMAGE_MODELS = {
    "elite": "openai/gpt-image-2.6-sunburst",
    "pro_max": "google/gemini-omni-1.2-flash",
    "pro": "google/gemini-3.8-flash",
    "basic": "deepseek/deepseek-v4.1-flash-1017",
    "free": "openrouter/free",
}

class GenerateRequest(BaseModel):
    prompt: str
    plan: Optional[str] = "pro"
    type: str = "image"  # image | video

@router.post("/generate")
async def generate(req: GenerateRequest):
    model = IMAGE_MODELS.get(req.plan or "pro", IMAGE_MODELS["pro"])
    prompt = f"Generate a detailed visual description for: {req.prompt}"
    result = await call_model(model, prompt)
    output = doom_wrap(result, "content")
    return {
        "status": "generated",
        "type": req.type,
        "model_used": model,
        "plan": req.plan,
        "output": output,
        "note": "Full media binary generation requires additional provider keys. Description ready.",
    }
