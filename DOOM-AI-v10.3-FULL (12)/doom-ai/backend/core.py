"""
DOOM AI — Core missing features
Notifications, Search, Audit, Templates, Knowledge, Reports,
Task Board, Calendar, Feedback, API Keys, Webhooks, Export.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

# In-memory stores (swap to SQLite later)
NOTIFICATIONS = []
AUDIT = []
TEMPLATES = [
    {"id": "ops-brief", "name": "Ops Brief", "category": "business"},
    {"id": "linkedin-post", "name": "LinkedIn Post", "category": "content"},
    {"id": "code-review", "name": "Code Review", "category": "engineering"},
    {"id": "campaign", "name": "Campaign Plan", "category": "marketing"},
    {"id": "user-story", "name": "User Story", "category": "product"},
]
KNOWLEDGE = [
    {"id": "k1", "title": "How approvals work", "body": "Actions that touch external tools require approval."},
    {"id": "k2", "title": "Plan limits", "body": "Free 20, Basic 100, Pro 500 daily calls."},
]
TASKS = []
EVENTS = []
FEEDBACK = []
API_KEYS = []
WEBHOOKS = []

class Notify(BaseModel):
    title: str
    body: str
    level: str = "info"

class SearchQuery(BaseModel):
    q: str

class TemplateRun(BaseModel):
    template_id: str
    context: str
    plan: Optional[str] = "free"

class KnowledgeAdd(BaseModel):
    title: str
    body: str

class TaskCreate(BaseModel):
    title: str
    space: str = "operations"
    assignee: Optional[str] = None

class EventCreate(BaseModel):
    title: str
    time: str
    space: str = "operations"

class FeedbackCreate(BaseModel):
    message: str
    type: str = "bug"

class ApiKeyCreate(BaseModel):
    name: str

class WebhookCreate(BaseModel):
    url: str
    event: str

@router.post("/notify")
async def add_notification(req: Notify):
    n = {"id": f"n{len(NOTIFICATIONS)+1}", "title": req.title, "body": req.body, "level": req.level, "time": datetime.utcnow().isoformat()}
    NOTIFICATIONS.append(n)
    AUDIT.append({"action": "notify", "detail": req.title, "time": n["time"]})
    return n

@router.get("/notifications")
async def list_notifications():
    return {"notifications": NOTIFICATIONS[-30:]}

@router.post("/search")
async def search(req: SearchQuery):
    q = req.q.lower()
    results = []
    for t in TEMPLATES:
        if q in t["name"].lower():
            results.append({"type": "template", "item": t})
    for k in KNOWLEDGE:
        if q in k["title"].lower() or q in k["body"].lower():
            results.append({"type": "knowledge", "item": k})
    for task in TASKS:
        if q in task["title"].lower():
            results.append({"type": "task", "item": task})
    return {"query": req.q, "results": results}

@router.get("/audit")
async def get_audit():
    return {"audit": AUDIT[-50:]}

@router.get("/templates")
async def list_templates():
    return {"templates": TEMPLATES}

@router.post("/templates/run")
async def run_template(req: TemplateRun):
    tpl = next((t for t in TEMPLATES if t["id"] == req.template_id), None)
    if not tpl:
        raise HTTPException(404, "Template not found")
    models = select_models(req.plan or "free", "content")
    prompt = f"Template: {tpl['name']}\nContext: {req.context}\nProduce the output."
    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(f"[{m}]\n{ans}")
    combined = "\n\n---\n\n".join(answers)
    output = doom_wrap(combined, "content")
    AUDIT.append({"action": "template_run", "detail": tpl["name"], "time": datetime.utcnow().isoformat()})
    return {"template": tpl["name"], "output": output, "model_count": len(models)}

@router.get("/knowledge")
async def list_knowledge():
    return {"knowledge": KNOWLEDGE}

@router.post("/knowledge")
async def add_knowledge(req: KnowledgeAdd):
    k = {"id": f"k{len(KNOWLEDGE)+1}", "title": req.title, "body": req.body}
    KNOWLEDGE.append(k)
    return k

@router.post("/tasks")
async def create_task(req: TaskCreate):
    t = {"id": f"t{len(TASKS)+1}", "title": req.title, "space": req.space, "assignee": req.assignee, "status": "open", "created": datetime.utcnow().isoformat()}
    TASKS.append(t)
    return t

@router.get("/tasks")
async def list_tasks():
    return {"tasks": TASKS}

@router.post("/calendar")
async def add_event(req: EventCreate):
    e = {"id": f"e{len(EVENTS)+1}", "title": req.title, "time": req.time, "space": req.space}
    EVENTS.append(e)
    return e

@router.get("/calendar")
async def list_events():
    return {"events": EVENTS}

@router.post("/feedback")
async def add_feedback(req: FeedbackCreate):
    f = {"id": f"fb{len(FEEDBACK)+1}", "message": req.message, "type": req.type, "time": datetime.utcnow().isoformat()}
    FEEDBACK.append(f)
    return f

@router.get("/feedback")
async def list_feedback():
    return {"feedback": FEEDBACK}

@router.post("/apikeys")
async def create_key(req: ApiKeyCreate):
    k = {"id": f"key{len(API_KEYS)+1}", "name": req.name, "key": f"doom_{req.name.lower()}_{len(API_KEYS)+1}", "created": datetime.utcnow().isoformat()}
    API_KEYS.append(k)
    return k

@router.get("/apikeys")
async def list_keys():
    return {"keys": [{"id": k["id"], "name": k["name"], "created": k["created"]} for k in API_KEYS]}

@router.post("/webhooks")
async def create_webhook(req: WebhookCreate):
    w = {"id": f"wh{len(WEBHOOKS)+1}", "url": req.url, "event": req.event, "active": True}
    WEBHOOKS.append(w)
    return w

@router.get("/webhooks")
async def list_webhooks():
    return {"webhooks": WEBHOOKS}

@router.get("/export")
async def export_data():
    return {
        "notifications": NOTIFICATIONS[-20:],
        "tasks": TASKS,
        "events": EVENTS,
        "audit": AUDIT[-30:],
        "exported_at": datetime.utcnow().isoformat(),
    }
