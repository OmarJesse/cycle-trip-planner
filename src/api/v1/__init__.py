from fastapi import APIRouter

from src.api.v1.chat import router as chat_router
from src.api.v1.gpx import router as gpx_router
from src.api.v1.tools import router as tools_router


router = APIRouter(prefix="/api/v1")
router.include_router(chat_router)
router.include_router(tools_router)
router.include_router(gpx_router)
