# trulens_eval_groundedness.py
# ----------------------------
# Pure trulens_eval Feedback API for groundedness, wired to your ChatAgentHandler.

import os
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

# --- TruLens EVAL API (do not mix with trulens.core) ---
from trulens_eval import Tru  # optional if you want to persist runs later
from trulens_eval import Feedback, Select
from trulens_eval.feedback.provider.openai import OpenAI as EvalOpenAI

# your agent
from backend.src.agents.orchestrator_agent.semantic_kernel_agent import ChatAgentHandler

load_dotenv()

# Optional: initialize a Tru DB/session if you later want to persist results
tru = Tru()

# Provider used for feedback (reads OPENAI_API_KEY; for Azure, see note below)
provider = EvalOpenAI()


async def generate_learning_path(query: str) -> str:
    agent = ChatAgentHandler(user_id="eval_user")
    answer, _calls = await agent.handle_message(query)
    return answer


def groundedness_direct(answer: str, contexts: List[str]) -> Dict[str, Any]:
    """
    Direct call to provider's groundedness with chain-of-thought reasons.
    Returns a dict like: {"score": float, "reasons": "..."}.
    """
    res = provider.groundedness_measure_with_cot_reasons(
        answer,
        contexts
    )
    # Normalize: some versions return an object; others a dict/float
    out: Dict[str, Any] = {}
    if hasattr(res, "score"):
        out["score"] = float(res.score)
        out["reasons"] = getattr(res, "reasons", None)
    elif isinstance(res, dict):
        out["score"] = float(res.get("score", 0.0))
        out["reasons"] = res.get("reasons")
    else:
        out["score"] = float(res)
        out["reasons"] = None
    return out


def groundedness_feedback(answer: str, contexts: List[str]) -> Dict[str, Any]:
    """
    Same metric but via the trulens_eval.Feedback pipeline to match your style.
    We bind `references=contexts` via kwargs; then call `f(answer)`.
    """
    f_grounded = Feedback(
        provider.groundedness_measure_with_cot_reasons,
        name="Groundedness"
    ).on_output()  # evaluate on function output (we pass 'answer' directly)

    # In Feedback API, you can pass fixed kwargs at call-time:
    scored = f_grounded(answer, references=contexts)

    # Normalize result shape
    out: Dict[str, Any] = {}
    if hasattr(scored, "score"):
        out["score"] = float(scored.score)
        out["reasons"] = getattr(scored, "reasons", None)
    elif isinstance(scored, dict):
        out["score"] = float(scored.get("score", 0.0))
        out["reasons"] = scored.get("reasons")
    else:
        out["score"] = float(scored)
        out["reasons"] = None
    return out


async def main():
    query = "Build me a 6-week learning path to pass Azure DP-203 using official sources."
    contexts = [
        "Microsoft Learn DP-203 study guide and modules ...",
        "Azure Synapse Analytics official documentation ...",
        "Azure Data Factory docs pipelines & ETL ..."
    ]

    answer = await generate_learning_path(query)
    print("\n=== Agent Answer ===\n", answer)

    # 1) Direct provider call
    direct = groundedness_direct(answer, contexts)
    print("\n[Direct] Groundedness:", round(direct["score"], 3))
    if direct.get("reasons"):
        print("Reasons:", direct["reasons"])

    # 2) Feedback API call (your preferred pattern)
    fb = groundedness_feedback(answer, contexts)
    print("\n[Feedback] Groundedness:", round(fb["score"], 3))
    if fb.get("reasons"):
        print("Reasons:", fb["reasons"])

    # Optional: if later you wire this into a persisted app/run, you can
    # use `tru.add_record(...)` to store the result rows.

if __name__ == "__main__":
    asyncio.run(main())
