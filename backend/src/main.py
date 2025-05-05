import asyncio
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

# ---- CONFIGURATION ----
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
AZURE_AI_INFERENCE_API_KEY = os.getenv(
    "AZURE_AI_INFERENCE_API_KEY"
)
AZURE_AI_INFERENCE_ENDPOINT = os.getenv(
    "AZURE_AI_INFERENCE_ENDPOINT"
)
service_id = "agent"


async def main() -> None:
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
