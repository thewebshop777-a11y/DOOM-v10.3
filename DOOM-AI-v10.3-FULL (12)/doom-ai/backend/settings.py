"""
DOOM AI — Settings
Persisted per workspace. Theme, plan, behavior, etc.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from main import SessionLocal
from sqlalchemy import text

router = APIRouter()

class SettingUpdate(BaseModel):
    key: str
    value: str
    workspace_id: str = "web-shop"

@router.get("/")
async def get_settings(workspace_id: str = "web-shop"):
    db = SessionLocal()
    try:
        rows = db.execute(
            text("SELECT key, value FROM settings WHERE workspace_id = :ws"),
            {"ws": workspace_id},
        ).fetchall()
        return {r[0]: r[1] for r in rows}
    finally:
        db.close()

@router.post("/")
async def update_setting(req: SettingUpdate):
    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT OR REPLACE INTO settings (workspace_id, key, value)
                VALUES (:ws, :key, :val)
            """),
            {"ws": req.workspace_id, "key": req.key, "val": req.value},
        )
        db.commit()
    finally:
        db.close()
    return {"status": "saved", "key": req.key, "value": req.value}

@router.get("/theme")
async def get_theme(workspace_id: str = "web-shop"):
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT value FROM settings WHERE workspace_id = :ws AND key = 'theme'"),
            {"ws": workspace_id},
        ).fetchone()
        return {"theme": row[0] if row else "charcoal-green"}
    finally:
        db.close()

@router.post("/theme")
async def set_theme(theme: str, workspace_id: str = "web-shop"):
    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT OR REPLACE INTO settings (workspace_id, key, value)
                VALUES (:ws, 'theme', :val)
            """),
            {"ws": workspace_id, "val": theme},
        )
        db.commit()
    finally:
        db.close()
    return {"status": "saved", "theme": theme}
