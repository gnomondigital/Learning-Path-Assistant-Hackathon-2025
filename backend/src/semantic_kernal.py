import asyncio
import os
from typing import Annotated

import semantic_kernel as sk
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import BingGroundingTool
from azure.identity.aio import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from semantic_kernel.agents import (AgentGroupChat, AzureAIAgent,
                                    AzureAIAgentSettings, AzureAIAgentThread,
                                    ChatCompletionAgent)
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import (AzureChatCompletion,
                                                   OpenAIChatCompletion)
from semantic_kernel.contents import AuthorRole
from semantic_kernel.functions import kernel_function

from backend.src.prompts.profile_builder import PROMPT
from backend.src.service.profile_builder.profile_builder import \
    ProfileBuilderAgent
from backend.src.prompts.academy_instructions import PROMPT as ACADEMY_PROMPT
# Initialize the Semantic Kernel
kernel = sk.Kernel()

# Configure tracing


async def enable_project_monitoring():
    application_insights_connection_string = await project_client.telemetry.get_connection_string()
    if not application_insights_connection_string:
        print("Application Insights was not enabled for this project.")
        print("Enable it via the 'Tracing' tab in your AI Foundry project page.")
        exit()
    else:
        print("Application Insights is enabled!")
    configure_azure_monitor(
        connection_string=application_insights_connection_string)

    project_client.telemetry.enable()


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


AGENT_NAME = "GD Academy"
FONTS_ZIP = "fonts/fonts.zip"
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")
AZURE_AI_INFERENCE_ENDPOINT = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
AZURE_AI_INFERENCE_API_KEY = os.getenv("AZURE_AI_INFERENCE_API_KEY")
MAX_COMPLETION_TOKENS = 10240
MAX_PROMPT_TOKENS = 20480
# The LLM is used to generate the SQL queries.
# Set the temperature and top_p low to get more deterministic results.
TEMPERATURE = 0.1
TOP_P = 0.1
INSTRUCTIONS_FILE = None

# Simulate a conversation with the agent
TASK = "a slogan for a new line of electric cars."
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=PROJECT_CONNECTION_STRING,
)


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
    

USER_INPUTS = [
    "Hello, I am John Doe.",
    "What is your name?",
    "What is my name?",
]

async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create an agent on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="profile_builder_agent",
            instructions=PROMPT,
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=[ProfileBuilderAgent()],  # Add the plugin to the agent
        )

       
    

        # 3. Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread = None
        
        try:
            await enable_project_monitoring()
            scenario = os.path.basename(__file__)
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(scenario):
                for user_input in USER_INPUTS:
                    print(f"# User: {user_input}")
                    # 4. Invoke the agent with the specified message for response
                    response = await agent.get_response(messages=user_input, thread=thread)
                    print(f"# {response.name}: {response}")
                    thread = response.thread

        finally:
            # 8. Cleanup: Delete the agents
            await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
