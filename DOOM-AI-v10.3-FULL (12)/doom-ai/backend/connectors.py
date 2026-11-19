"""
DOOM AI — Real connectors with persistence
Tracks which workspace has which accounts connected.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
from main import settings, SessionLocal
from sqlalchemy import text

router = APIRouter()

CONNECTORS = [
    {"id": "notion", "name": "Notion", "category": "Productivity", "composio_app": "notion"},
    {"id": "slack", "name": "Slack", "category": "Communication", "composio_app": "slack"},
    {"id": "canva", "name": "Canva", "category": "Design", "composio_app": "canva"},
    {"id": "figma", "name": "Figma", "category": "Design", "composio_app": "figma"},
    {"id": "outlook", "name": "Outlook", "category": "Communication", "composio_app": "outlook"},
    {"id": "teams", "name": "Microsoft Teams", "category": "Communication", "composio_app": "microsoftteams"},
    {"id": "github", "name": "GitHub", "category": "Dev", "composio_app": "github"},
    {"id": "vercel", "name": "Vercel", "category": "Dev", "composio_app": "vercel"},
    {"id": "hubspot", "name": "HubSpot", "category": "CRM", "composio_app": "hubspot"},
    {"id": "zoho", "name": "Zoho CRM", "category": "CRM", "composio_app": "zohocrm"},
    {"id": "salesforce", "name": "Salesforce", "category": "CRM", "composio_app": "salesforce"},
    {"id": "mixpanel", "name": "Mixpanel", "category": "Analytics", "composio_app": "mixpanel"},
    {"id": "amplitude", "name": "Amplitude", "category": "Analytics", "composio_app": "amplitude"},
    {"id": "intercom", "name": "Intercom", "category": "Support", "composio_app": "intercom"},
    {"id": "google-sheets", "name": "Google Sheets", "category": "Productivity", "composio_app": "googlesheets"},
    {"id": "google-docs", "name": "Google Docs", "category": "Productivity", "composio_app": "googledocs"},
    {"id": "google-drive", "name": "Google Drive", "category": "Storage", "composio_app": "googledrive"},
    {"id": "jira", "name": "Jira", "category": "Productivity", "composio_app": "jira"},
    {"id": "supabase", "name": "Supabase", "category": "Dev", "composio_app": "supabase"},
    {"id": "zendesk", "name": "Zendesk", "category": "Support", "composio_app": "zendesk"},
    {"id": "asana", "name": "Asana", "category": "Productivity", "composio_app": "asana"},
    {"id": "airtable", "name": "Airtable", "category": "Productivity", "composio_app": "airtable"},
    {"id": "linear", "name": "Linear", "category": "Productivity", "composio_app": "linear"},
    {"id": "youtube", "name": "YouTube", "category": "Marketing", "composio_app": "youtube"},
    {"id": "zoho-desk", "name": "Zoho Desk", "category": "Support", "composio_app": "zohodesk"},
    {"id": "zoho-books", "name": "Zoho Books", "category": "Finance", "composio_app": "zohobooks"},
    {"id": "linkedin", "name": "LinkedIn", "category": "Marketing", "composio_app": "linkedin"},
    {"id": "facebook", "name": "Facebook", "category": "Marketing", "composio_app": "facebook"},
    {"id": "instagram", "name": "Instagram", "category": "Marketing", "composio_app": "instagram"},
]

class ConnectorStatus(BaseModel):
    id: str
    name: str
    category: str
    connected: bool = False
    composio_app: str

def get_connected_ids(workspace_id: str = "web-shop") -> set:
    db = SessionLocal()
    try:
        rows = db.execute(
            text("SELECT connector_id FROM connected_accounts WHERE workspace_id = :ws AND status = 'connected'"),
            {"ws": workspace_id},
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        db.close()

@router.get("/", response_model=List[ConnectorStatus])
async def list_connectors(workspace_id: str = "web-shop"):
    connected = get_connected_ids(workspace_id)
    return [
        ConnectorStatus(
            id=c["id"],
            name=c["name"],
            category=c["category"],
            connected=c["id"] in connected,
            composio_app=c["composio_app"],
        )
        for c in CONNECTORS
    ]

@router.post("/{connector_id}/connect")
async def connect_connector(connector_id: str, workspace_id: str = "web-shop"):
    conn = next((c for c in CONNECTORS if c["id"] == connector_id), None)
    if not conn:
        raise HTTPException(404, "Connector not found")

    if not settings.composio_api_key or settings.composio_api_key == "your-composio-key":
        # Demo: mark as connected anyway so UI shows it
        db = SessionLocal()
        try:
            db.execute(
                text("""
                    INSERT OR REPLACE INTO connected_accounts
                    (workspace_id, connector_id, connector_name, status, meta)
                    VALUES (:ws, :cid, :name, 'connected', :meta)
                """),
                {"ws": workspace_id, "cid": connector_id, "name": conn["name"], "meta": json.dumps({"demo": True})},
            )
            db.commit()
        finally:
            db.close()
        return {
            "status": "demo_connected",
            "connector": connector_id,
            "note": "Demo mode — add COMPOSIO_API_KEY for real OAuth",
        }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.composio_base}/auth/initiate",
            headers={"x-api-key": settings.composio_api_key},
            json={
                "appName": conn["composio_app"],
                "redirectUrl": "http://localhost:8000/connectors/callback",
            },
        )
        if resp.status_code != 200:
            return {"status": "error", "detail": resp.text}
        data = resp.json()
        return {
            "status": "auth_url_generated",
            "connector": connector_id,
            "auth_url": data.get("redirectUrl") or data.get("authUrl"),
        }

@router.post("/{connector_id}/callback")
async def connector_callback(connector_id: str, workspace_id: str = "web-shop"):
    """Call this after successful OAuth to persist the connection."""
    conn = next((c for c in CONNECTORS if c["id"] == connector_id), None)
    if not conn:
        raise HTTPException(404)
    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT OR REPLACE INTO connected_accounts
                (workspace_id, connector_id, connector_name, status)
                VALUES (:ws, :cid, :name, 'connected')
            """),
            {"ws": workspace_id, "cid": connector_id, "name": conn["name"]},
        )
        db.commit()
    finally:
        db.close()
    return {"status": "connected", "connector": connector_id}

@router.post("/{connector_id}/disconnect")
async def disconnect_connector(connector_id: str, workspace_id: str = "web-shop"):
    db = SessionLocal()
    try:
        db.execute(
            text("UPDATE connected_accounts SET status = 'disconnected' WHERE workspace_id = :ws AND connector_id = :cid"),
            {"ws": workspace_id, "cid": connector_id},
        )
        db.commit()
    finally:
        db.close()
    return {"status": "disconnected", "connector": connector_id}

@router.get("/connected")
async def list_connected(workspace_id: str = "web-shop"):
    db = SessionLocal()
    try:
        rows = db.execute(
            text("SELECT connector_id, connector_name, status, connected_at FROM connected_accounts WHERE workspace_id = :ws"),
            {"ws": workspace_id},
        ).fetchall()
        return [
            {"id": r[0], "name": r[1], "status": r[2], "connected_at": r[3]}
            for r in rows
        ]
    finally:
        db.close()
