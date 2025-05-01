# rag_agent_tools.py

import logging
import os

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AsyncToolSet, BingGroundingTool
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.functions import kernel_function

from backend.src.utils.config import Settings

logger = logging.getLogger(__name__)


class WebAgent:
    def __init__(self):
        self.client = None
        self.toolset = AsyncToolSet()
        self.agent = None
        self.thread = None

    async def init(self):
        creds = DefaultAzureCredential()
        self.client = AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=Settings.PROJECT_CONNECTION_STRING,
        )
        bing_conn = await self.client.connections.get(Settings.BING_CONNECTION_NAME)
        self.toolset.add(BingGroundingTool(connection_id=bing_conn.id))

        self.agent = await self.client.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name="RAG-Bing-Agent",
            instructions="You can search the web using Bing.",
            toolset=self.toolset,
            headers={"x-ms-enable-preview": "true"}
        )
        self.thread = await self.client.agents.create_thread()

    @kernel_function(name="search_web", description="Perform a Bing web search")
    async def search_web(self, query: str) -> str:
        if not self.agent or not self.thread:
            raise RuntimeError("Agent not initialized. Call init() first.")

        await self.client.agents.create_message(
            thread_id=self.thread.id,
            role="user",
            content=query
        )

        response = await self.client.agents.invoke_agent(
            agent_id=self.agent.id,
            thread_id=self.thread.id,
        )

        return response.content if response else "No result from Bing."

    async def cleanup(self):
        if self.thread:
            await self.client.agents.delete_thread(self.thread.id)
        if self.agent:
            await self.client.agents.delete_agent(self.agent.id)
