import logging
from typing import Any, Dict

from pymongo.mongo_client import MongoClient

from backend.src.storage.base import BaseMetadataStore

logger = logging.getLogger(__name__)


class MongoMetadataStore(BaseMetadataStore):
    """MongoDB Metadata Store"""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.client = MongoClient(config["uri"])
        try:
            self.client.admin.command("ping")
            logger.info(
                "Pinged your deployment.You successfully connected to MongoDB"
            )
        except Exception as e:
            logger.error(e)

        db_name = config.get("db_name", "LearningAgent")
        self.db = self.client[db_name]
        self.users = self.db["users"]
        self.confluence_content = self.db["confluence_content"]
