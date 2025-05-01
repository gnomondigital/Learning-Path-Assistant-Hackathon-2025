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
from backend.src.agents.profile_builder.profile_builder import \
    ProfileBuilderAgent
from backend.src.agents.web_agent.web_agent import WebAgent
from backend.src.prompts.academy_instructions import PROMPT as ACADEMY_PROMPT
from backend.src.prompts.profile_builder import PROMPT as PROFILE_PROMPT
from backend.src.prompts.search_prompt import PROMPT as WEB_PROMPT
from backend.src.instructions.instructions_system import GLOBAL_PROMPT

# ---- CONFIGURATION ----
AGENT_NAME = "GD Academy"
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")

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
    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient.from_connection_string(credential=creds, conn_str=PROJECT_CONNECTION_STRING) as client,
    ):
        # Build all agents with their plugins
        profile_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="profile_builder_agent",
            instructions=PROFILE_PROMPT,
        )
        profile_agent = AzureAIAgent(
            client=client,
            definition=profile_definition,
            plugins=[ProfileBuilderAgent()],
        )

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
            name="academy_agent",
            instructions=GLOBAL_PROMPT,
        )
        academy_agent = AzureAIAgent(
            client=client,
            definition=academy_definition,
            plugins=[AcademyAgent()],
        )

        # Group Chat with termination strategy
        chat = AgentGroupChat(
            agents=[profile_agent, web_agent, academy_agent],
            termination_strategy=ApprovalTerminationStrategy(
                agents=[web_agent], maximum_iterations=10
            ),
        )

        print("💬 Type your question or message below (type 'exit' to quit):")
        while True:
            user_input = input("\n👤 You: ")
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting chat. Goodbye!")
                break

            try:
                await chat.add_chat_message(message=user_input)
                async for content in chat.invoke():
                    print(
                        f"🤖 {content.role} - {content.name or '*'}: {content.content}")
            except Exception as e:
                print(f"⚠️ Error during chat: {e}")


# ---- ENTRY POINT ----
if __name__ == "__main__":
    asyncio.run(main())
