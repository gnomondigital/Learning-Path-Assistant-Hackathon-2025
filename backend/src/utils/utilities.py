import html
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import ThreadMessage, VectorStore
from utils.terminal_colors import TerminalColors as tc

logger = logging.getLogger(__name__)


class Utilities:
    def __init__(self):
        self.shared_files_path = Path("data")
        self.shared_files_path.mkdir(exist_ok=True)

    @property
    def shared_files_path(self) -> Path:
        """Get the path to the shared files directory."""
        return Path(__file__).parent.parent.parent.resolve()

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
        logger.info(f"{tc.PURPLE}{message}{tc.RESET}")

    def log_msg_green(self, msg: str) -> None:
        """Print a message in green."""
        print(f"{tc.GREEN}{msg}{tc.RESET}")

    def log_msg_purple(self, msg: str) -> None:
        """Print a message in purple."""
        print(f"{tc.PURPLE}{msg}{tc.RESET}")

    def log_token_blue(self, msg: str) -> None:
        """Print a token in blue."""
        print(f"{tc.BLUE}{msg}{tc.RESET}", end="", flush=True)

    async def get_file(self, project_client: AIProjectClient, file_id: str, attachment_name: str) -> None:
        """Retrieve the file and save it to the local disk."""
        self.log_msg_green(f"Getting file with ID: {file_id}")

        attachment_part = attachment_name.split(":")[-1]
        file_name = Path(attachment_part).stem
        file_extension = Path(attachment_part).suffix
        file_name = f"{file_name}.{file_id}{file_extension}"

        folder_path = Path(self.shared_files_path) / "files"
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / file_name

        # Save the file using a synchronous context manager
        with file_path.open("wb") as file:
            async for chunk in await project_client.agents.get_file_content(file_id):
                file.write(chunk)

        self.log_msg_green(f"File saved to {file_path}")
        # Cleanup the remote file
        await project_client.agents.delete_file(file_id)

    async def get_files(self, message: ThreadMessage, project_client: AIProjectClient) -> None:
        """Get the image files from the message and kickoff download."""
        if message.image_contents:
            for index, image in enumerate(message.image_contents, start=0):
                attachment_name = (
                    "unknown" if not message.file_path_annotations else message.file_path_annotations[
                        index].text + ".png"
                )
                await self.get_file(project_client, image.image_file.file_id, attachment_name)
        elif message.attachments:
            for index, attachment in enumerate(message.attachments, start=0):
                attachment_name = (
                    "unknown" if not message.file_path_annotations else message.file_path_annotations[
                        index].text
                )
                await self.get_file(project_client, attachment.file_id, attachment_name)

    async def upload_file(
        self,
        project_client: AIProjectClient,
        file_path: Path,
        purpose: str = "assistants"
    ) -> Dict[str, Any]:
        """Upload a file to the project."""
        try:
            file_info = await project_client.agents.upload_file(
                file_path=str(file_path),  # Convert Path to string
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
                file_path = Path(file)
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue

                try:
                    file_info = await self.upload_file(
                        project_client,
                        file_path=file_path,
                        purpose="assistants"
                    )
                    if file_info and 'id' in file_info:
                        file_ids.append(file_info['id'])
                        logger.info(f"Successfully uploaded: {file_path}")
                    else:
                        logger.warning(f"No file ID received for {file_path}")
                except Exception as e:
                    logger.error(f"Failed to upload {file_path}: {str(e)}")
                    continue

            if not file_ids:
                logger.error("No files were successfully uploaded")
                return None

            self.log_msg_purple(
                f"Creating vector store with {len(file_ids)} files")

            try:
                # Create a vector store
                vector_store = await project_client.agents.create_vector_store_and_poll(
                    file_ids=file_ids,
                    name=vector_store_name
                )

                if vector_store:
                    self.log_msg_purple(
                        f"Vector store '{vector_store_name}' created successfully")
                    return vector_store
                else:
                    logger.error("Vector store creation returned None")
                    return None
            except Exception as e:
                logger.error(f"Error creating vector store: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error in create_vector_store: {str(e)}")
            return None
