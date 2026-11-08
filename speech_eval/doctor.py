"""Deployment inspection without importing neural models or downloading files."""

from importlib import metadata
from pathlib import Path
import sys
from .registry import list_metrics


def doctor(configs=None, verify_hashes=False):
    configs = configs or {}
    rows = []
    for spec in list_metrics():
        missing = []
        packages = {}
        for requirement in spec.get("dependencies", []):
            name = requirement.split()[0].split("=")[0].split(">")[0].split("<")[0].split("[")[0]
            try:
                packages[name] = metadata.version(name)
            except metadata.PackageNotFoundError:
                missing.append(name)
        family = spec.get("family")
        runtime = None
        if family and family.startswith("aecmos_"):
            installed = {}
            for name in ("onnxruntime", "onnxruntime-gpu"):
                try:
                    installed[name] = metadata.version(name)
                except metadata.PackageNotFoundError:
                    pass
            runtime = {
                "installed": installed,
                "compatible_distribution": len(installed) == 1
                and list(installed.values()) == ["1.16.3"],
                "requirement": "exactly one ONNX Runtime 1.16.3 distribution; CUDA initialization requires inference test",
            }
        config = configs.get(family, {}) if family else {}
        artifacts = {}
        for key in (
            "checkpoint",
            "source_dir",
            "source_file",
            "model_dir",
            "config_file",
            "ssl_checkpoint",
            "primary_model",
            "p808_model",
            "binary",
        ):
            if config.get(key):
                path = Path(config[key]).expanduser()
                artifacts[key] = {"exists": path.exists(), "path": str(path)}
                if verify_hashes and path.exists():
                    from .model_worker import artifact

                    actual = artifact(path)["sha256"]
                    artifacts[key]["sha256"] = actual
                    expected = config.get("expected_hashes", {}).get(key)
                    artifacts[key]["matches_expected"] = (
                        None if expected is None else actual == expected
                    )
        configured = family is None or bool(config)
        rows.append(
            {
                "metric": spec["id"],
                "family": family,
                "dependencies": packages,
                "missing_dependencies": missing,
                "configured": configured,
                "artifacts": artifacts,
                "runtime_validation": spec.get("validation", {}),
                "runtime_inspection": runtime,
                "note": "Inspection only; run validation on this machine to establish runtime support",
            }
        )
    return {"python": sys.version, "executable": sys.executable, "metrics": rows}
