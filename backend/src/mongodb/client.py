from backend.src.mongodb.base import get_metadata_store_client
from backend.src.utils.config import settings

METADATA_STORE_CLIENT = get_metadata_store_client(
    config=settings.METADATA_STORE_CONFIG)
