import asyncio

from deepeval import evaluate
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler
from notebooks.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


class ToolEvaluation:
    def __init__(self, user_id: str, test_query: str):
        self.user_id = user_id
        self.test_query = test_query
        self.agent = ChatAgentHandler(user_id=self.user_id)

    async def _get_agent_response(self):
        response, function_calling = await self.agent.handle_message(self.test_query)
        logger.info("fcc tools used ", function_calling)
        tools_used = [ToolCall(name=plugin) for plugin in function_calling]
        return response, tools_used

    def evaluate(self, expected_tools):
        response, tools_used = asyncio.run(self._get_agent_response())

        test_case = LLMTestCase(
            input=self.test_query,
            actual_output=response,
            tools_called=tools_used,
            expected_tools=expected_tools,
        )

        metric = ToolCorrectnessMetric()
        result = evaluate(test_cases=[test_case], metrics=[metric])
        logger.info(f"Tool Correctness: {result}")
        return result


def run_evaluation():
    test_query = "i want to learn python from internal and external content, give me my learning path without creating my profile."
    expected_tools = [
        ToolCall(name="learning_path_building_external_content_web-search_web"),
        ToolCall(name="internal_content_mcp-confluence_search"),
        ToolCall(name="internal_content_rag-retrieve_documents"),
    ]

    evaluator = ToolEvaluation(user_id="test_user", test_query=test_query)
    evaluation_result = evaluator.evaluate(expected_tools=expected_tools)
    print(f"Evaluation Result: {evaluation_result}")
