import json
from pathlib import Path
import sys
import tempfile
import unittest
from speech_eval.external import scp_metric


class ExternalTests(unittest.TestCase):
    def test_missing_invalid_and_duplicate_outputs(self):
        # A subprocess fixture exercises the actual process/SCP boundary without a GPU model.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            script = p / "fixture.py"
            script.write_text(
                "import sys\nfrom pathlib import Path\np=Path(sys.argv[1]);p.mkdir()\n(p/'Metric.scp').write_text('a 3.0\\nb nan\\na 4.0\\n')\n"
            )
            result = scp_metric(
                metric="fixture",
                records=[{"id": "a"}, {"id": "b"}, {"id": "c"}],
                work_dir=p / "runs",
                config={
                    "python": sys.executable,
                    "script": str(script),
                    "output_stem": "Metric",
                    "arguments": ["{output_dir}"],
                    "model_provenance": {"revision": "test-fixture-v1"},
                },
            )
            self.assertEqual(result["status"], "incomplete")
            self.assertIsNone(result["value"])
            self.assertEqual(result["duplicates"], ["a"])
            self.assertEqual(len(result["rows"]), 3)
            json.dumps(result, allow_nan=False)

    def test_unpinned_model_rejected(self):
        with self.assertRaises(ValueError):
            scp_metric(
                metric="fixture",
                records=[],
                work_dir="unused",
                config={
                    "python": "python",
                    "script": "none",
                    "output_stem": "x",
                    "arguments": [],
                    "model_provenance": {},
                },
            )

    def test_micro_counts_not_macro_rates(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            script = p / "fixture.py"
            script.write_text(
                "import sys\nfrom pathlib import Path\np=Path(sys.argv[1]);p.mkdir()\n(p/'WhisperWER.scp').write_text('a 1.0\\nb 0.0\\n')\n(p/'counts.csv').write_text('key,status,N,S,D,I\\na,ok,1,1,0,0\\nb,ok,3,0,0,0\\n')\n"
            )
            result = scp_metric(
                metric="whisper_wer",
                records=[{"id": "a"}, {"id": "b"}],
                work_dir=p / "runs",
                config={
                    "python": sys.executable,
                    "script": str(script),
                    "output_stem": "WhisperWER",
                    "counts_csv": "counts.csv",
                    "arguments": ["{output_dir}"],
                    "model_provenance": {"revision": "test-fixture-v1"},
                },
            )
            self.assertEqual(result["value"], 25)
