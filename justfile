# justfile

frontend:
    uv run streamlit run frontend/streamlit_app.py

backend:
    uv run uvicorn src.api.main:app --reload

dev:
    uv run streamlit run frontend/streamlit_app.py &
    uv run uvicorn src.api.main:app --reload

