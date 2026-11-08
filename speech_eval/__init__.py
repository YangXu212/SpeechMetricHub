"""Optional-dependency speech scorers; importing this package loads no models."""

__version__ = "0.3.0"

from .registry import list_metrics, register, run
from .models import evaluate

__all__ = ["list_metrics", "register", "run", "evaluate"]
