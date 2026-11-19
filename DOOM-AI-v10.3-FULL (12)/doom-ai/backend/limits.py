"""
DOOM AI — Plan limits and free trial enforcement
"""
from datetime import datetime
from main import SessionLocal
from sqlalchemy import text

PLAN_LIMITS = {
    "free": {"daily_calls": 20, "max_models": 1},
    "basic": {"daily_calls": 100, "max_models": 2},
    "pro": {"daily_calls": 500, "max_models": 4},
    "pro_max": {"daily_calls": 2000, "max_models": 7},
    "elite": {"daily_calls": 10000, "max_models": 10},
}

def check_free_trial(workspace_id: str = "web-shop") -> tuple:
    """Returns (allowed, days_left, expired)."""
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT started_at FROM trials WHERE workspace_id = :ws"),
            {"ws": workspace_id},
        ).fetchone()
        if not row:
            db.execute(
                text("INSERT INTO trials (workspace_id, plan) VALUES (:ws, 'free')"),
                {"ws": workspace_id},
            )
            db.commit()
            return True, 14, False
        started = datetime.fromisoformat(row[0].replace("Z", "+00:00").split("+")[0])
        elapsed = (datetime.utcnow() - started).days
        days_left = max(0, 14 - elapsed)
        expired = elapsed >= 14
        return not expired, days_left, expired
    finally:
        db.close()

def check_plan_limit(plan: str, workspace_id: str = "web-shop") -> tuple:
    plan = (plan or "free").lower()
    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT COUNT(*) FROM usage_log
                WHERE workspace_id = :ws
                AND date(created_at) = date('now')
            """),
            {"ws": workspace_id},
        ).fetchone()
        used = row[0] if row else 0
        allowed = used < limit["daily_calls"]
        return allowed, used, limit["daily_calls"]
    finally:
        db.close()

def log_usage(plan: str, power: str, model_count: int, workspace_id: str = "web-shop"):
    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO usage_log (workspace_id, plan, power, model_count)
                VALUES (:ws, :plan, :power, :cnt)
            """),
            {"ws": workspace_id, "plan": plan, "power": power, "cnt": model_count},
        )
        db.commit()
    finally:
        db.close()
