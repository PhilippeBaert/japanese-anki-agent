from fastapi import APIRouter
from ..config import load_config
from ..models import AnkiConfig

router = APIRouter()


@router.get("/config", response_model=AnkiConfig)
async def get_config():
    """Get the current Anki configuration including fields and tags"""
    return await load_config()
