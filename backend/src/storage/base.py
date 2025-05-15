from abc import ABC

from backend.src.utils.config import MetadataStoreConfig


class BaseMetadataStore(ABC):
    pass


METADATA_STORE_REGISTRY = {}


def register_metadata_store(provider: str, cls, overwrite=False):
    """
    Registers all the available metadata store.

    Args:
        provider: The type of the metadata store to be registered.
        cls: The metadata store class to be registered.

    Returns:
        None
    """
    global METADATA_STORE_REGISTRY
    if provider in METADATA_STORE_REGISTRY and not overwrite:
        raise ValueError(
            f"""\
            Error while registering class {cls.__name__}\
            already taken by {METADATA_STORE_REGISTRY[provider].__name__}\
            """
        )
    METADATA_STORE_REGISTRY[provider] = cls


def get_metadata_store_client(
    config: MetadataStoreConfig,
) -> BaseMetadataStore:
    if config.provider in METADATA_STORE_REGISTRY:
        return METADATA_STORE_REGISTRY[config.provider](config=config.config)
    else:
        raise ValueError(f"Unknown metadata store type: {config.provider}")
