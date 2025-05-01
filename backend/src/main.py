import asyncio
import os

import semantic_kernel as sk
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import (AgentGroupChat, AzureAIAgent,
                                    AzureAIAgentSettings)
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.contents import AuthorRole

from backend.src.agents.confluence.academy_agent import AcademyAgent
from backend.src.agents.web_agent.web_agent import WebAgent
from backend.src.prompts.academy_instructions import PROMPT as ACADEMY_PROMPT
from backend.src.prompts.profile_builder import PROMPT
from backend.src.prompts.search_prompt import PROMPT as WEB_PROMPT
from backend.src.agents.profile_builder.profile_builder import \
    ProfileBuilderAgent

# Initialize the Semantic Kernel
kernel = sk.Kernel()


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
        profile_builder_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="profile_builder_agent",
            instructions=PROMPT,
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        profile_builder_agent = AzureAIAgent(
            client=client,
            definition=profile_builder_definition,
            plugins=[ProfileBuilderAgent()],  # Add the plugin to the agent
        )

        # 1 Create an academy agent
        web_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="web_agent",
            instructions=WEB_PROMPT,
        )
        web_agent = AzureAIAgent(
            client=client,
            definition=web_definition,
            plugins=[WebAgent()],
        )

        academy_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="academy_learning_agent",
            instructions=ACADEMY_PROMPT,
        )
        academy_agent = AzureAIAgent(
            client=client,
            definition=academy_definition,
            plugins=[AcademyAgent()],
        )

        # 5. Place the agents in a group chat with a custom termination strategy
        chat = AgentGroupChat(
            agents=[profile_builder_agent, academy_agent, web_agent],
            termination_strategy=ApprovalTerminationStrategy(
                agents=[web_agent], maximum_iterations=10),
        )

        try:
            await chat.add_chat_message(message=TASK)
            print(f"# {AuthorRole.USER}: '{TASK}'")
            # 7. Invoke the chat
            async for content in chat.invoke():
                print(
                    f"# {content.role} - {content.name or '*'}: '{content.content}'")
        except Exception as e:
            print(f"Error: {e}")
            raise e


if __name__ == "__main__":
    asyncio.run(main())
