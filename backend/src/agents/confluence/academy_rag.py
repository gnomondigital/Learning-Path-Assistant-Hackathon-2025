import logging
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
from semantic_kernel.functions import kernel_function

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
        old_page_ids = {page["page_id"] for page in old_pages}

        pages_to_add = []
        pages_to_update = []
        for page in new_pages:
            old_page_update = next(
                (
                    p["last_update"]
                    for p in old_pages
                    if p["page_id"] == page["page_id"]
                ),
                None,
            )

            if page["page_id"] not in old_page_ids:
                pages_to_add.append(page)
            elif (
                old_page_update is not None
                and page["last_update"] > old_page_update
            ):
                pages_to_update.append(page)
            else:
                logger.info(
                    f"Page {page['page_id']} is already up to date in the metadata store."
                )

        return pages_to_add, pages_to_update

    def add_pages_to_local(self, pages_to_add: List[Dict]) -> None:
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

    def update_pages_in_local(self, pages_to_update: List[Dict]) -> None:
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

    def index_data_in_azure(self, pages_to_index: List[Dict]) -> None:
        """
        Index the data in Azure Cognitive Search.
        """
        logger.info("Indexing data in Azure Cognitive Search...")

        search_service_endpoint = self.AZURE_SEARCH_SERVICE_ENDPOINT
        search_api_key = self.AZURE_SEARCH_API_KEY
        index_name = "confluence-pages-index"
        print(search_service_endpoint, search_api_key, index_name)

        credential = AzureKeyCredential(search_api_key)

        index_client = SearchIndexClient(
            endpoint=search_service_endpoint, credential=credential
        )
        search_client = SearchClient(
            endpoint=search_service_endpoint,
            index_name=index_name,
            credential=credential,
        )

        # Check if index exists
        try:
            index_client.get_index(index_name)
            logger.info(f"Index '{index_name}' already exists.")
        except Exception:
            logger.info(f"Creating new index '{index_name}'...")
            fields = [
                SimpleField(
                    name="id", type=SearchFieldDataType.String, key=True
                ),
                SearchableField(name="title", type=SearchFieldDataType.String),
                SearchableField(
                    name="content", type=SearchFieldDataType.String
                ),
                SimpleField(name="version", type=SearchFieldDataType.Int32),
                SimpleField(
                    name="last_update", type=SearchFieldDataType.String
                ),
                SearchableField(name="space", type=SearchFieldDataType.String),
            ]
            index = SearchIndex(name=index_name, fields=fields)
            index_client.create_index(index)

        # Prepare documents
        documents = []
        for page in pages_to_index:
            doc = {
                "id": str(page["page_id"]),
                "title": page["title"],
                "content": page["body"],
                "version": page["version"],
                "last_update": str(page["last_update"]),
                "space": page["space"],
            }
            documents.append(doc)

        # Upload to Azure Search
        if documents:
            result = search_client.upload_documents(documents=documents)
            logger.info(f"Indexed {len(documents)} documents in Azure Search.")
        else:
            logger.info("No documents to index.")

        return search_client

    def update_content_process(self):
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

        (
            self.add_pages_to_local(pages_to_add=pages_to_add)
            if pages_to_add
            else None
        )
        (
            self.update_pages_in_local(pages_to_update=pages_to_update)
            if pages_to_update
            else None
        )
        logger.info(
            f"""Added {len(pages_to_add)} new pages and\
                updated {len(pages_to_update)} pages in the metadata store.
            """
        )
        search_client = self.index_data_in_azure(
            pages_to_index=pages_to_add + pages_to_update
        )
        logger.info(
            f"""Indexed {len(pages_to_add) + len(pages_to_update)} pages in Azure Search.
            """
        )
        return search_client


class SearchPlugin:

    def __init__(self, search_client: SearchClient):
        self.search_client = search_client

    @kernel_function(
        name="build_augmented_prompt",
        description="Build an augmented prompt using retrieval context or function results.",
    )
    def build_augmented_prompt(
        self, query: str, retrieval_context: str
    ) -> str:
        return (
            f"Retrieved Context:\n{retrieval_context}\n\n"
            f"User Query: {query}\n\n"
            "First review the retrieved context, if this does not answer"
            " the query, try calling an available plugin functions that"
            " might give you an answer. If no context is available, say so."
        )

    @kernel_function(
        name="retrieve_documents",
        description="Retrieve documents from the Azure Search service.",
    )
    def get_retrieval_context(self, query: str) -> str:
        results = self.search_client.search(
            query,
            top=2,
        )
        context_strings = []
        for result in results:
            context_strings.append(f"Document: {result['content']}")
        return context_strings
