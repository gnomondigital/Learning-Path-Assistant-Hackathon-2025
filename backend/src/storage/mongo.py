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
        self.token_usages = self.db["token_usages"]
        self.confluence_content = self.db["confluence_content"]
        self.profiles = self.db["profiles"]
        self.learning_paths = self.db["learning_paths"]

    def _init_user_token_usage_stats(self):
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "user_id": "$user_id",
                        "day": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$created_at",
                            }
                        },
                    },
                    "total_prompt_tokens": {"$sum": "$prompt_tokens"},
                    "total_completion_tokens": {"$sum": "$completion_tokens"},
                    "total_tokens": {"$sum": "$total_tokens"},
                    "total_prompt_price": {"$sum": "$prompt_price"},
                    "total_completion_price": {"$sum": "$completion_price"},
                    "total_price": {"$sum": "$total_price"},
                    "total_searches": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "user_id": "$_id.user_id",
                    "day": "$_id.day",
                    "total_prompt_tokens": 1,
                    "total_completion_tokens": 1,
                    "total_tokens": 1,
                    "total_prompt_price": 1,
                    "total_completion_price": 1,
                    "total_price": 1,
                    "total_searches": 1,
                }
            },
        ]
        if "stats" in self.db.list_collection_names():
            logger.info("Dropping stats collection...")
            self.db.stats.drop()

        logger.info("Creating stats view...")
        self.db.create_collection(
            "stats", viewOn="token_usages", pipeline=pipeline)
        logger.info("View created successfully!")
