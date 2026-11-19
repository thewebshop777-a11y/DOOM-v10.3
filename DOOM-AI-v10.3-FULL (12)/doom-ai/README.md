# DOOM AI v10.3 — Clean structure + tiered routing

## Structure

```
backend/
  main.py          # FastAPI app
  router.py        # Plan + task weight → model selection
  openrouter.py    # Single OpenRouter call
  inquiry.py       # Light task (1 model)
  powers.py        # Medium / analysis / coding (council)
  auth.py
  connectors.py
  modules.py
frontend/
  index.html
```

## Routing rules

| Plan     | Models | Light | Medium | Analysis | Coding | Max |
|----------|--------|-------|--------|----------|--------|-----|
| Free     | 1      | 1     | 1      | 1        | 1      | 1   |
| Basic    | 2      | 1     | 2      | 2        | 2      | 2   |
| Pro      | 4      | 1     | 2–4    | 2–4      | 2–4    | 4   |
| Pro Max  | 7      | 1     | 2      | 3        | 5      | 7   |
| Elite    | 10     | 1     | 2      | 3        | 5      | 10  |

Free is 14-day only. Higher plans unlock more models and higher counts for heavier tasks.

## Run

```cmd
cd /d C:\Users\Admin\Downloads\DOOM-AI-v10.3-FULL\doom-ai
setup-doom.bat
start-doom.bat
```

Open http://localhost:8000

Add OPENROUTER_API_KEY in backend/.env for live routing.
