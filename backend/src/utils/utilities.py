import re
import html
import logging
from pathlib import Path
from typing import List, Optional
from typing import Dict, Any

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import VectorStore
from utils.terminal_colors import TerminalColors as tc

logger = logging.getLogger(__name__)
class Utilities:
    def __init__(self):
        self.shared_files_path = Path("data")
        self.shared_files_path.mkdir(exist_ok=True)

    def clean_html_and_emojis(text):
        text = html.unescape(text)
        text_no_html = re.sub(r"<[^>]+>", "", text)
        text_no_html = re.sub(r"\s+", " ", text_no_html).strip()

        emoji_pattern = re.compile(
            "[\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\U0001f700-\U0001f77f"
            "\U0001f780-\U0001f7ff"
            "\U0001f800-\U0001f8ff"
            "\U0001f900-\U0001f9ff"
            "\U0001fa00-\U0001fa6f"
            "\U0001fa70-\U0001faff"
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "]+",
            flags=re.UNICODE,
        )

        text_cleaned = emoji_pattern.sub(r"", text_no_html)

        return text_cleaned

    def load_instructions(self, instructions_file: str) -> str:
        """Load instructions from a file."""
        with open(instructions_file, "r", encoding="utf-8", errors="ignore") as file:
            return file.read()

    def log_msg_purple(self, message: str) -> None:
        """Log a message in purple color."""
        logger.info(f"{tc.PURPLE}{message}{tc.END}")

    async def upload_file(
        self, 
        project_client: AIProjectClient, 
        file_path: Path, 
        purpose: str = "assistants"
    ) -> Dict[str, Any]:
        """Upload a file to the project."""
        try:
            file_info = await project_client.files.upload_file(
                file_path=file_path,
                purpose=purpose
            )
            self.log_msg_purple(f"Uploaded file: {file_path}")
            return file_info
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {str(e)}")
            raise
            
    async def create_vector_store(
        self, 
        project_client: AIProjectClient, 
        files: List[str], 
        vector_store_name: str
    ) -> Optional[VectorStore]:
        """Create a vector store and upload files to it."""
        try:
            file_ids = []
            
            # Upload the files
            for file in files:
                file_path = self.shared_files_path / file
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                    
                file_info = await self.upload_file(
                    project_client, 
                    file_path=file_path, 
                    purpose="assistants"
                )
                file_ids.append(file_info.id)
                
            if not file_ids:
                logger.error("No files were successfully uploaded")
                return None
                
            self.log_msg_purple("Creating the vector store")
            
            # Create a vector store
            vector_store = await project_client.agents.create_vector_store_and_poll(
                file_ids=file_ids, 
                name=vector_store_name
            )
            
            self.log_msg_purple(f"Vector store '{vector_store_name}' created successfully")
            return vector_store
            
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise
