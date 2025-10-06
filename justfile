# justfile

frontend:
    cd fintrack-frontend && npm run dev

backend:
    uv run uvicorn src.api.main:app --reload

dev:
    cd fintrack-frontend && npm run dev
    uv run uvicorn src.api.main:app --reload
