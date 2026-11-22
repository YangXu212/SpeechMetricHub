"""Optional-dependency speech scorers; importing this package loads no models."""

__version__ = "0.10.0"

from .registry import list_metrics, register, run
from .models import evaluate
from .comparison import compare_recognition

__all__ = ["list_metrics", "register", "run", "evaluate", "compare_recognition"]
