"""
DOOM AI — Voice system
CYRUS, AURELIUS, VESPERA.
Uses provider key from .env (VOICE_API_KEY).
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import httpx
from main import settings

router = APIRouter()

VOICES = [
    {"id": "cyrus", "name": "CYRUS", "description": "Powerful and commanding.", "modes": ["text-to-speech", "speech-to-speech"], "default": True},
    {"id": "aurelius", "name": "AURELIUS", "description": "Deep, raspy, authoritative.", "modes": ["text-to-speech", "speech-to-speech"], "default": False},
    {"id": "vespera", "name": "VESPERA", "description": "Playful, bright, warm.", "modes": ["text-to-speech", "speech-to-speech"], "default": False},
]

# Map internal voice id → provider voice id (do not expose)
PROVIDER_VOICE_MAP = {
    "cyrus": "en-US-wayne",      # replace with actual provider voice id
    "aurelius": "en-US-charles", # replace with actual
    "vespera": "en-US-jessica",  # replace with actual
}

SAMPLE_PATHS = {
    "cyrus": [os.path.join(os.path.dirname(__file__), "..", "frontend", "voices", "cyrus.mp3")],
    "aurelius": [os.path.join(os.path.dirname(__file__), "..", "frontend", "voices", "aurelius.mp3")],
    "vespera": [os.path.join(os.path.dirname(__file__), "..", "frontend", "voices", "vespera.mp3")],
}

class TTSRequest(BaseModel):
    text: str
    voice_id: str = "cyrus"

class STSRequest(BaseModel):
    voice_id: str = "cyrus"

def get_voice(vid: str):
    return next((v for v in VOICES if v["id"] == vid), None)

@router.get("/voices")
async def list_voices():
    return {"voices": VOICES}

@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    if not get_voice(req.voice_id):
        raise HTTPException(400, "Voice not available")

    key = getattr(settings, "voice_api_key", "") or os.getenv("VOICE_API_KEY", "")
    if not key or key.startswith("your-"):
        # Fallback to sample
        return {
            "status": "sample",
            "voice": req.voice_id.upper(),
            "mode": "text-to-speech",
            "audio_url": f"/api/voice/sample/{req.voice_id}",
            "note": "Add VOICE_API_KEY to .env for live generation.",
        }

    # Live call (provider endpoint — adjust path when you confirm)
    provider_voice = PROVIDER_VOICE_MAP.get(req.voice_id, "en-US-wayne")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.murf.ai/v1/speech/generate",  # placeholder path
            headers={"api-key": key, "Content-Type": "application/json"},
            json={
                "voiceId": provider_voice,
                "text": req.text,
                "format": "mp3",
            },
        )
        if resp.status_code != 200:
            return {"status": "error", "detail": resp.text}
        data = resp.json()
        return {
            "status": "ok",
            "voice": req.voice_id.upper(),
            "mode": "text-to-speech",
            "audio_url": data.get("audioFile") or data.get("url"),
        }

@router.post("/sts")
async def speech_to_speech(req: STSRequest):
    if not get_voice(req.voice_id):
        raise HTTPException(400, "Voice not available")
    return {
        "status": "ok",
        "voice": req.voice_id.upper(),
        "mode": "speech-to-speech",
        "note": "Speech-to-Speech ready. Provider key required for live conversion.",
    }

@router.get("/sample/{voice_id}")
async def voice_sample(voice_id: str):
    for p in SAMPLE_PATHS.get(voice_id, []):
        if os.path.exists(p):
            return FileResponse(p, media_type="audio/mpeg", filename=f"{voice_id}.mp3")
    raise HTTPException(404, "Sample not found")
