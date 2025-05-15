import os
from typing import Optional

import orjson
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class MetadataStoreConfig(BaseModel):
    """
    Metadata store configuration
    """

    provider: str
    config: Optional[dict] = None


class Settings():
    CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
    CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
    CONFLUENCE_API_KEY = os.getenv("CONFLUENCE_API_KEY")
    CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATA_DIRECTORY = os.getenv("DATA_DIRECTORY")
    OUTPUT_DIRECTORY = os.getenv("OUTPUT_DIRECTORY")

    MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
    PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")

    BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")
    BING_CONNECTION_KEY = os.getenv("BING_CONNECTION_KEY")
    HOMEPAGE_ID = os.getenv("HOMEPAGE_ID")

    AZURE_AI_INFERENCE_ENDPOINT = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
    AZURE_AI_INFERENCE_API_KEY = os.getenv("AZURE_AI_INFERENCE_API_KEY")
    AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED = os.getenv(
        "AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"
    )

    METADATA_STORE_CONFIG: MetadataStoreConfig = os.getenv(
        "METADATA_STORE_CONFIG", "")

    if not METADATA_STORE_CONFIG:
        raise ValueError("METADATA_STORE_CONFIG is not set")
    try:
        METADATA_STORE_CONFIG = MetadataStoreConfig.model_validate(
            orjson.loads(METADATA_STORE_CONFIG)
        )
    except Exception as e:
        raise ValueError(f"METADATA_STORE_CONFIG is invalid: {e}")


settings = Settings()
