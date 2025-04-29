import asyncio
import logging
import os

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (Agent, AgentThread, AsyncFunctionTool,
                                      AsyncToolSet, BingGroundingTool,
                                      CodeInterpreterTool, FileSearchTool)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from stream_event_handler import StreamEventHandler
from terminal_colors import TerminalColors as tc
from utilities import Utilities

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

TEMPERATURE = 0.1
TOP_P = 0.1
INSTRUCTIONS_FILE = None

toolset = AsyncToolSet()
utilities = Utilities()

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=PROJECT_CONNECTION_STRING,
)

functions = AsyncFunctionTool()


INSTRUCTIONS_FILE = "instructions/profile_builder.txt"

async def add_agent_tools() -> None:
    font_file_info = None
    toolset.add(functions)