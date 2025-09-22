from notebooks.utils.logging_utils import setup_logger
from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler
import asyncio

import pandas as pd
from phoenix.evals import (HALLUCINATION_PROMPT_RAILS_MAP,
                           HALLUCINATION_PROMPT_TEMPLATE, OpenAIModel,
                           llm_classify)

logger = setup_logger(__name__)


class PhonixEvaluator:
    def __init__(
            self, user_id, test_query, reference,
            model_name="gpt-4", temperature=0.0):
        self.user_id = user_id
        self.test_query = test_query
        self.reference = reference
        self.model_name = model_name
        self.temperature = temperature
        self.model = OpenAIModel(
            model=self.model_name, temperature=self.temperature)
        self.rails = list(HALLUCINATION_PROMPT_RAILS_MAP.values())

    async def get_agent_response(self):
        agent = ChatAgentHandler(user_id=self.user_id)
        response, _ = await agent.handle_message(self.test_query)
        return response

    def evaluate(self):
        # Run the agent response asynchronously
        response = asyncio.run(self.get_agent_response())

        # Prepare the DataFrame
        df = pd.DataFrame(
            {
                "input": [self.test_query],
                "output": [response],
                "reference": [self.reference],
            }
        )

        # Perform evaluation
        results = llm_classify(
            data=df,
            template=HALLUCINATION_PROMPT_TEMPLATE,
            model=self.model,
            rails=self.rails,
            provide_explanation=True,
        )

        # Log and return results
        pd.set_option("display.max_colwidth", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.expand_frame_repr", False)
        logger.info(results)
        return results


def run_evaluation():
    test_query = "I want to learn Data Science from scratch. I know nothing without creating my profile just give me my learning path."
    reference = """
    1. Start with basic programming in Python.
    2. Learn fundamental statistics and mathematics for data science.
    3. Practice data manipulation using Pandas and NumPy.
    4. Get familiar with data visualization tools like Matplotlib, Seaborn, or Power BI.
    5. Learn how to handle databases and SQL queries.
    6. Explore machine learning using scikit-learn.
    7. Deepen your knowledge with deep learning using TensorFlow or PyTorch.
    8. Understand big data tools such as Apache Spark.
    9. Learn about data pipelines and workflow orchestration.
    10. Optional: Learn web scraping, data collection tools, and basic cloud deployment (e.g., with microservices or Docker).
    """

    evaluator = PhonixEvaluator(
        user_id="test_user", test_query=test_query, reference=reference)
    results = evaluator.evaluate()
    logger.info(results)
