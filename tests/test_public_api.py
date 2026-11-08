import json
import subprocess
import sys
import unittest

import speech_eval
import speechmetrichub as smh


class PublicAPITests(unittest.TestCase):
    def test_legacy_alias_is_identical(self):
        for name in ("run", "evaluate", "register", "list_metrics"):
            self.assertIs(getattr(smh, name), getattr(speech_eval, name))

    def test_public_scoring(self):
        result = smh.run("wer", reference="hello world", hypothesis="hello word")
        self.assertEqual(result["value"], 50.0)
        self.assertEqual(result["S"], 1)

    def test_module_cli_is_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "speechmetrichub", "list", "--category", "audio_aesthetics"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(len(json.loads(result.stdout)), 4)

    def test_lightweight_import(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys,speechmetrichub; assert 'torch' not in sys.modules; assert 'meeteval' not in sys.modules",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
