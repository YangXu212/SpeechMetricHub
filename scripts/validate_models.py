"""Repeat real model interface validation against explicitly supplied local audio.

Example: python scripts/validate_models.py --config deployment.local.json
  --hypothesis noisy.wav --reference clean.wav --nonmatching-reference other.wav
  --reference-text "the ground truth" --output model-validation.json
"""

import argparse
import json
from pathlib import Path

from speech_eval import evaluate, list_metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in (
        "config",
        "hypothesis",
        "reference",
        "nonmatching-reference",
        "reference-text",
        "output",
    ):
        parser.add_argument("--" + arg, required=True)
    parser.add_argument("--families", nargs="+")
    args = parser.parse_args()
    configs = json.loads(Path(args.config).read_text(encoding="utf-8"))
    families = {}
    for spec in list_metrics():
        if spec.get("family") and (not args.families or spec["family"] in args.families):
            families.setdefault(spec["family"], []).append(spec["id"])
    if args.families and set(args.families) - set(families):
        parser.error("Unknown model family")
    rows = {}
    for family, metrics in families.items():
        reference = args.reference_text if family == "whisper_wer" else args.reference
        if (
            family.startswith("scoreq_")
            and configs.get(family, {}).get("reference_kind") == "nonmatching"
        ):
            reference = args.nonmatching_reference
        rows.update(
            evaluate(metrics, hypothesis=args.hypothesis, reference=reference, configs=configs)
        )
        print(family, {m: rows[m]["status"] for m in metrics}, flush=True)
        Path(args.output).write_text(
            json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
        )
    return 0 if rows and all(v["status"] == "ok" for v in rows.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
