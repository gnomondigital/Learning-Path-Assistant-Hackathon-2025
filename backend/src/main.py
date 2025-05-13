import asyncio
import logging
import os

import semantic_kernel as sk
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.function_choice_behavior import \
    FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments

from backend.src.agents.confluence.academy_agent import AcademyAgent
from backend.src.agents.profile_builder.profile_builder import \
    ProfileBuilderAgent
from backend.src.agents.web_agent.web_agent import WebAgent
from backend.src.instructions.instructions_system import GLOBAL_PROMPT
from backend.src.prompts.academy_instructions import PROMPT as ACADEMY_PROMPT
from backend.src.prompts.profile_builder import \
    PROMPT as PROFILE_BUILDER_PROMPT
from backend.src.prompts.search_prompt import PROMPT as SEARCH_PROMPT

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
AZURE_AI_INFERENCE_API_KEY = os.getenv("AZURE_AI_INFERENCE_API_KEY")
AZURE_AI_INFERENCE_ENDPOINT = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
service_id = "agent"


class SemanticKernelAgentHandler:
    def __init__(self, user_id: str = None) -> None:
        logger.debug("Initializing SemanticKernelAgentHandler")
        self.kernel = sk.Kernel()
        self.user_id = user_id
        self.client = sk.connectors.ai.open_ai.AzureChatCompletion(
            api_key=AZURE_AI_INFERENCE_API_KEY,
            deployment_name=API_DEPLOYMENT_NAME,
            endpoint=AZURE_AI_INFERENCE_ENDPOINT,
        )
        self.kernel.add_service(
            AzureChatCompletion(
                service_id=service_id,
                api_key=AZURE_AI_INFERENCE_API_KEY,
                deployment_name=API_DEPLOYMENT_NAME,
                endpoint=AZURE_AI_INFERENCE_ENDPOINT,
            )
        )
        self.kernel.add_plugin(AcademyAgent(), plugin_name="Academy_Agent")
        self.kernel.add_plugin(WebAgent(), plugin_name="Web_search_Agent")
        self.kernel.add_plugin(
            ProfileBuilderAgent(user_id=self.user_id),
            plugin_name="profile_builder_agent",
        )
        logger.debug("Plugins added to kernel")

        settings = self.kernel.get_prompt_execution_settings_from_service_id(
            service_id=service_id
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        self.agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="Host",
            instructions=GLOBAL_PROMPT.format(
                PROFILE_BUILDER=PROFILE_BUILDER_PROMPT,
                WEB_SEARCH_PROMPT=SEARCH_PROMPT,
                CONFLUENCE_PROMPT=ACADEMY_PROMPT,
            ),
            arguments=KernelArguments(settings=settings),
        )
        self.thread = None
        logger.debug("SemanticKernelAgentHandler initialized successfully")

    async def start_thread(self) -> ChatHistoryAgentThread:
        logger.debug("Starting new chat thread")
        if not self.thread:
            self.thread = ChatHistoryAgentThread()
        return self.thread

    async def clean_up_thread(self) -> None:
        logger.debug("Cleaning up chat thread and agent")
        if self.thread:
            await self.client.agents.delete_thread(self.thread.id)
            logger.debug(f"Thread {self.thread.id} deleted")
        if self.agent:
            await self.client.agents.delete_agent(self.agent.id)
            logger.debug(f"Agent {self.agent.id} deleted")

    async def process_message(
        self, user_message: str, thread: ChatHistoryAgentThread = None
    ) -> str:
        logger.debug(f"Processing message: {user_message}")
        if not self.thread:
            await self.start_thread()
        async for response in self.agent.invoke(
            messages=user_message, thread=self.thread, streaming=True
        ):
            logger.debug(f"Received response: {response.content}")
            return response.content
