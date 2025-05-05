import asyncio
import os
from typing import Annotated

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel import Kernel
from semantic_kernel.agents import (AzureAIAgentSettings, ChatCompletionAgent,
                                    ChatHistoryAgentThread)
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments

from backend.src.agents.confluence.academy_agent import AcademyAgent
from backend.src.agents.profile_builder.profile_builder import \
    ProfileBuilderAgent
from backend.src.agents.web_agent.web_agent import WebAgent

# ---- CONFIGURATION ----
AGENT_NAME = "GD Academy"
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
API_KEY = os.getenv("API_KEY")


async def main() -> None:
    print("Initializing Azure AI agents...\n")
    service_id = "agent"
    kernel = Kernel()
    kernel.add_plugin(ProfileBuilderAgent(), plugin_name="menu")
    kernel.add_plugin(WebAgent(), plugin_name="web")
    kernel.add_plugin(AcademyAgent(), plugin_name="academy")
    kernel.add_service(
        AzureChatCompletion(
            deployment_name=API_DEPLOYMENT_NAME,
            api_key=API_KEY,
            endpoint=AZURE_ENDPOINT,
            service_id=service_id,
        )
    )
    settings = kernel.get_prompt_execution_settings_from_service_id(
        service_id=service_id
    )
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    agent = ChatCompletionAgent(
        kernel=kernel,
        name="Host",
        instructions="Answer questions based on the profile builder, web search, or academy information.",
        arguments=KernelArguments(settings=settings),
    )

    thread: ChatHistoryAgentThread = None
    while True:
        input_text = input("Enter your message (or 'exit' to quit): ")
        if input_text.lower() == "exit":
            break
        print(f"User: {input_text}")
        # 5. Invoke the agent for a response
        async for response in agent.invoke(messages=input_text, thread=thread):
            print(f"Agent :{response.name}: {response}")
            thread = response.thread

    # 6. Cleanup: Clear the thread
    await thread.delete() if thread else None


# ---- ENTRY POINT ----
if __name__ == "__main__":
    asyncio.run(main())
