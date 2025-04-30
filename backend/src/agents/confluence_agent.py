import asyncio
import logging
import os
from pathlib import Path

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (Agent, AgentThread, AsyncFunctionTool,
                                      AsyncToolSet, BingGroundingTool,
                                      FileSearchTool)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from service.confluence.ingestion import ConfluenceIngestion
from utils.config import Settings
from utils.stream_event_handler import StreamEventHandler
from utils.utilities import Utilities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
functions = AsyncFunctionTool(functions=set())


class RAGAgent:
    def __init__(self):
        load_dotenv()
        self.settings = Settings()
        self.project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=self.settings.PROJECT_CONNECTION_STRING,
        )
        self.toolset = AsyncToolSet()
        self.confluence_ingestion = ConfluenceIngestion()
        self.utilities = Utilities()

    async def setup_tools(self):
        """Setup the tools for the RAG agent."""
        try:
            # First, run the ingestion process to get the documents
            # self.confluence_ingestion.extract_and_process_confluence_data()

            # Get all markdown files after ingestion
            data_dir = Path(Settings.DATA_DIRECTORY)
            markdown_files = []
            if data_dir.exists():
                for file in os.listdir(data_dir):
                    if file.endswith('.md'):
                        full_path = str(data_dir / file)
                        markdown_files.append(full_path)
                        logger.info(f"Found file: {full_path}")

            if not markdown_files:
                logger.error(f"No markdown files found in {data_dir}")
                return

            self.toolset.add(functions)
            # Create a vector store with the ingested documents
            vector_store = await self.utilities.create_vector_store(
                project_client=self.project_client,
                files=markdown_files,
                vector_store_name="Confluence Knowledge Base"
            )

            # Add the file search tool with the vector store
            file_search_tool = FileSearchTool(
                vector_store_ids=[vector_store.id])
            self.toolset.add(file_search_tool)

        except Exception as e:
            logger.error(f"Error in setup_tools: {str(e)}")
            raise

    async def initialize_agent(self) -> tuple[Agent, AgentThread]:
        """Initialize the RAG agent with tools and instructions."""
        await self.setup_tools()

        instructions = open(
            "src/instructions/agent_instructions.txt", "r").read()

        agent = await self.project_client.agents.create_agent(
            model=self.settings.MODEL_DEPLOYMENT_NAME,
            name="Confluence RAG Agent",
            instructions=instructions,
            toolset=self.toolset,
            temperature=0.1,
            headers={"x-ms-enable-preview": "true"},
        )

        thread = await self.project_client.agents.create_thread()

        return agent, thread

    async def process_query(self, query: str, agent: Agent, thread: AgentThread):
        """Process a user query using the RAG agent with FileSearchTool."""
        try:
            # Ensure previous messages are retrieved
            thread_messages = await self.project_client.agents.list_messages(thread.id)

            # Log previous messages to confirm they exist
            logger.info(f"Thread Messages Before Query: {thread_messages}")

            # Post the query to the agent
            await self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=query
            )

            # Stream agent response
            stream = await self.project_client.agents.create_stream(
                thread_id=thread.id,
                agent_id=agent.id,
                event_handler=StreamEventHandler(
                    functions=functions, project_client=self.project_client, utilities=self.utilities),
                instructions=agent.instructions,
                max_completion_tokens=10240,
                max_prompt_tokens=20480,
                temperature=0.1,
                top_p=0.1
            )

            async with stream as s:
                await s.until_done()

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return f"Error: {str(e)}"

    async def cleanup(self, agent: Agent, thread: AgentThread) -> None:
        """Cleanup the resources."""
        await self.project_client.agents.delete_thread(thread.id)
        await self.project_client.agents.delete_agent(agent.id)
