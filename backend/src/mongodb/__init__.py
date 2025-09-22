from backend.src.mongodb.base import register_metadata_store
from backend.src.mongodb.mongo import MongoMetadataStore

register_metadata_store("mongo", MongoMetadataStore)
