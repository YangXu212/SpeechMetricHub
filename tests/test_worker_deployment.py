"""A tiny real venv checks cross-interpreter locks without model dependencies."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import venv

from speech_eval.deployment import (
    create_deployment,
    validate_worker_deployment,
    verify_deployment,
)


class WorkerDeploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storage = tempfile.TemporaryDirectory(prefix="smh_test_worker_")
        cls.root = Path(cls.storage.name)
        venv.EnvBuilder(with_pip=False).create(cls.root / "worker")
        cls.python = (
            cls.root / "worker" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        )
        cls.source = cls.root / "source.py"
        cls.source.write_text("# public source fixture\n", encoding="utf-8")
        cls.tokenizer = cls.root / "tokenizer.json"
        cls.tokenizer.write_text('{"fixture": true}', encoding="utf-8")
        cls.family = "aecmos_16k"
        cls.inner_config = {
            "source_file": str(cls.source),
            "tokenizer_file": str(cls.tokenizer),
            "device": "cpu",
            "threads": 2,
        }
        cls.env = {"PYTHONPATH": str(Path(__file__).resolve().parents[1])}

    @classmethod
    def tearDownClass(cls):
        cls.storage.cleanup()

    def setUp(self):
        self.env_patch = patch.dict(os.environ, self.env)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.lock_path = self.root / "deployment.json"
        script = (
            "import json,sys; from pathlib import Path; "
            "from speech_eval.deployment import create_deployment; "
            "lock=create_deployment(json.loads(sys.argv[1])); "
            "Path(sys.argv[2]).write_text(json.dumps(lock))"
        )
        subprocess.run(
            [
                str(self.python),
                "-c",
                script,
                json.dumps({self.family: self.inner_config}),
                str(self.lock_path),
            ],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.config = {
            **self.inner_config,
            "python": str(self.python),
            "worker_deployment": str(self.lock_path),
        }

    def test_real_alternate_interpreter_and_artifact_coverage(self):
        self.assertNotEqual(Path(sys.executable).absolute(), self.python.absolute())
        lock = create_deployment({self.family: self.config})
        hashes = lock["configs"][self.family]["expected_hashes"]
        self.assertEqual(set(hashes), {"source_file", "tokenizer_file", "worker_deployment"})
        self.assertEqual(verify_deployment(lock)["status"], "ok")

    def test_alternate_interpreter_requires_own_lock(self):
        config = {k: v for k, v in self.config.items() if k != "worker_deployment"}
        with self.assertRaisesRegex(ValueError, "requires worker_deployment"):
            create_deployment({self.family: config})

    def test_effective_configuration_cannot_drift(self):
        config = {**self.config, "threads": 4}
        with self.assertRaisesRegex(ValueError, "configuration differs"):
            create_deployment({self.family: config})

    def test_worker_environment_is_verified_inside_worker(self):
        inner = json.loads(self.lock_path.read_text())
        inner["environment"]["python"] = "0.0.0"
        self.lock_path.write_text(json.dumps(inner))
        with self.assertRaisesRegex(ValueError, "Worker deployment mismatch"):
            create_deployment({self.family: self.config})

    def test_tampered_manifest_invalidates_parent_lock(self):
        lock = create_deployment({self.family: self.config})
        self.lock_path.write_text(self.lock_path.read_text() + "\n")
        report = verify_deployment(lock)
        self.assertEqual(report["status"], "deployment_mismatch")
        self.assertTrue(any("worker_deployment" in reason for reason in report["failures"]))

    def test_nested_routing_is_rejected_before_process_execution(self):
        inner = json.loads(self.lock_path.read_text())
        inner["configs"][self.family]["worker_deployment"] = str(self.lock_path)
        self.lock_path.write_text(json.dumps(inner))
        with self.assertRaisesRegex(ValueError, "Nested"):
            create_deployment({self.family: self.config})

    def test_missing_family_is_rejected(self):
        inner = json.loads(self.lock_path.read_text())
        inner["configs"] = {}
        self.lock_path.write_text(json.dumps(inner))
        with self.assertRaisesRegex(ValueError, "does not configure family"):
            create_deployment({self.family: self.config})

    def test_process_timeout_and_bad_payload_are_explicit(self):
        with patch(
            "speech_eval.deployment.subprocess.run",
            side_effect=subprocess.TimeoutExpired("worker", 1),
        ):
            with self.assertRaisesRegex(ValueError, "exceeded"):
                validate_worker_deployment(self.config, self.family, timeout=1)
        with patch(
            "speech_eval.deployment.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, "not json", ""),
        ):
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                validate_worker_deployment(self.config, self.family)

    def test_same_interpreter_does_not_accept_worker_wrapper(self):
        config = copy.deepcopy(self.config)
        config["python"] = sys.executable
        with self.assertRaisesRegex(ValueError, "only for an alternate"):
            create_deployment({self.family: config})

    def test_system_site_worker_includes_base_and_prefers_overlay(self):
        shared = self.root / "shared_worker"
        venv.EnvBuilder(with_pip=False, system_site_packages=True).create(shared)
        python = shared / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        script = """
import json, site, sys, sysconfig
from importlib import metadata
from pathlib import Path
from speech_eval.deployment import environment
base_paths = [p for p in site.getsitepackages()
              if not Path(p).resolve().is_relative_to(Path(sys.prefix).resolve())]
base = {}
for d in metadata.distributions(path=base_paths):
    if d.metadata['Name']:
        base.setdefault(d.metadata['Name'].lower().replace('_', '-'), d.version)
before = environment()['packages']
missing = sorted(set(base) - set(before))
if base:
    name = sorted(base)[0]
    folder = Path(sysconfig.get_path('purelib')) / (name.replace('-', '_') + '-999.0.0.dist-info')
    folder.mkdir()
    (folder / 'METADATA').write_text('Metadata-Version: 2.1\\nName: ' + name + '\\nVersion: 999.0.0\\n')
    after = environment()['packages']
    overlay = after.get(name)
else:
    overlay = None
print(json.dumps({'base_count': len(base), 'missing': missing, 'overlay': overlay}))
"""
        result = subprocess.run(
            [str(python), "-c", script],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        report = json.loads(result.stdout)
        if not report["base_count"]:
            self.skipTest("Base interpreter has no installed distributions to inherit")
        self.assertEqual(report["missing"], [])
        self.assertEqual(report["overlay"], "999.0.0")


if __name__ == "__main__":
    unittest.main()
