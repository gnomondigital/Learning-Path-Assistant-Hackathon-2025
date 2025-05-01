import base64
import re

import requests
from semantic_kernel.functions import kernel_function

from backend.src.utils.config import Settings


class AcademyAgent:
    """
    A Semantic Kernel plugin for interacting with Confluence.
    """

    def __init__(
            self,
            base_url: str = Settings.CONFLUENCE_URL,
            username: str = Settings.CONFLUENCE_USERNAME,
            api_token: str = Settings.CONFLUENCE_API_KEY):
        self.base_url = base_url.rstrip('/')
        self.auth = (username, api_token)
        self.api_base = base_url

        # Create auth header from credentials
        auth_str = f"{username}:{api_token}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        }

    @kernel_function(name="search_confluence", description="Search for content in Confluence")
    def search_content(self, query: str, limit: str = "5") -> str:
        try:
            limit_int = int(limit)
            endpoint = f"{self.api_base}/content/search"
            params = {
                "cql": f'text ~ "{query}"',
                "limit": limit_int,
                "expand": "body.view,space"
            }

            response = requests.get(
                endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            results = response.json()

            if results.get("size", 0) == 0:
                return "No results found in Confluence for your query."

            formatted_results = []
            for i, result in enumerate(results.get("results", []), 1):
                title = result.get("title", "Untitled")
                space = result.get("space", {}).get("name", "Unknown Space")
                url = f"{self.base_url}{result.get('_links', {}).get('webui', '')}"
                content = result.get("body", {}).get(
                    "view", {}).get("value", "")
                content = re.sub(r'<[^>]+>', '', content)[:200] + \
                    "..." if len(content) > 200 else content

                formatted_results.append(
                    f"{i}. **{title}** (in {space})\n"
                    f"   URL: {url}\n"
                    f"   Snippet: {content}\n"
                )

            return "\n".join(formatted_results)

        except Exception as e:
            return f"Error searching Confluence: {str(e)}"

    @kernel_function(name="get_page_by_id", description="Get page content from Confluence by ID")
    def get_page_content(self, page_id: str) -> str:
        try:
            endpoint = f"{self.api_base}/content/{page_id}"
            params = {"expand": "body.view"}

            response = requests.get(
                endpoint, headers=self.headers, params=params)
            response.raise_for_status()

            result = response.json()
            title = result.get("title", "Untitled")
            content = result.get("body", {}).get("view", {}).get("value", "")
            content = re.sub(r'<[^>]+>', '', content)

            url = f"{self.base_url}{result.get('_links', {}).get('webui', '')}"
            return f"# {title}\n\n{content}\n\nSource: {url}"

        except Exception as e:
            return f"Error retrieving Confluence page: {str(e)}"

    @kernel_function(name="get_recent_pages", description="Get recent pages from a Confluence space")
    def get_recent_pages(self, space_key: str, limit: str = "5") -> str:
        try:
            limit_int = int(limit)
            endpoint = f"{self.api_base}/content"
            params = {
                "spaceKey": space_key,
                "limit": limit_int,
                "orderby": "history.modified desc",
                "expand": "history"
            }

            response = requests.get(
                endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            results = response.json()

            if results.get("size", 0) == 0:
                return f"No pages found in Confluence space '{space_key}'."

            formatted_results = []
            for i, result in enumerate(results.get("results", []), 1):
                title = result.get("title", "Untitled")
                page_id = result.get("id", "")
                url = f"{self.base_url}{result.get('_links', {}).get('webui', '')}"
                modified = result.get("history", {}).get(
                    "lastUpdated", {}).get("when", "Unknown")[:10]

                formatted_results.append(
                    f"{i}. **{title}** (ID: {page_id})\n"
                    f"   URL: {url}\n"
                    f"   Last modified: {modified}\n"
                )

            return "\n".join(formatted_results)

        except Exception as e:
            return f"Error retrieving recent Confluence pages: {str(e)}"
