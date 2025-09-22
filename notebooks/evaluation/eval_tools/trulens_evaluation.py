import asyncio

from dotenv import load_dotenv
from trulens_eval import Tru
from trulens_eval.feedback.provider.openai import OpenAI as EvalOpenAI

from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler

load_dotenv()
tru = Tru()
provider = EvalOpenAI()

QUERY = ("Build me a 6-week learning path to pass Azure DP-203 "
         "using official sources.")
CONTEXTS = [
    "Microsoft Learn DP-203 study guide and modules ...",
    "Azure Synapse Analytics official documentation ...",
    "Azure Data Factory docs pipelines & ETL ..."
]


async def generate_learning_path(query: str) -> str:
    agent = ChatAgentHandler(user_id="eval_user")
    answer, _ = await agent.handle_message(query)
    return answer


def groundedness_score(answer: str, contexts: list) -> dict:
    res = provider.groundedness_measure_with_cot_reasons(answer, contexts)
    if hasattr(res, "score"):
        return {
            "score": float(res.score),
            "reasons": getattr(res, "reasons", None)
        }
    return {"score": float(res), "reasons": None}


async def run_trulens_eval():
    answer = await generate_learning_path(QUERY)
    print(f"\n=== Agent Answer ===\n{answer}")

    score_data = groundedness_score(answer, CONTEXTS)
    print(f"\nGroundedness Score: {score_data['score']:.3f}")
    if score_data.get("reasons"):
        print(f"Reasons: {score_data['reasons']}")

    return score_data


if __name__ == "__main__":
    asyncio.run(run_trulens_eval())
