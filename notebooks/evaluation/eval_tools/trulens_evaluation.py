from notebooks.utils.logging_utils import setup_logger
from typing import Any, Dict, List

from dotenv import load_dotenv
from trulens_eval import Feedback, Tru
from trulens_eval.feedback.provider.openai import OpenAI as EvalOpenAI
import asyncio

from backend.src.agents.orchestrator_agent.semantic_kernel_agent import \
    ChatAgentHandler

logger = setup_logger(__name__)


class LearningPathEvaluator:
    def __init__(self):
        load_dotenv()
        self.tru = Tru()
        self.provider = EvalOpenAI()

    async def generate_learning_path(self, query: str) -> str:
        agent = ChatAgentHandler(user_id="eval_user")
        answer, _calls = await agent.handle_message(query)
        return answer

    def groundedness_direct(self, answer: str, contexts: List[str]) -> Dict[str, Any]:
        """
        Direct call to provider's groundedness with chain-of-thought reasons.
        Returns a dict like: {"score": float, "reasons": "..."}.
        """
        res = self.provider.groundedness_measure_with_cot_reasons(
            answer,
            contexts
        )
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

    def groundedness_feedback(self, answer: str, contexts: List[str]) -> Dict[str, Any]:
        """
        Same metric but via the trulens_eval.Feedback pipeline to match your style.
        We bind `references=contexts` via kwargs; then call `f(answer)`.
        """
        f_grounded = Feedback(
            self.provider.groundedness_measure_with_cot_reasons,
            name="Groundedness"
        ).on_output()

        scored = f_grounded(answer, references=contexts)

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

    async def evaluate(self, query: str, contexts: List[str]) -> None:
        """
        Evaluate the groundedness of the generated learning path.
        """
        answer = await self.generate_learning_path(query)
        logger.info("\n=== Agent Answer ===\n%s", answer)

        direct = self.groundedness_direct(answer, contexts)
        logger.info("\n[Direct] Groundedness: %s", round(direct["score"], 3))
        if direct.get("reasons"):
            logger.info("Reasons: %s", direct["reasons"])

        fb = self.groundedness_feedback(answer, contexts)
        logger.info("\n[Feedback] Groundedness: %s", round(fb["score"], 3))
        if fb.get("reasons"):
            logger.info("Reasons: %s", fb["reasons"])


def run_evaluation():

    evaluator = LearningPathEvaluator()
    asyncio.run(
        evaluator.evaluate(
            query="Build me a 6-week learning path to pass Azure DP-203 using official sources.",
            contexts=[
                "Microsoft Learn DP-203 study guide and modules ...",
                "Azure Synapse Analytics official documentation ...",
                "Azure Data Factory docs pipelines & ETL ..."
            ]
        )
    )
