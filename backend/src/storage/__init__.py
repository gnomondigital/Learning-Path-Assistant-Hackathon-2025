from backend.src.storage.base import register_metadata_store
from backend.src.storage.mongo import MongoMetadataStore

register_metadata_store("mongo", MongoMetadataStore)
