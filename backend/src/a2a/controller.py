from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.src.a2a.agent import get_agent_card
from backend.src.a2a.executor import SemanticKernelLearningAgentExecutor

router = APIRouter()
A2A_PATH = "api/v1/a2a"

@router.get("/.well-known/agent.json")
async def retrieve_agent_card(
    request: Request
):
    agent_card = get_agent_card(base_url=f"{request.base_url}{A2A_PATH}")
    return JSONResponse(agent_card.model_dump(mode="json", exclude_none=True))


@router.post("")
async def handle_message(
    request: Request
):
    agent_card = get_agent_card(base_url=f"{request.base_url}{A2A_PATH}")

    request_handler = DefaultRequestHandler(
        agent_executor=SemanticKernelLearningAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    return await A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )._handle_requests(request)
