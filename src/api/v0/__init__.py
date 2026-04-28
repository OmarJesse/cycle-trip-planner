from fastapi import APIRouter

from src.api.v0.chat import router as chat_router
from src.api.v0.tools import router as tools_router

router = APIRouter(prefix="/api/v0")
router.include_router(chat_router)
router.include_router(tools_router)

