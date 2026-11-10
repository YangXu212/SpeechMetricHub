"""Compare paired audio using an explicitly selected pitch/voicing profile.

Example: python examples/pitch.py reference.wav reconstruction.wav --profile strict
"""

import argparse
import json

from speechmetrichub import evaluate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference")
    parser.add_argument("hypothesis")
    parser.add_argument("--profile", choices=("strict", "amphion", "espnet"), default="strict")
    parser.add_argument("--sample-rate", type=int, default=None)
    args = parser.parse_args()
    metrics = {
        "strict": ["vuv_f1", "f0_rmse"],
        "amphion": ["vuv_f1_amphion", "f0_rmse_amphion"],
        "espnet": ["log_f0_rmse_espnet"],
    }[args.profile]
    inputs = {"reference": args.reference, "hypothesis": args.hypothesis}
    if args.sample_rate is not None:
        inputs["sample_rate"] = args.sample_rate
    if args.profile == "amphion":
        inputs["method"] = "cut"
    results = evaluate(metrics, **inputs)
    print(json.dumps(results, indent=2, allow_nan=False))
    if any(result["status"] != "ok" for result in results.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
