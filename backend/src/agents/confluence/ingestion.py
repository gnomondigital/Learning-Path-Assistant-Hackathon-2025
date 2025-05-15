import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List

from atlassian import Confluence
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
)
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
            password=Settings.CONFLUENCE_API_KEY,
        )
        self.confluence_content = metadata_store.confluence_content
        self.AZURE_SEARCH_SERVICE_ENDPOINT = (
            Settings.AZURE_SEARCH_SERVICE_ENDPOINT
        )
        self.AZURE_SEARCH_API_KEY = Settings.AZURE_SEARCH_API_KEY

    def fetch_all_pages_from_db(self) -> List[Dict]:
        """
        Get all pages that have been retrieved from Confluence.
        """
        logger.info("Fetching all pages from metadata store...")
        pages = self.confluence_content.find({})
        return pages

    def fetch_all_pages_from_source(
        self, space_key: str = "GDA", limit: int = 50
    ) -> List[Dict]:

        pages = self.confluence.get_all_pages_from_space_as_generator(
            space_key,
            limit=limit,
            expand="history,space,version",
            content_type="page",
        )
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
                page_id, expand="body.storage"
            )
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

    def comapre_remote_and_local_content(
        self, new_pages: List[str], old_pages: List[str]
    ) -> List[str]:
        """
        we have a list of the two pages and we want to compare them
        we extruct what to add , what to modify by comparing last_update
        """
        logger.info("Comparing page IDs and updated pages...")
        old_page_ids = {page["id"] for page in old_pages}

        pages_to_add = []
        pages_to_update = []
        for page in new_pages:
            if page["id"] not in old_page_ids:
                pages_to_add.append(page)
            elif page["last_update"] > next(
                (p["last_update"] for p in old_pages if p["id"] == page["id"]),
                None,
            ):
                pages_to_update.append(page)
            else:
                logger.info(
                    f"Page {page['id']} is already up to date in the metadata store."
                )

        return pages_to_add, pages_to_update

    async def add_pages_to_local(self, pages_to_add: List[Dict]) -> None:
        """
        Add new pages to the metadata store.
        """
        logger.info("Adding new pages to metadata store...")
        result = self.confluence_content.insert_many(pages_to_add)
        if result:
            logger.info(
                f"Added {len(pages_to_add)} new pages to the metadata store."
            )
        else:
            logger.error("Failed to add new pages to the metadata store.")

    async def update_pages_in_local(self, pages_to_update: List[Dict]) -> None:
        """
        Update existing pages in the metadata store.
        """
        logger.info("Updating existing pages in metadata store...")
        for page in pages_to_update:
            result = self.confluence_content.update_one(
                {"page_id": page["page_id"]}, {"$set": page}
            )
            if result:
                logger.info(
                    f"Updated page {page['id']} in the metadata store."
                )
            else:
                logger.error(
                    f"Failed to update page {page['id']} in the metadata store."
                )

    async def update_content_process(self):
        """
        Update the content in the metadata store.
        """
        logger.info("Updating content in metadata store...")
        local_pages = self.fetch_all_pages_from_db()
        remote_pages = self.fetch_all_pages_from_source()
        pages_to_add, pages_to_update = self.comapre_remote_and_local_content(
            old_pages=local_pages,
            new_pages=remote_pages,
        )

        await self.add_pages_to_local(pages_to_add=pages_to_add)
        await self.update_pages_in_local(pages_to_update=pages_to_update)
        logger.info(
            f"""Added {len(pages_to_add)} new pages and\
                updated {len(pages_to_update)} pages in the metadata store.
            """
        )


if __name__ == "__main__":
    ingestion = ConfluenceIngestion()
    output = asyncio.run(ingestion.update_content_process())
    logger.info("Confluence data extraction and processing completed.")
