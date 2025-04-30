import asyncio
import logging
import os

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (Agent, AgentThread, AsyncFunctionTool,
                                      AsyncToolSet, BingGroundingTool,
                                      CodeInterpreterTool, FileSearchTool,
                                      ToolDefinition)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from opentelemetry import trace

from backend.src.prompts.profile_builder import PROMPT
from backend.src.service.profile_builder.profile_builder import \
    ProfileBuilderAgent
from backend.src.service.profile_builder.profile_questions import \
    PROFILE_QUESTIONS
from backend.src.utils.stream_event_handler import StreamEventHandler
from backend.src.utils.terminal_colors import TerminalColors as tc
from backend.src.utils.utilities import Utilities
import semantic_kernel as sk

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

load_dotenv()

AGENT_NAME = "GD Academy"
FONTS_ZIP = "fonts/fonts.zip"
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
PROJECT_CONNECTION_STRING = os.environ["PROJECT_CONNECTION_STRING"]
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")
MAX_COMPLETION_TOKENS = 10240
MAX_PROMPT_TOKENS = 20480
# The LLM is used to generate the SQL queries.
# Set the temperature and top_p low to get more deterministic results.
TEMPERATURE = 0.1
TOP_P = 0.1
INSTRUCTIONS_FILE = None


toolset = AsyncToolSet()
utilities = Utilities()

class ProfileBuilderAgent:
    def __init__(self, agent_name: str = "Profile Builder Agent"):
        self.name = agent_name

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=PROJECT_CONNECTION_STRING,
)

functions = AsyncFunctionTool(
    functions=set(),
)

INSTRUCTIONS_FILE = "instructions/profile_builder.txt"


async def add_profile_builder_tool() -> None:
    """Add Profile Builder Tool to the agent's toolset."""

    profile_builder = ProfileBuilderAgent(
        prompt_text=PROMPT, questions=PROFILE_QUESTIONS)
    profile_builder_tool = AsyncFunctionTool(
        {profile_builder.ask_question,
         profile_builder.collect_responses,
         profile_builder.execute})

    # Add the Profile Builder Tool to your toolset
    toolset.add(profile_builder_tool)
    return profile_builder_tool


async def initialize_agent(project_client: AIProjectClient = project_client) -> tuple[Agent, AgentThread]:
    """Initialize the agent with profile-building instructions."""
    profile_builder_tool = await add_profile_builder_tool()

    agent = await project_client.agents.create_agent(
        model=API_DEPLOYMENT_NAME,
        name="Profile Builder Agent",
        instructions=PROMPT,
        toolset=toolset,
        temperature=0.1
    )

    thread = await project_client.agents.create_thread()

    return agent, thread


async def cleanup(agent: Agent, thread: AgentThread) -> None:
    """Cleanup the resources."""
    await project_client.agents.delete_thread(thread.id)
    await project_client.agents.delete_agent(agent.id)


async def post_message(thread_id: str, content: str, agent: Agent, thread: AgentThread) -> None:
    """Post a message to the Azure AI Agent Service."""
    try:
        await project_client.agents.create_message(
            thread_id=thread_id,
            role="user",
            content=content,
        )

        stream = await project_client.agents.create_stream(
            thread_id=thread.id,
            agent_id=agent.id,
            event_handler=StreamEventHandler(
                functions=functions, project_client=project_client, utilities=utilities),
            max_completion_tokens=MAX_COMPLETION_TOKENS,
            max_prompt_tokens=MAX_PROMPT_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            instructions=agent.instructions,
        )

        async with stream as s:
            await s.until_done()
    except Exception as e:
        utilities.log_msg_purple(
            f"An error occurred posting the message: {e!s}")


async def main() -> None:
    """
    Example questions: Sales by region, top-selling products, total shipping costs by region, show as a pie chart.
    """
    async with project_client:
        agent, thread = await initialize_agent()
        if not agent or not thread:
            print(f"{tc.BG_BRIGHT_RED}Initialization failed. Ensure you have uncommented the instructions file for the lab.{tc.RESET}")
            print("Exiting...")
            return

        cmd = None

        while True:
            prompt = input(
                f"\n\n{tc.GREEN}Enter your query (type exit or save to finish): {tc.RESET}").strip()
            if not prompt:
                continue

            cmd = prompt.lower()
            if cmd in {"exit", "save"}:
                break

            await post_message(agent=agent, thread_id=thread.id, content=prompt, thread=thread)

        if cmd == "save":
            print("The agent has not been deleted, so you can continue experimenting with it in the Azure AI Foundry.")
            print(
                f"Navigate to https://ai.azure.com, select your project, then playgrounds, agents playgound, then select agent id: {agent.id}"
            )
        else:
            await cleanup(agent, thread)
            print("The agent resources have been cleaned up.")

project_client.telemetry.enable()

scenario = os.path.basename(__file__)
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span(scenario):
    with project_client:
        # Create an agent and run stream with event handler
        agent = project_client.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"], name="my-assistant", instructions="You are a helpful assistant"
        )
        print(f"Created agent, agent ID {agent.id}")

        thread = project_client.agents.create_thread()
        print(f"Created thread, thread ID {thread.id}")

        message = project_client.agents.create_message(
            thread_id=thread.id, role="user", content="Hello, tell me a joke"
        )
        print(f"Created message, message ID {message.id}")

        with project_client.agents.create_stream(
            thread_id=thread.id, agent_id=agent.id, event_handler=MyEventHandler()
        ) as stream:
            stream.until_done()

        project_client.agents.delete_agent(agent.id)
        print("Deleted agent")

        messages = project_client.agents.list_messages(thread_id=thread.id)
        print(f"Messages: {messages}")

if __name__ == "__main__":
    print("Starting async program...")
    asyncio.run(main())
    print("Program finished.")
