import logging
import os

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AsyncToolSet, BingGroundingTool
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.functions import kernel_function

from backend.src.prompts.search_prompt import PROMPT
from backend.src.utils.config import Settings

logger = logging.getLogger(__name__)


class WebAgent:
    def __init__(self) -> None:
        logger.debug("Initializing WebAgent instance.")
        self.client = None
        self.toolset = AsyncToolSet()
        self.agent = None
        self.thread = None

    async def init_web_agent(self) -> None:
        logger.info("Initializing web agent.")
        if not self.agent:
            creds = DefaultAzureCredential()
            self.client = AIProjectClient.from_connection_string(
                credential=creds,
                conn_str=Settings.PROJECT_CONNECTION_STRING,
            )
        logger.debug("Fetching Bing connection.")
        bing_conn = await self.client.connections.get(
            connection_name=Settings.BING_CONNECTION_NAME
        )
        if not bing_conn:
            logger.error(
                f"Bing connection '{Settings.BING_CONNECTION_NAME}' not found."
            )
            raise ValueError(
                f"Bing connection '{Settings.BING_CONNECTION_NAME}' not found."
            )

        conn_id = bing_conn.id
        logger.info(f"Using Bing connection ID: {conn_id}")
        bing = BingGroundingTool(connection_id=conn_id)
        logger.debug("Creating agent with BingGroundingTool.")
        self.agent = await self.client.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name="Bing-Agent",
            instructions=PROMPT,
            tools=bing.definitions,
            headers={"x-ms-enable-preview": "true"},
        )
        logger.info(f"Created agent, ID: {self.agent.id}")
        logger.debug("Creating thread for the agent.")
        self.thread = await self.client.agents.create_thread()

    @kernel_function(
        name="search_web",
        description="Perform a Bing web search, search the web as an external tool for data sources . the query can be content, news, or sources for learning path",
    )
    async def search_web(self, query: str) -> str:
        logger.info(f"Executing search_web with query: {query}")
        await self.init_web_agent()
        if not self.agent or not self.thread:
            logger.error("Agent not initialized. Call init() first.")
            raise RuntimeError("Agent not initialized. Call init() first.")

        message = await self.client.agents.create_message(
            thread_id=self.thread.id, role="user", content=query
        )
        logger.debug("Starting agent run.")
        run = await self.client.agents.create_and_process_run(
            thread_id=self.thread.id, agent_id=self.agent.id
        )
        logger.info(f"Run finished with status: {run.status}")
        run_steps = await self.client.agents.list_run_steps(
            run_id=run.id, thread_id=self.thread.id
        )
        run_steps_data = run_steps.data if hasattr(run_steps, "data") else None
        logger.info(f"Last run step detail: {run_steps_data}")

        if run.status == "failed":
            logger.error(f"Run failed: {run.last_error}")
            return "Run failed. No result from Bing."
        logger.debug("Deleting agent after run.")
        await self.client.agents.delete_agent(self.agent.id)

        logger.debug("Fetching response messages.")
        response = await self.client.agents.list_messages(
            thread_id=self.thread.id
        )
        logger.info("Search completed successfully.")
        return response

    async def cleanup(self) -> None:
        logger.info("Cleaning up resources.")
        if self.thread:
            logger.debug(f"Deleting thread with ID: {self.thread.id}")
            await self.client.agents.delete_thread(self.thread.id)
        if self.agent:
            logger.debug(f"Deleting agent with ID: {self.agent.id}")
            await self.client.agents.delete_agent(self.agent.id)
        logger.info("Cleanup completed.")
