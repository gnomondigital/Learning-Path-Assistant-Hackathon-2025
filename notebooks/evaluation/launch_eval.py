"""
Launch evaluation script for different evaluation tools.
Example usages:
uv run python notebooks/evaluation/launch_eval.py geval
"""

import subprocess
import sys

evals = {
    "arize": "arize_evaluation",
    "deep_tools": "deep_eval.used_tools_eval",
    "deep_toxicity": "deep_eval.response_toxicity_eval",
    "phoenix": "phonix_eval",
    "geval": "g_eval",
    "trulens": "trulens_evaluation"
}
name = sys.argv[1] if len(sys.argv) > 1 else "geval"

module = f"notebooks.evaluation.eval_tools.{evals.get(name, 'g_eval')}"

subprocess.run(["uv", "run", "python", "-m", module])
