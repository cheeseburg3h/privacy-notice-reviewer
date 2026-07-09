from __future__ import annotations

from app.config import APP_NAME

try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover - optional runtime dependency
    FastAPI = None  # type: ignore[assignment]


def create_app():
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Run `pip install -r requirements.txt` to start the API.")

    app = FastAPI(title=APP_NAME)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "model_name": APP_NAME}

    return app


app = create_app() if FastAPI is not None else None

