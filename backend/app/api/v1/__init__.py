"""APIバージョン v1 のエンドポイント集約。"""

from fastapi import APIRouter

from app.api.v1.memos import router as memos_router
from app.api.v1.tags import router as tags_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(tags_router)
api_router.include_router(memos_router)

__all__ = ["api_router"]
