import logging
import os
from typing import Optional

import semantic_kernel as sk
from pydantic import BaseModel
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.function_choice_behavior import \
    FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion, OpenAIChatPromptExecutionSettings)
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments

from backend.src.agents.bing_seach.bing_search_agent import BingSearch
from backend.src.agents.bing_seach.search_prompt_instructions import \
    PROMPT as SEARCH_PROMPT
from backend.src.agents.confluence.academy_instructions import \
    PROMPT as ACADEMY_PROMPT
from backend.src.agents.profile_builder.profile_builder_instructions import \
    PROMPT as PROFILE_BUILDER_PROMPT
from backend.src.instructions.instructions_system import GLOBAL_PROMPT

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
AZURE_AI_INFERENCE_API_KEY = os.getenv(
    "AZURE_AI_INFERENCE_API_KEY"
)
AZURE_AI_INFERENCE_ENDPOINT = os.getenv(
    "AZURE_AI_INFERENCE_ENDPOINT"
)
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_USERNAME = os.getenv(
    "CONFLUENCE_USERNAME"
)
CONFLUENCE_API_KEY = os.getenv(
    "CONFLUENCE_API_KEY"
)

SERVICE_ID = "agent"


class Profile(BaseModel):
    current_postion: str
    target_role: str
    learning_obstacles: str
    time_limit: str
    preferred_learning_style: list[str]
    additional_informations: dict[str, str]


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(
        service_id=service_id, api_key=AZURE_AI_INFERENCE_API_KEY,
        deployment_name=API_DEPLOYMENT_NAME,
        endpoint=AZURE_AI_INFERENCE_ENDPOINT,))
    return kernel


class ChatAgentHandler:
    def __init__(self):
        self.agent = None
        self.thread: Optional[ChatHistoryAgentThread] = None
        self.initialized = False

    async def initialize(self):
        if self.initialized:
            return

        settings = OpenAIChatPromptExecutionSettings()
        settings.response_format = Profile

        profile_builder = ChatCompletionAgent(
            kernel=_create_kernel_with_chat_completion("profile_builder"),
            name="ProfileBuilderAgent",
            instructions=PROFILE_BUILDER_PROMPT,
            arguments=KernelArguments(settings=settings),
        )

        self.confluence_plugin = MCPStdioPlugin(
            name="atlassian",
            description="Confluence plugin for Atlassian",
            command="docker",
            args=[
                "run",
                "-i",
                "--rm",
                "-e", "CONFLUENCE_URL",
                "-e", "CONFLUENCE_USERNAME",
                "-e", "CONFLUENCE_API_TOKEN",
                "ghcr.io/sooperset/mcp-atlassian:latest"
            ],
            env={
                "CONFLUENCE_URL": CONFLUENCE_URL,
                "CONFLUENCE_USERNAME": CONFLUENCE_USERNAME,
                "CONFLUENCE_API_TOKEN": CONFLUENCE_API_KEY,
            }
        )

        await self.confluence_plugin.__aenter__()

        kernel = sk.Kernel()
        kernel.add_plugin(BingSearch(), plugin_name="Web_search_Agent")
        kernel.add_plugin(profile_builder, plugin_name="Profile_Builder_Agent")
        kernel.add_plugin(self.confluence_plugin,
                          plugin_name="Confluence_Agent")

        kernel.add_service(AzureChatCompletion(
            service_id=SERVICE_ID,
            api_key=AZURE_AI_INFERENCE_API_KEY,
            deployment_name=API_DEPLOYMENT_NAME,
            endpoint=AZURE_AI_INFERENCE_ENDPOINT,
        ))

        settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=SERVICE_ID
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        self.agent = ChatCompletionAgent(
            kernel=kernel,
            name="Host",
            instructions=GLOBAL_PROMPT.format(
                PROFILE_BUILDER=PROFILE_BUILDER_PROMPT,
                WEB_SEARCH_PROMPT=SEARCH_PROMPT,
                CONFLUENCE_PROMPT=ACADEMY_PROMPT
            ),
            arguments=KernelArguments(settings=settings),
        )
        self.initialized = True

    async def handle_message(self, message: str) -> str:
        await self.initialize()

        output_text = ""
        async for response in self.agent.invoke(messages=message, thread=self.thread):
            output_text += str(response)
            self.thread = response.thread
        return output_text

    async def cleanup(self):
        if self.thread:
            await self.thread.delete()
        if self.confluence_plugin:
            await self.confluence_plugin.__aexit__(None, None, None)
        self.initialized = False
