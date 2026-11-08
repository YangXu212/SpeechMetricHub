"""SpeechMetricHub: protocol-aware evaluation through upstream speech scorers.

The historical ``speech_eval`` import remains supported. Both namespaces expose
the same function objects; no scoring algorithm is changed by this public facade.
"""

from speech_eval import __version__, evaluate, list_metrics, register, run
from speech_eval.batch import evaluate_batch
from speech_eval.registry import get_metric
from speech_eval.deployment import create_deployment, verify_deployment, load_deployment

__all__ = [
    "__version__",
    "run",
    "evaluate",
    "evaluate_batch",
    "list_metrics",
    "get_metric",
    "register",
    "create_deployment",
    "verify_deployment",
    "load_deployment",
]
