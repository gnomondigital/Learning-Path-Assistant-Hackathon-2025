import asyncio
import os

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
from semantic_kernel import Kernel

from backend.src.agents.confluence.academy_agent import AcademyAgent
from backend.src.agents.profile_builder.profile_builder import ProfileBuilderAgent
from backend.src.agents.web_agent.web_agent import WebAgent
from backend.src.prompts.academy_instructions import PROMPT as ACADEMY_PROMPT
from backend.src.prompts.profile_builder import PROMPT as PROFILE_PROMPT
from backend.src.prompts.search_prompt import PROMPT as WEB_PROMPT
from backend.src.instructions.instructions_system import GLOBAL_PROMPT
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread




# ---- CONFIGURATION ----
AGENT_NAME = "GD Academy"
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
API_KEY = os.getenv("API_KEY")

# Azure agent settings
TEMPERATURE = 0.1
TOP_P = 0.1
MAX_COMPLETION_TOKENS = 10240
MAX_PROMPT_TOKENS = 20480


# ---- TERMINATION STRATEGY ----
class ApprovalTerminationStrategy(TerminationStrategy):
    async def should_agent_terminate(self, agent, history):
        return "approved" in history[-1].content.lower()


# ---- MAIN CHAT FUNCTIONALITY ----
async def main() -> None:
    print("Initializing Azure AI agents...\n")
    service_id = "agent"
    ai_agent_settings = AzureAIAgentSettings(model_deployment_name=API_DEPLOYMENT_NAME)
    kernel = Kernel()
    kernel.add_plugin(ProfileBuilderAgent(), plugin_name="menu")
    kernel.add_plugin(WebAgent(), plugin_name="web")
    kernel.add_plugin(AcademyAgent(), plugin_name="academy")
    kernel.add_service(AzureChatCompletion(deployment_name=API_DEPLOYMENT_NAME, api_key=API_KEY, endpoint=AZURE_ENDPOINT,service_id=service_id))
    settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient.from_connection_string(credential=creds, conn_str=PROJECT_CONNECTION_STRING) as client,
    ):
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
