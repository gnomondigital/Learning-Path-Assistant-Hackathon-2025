import asyncio

from deepeval import evaluate
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler

test_query = "i want to learn python from internal and external content, give me my learning path without creating my profile."

async def get_agent_response():
    agent = ChatAgentHandler(user_id="test_user")
    response, function_calling = await agent.handle_message(test_query)
    print(
        "fcc tools used ", function_calling
    )
    tools_used = [
        ToolCall(name=plugin) for plugin in function_calling
    ]
    return response, tools_used

response, tools_used = asyncio.run(get_agent_response())

expected_tools = [
    ToolCall(name="learning_path_building_external_content_web-search_web"),
    ToolCall(name="internal_content_mcp-confluence_search"),
    ToolCall(name="internal_content_rag-retrieve_documents")
]

test_case = LLMTestCase(
    input=test_query,
    actual_output=response,
    tools_called=tools_used,
    expected_tools=expected_tools,
)

metric = ToolCorrectnessMetric()

evaluate(test_cases=[test_case], metrics=[metric])