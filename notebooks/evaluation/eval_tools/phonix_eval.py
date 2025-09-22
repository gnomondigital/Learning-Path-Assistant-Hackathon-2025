import asyncio

import pandas as pd
from phoenix.evals import (HALLUCINATION_PROMPT_RAILS_MAP,
                           HALLUCINATION_PROMPT_TEMPLATE, OpenAIModel,
                           llm_classify)

from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler
from notebooks.utils import setup_logger

logger = setup_logger(__name__)


test_query = "I want to learn Data Science from scratch. I know nothing without creating my profile just give me my learning path."


async def get_agent_response():
    agent = ChatAgentHandler(user_id="test_user")
    response, _ = await agent.handle_message(test_query)
    return response


response = asyncio.run(get_agent_response())

df = pd.DataFrame(
    {
        "input": [test_query],
        "output": [response],
        "reference": [
            """
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
        ],
    }
)

model = OpenAIModel(
    model="gpt-4",
    temperature=0.0,
)

rails = list(HALLUCINATION_PROMPT_RAILS_MAP.values())

results = llm_classify(
    data=df,
    template=HALLUCINATION_PROMPT_TEMPLATE,
    model=model,
    rails=rails,
    provide_explanation=True,
)

pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_columns", None)
pd.set_option(
    "display.expand_frame_repr", False
)

logger.info(results)
