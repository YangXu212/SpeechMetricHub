"""Local deployment locks: artifacts, interpreter, distribution versions and library source.

Locks are integrity/reproducibility manifests, not a substitute for inference validation.
Create one inside each dedicated worker environment. An alternate interpreter
requires its own verified deployment lock; the parent also hashes that lock.
"""

import copy
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import site
import subprocess
import sys
import sysconfig
import tempfile

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
    "tokenizer_file",
    "worker_deployment",
)


def _effective_config(config):
    result = {
        key: value
        for key, value in config.items()
        if key not in ("python", "worker_deployment", "expected_hashes")
    }
    for key in ARTIFACT_KEYS:
        if result.get(key):
            result[key] = str(Path(result[key]).resolve(strict=True))
    return result


def validate_worker_deployment(config, family, *, timeout=120):
    """Verify a worker lock inside its actual interpreter, without loading a model.

    PYTHONPATH is inherited deliberately so an explicitly staged source tree can
    be tested before installation. Its source identity is still checked by the
    worker lock. A temporary cwd prevents accidental imports from the caller's
    repository. Nested worker routing is not supported.
    """
    if not config.get("python") or not config.get("worker_deployment"):
        raise ValueError("An alternate interpreter requires python and worker_deployment")
    worker = Path(config["python"]).absolute()
    path = Path(config["worker_deployment"]).resolve(strict=True)
    content = path.read_bytes()
    manifest = json.loads(content)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("configs"), dict):
        raise ValueError("Worker deployment must contain a configs object")
    inner = manifest["configs"].get(family)
    if not isinstance(inner, dict):
        raise ValueError(f"Worker deployment does not configure family: {family}")
    if inner.get("worker_deployment"):
        raise ValueError("Nested worker_deployment routing is not supported")
    if inner.get("python") and Path(inner["python"]).absolute() != worker:
        raise ValueError("Worker lock points to a different interpreter")
    if _effective_config(config) != _effective_config(inner):
        raise ValueError(f"Worker configuration differs from parent: {family}")
    manifest_hash = hashlib.sha256(content).hexdigest()
    expected = config.get("expected_hashes", {}).get("worker_deployment")
    if expected is not None and expected != manifest_hash:
        raise ValueError(f"Artifact hash mismatch: {family}/worker_deployment")
    script = (
        "import hashlib,json,sys; from pathlib import Path; "
        "from speech_eval.deployment import verify_deployment; "
        "raw=Path(sys.argv[1]).read_bytes(); lock=json.loads(raw); "
        "result=verify_deployment(lock,families=[sys.argv[2]]); "
        "print(json.dumps({'verification':result,'interpreter':sys.executable,"
        "'manifest_sha256':hashlib.sha256(raw).hexdigest(),"
        "'config':lock['configs'][sys.argv[2]]}))"
    )
    try:
        with tempfile.TemporaryDirectory(prefix="smh_worker_lock_") as directory:
            process = subprocess.run(
                [str(worker), "-c", script, str(path), family],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"Worker deployment verification exceeded {timeout} seconds") from exc
    except OSError as exc:
        raise ValueError(f"Cannot run worker deployment interpreter: {exc}") from exc
    if process.returncode:
        raise ValueError(
            f"Worker deployment verification exited {process.returncode}: " + process.stderr[-2000:]
        )
    try:
        result = json.loads(process.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Worker deployment returned invalid JSON") from exc
    if not isinstance(result, dict) or not isinstance(result.get("verification"), dict):
        raise ValueError("Worker deployment returned an invalid verification object")
    checked = result["verification"]
    if checked.get("status") != "ok" or family not in checked.get("verified_families", []):
        raise ValueError(f"Worker deployment mismatch: {checked.get('failures', checked)}")
    if Path(result.get("interpreter", "")).absolute() != worker:
        raise ValueError("Worker returned a different interpreter identity")
    if result.get("manifest_sha256") != manifest_hash or result.get("config") != inner:
        raise ValueError("Worker deployment changed during verification")
    return checked


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
    package_paths = {
        sysconfig.get_path("purelib"),
        sysconfig.get_path("platlib"),
        *site.getsitepackages(),
    }
    if site.ENABLE_USER_SITE:
        package_paths.add(site.getusersitepackages())

    # --system-site-packages workers inherit their base environment. Include
    # those declared site directories, while keeping the first distribution
    # on sys.path (the worker overlay) authoritative for duplicate names.
    def normalized(path):
        return os.path.normcase(os.path.abspath(path))

    declared = {normalized(path): path for path in package_paths if path}
    ordered = []
    for path in [*sys.path, *sorted(package_paths)]:
        key = normalized(path)
        if key in declared and key not in ordered:
            ordered.append(key)
    packages = {}
    for path in ordered:
        for distribution in metadata.distributions(path=[declared[path]]):
            name = distribution.metadata["Name"]
            if name:
                packages.setdefault(name.lower().replace("_", "-"), distribution.version)
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
        alternate = (
            config.get("python")
            and Path(config["python"]).absolute() != Path(sys.executable).absolute()
        )
        if alternate and not config.get("worker_deployment"):
            raise ValueError("An alternate interpreter requires worker_deployment")
        if config.get("worker_deployment") and not alternate:
            raise ValueError("worker_deployment is only for an alternate interpreter")
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
        if alternate:
            validate_worker_deployment(config, family)
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
