import logging
from datetime import datetime
from typing import Dict, List

from atlassian import Confluence
from requests.auth import HTTPBasicAuth

from backend.src.agents.confluence.model.base import ConfluencePageModel
from backend.src.storage.client import METADATA_STORE_CLIENT
from backend.src.utils.config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestions")


class ConfluenceIngestion:
    def __init__(self, metadata_store=METADATA_STORE_CLIENT):
        self.auth = HTTPBasicAuth(
            Settings.CONFLUENCE_USERNAME, Settings.CONFLUENCE_API_KEY
        )
        self.base_url = f"{Settings.CONFLUENCE_URL}"
        self.confluence = Confluence(
            url=self.base_url,
            username=Settings.CONFLUENCE_USERNAME,
            password=Settings.CONFLUENCE_API_KEY,)
        self.confluence_content = metadata_store.confluence_content

    def get_all_retrieved_pages(self) -> List[Dict]:
        """
        Get all pages that have been retrieved from Confluence.
        """
        logger.info("Fetching all pages from metadata store...")
        pages = self.confluence_content.find({})
        return pages

    def fetch_all_pages(
            self, space_key: str = "GDA", limit: int = 50) -> List[Dict]:

        pages = self.confluence.get_all_pages_from_space_as_generator(
            space_key, limit=limit,
            expand="history,space,version",
            content_type='page')
        logger.info("Fetching all pages from Confluence...")
        structured_pages = []
        for page in pages:
            page_id = page["id"]
            type = page["type"]
            title = page["title"]
            space = page["space"]["name"]
            space_id = page["space"]["id"]
            last_update = page["version"]["when"]
            last_updater = page["version"]["by"]["displayName"]
            version = page["version"]["number"]
            space_key = page["space"]["key"]
            content = self.confluence.get_page_by_id(
                page_id, expand="body.storage")
            body = content["body"]["storage"]["value"]

            # Store the page data in the metadata store
            page_obj = ConfluencePageModel(
                page_id=page_id,
                title=title,
                body=body,
                version=version,
                space=space,
                space_id=space_id,
                space_key=space_key,
                last_update=last_update,
                last_updater=last_updater,
                last_indexed_at=datetime.now(),
                type=type,
            )
            structured_pages.append(page_obj.model_dump())
        return structured_pages

    def compare_page_ids_and_updated_pages(
            self, new_pages: List[str], old_pages: List[str]
    ) -> List[str]:
        """
        Compare the page IDs from Confluence with the ones in the metadata store.
        store the new one, update what's modified.
        """
        logger.info("Comparing page IDs...")
        new_page_ids = list(set(retrieved_page_ids) - set(page_ids))
        updated_page_ids = list(set(page_ids) - set(retrieved_page_ids))
        logger.info(f"New page IDs: {new_page_ids}")
        logger.info(f"Updated page IDs: {updated_page_ids}")
        return new_page_ids, updated_page_ids


if __name__ == "__main__":
    ingestion = ConfluenceIngestion()
    output = ingestion.fetch_all_pages()
    logger.info("Confluence data extraction and processing completed.")
