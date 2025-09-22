from notebooks.utils.logging_utils import setup_logger
from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler
import asyncio


import pandas as pd
from phoenix.evals import OpenAIModel, llm_classify


logger = setup_logger(__name__)


class RouterEvaluator:
    ROUTER_EVAL_TEMPLATE = """You are comparing a response to a question, and
    verifying whether that response should have made a function call instead
    of responding directly. Here is the data:
        [BEGIN DATA]
        ************
        [Question]: {question}
        ************
        [LLM Response]: {response}
        ************
        [END DATA]

    Compare the Question above to the response. You must determine whether
    the response
    decided to call the correct function.

    Your response must be single word, either "correct" or "incorrect", and
    should not contain any text or characters aside from that word. "incorrect"
    means that the agent should have made function call instead of responding
    directly and did not, or the function call chosen was the incorrect one.
    "correct" means the selected function would correctly and fully answer the
    user's question.

    Here is more information on each function:
    - product_search: Search for products based on criteria.
    - track_package: Track the status of a package based on the tracking
    number."""

    rails = ["incorrect", "correct"]

    def __init__(self, user_id="test_user"):
        self.agent = ChatAgentHandler(user_id=user_id)

    async def evaluate_router_behavior(self, test_query):
        response, _ = await self.agent.handle_message(test_query)

        response_df = pd.DataFrame(
            {"question": [test_query], "response": [response]}
        )

        results = llm_classify(
            data=response_df,
            template=self.ROUTER_EVAL_TEMPLATE,
            model=OpenAIModel(model="gpt-4o"),
            rails=self.rails,
            provide_explanation=True,
            concurrency=4,
        )

        return results


def run_evaluation():
    evaluator = RouterEvaluator()
    test_query = "I want to learn Data Science , give my learning path without creating my profile."
    results = asyncio.run(evaluator.evaluate_router_behavior(test_query))

    pd.set_option("display.max_colwidth", None)
    logger.info("user and answer evaluation : %s", results)
