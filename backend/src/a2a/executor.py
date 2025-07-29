import logging
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import Message, Part, Role, TextPart
from a2a.utils import new_task

from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticKernelLearningAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = ChatAgentHandler()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        stream, _ = await self.agent.handle_message(
            message=query, session_id=task.context_id
        )
        reply_msg_content = stream

        reply_msg_id = str(uuid4())
        task_id = str(uuid4())

        reply_message_obj = Message(
            role=Role.agent,
            parts=[Part(root=TextPart(text=reply_msg_content))],
            messageId=reply_msg_id,
            contextId=context.context_id,
            taskId=task_id,
        )

        await event_queue.enqueue_event(reply_message_obj)

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')
