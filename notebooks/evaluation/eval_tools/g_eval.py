import asyncio
import time

import openai

from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler
from notebooks.utils import setup_logger

logger = setup_logger(__name__)


# Agent input and response
user_goal = "I am proficient in Python and SQL. I want to learn how to build and deploy machine learning models without creating my profile."


async def get_agent_response():
    agent = ChatAgentHandler(user_id="test_user")
    response, _ = await agent.handle_message(user_goal)
    return response


start = time.perf_counter()
agent_output = asyncio.run(get_agent_response())
end = time.perf_counter()
latency = end - start  # seconds
logger.info(f"Latency: {latency:.2f}s")

logger.info(f"Agent Output: {agent_output}")
# GEval prompt (LLM-as-a-judge)
prompt = f"""
You are an expert evaluator of AI-generated learning paths. A user asked for help with the following goal:

"{user_goal}"

The AI agent responded with this learning path:

{agent_output}

⚠️ Please note: If the AI only responds with steps to create a learning profile or gather user information, **this is not sufficient** to meet the goal of learning what the user needs. Such a response should receive **low scores across all categories.**

Evaluate the response in the following four categories from 1 to 5 (5 = excellent):
1. Relevance: Does it directly address the user's goal?
2. Completeness: Does it include specific learning steps, tools, and topics?
3. Logical Coherence: Are the steps logically ordered to support a beginner's learning?
4. Latency: How long did it take to generate the response? (in seconds) and this is the latency value: {latency:.2f} (ideal is between 8 and 10 seconds)

For each category, assign a score from 1 (very poor) to 5 (excellent) based on the quality of the agent's response.

After scoring, calculate the overall score as the average of the four category scores (rounded to two decimal places).

Return only a JSON object like this:
{{
    "relevance": 2,
    "completeness": 2,
    "coherence": 2,
    "latency": 2,
    "overall_score": 2.00,
    "comment": "The response focuses on profile creation, not actual learning. It lacks content like Python, statistics, or projects. Logical flow exists, but not toward the goal."
}}
"""


response = openai.chat.completions.create(
    model="gpt-4", messages=[{"role": "user", "content": prompt}]
)

logger.info(response.choices[0].message.content)
