from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.errors import register_exception_handlers

app = FastAPI(title="Memo App API")
register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    """ヘルスチェック。"""
    return {"status": "ok"}
