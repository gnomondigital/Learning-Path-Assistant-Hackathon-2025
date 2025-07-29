
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from backend.src.a2a.executor import SemanticKernelLearningAgentExecutor

AGENT_ID = "automated_learning_path_agent"


def get_agent_card(base_url: str):
    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=True
    )
    skills = [
        AgentSkill(
            id="retrive_data_from_db",
            name="retrive_data_from_db",
            description="Retrieves data from a database using a SQL query.",
            tags=["retrive_data_from_db", "query", "database"],
        ),
        AgentSkill(
            id="learning_path_building_external_content_web",
            name="BingSearch",
            description="Searches the web for external content relevant to learning paths.",
            tags=["web", "search", "external", "bing"],
        ),
        AgentSkill(
            id="Profile_Builder_Agent",
            name="Profile Builder",
            description="Builds and manages user learning profiles.",
            tags=["profile", "user", "builder"],
        ),
        AgentSkill(
            id="internal_content_mcp",
            name="ConfluencePlugin",
            description="Retrieves internal content from Confluence MCP.",
            tags=["internal", "confluence", "content", "mcp"],
        ),
        AgentSkill(
            id="internal_content_rag",
            name="SearchPlugin",
            description="Performs internal content retrieval using RAG search.",
            tags=["internal", "rag", "search"],
        ),
        AgentSkill(
            id="gmail_email_plugin",
            name="GmailPlugin",
            description="Accesses and manages Gmail emails.",
            tags=["gmail", "email", "plugin"],
        ),
        AgentSkill(
            id="google_calendar_plugin",
            name="GoogleCalendarPlugin",
            description="Accesses and manages Google Calendar events.",
            tags=["google", "calendar", "plugin"],
        ),
    ]
    return AgentCard(
        name=AGENT_ID,
        description="An agent that helps create personalized learning paths.",
        url=base_url,
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain", "image"],
        capabilities=capabilities,
        skills=skills,
    )


def get_agent_executor(base_url: str):
    request_handler = DefaultRequestHandler(
        agent_executor=SemanticKernelLearningAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=get_agent_card(base_url=base_url),
    )
    return server
