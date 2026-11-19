"""
DOOM AI — Model router
Clean tiered routing by plan and task weight.
"""
from typing import List, Dict

# Available models per plan (ordered by preference)
PLAN_POOLS: Dict[str, List[str]] = {
    "free": [
        "openrouter/free",
    ],
    "basic": [
        "deepseek/deepseek-v4.1-flash-1017",
        "openai/gpt-6-luna",
    ],
    "pro": [
        "openai/gpt-6.1-terra",
        "google/gemini-4-hydrogen",
        "google/gemini-3.8-flash",
        "anthropic/claude-sonnet-5.5",
    ],
    "pro_max": [
        "anthropic/claude-opus-5.5",
        "openai/gpt-6-sol",
        "google/gemini-4-argon",
        "kimi/k3.1-pro",
        "deepseek/deepseek-v4-pro",
        "openai/gpt-chat-latest",
        "google/gemini-omni-1.2-flash",
    ],
    "elite": [
        "anthropic/claude-fable-5.2",
        "anthropic/claude-fable-5.1",
        "openai/gpt-6.1-terra-pro",
        "openai/gpt-6-astra",
        "anthropic/claude-4.6-opus",
        "nvidia/nemotron-3-ultra",
        "thinking-machines/inkling-2-small",
        "google/gemini-4-carbon",
        "google/gemini-3.1-flash-image",
        "openai/gpt-image-2.6-sunburst",
    ],
}

# Task weight → desired model count (before plan cap)
TASK_COUNTS: Dict[str, int] = {
    "light": 1,       # Inquiry Desk, simple lookups
    "medium": 2,      # Regular powers
    "analysis": 3,    # Predictor, deep business
    "coding": 5,      # Engineering, complex code
    "heavy": 7,       # Multi-step agentic
}

# Map power name → task weight
POWER_WEIGHT: Dict[str, str] = {
    "inquiry": "light",
    "business": "medium",
    "website": "medium",
    "content": "medium",
    "workflow": "medium",
    "predictor": "analysis",
    "team_space": "medium",
    "ai_employees": "medium",
    "warning": "analysis",
    "engineering": "coding",
}

def get_plan_models(plan: str) -> List[str]:
    plan = (plan or "free").lower().replace(" ", "_").replace("-", "_")
    return PLAN_POOLS.get(plan, PLAN_POOLS["free"])

def select_models(plan: str, power: str) -> List[str]:
    """Return the models to call for this plan + power."""
    pool = get_plan_models(plan)
    max_available = len(pool)

    weight = POWER_WEIGHT.get(power, "medium")
    desired = TASK_COUNTS.get(weight, 2)

    # Free and Basic have hard caps
    if plan == "free":
        desired = 1
    elif plan == "basic":
        desired = min(desired, 2)

    count = min(desired, max_available)
    return pool[:count]

def doom_wrap(raw: str, power: str = "inquiry") -> str:
    labels = {
        "inquiry": "DOOM",
        "business": "DOOM · Business",
        "predictor": "DOOM · Predictor",
        "website": "DOOM · Website",
        "content": "DOOM · Content",
        "workflow": "DOOM · Workflow",
        "team_space": "DOOM · Team",
        "ai_employees": "DOOM · Employees",
        "engineering": "DOOM · Engineering",
    }
    label = labels.get(power, "DOOM")
    return f"{label}\n\n{raw.strip()}"
