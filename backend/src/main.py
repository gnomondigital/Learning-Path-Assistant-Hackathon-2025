import asyncio
import os

import semantic_kernel as sk
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.function_choice_behavior import \
    FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments

from backend.src.agents.confluence.academy_agent import AcademyAgent
from backend.src.agents.profile_builder.profile_builder import \
    ProfileBuilderAgent
from backend.src.agents.web_agent.web_agent import WebAgent
from backend.src.instructions.instructions_system import GLOBAL_PROMPT

# ---- CONFIGURATION ----
API_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
AZURE_AI_INFERENCE_API_KEY = os.getenv("AZURE_AI_INFERENCE_API_KEY")
AZURE_AI_INFERENCE_ENDPOINT = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
service_id = "agent"


class SemanticKernelAgentHandler:
    def __init__(self):
        self.kernel = sk.Kernel()

        self.kernel.add_service(
            AzureChatCompletion(
                service_id=service_id,
                api_key=AZURE_AI_INFERENCE_API_KEY,
                deployment_name=API_DEPLOYMENT_NAME,
                endpoint=AZURE_AI_INFERENCE_ENDPOINT,
            )
        )

        self.kernel.add_plugin(AcademyAgent(), plugin_name="Academy_Agent")
        self.kernel.add_plugin(WebAgent(), plugin_name="Web_search_Agent")
        self.kernel.add_plugin(
            ProfileBuilderAgent(), plugin_name="profile_builder_agent"
        )

        settings = self.kernel.get_prompt_execution_settings_from_service_id(
            service_id=service_id
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        self.agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="Host",
            instructions=GLOBAL_PROMPT,
            arguments=KernelArguments(settings=settings),
        )
        self.thread = None

    async def start_thread(self):
        if not self.thread:
            self.thread = ChatHistoryAgentThread()
        return self.thread

    async def process_message(
        self, user_message: str, thread: ChatHistoryAgentThread = None
    ) -> str:
        if not self.thread:
            await self.start_thread()
        # 5. Invoke the agent for a response
        async for response in self.agent.invoke(
            messages=user_message, thread=self.thread
        ):
            return response.content
