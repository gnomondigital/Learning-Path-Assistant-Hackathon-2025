import base64
import logging
import re

import requests
from semantic_kernel.functions import kernel_function

from backend.src.utils.config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AcademyAgent:
    def __init__(
        self,
        base_url: str = Settings.CONFLUENCE_URL,
        username: str = Settings.CONFLUENCE_USERNAME,
        api_token: str = Settings.CONFLUENCE_API_KEY,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/rest/api"
        self.auth = (username, api_token)
        auth_str = f"{username}:{api_token}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json",
        }
        logger.info(
            "AcademyAgent initialized with base_url: %s", self.base_url
        )

    @kernel_function(
        name="search_confluence",
        description="Search for content in a specific subject, confluece is considered as an internal knowledge base. Used to retrieve content for all subjects and building learning paths.",
    )
    def search_content(self, query: str) -> str:
        logger.info("Searching Confluence with query: %s", query)
        try:
            endpoint = f"{self.api_base}/content/search"
            params = {
                "cql": f'text ~ "{query}"',
                "expand": "body.view,space",
            }
            response = requests.get(
                endpoint, headers=self.headers, params=params
            )
            response.raise_for_status()
            search_response = response.json()
            logger.info("Search results retrieved successfully")
            if search_response.get("size", 0) == 0:
                logger.warning("No results found for query: %s", query)
                return "No results found in Confluence for your query."
            formatted_search_results = []
            for i, result in enumerate(search_response.get("results", []), 1):
                title = result.get("title", "Untitled")
                space = result.get("space", {}).get("name", "Unknown Space")
                url = f"{self.base_url}{result.get('_links', {}).get('webui', '')}"
                content = (
                    result.get("body", {}).get("view", {}).get("value", "")
                )
                content = (
                    re.sub(r"<[^>]+>", "", content)[:200] + "..."
                    if len(content) > 200
                    else content
                )
                formatted_search_results.append(
                    f"{i}. **{title}** (in {space})\n"
                    f"   URL: {url}\n"
                    f"   Snippet: {content}\n"
                )
            return "\n".join(formatted_search_results)
        except requests.exceptions.RequestException as e:
            logger.error("Error searching Confluence: %s", str(e))
            return f"Error searching Confluence: {str(e)}"

    @kernel_function(
        name="get_page_by_id",
        description="Get page content from Confluence by ID",
    )
    def get_page_content(self, page_id: str) -> str:
        logger.info("Retrieving page content for page_id: %s", page_id)
        try:
            endpoint = f"{self.api_base}/content/{page_id}"
            params = {"expand": "body.view"}
            response = requests.get(
                endpoint, headers=self.headers, params=params
            )
            response.raise_for_status()
            page_data = response.json()
            logger.info(
                "Page content retrieved successfully for page_id: %s", page_id
            )
            title = page_data.get("title", "Untitled")
            content = (
                page_data.get("body", {}).get("view", {}).get("value", "")
            )
            content = re.sub(r"<[^>]+>", "", content)
            url = f"{self.base_url}{page_data.get('_links', {}).get('webui', '')}"
            return f"# {title}\n\n{content}\n\nSource: {url}"
        except requests.exceptions.RequestException as e:
            logger.error("Error retrieving Confluence page: %s", str(e))
            return f"Error retrieving Confluence page: {str(e)}"

    @kernel_function(
        name="get_recent_pages",
        description="Get recent pages from a Confluence space",
    )
    def get_recent_pages(self, space_key: str) -> str:
        logger.info("Retrieving recent pages for space_key: %s", space_key)
        try:
            endpoint = f"{self.api_base}/search"
            cql_query = (
                f'space="{space_key}" AND type=page ORDER BY lastmodified DESC'
            )
            params = {
                "cql": cql_query,
                "expand": "content.history,content._links",
            }
            response = requests.get(
                endpoint, headers=self.headers, params=params
            )
            response.raise_for_status()
            recent_pages_data = response.json()
            logger.info(
                "Recent pages retrieved successfully for space_key: %s",
                space_key,
            )
            if not recent_pages_data.get("results"):
                logger.warning(
                    "No pages found in Confluence space: %s", space_key
                )
                return f"No pages found in Confluence space '{space_key}'."
            formatted_recent_pages = []
            for i, result in enumerate(recent_pages_data["results"], 1):
                content = result.get("content", {})
                title = content.get("title", "Untitled")
                page_id = content.get("id", "")
                webui_link = content.get("_links", {}).get("webui", "")
                url = f"{self.base_url}{webui_link}"
                modified = (
                    content.get("history", {})
                    .get("lastUpdated", {})
                    .get("when", "Unknown")[:10]
                )
                formatted_recent_pages.append(
                    f"{i}. **{title}** (ID: {page_id})\n"
                    f"  URL: {url}\n"
                    f"  Last modified: {modified}\n"
                )
            return "\n".join(formatted_recent_pages)
        except requests.exceptions.RequestException as e:
            logger.error(
                "Error retrieving recent Confluence pages: %s", str(e)
            )
            return f"Error retrieving recent Confluence pages: {str(e)}"
