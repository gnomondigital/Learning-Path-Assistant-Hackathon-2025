import json
import logging
import os

import requests
from requests.auth import HTTPBasicAuth
from utils.config import Settings
from utils.utilities import Utilities

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestions")


class ConfluenceIngestion:
    def __init__(self):
        self.auth = HTTPBasicAuth(
            Settings.CONFLUENCE_USERNAME, Settings.CONFLUENCE_API_KEY
        )
        self.base_url = f"{Settings.CONFLUENCE_URL}/rest/api"

    def fetch_children(self, page_id: str) -> list:
        """Fetch child pages of a given Confluence page."""
        endpoint = f"/content/{page_id}/child/page"
        params = {"expand": "title"}
        url = f"{self.base_url}{endpoint}?expand={params['expand']}"
        response = requests.get(url, auth=self.auth)

        if response.status_code == 200:
            children_data = response.json()
            return [
                child["title"] for child in children_data.get("results", [])
            ]
        else:
            logger.warning(f"Could not fetch children for page {page_id}")
            return []

    def extract_confluence_data(self) -> list:
        """Extract Confluence data from the specified space."""
        url = f"{self.base_url}/content"
        params = {
            "spaceKey": Settings.CONFLUENCE_SPACE_KEY,
            "expand": "ancestors,body.storage,version,metadata.labels",
            "limit": 100,
        }
        data = []
        while url:
            response = requests.get(url, auth=self.auth, params=params)
            if response.status_code == 200:
                pages = response.json()
                for page in pages.get("results", []):
                    page_id = page["id"]
                    labels = [
                        label["name"]
                        for label in page.get("metadata", {})
                        .get("labels", {})
                        .get("results", [])
                    ]

                    page_data = {
                        "title": page["title"],
                        "url": f"{Settings.CONFLUENCE_URL}/pages/viewpage.action?pageId={page_id}",
                        "ancestors": [
                            ancestor["title"]
                            for ancestor in page.get("ancestors", [])
                        ],
                        "children": self.fetch_children(page_id),
                        "last_modified": page["version"]["when"],
                        "page_id": page_id,
                        "tags": labels,
                    }
                    data.append(page_data)
                url = pages.get("_links", {}).get("next")
                if url:
                    url = f"{Settings.CONFLUENCE_URL}{url}"
                    params = None
            else:
                logger.error(f"Error: {response.status_code}, {response.text}")
                break

        return data

    def save_to_json(
        self, data: list, filename: str = "data/confluence_data.json"
    ) -> None:
        """Save the Confluence data to a JSON file."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Data saved to '{filename}'")

    def extract_and_process_confluence_data(self) -> None:
        """Extract data from Confluence, clean, and save it."""
        extracted_data = self.extract_confluence_data()
        if extracted_data:
            logger.info(
                f"Extracted {len(extracted_data)} pages from Confluence."
            )
            self.save_to_json(extracted_data)
            for page in extracted_data:
                self.fetch_page_details(page["page_id"])

    def fetch_page_details(self, page_id: str) -> dict:
        """Fetch detailed content for a single page and save it."""
        endpoint = f"/content/{page_id}"
        params = {"expand": "title,body.storage"}
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, auth=self.auth, params=params)

        if response.status_code == 200:
            page = response.json()
            title = page["title"]
            raw_content = page["body"]["storage"]["value"]
            cleaned_content = Utilities.clean_html_and_emojis(raw_content)
            self.save_to_markdown(cleaned_content, title)
            return {
                "page_id": page_id,
                "title": title,
                "content": cleaned_content,
            }
        else:
            logger.error(
                f"Error fetching details for page {page_id}: {response.status_code}"
            )
            return None

    def save_to_markdown(
        self,
        content: str,
        title: str,
        directory: str = Settings.DATA_DIRECTORY,
    ) -> None:
        """Save page content to markdown."""
        safe_title = (
            title.replace("/", "_").replace("\\", "_").replace(" ", "_")
        )
        filename = os.path.join(directory, f"{safe_title}.md")
        os.makedirs(directory, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Content saved to {filename}")
