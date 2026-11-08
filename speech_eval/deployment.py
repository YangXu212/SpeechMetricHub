"""Local deployment locks: artifacts, interpreter, distribution versions and library source.

Locks are integrity/reproducibility manifests, not a substitute for inference validation.
Create one inside each dedicated worker environment; alternate interpreters are rejected.
"""

import copy
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import site
import sys
import sysconfig

ARTIFACT_KEYS = (
    "checkpoint",
    "source_dir",
    "source_file",
    "model_dir",
    "config_file",
    "ssl_checkpoint",
    "primary_model",
    "p808_model",
    "binary",
)


def environment():
    from . import __version__

    root = Path(__file__).parent.parent
    sources = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for package in ("speech_eval", "speechmetrichub")
        for p in sorted((root / package).iterdir())
        if p.suffix in (".py", ".json")
    }
    # Importing setuptools/librosa may append vendored dependency directories to
    # sys.path. Those are not independently installed distributions and must not
    # make a lock depend on the order in which callers import optional scorers.
    package_paths = {sysconfig.get_path("purelib"), sysconfig.get_path("platlib")}
    if site.ENABLE_USER_SITE:
        package_paths.add(site.getusersitepackages())
    packages = {
        d.metadata["Name"].lower().replace("_", "-"): d.version
        for d in metadata.distributions(path=sorted(package_paths))
        if d.metadata["Name"]
    }
    return {
        "speechmetrichub": __version__,
        "python": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
        "packages": packages,
        "library_sha256": hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest(),
    }


def create_deployment(configs):
    from .model_worker import artifact
    from .registry import list_metrics

    known = {m.get("family") for m in list_metrics() if m.get("family")}
    if not isinstance(configs, dict):
        raise ValueError("configs must map model families to deployment settings")
    result = copy.deepcopy(configs)
    for family, config in result.items():
        if family not in known or not isinstance(config, dict):
            raise ValueError(f"Unknown family or invalid config: {family}")
        if (
            config.get("python")
            and Path(config["python"]).absolute() != Path(sys.executable).absolute()
        ):
            raise ValueError("Create and use a lock inside its worker interpreter")
        hashes = {}
        for key in ARTIFACT_KEYS:
            if config.get(key):
                item = artifact(config[key])
                config[key], hashes[key] = item["path"], item["sha256"]
        if not hashes:
            raise ValueError(f"No local artifacts configured for {family}")
        for key, expected in config.get("expected_hashes", {}).items():
            if hashes.get(key) != expected:
                raise ValueError(f"Artifact hash mismatch: {family}/{key}")
        config["expected_hashes"] = hashes
    env = environment()
    if "onnxruntime" in env["packages"] and "onnxruntime-gpu" in env["packages"]:
        raise ValueError("Install only one ONNX Runtime distribution in a worker environment")
    return {"schema": "speechmetrichub-deployment-v1", "environment": env, "configs": result}


def verify_deployment(manifest, *, families=None):
    if isinstance(manifest, (str, Path)):
        manifest = json.loads(Path(manifest).read_text(encoding="utf-8"))
    failures = []
    verified_families = []
    try:
        if not isinstance(manifest, dict) or not isinstance(manifest.get("environment"), dict):
            raise ValueError("Deployment manifest and environment must be JSON objects")
        if manifest.get("schema") != "speechmetrichub-deployment-v1":
            raise ValueError("Unsupported deployment schema")
        if not isinstance(manifest.get("configs"), dict):
            raise ValueError("Deployment configs must be a JSON object")
        if families is not None:
            families = list(families)
            missing = set(families) - set(manifest["configs"])
            if missing:
                raise ValueError(f"Families not configured in deployment: {sorted(missing)}")
            manifest = {
                **manifest,
                "configs": {name: manifest["configs"][name] for name in families},
            }
        current = create_deployment(manifest["configs"])
        verified_families = sorted(current["configs"])
        expected = manifest["environment"]
        for key in ("speechmetrichub", "python", "system", "machine", "library_sha256"):
            if expected.get(key) != current["environment"][key]:
                failures.append(f"Environment mismatch: {key}")
        # Extra packages also change dependency resolution and must trigger a new lock.
        if expected.get("packages") != current["environment"]["packages"]:
            failures.append("Installed distribution versions differ from lock")
        if current["configs"] != manifest["configs"]:
            failures.append("Artifact paths or hash coverage differ from lock")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        failures.append(str(exc))
    return {
        "status": "ok" if not failures else "deployment_mismatch",
        "failures": failures,
        "scope": "artifact and environment integrity; runtime scoring must be validated separately",
        "verified_families": verified_families,
    }


def load_deployment(path, *, families=None):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    checked = verify_deployment(manifest, families=families)
    if checked["status"] != "ok":
        raise ValueError("Deployment verification failed: " + "; ".join(checked["failures"]))
    return copy.deepcopy(
        {
            name: config
            for name, config in manifest["configs"].items()
            if families is None or name in families
        }
    )
