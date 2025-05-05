import asyncio
import os
from typing import Annotated

import semantic_kernel as sk
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel import Kernel
from semantic_kernel.agents import (AgentGroupChat, AzureAIAgent,
                                    AzureAIAgentSettings, ChatCompletionAgent,
                                    ChatHistoryAgentThread)
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.chat_completion_client_base import \
    ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import \
    FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (AzureChatCompletion,
                                                   OpenAIChatCompletion)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import \
    AzureChatPromptExecutionSettings
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments

from backend.src.agents.confluence.academy_agent import AcademyAgent
from backend.src.agents.profile_builder.profile_builder import \
    ProfileBuilderAgent
from backend.src.agents.web_agent.web_agent import WebAgent
from backend.src.instructions.instructions_system import GLOBAL_PROMPT
from backend.src.prompts.academy_instructions import PROMPT as ACADEMY_PROMPT
from backend.src.prompts.profile_builder import PROMPT as PROFILE_PROMPT
from backend.src.prompts.search_prompt import PROMPT as WEB_PROMPT

# ---- CONFIGURATION ----
AGENT_NAME = "GD Academy"
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")
AZURE_AI_INFERENCE_API_KEY = os.getenv(
    "AZURE_AI_INFERENCE_API_KEY"
)
AZURE_AI_INFERENCE_ENDPOINT = os.getenv(
    "AZURE_AI_INFERENCE_ENDPOINT"
)
service_id = "agent"
# Azure agent settings
TEMPERATURE = 0.1
TOP_P = 0.1
MAX_COMPLETION_TOKENS = 10240
MAX_PROMPT_TOKENS = 20480


class MenuPlugin:
    """A sample Menu Plugin used for the concept sample."""

    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self) -> Annotated[str, "Returns the specials from the menu."]:
        return """
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        """

    @kernel_function(description="Provides the price of the requested menu item.")
    def get_item_price(
        self, menu_item: Annotated[str, "The name of the menu item."]
    ) -> Annotated[str, "Returns the price of the menu item."]:
        return "$9.99"


async def main() -> None:
    service_id = "agent"
    kernel = sk.Kernel()
    kernel.add_service(AzureChatCompletion(
        service_id=service_id,
        api_key=AZURE_AI_INFERENCE_API_KEY,
        deployment_name=API_DEPLOYMENT_NAME,
        endpoint=AZURE_AI_INFERENCE_ENDPOINT,
    ))
    kernel.add_plugin(
        AcademyAgent(),
        plugin_name="AcademyAgent",
    )
    kernel.add_plugin(
        WebAgent(),
        plugin_name="WebAgent",
    )
    kernel.add_plugin(
        ProfileBuilderAgent(),
        plugin_name="ProfileBuilderAgent",
    )

    settings = kernel.get_prompt_execution_settings_from_service_id(
        service_id=service_id)
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    agent = ChatCompletionAgent(
        kernel=kernel,
        name="Host",
        instructions=GLOBAL_PROMPT,
        arguments=KernelArguments(settings=settings),
    )
    thread: ChatHistoryAgentThread = None
    while True:
        # Get user input
        user_input = input("User: ")
        if user_input.lower() == "exit":
            await thread.delete() if thread else None
            break
        # Add user message to history
        async for response in agent.invoke(messages=user_input, thread=thread):
            print(f"# {response.name}: {response}")
            thread = response.thread


# ---- ENTRY POINT ----
if __name__ == "__main__":
    asyncio.run(main())
