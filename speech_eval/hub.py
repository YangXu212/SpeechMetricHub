"""Convenient access to an explicitly provisioned, locked deployment."""

import os

from .deployment import load_deployment
from .registry import get_metric, run
from .models import evaluate


class MetricHub:
    """Verify the environment once and lazily validate requested model artifacts.

    No model is downloaded or retained in GPU memory. A worker still verifies
    expected artifact hashes for each call. Recreate this object after intentional
    environment changes. Config overrides are rejected to preserve the lock.
    """

    def __init__(self, deployment=None):
        self.deployment = deployment or os.environ.get("SPEECHMETRICHUB_DEPLOYMENT")
        if not self.deployment:
            raise ValueError("Provide a deployment lock or set SPEECHMETRICHUB_DEPLOYMENT")
        load_deployment(self.deployment, families=[])
        self._configs = {}

    def _config(self, family):
        if family not in self._configs:
            self._configs.update(load_deployment(self.deployment, families=[family]))
        return self._configs[family]

    def run(self, name, **inputs):
        if "config" in inputs:
            raise ValueError("Do not override a locked deployment config")
        family = get_metric(name).get("family")
        if family:
            inputs["config"] = self._config(family)
        return run(name, **inputs)

    def evaluate(self, metrics, **inputs):
        if "configs" in inputs:
            raise ValueError("Do not override locked deployment configs")
        metrics = list(metrics)
        families = {get_metric(name).get("family") for name in metrics} - {None}
        return evaluate(
            metrics, configs={family: self._config(family) for family in families}, **inputs
        )
