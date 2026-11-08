import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from speechmetrichub import MetricHub, create_deployment, verify_deployment


class HubTests(unittest.TestCase):
    def test_pinned_profile_satisfies_cpu_extras(self):
        # Catch drift between package extras and the deployable full profile.
        from packaging.requirements import Requirement

        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib

        root = Path(__file__).resolve().parents[1]
        pins = {}
        for line in (root / "requirements.txt").read_text().splitlines():
            if not line.strip() or line.startswith(("#", "--")):
                continue
            requirement = Requirement(line)
            pins[requirement.name.lower().replace("_", "-")] = next(
                iter(requirement.specifier)
            ).version
        project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
        for extra, requirements in project["optional-dependencies"].items():
            if extra in ("aecmos-gpu", "cuda11-libs"):
                continue
            for text in requirements:
                requirement = Requirement(text)
                if requirement.marker and not requirement.marker.evaluate(
                    {"python_version": "3.10", "sys_platform": "linux"}
                ):
                    continue
                name = requirement.name.lower().replace("_", "-")
                self.assertIn(name, pins, (extra, text))
                self.assertIn(pins[name], requirement.specifier, (extra, text, pins[name]))

    def test_scoped_integrity_and_missing_family(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.py"
            source.write_text("# fixture\n")
            lock = create_deployment({"aecmos_16k": {"source_file": str(source)}})
            source.write_text("# tampered\n")
            self.assertEqual(verify_deployment(lock)["status"], "deployment_mismatch")
            self.assertEqual(verify_deployment(lock, families=[])["status"], "ok")
            self.assertEqual(
                verify_deployment(lock, families=["aecmos_16k"])["status"], "deployment_mismatch"
            )
            self.assertEqual(
                verify_deployment(lock, families=["nisqa"])["status"], "deployment_mismatch"
            )
            changed = copy.deepcopy(lock)
            changed["environment"]["packages"]["unexpected-package"] = "1"
            self.assertEqual(
                verify_deployment(changed, families=[])["status"], "deployment_mismatch"
            )
            lock["configs"] = None
            self.assertEqual(verify_deployment(lock)["status"], "deployment_mismatch")

    def test_hub_and_environment_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            lock = Path(folder) / "deployment.json"
            lock.write_text(json.dumps(create_deployment({})))
            hub = MetricHub(lock)
            self.assertEqual(hub.run("wer", reference="a b", hypothesis="a")["value"], 50)
            self.assertEqual(
                hub.evaluate(["wer"], reference="a b", hypothesis="a")["wer"]["value"], 50
            )
            with self.assertRaises(ValueError):
                hub.run("wer", config={})
            with self.assertRaises(ValueError):
                hub.evaluate(["wer"], configs={})
            with self.assertRaises(ValueError):
                hub.run("nisqa", hypothesis="not-used.wav")
            request = Path(folder) / "request.json"
            request.write_text(json.dumps({"reference": "a b", "hypothesis": "a"}))
            env = {**os.environ, "SPEECHMETRICHUB_DEPLOYMENT": str(lock)}
            command = [
                sys.executable,
                "-m",
                "speechmetrichub",
                "run",
                "wer",
                "--input",
                str(request),
            ]
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["value"], 50)
            request.write_text(json.dumps({"reference": "a", "hypothesis": "a", "config": {}}))
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("override", json.loads(result.stdout)["reason"])
