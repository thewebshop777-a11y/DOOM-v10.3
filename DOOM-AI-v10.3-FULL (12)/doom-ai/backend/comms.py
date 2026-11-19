"""
DOOM AI — Operations internal communication
Messages, DMs, Threads, Channels.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()

CHANNELS = [
    {"id": "general", "name": "#general"},
    {"id": "ops", "name": "#ops"},
    {"id": "alerts", "name": "#alerts"},
]
MESSAGES = []
THREADS = {}

class Message(BaseModel):
    channel: str = "general"
    text: str
    author: str = "user"
    thread_id: Optional[str] = None
    dm_to: Optional[str] = None

@router.get("/channels")
async def list_channels():
    return {"channels": CHANNELS}

@router.post("/channels")
async def create_channel(name: str):
    cid = name.lower().replace(" ", "-").replace("#", "")
    ch = {"id": cid, "name": f"#{cid}"}
    CHANNELS.append(ch)
    return ch

@router.post("/message")
async def send_message(req: Message):
    msg = {
        "id": f"m{len(MESSAGES)+1}",
        "channel": req.channel,
        "text": req.text,
        "author": req.author,
        "time": datetime.utcnow().isoformat(),
        "thread_id": req.thread_id,
        "dm_to": req.dm_to,
    }
    MESSAGES.append(msg)
    if req.thread_id:
        THREADS.setdefault(req.thread_id, []).append(msg)
    return msg

@router.get("/messages")
async def list_messages(channel: str = "general"):
    return {"messages": [m for m in MESSAGES if m["channel"] == channel and not m.get("dm_to")]}

@router.get("/dm")
async def list_dms(user: str):
    return {"dms": [m for m in MESSAGES if m.get("dm_to") == user or m["author"] == user]}

@router.get("/thread/{thread_id}")
async def get_thread(thread_id: str):
    return {"thread": THREADS.get(thread_id, [])}
