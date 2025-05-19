import logging
import os
from collections.abc import AsyncIterable
from typing import Awaitable, Callable, Optional

import semantic_kernel as sk
from pydantic import BaseModel
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel.contents import FunctionCallContent, FunctionResultContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import (
    StreamingChatMessageContent,
)
from semantic_kernel.filters import FunctionInvocationContext
from semantic_kernel.functions.kernel_arguments import KernelArguments

from backend.src.agents.bing_seach.bing_search_agent import BingSearch
from backend.src.agents.bing_seach.search_prompt_instructions import (
    PROMPT as WEB_SEARCH_PROMPT,
)
from backend.src.agents.confluence.academy_rag import (
    ConfluenceIngestion,
    SearchPlugin,
)
from backend.src.agents.orchestrator_agent.instructions_system import (
    GLOBAL_PROMPT,
)
from backend.src.agents.profile_builder.profile_builder_instructions import (
    PROMPT as PROFILE_BUILDER_PROMPT,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
AZURE_AI_INFERENCE_API_KEY = os.getenv("AZURE_AI_INFERENCE_API_KEY")
AZURE_AI_INFERENCE_ENDPOINT = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_API_KEY = os.getenv("CONFLUENCE_API_KEY")

SERVICE_ID = "agent"


class Profile(BaseModel):
    current_postion: str
    target_role: str
    learning_obstacles: str
    time_limit: str
    preferred_learning_style: list[str]


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(
        AzureChatCompletion(
            service_id=service_id,
            api_key=AZURE_AI_INFERENCE_API_KEY,
            deployment_name=API_DEPLOYMENT_NAME,
            endpoint=AZURE_AI_INFERENCE_ENDPOINT,
        )
    )
    return kernel


intermediate_steps: list[ChatMessageContent] = []


async def handle_intermediate_steps(message: ChatMessageContent) -> None:
    intermediate_steps.append(message)


async def logger_filter(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    logger.info(
        f"FunctionInvoking - {context.function.plugin_name}.{context.function.name}"
    )

    await next(context)

    logger.info(
        f"FunctionInvoked - {context.function.plugin_name}.{context.function.name}"
    )


class ChatAgentHandler:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.agent = None
        self.thread: Optional[ChatHistoryAgentThread] = None
        self.initialized = False
        self.confluence_plugin = None
        self.intermediate_streaming_steps: list[ChatMessageContent] = []

    async def handle_streaming_intermediate_steps(
        self, message: ChatMessageContent
    ) -> None:
        self.intermediate_streaming_steps.append(message)

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

        search_client = ConfluenceIngestion().update_content_process()
        self.confluence_plugin = MCPStdioPlugin(
            name="atlassian",
            description="Confluence plugin for Atlassian",
            command="docker",
            args=[
                "run",
                "-i",
                "--rm",
                "-e",
                "CONFLUENCE_URL",
                "-e",
                "CONFLUENCE_USERNAME",
                "-e",
                "CONFLUENCE_API_TOKEN",
                "ghcr.io/sooperset/mcp-atlassian:latest",
            ],
            env={
                "CONFLUENCE_URL": CONFLUENCE_URL,
                "CONFLUENCE_USERNAME": CONFLUENCE_USERNAME,
                "CONFLUENCE_API_TOKEN": CONFLUENCE_API_KEY,
            },
        )

        await self.confluence_plugin.__aenter__()

        kernel = sk.Kernel()
        kernel.add_plugin(BingSearch(), plugin_name="Web_search_Agent")
        kernel.add_plugin(profile_builder, plugin_name="Profile_Builder_Agent")
        kernel.add_plugin(
            self.confluence_plugin, plugin_name="Confluence_Agent"
        )
        kernel.add_plugin(
            SearchPlugin(search_client=search_client),
            plugin_name="azure_ai_search",
        )

        kernel.add_service(
            AzureChatCompletion(
                service_id=SERVICE_ID,
                api_key=AZURE_AI_INFERENCE_API_KEY,
                deployment_name=API_DEPLOYMENT_NAME,
                endpoint=AZURE_AI_INFERENCE_ENDPOINT,
            )
        )
        kernel.add_filter("function_invocation", logger_filter)

        settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=SERVICE_ID
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        self.agent = ChatCompletionAgent(
            kernel=kernel,
            name="Host",
            instructions=GLOBAL_PROMPT.format(
                WEB_SEARCH_PROMPT=WEB_SEARCH_PROMPT
            ),
            arguments=KernelArguments(settings=settings),
        )
        self.initialized = True

    async def handle_message(self, message: str) -> str:
        await self.initialize()
        intermediate_steps.clear()
        function_calling = []
        output_text = ""
        async for response in self.agent.invoke(
            messages=message,
            thread=self.thread,
            on_intermediate_message=handle_intermediate_steps,
        ):
            output_text += str(response)
            self.thread = response.thread
        print(f"# {response.name}: {response.content}")
        print("\nIntermediate Steps:")
        for msg in intermediate_steps:
            if any(
                isinstance(item, FunctionResultContent) for item in msg.items
            ):
                for fr in msg.items:
                    if isinstance(fr, FunctionResultContent):
                        print(
                            f"Function Result:> {fr.result} for function: {fr.name}"
                        )
            elif any(
                isinstance(item, FunctionCallContent) for item in msg.items
            ):
                for fcc in msg.items:
                    if isinstance(fcc, FunctionCallContent):
                        print(
                            f"Function Call:> {fcc.name} with arguments: {fcc.arguments}"
                        )
                        function_calling.append(fcc.name)
            else:
                print(f"{msg.role}: {msg.content}")
        return output_text, function_calling

    async def handle_message_streaming(
        self, message: str
    ) -> AsyncIterable[StreamingChatMessageContent]:
        await self.initialize()

        async for result in self.agent.invoke_stream(
            messages=message,
            thread=self.thread,
            on_intermediate_message=self.handle_streaming_intermediate_steps,
        ):
            yield f"data: {result.content}\n\nlogs: {self.intermediate_streaming_steps}\n\n"
            self.thread = result.thread

    async def cleanup(self):
        if self.thread:
            await self.thread.delete()

        if self.confluence_plugin:
            try:
                logging.info("Cleaning up Confluence plugin.")
                await self.confluence_plugin.__aexit__(None, None, None)

                logging.info("Confluence plugin cleaned up successfully.")
            except RuntimeError as e:
                logging.error(f"Error during Confluence plugin cleanup: {e}")

        self.initialized = False
