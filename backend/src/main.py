import asyncio
import os

import semantic_kernel as sk
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.function_choice_behavior import \
    FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments

from backend.src.agents.confluence.academy_agent import AcademyAgent

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
