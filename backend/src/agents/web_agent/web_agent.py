# rag_agent_tools.py

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
    def __init__(self):
        self.client = None
        self.toolset = AsyncToolSet()
        self.agent = None
        self.thread = None

    async def init_web_agent(self):
        if not self.agent:
            creds = DefaultAzureCredential()
            self.client = AIProjectClient.from_connection_string(
                credential=creds,
                conn_str=Settings.PROJECT_CONNECTION_STRING,
            )
        bing_conn = await self.client.connections.get(
            connection_name=Settings.BING_CONNECTION_NAME)
        if not bing_conn:
            raise ValueError(
                f"Bing connection '{Settings.BING_CONNECTION_NAME}' not found.")

        conn_id = bing_conn.id
        print(f"Using Bing connection ID: {conn_id}")
        bing = BingGroundingTool(connection_id=conn_id)
        self.agent = await self.client.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name="Bing-Agent",
            instructions=PROMPT,
            tools=bing.definitions,
            headers={"x-ms-enable-preview": "true"}
        )
        print(f"Created agent, ID: {self.agent.id}")
        self.thread = await self.client.agents.create_thread()

    @kernel_function(name="search_web", description="Perform a Bing web search")
    async def search_web(self, query: str) -> str:
        await self.init_web_agent()
        if not self.agent or not self.thread:
            raise RuntimeError("Agent not initialized. Call init() first.")

        message = await self.client.agents.create_message(
            thread_id=self.thread.id, role="user", content=query
        )
        # Create and process agent run in thread with tools
        run = await self.client.agents.create_and_process_run(
            thread_id=self.thread.id, agent_id=self.agent.id
        )
        print(f"Run finished with status: {run.status}")
        run_steps = await self.client.agents.list_run_steps(
            run_id=run.id, thread_id=self.thread.id
        )
        run_steps_data = run_steps.data if hasattr(run_steps, "data") else None
        print(f"Last run step detail: {run_steps_data}")

        if run.status == "failed":
            print(f"Run failed: {run.last_error}")
            return "Run failed. No result from Bing."
        await self.client.agents.delete_agent(self.agent.id)

        response = await self.client.agents.list_messages(
            thread_id=self.thread.id
        )
        return response

    async def cleanup(self):
        if self.thread:
            await self.client.agents.delete_thread(self.thread.id)
        if self.agent:
            await self.client.agents.delete_agent(self.agent.id)
