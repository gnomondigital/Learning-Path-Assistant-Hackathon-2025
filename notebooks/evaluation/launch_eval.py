"""
Launch evaluation script for different evaluation tools.
Example usages:
uv run  notebooks/evaluation/launch_eval.py geval
uv run  notebooks/evaluation/launch_eval.py arize
"""

from notebooks.evaluation.eval_tools.trulens_evaluation import run_evaluation as run_trulens_eval
from notebooks.evaluation.eval_tools.phonix_eval import \
    run_evaluation as run_phoenix
from notebooks.evaluation.eval_tools.g_eval import run_evaluation as run_geval
from notebooks.evaluation.eval_tools.deep_eval.used_tools_eval import \
    run_evaluation as run_deep_tools
from notebooks.evaluation.eval_tools.deep_eval.response_toxicity_eval import \
    run_evaluation as run_deep_toxicity
import asyncio
import sys
from notebooks.utils.logging_utils import setup_logger

logger = setup_logger(__name__)
# Import all evaluation modules directly
# from eval_tools.arize_evaluation import \
#     run_evaluation as run_arize


def run_evaluation(eval_name: str):
    """Import and run the specified evaluation."""
    eval_map = {
        # "arize": run_arize,
        "deep_tools": run_deep_tools,
        "deep_toxicity": run_deep_toxicity,
        "phoenix": run_phoenix,
        "geval": run_geval,
        "trulens": run_trulens_eval
    }

    if eval_name not in eval_map:
        logger.info(f"Unknown evaluation: {eval_name}")
        return None

    func = eval_map[eval_name]

    if eval_name == "trulens":
        return asyncio.run(func())
    return func()


if __name__ == "__main__":
    eval_name = sys.argv[1] if len(sys.argv) > 1 else "geval"
    result = run_evaluation(eval_name)
    logger.info(f"Evaluation '{eval_name}' completed with result: {result}")
