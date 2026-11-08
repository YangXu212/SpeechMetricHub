import argparse
import json
from pathlib import Path
from .registry import list_metrics, run


def execute():
    p = argparse.ArgumentParser(
        description="Speech evaluation registry and optional scorer adapters"
    )
    sub = p.add_subparsers(dest="command", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--domain", "--task", dest="domain")
    ls.add_argument("--category")
    ls.add_argument("--reference-kind")
    check = sub.add_parser("doctor")
    check.add_argument("--config")
    check.add_argument("--verify-hashes", action="store_true")
    multi = sub.add_parser("evaluate")
    multi.add_argument("--input", required=True)
    multi.add_argument("--output")
    calc = sub.add_parser("run")
    calc.add_argument("metric")
    calc.add_argument("--input", required=True)
    calc.add_argument("--output")
    batch = sub.add_parser("batch")
    batch.add_argument("metric")
    batch.add_argument("--input", required=True)
    batch.add_argument("--output")
    for command in (calc, multi, batch):
        command.add_argument("--deployment", help="Verify and load a locked deployment manifest")
    lock = sub.add_parser("lock")
    lock.add_argument("--config", required=True)
    lock.add_argument("--output", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--deployment", required=True)
    verify.add_argument("--output")
    args = p.parse_args()
    payload = None
    if args.command in ("run", "evaluate", "batch"):
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if args.deployment:
            from .deployment import load_deployment
            from .registry import get_metric

            configs = load_deployment(args.deployment)
            if args.command == "evaluate":
                if "configs" in payload:
                    raise ValueError("Do not override locked configs in request data")
                for name in payload["metrics"]:
                    family = get_metric(name).get("family")
                    if family and family not in configs:
                        raise ValueError(f"Family not configured in deployment: {family}")
                payload["configs"] = configs
            else:
                family = get_metric(args.metric).get("family")
                if "config" in payload or (
                    args.command == "batch"
                    and any("config" in r["inputs"] for r in payload["records"])
                ):
                    raise ValueError("Do not override locked config in request data")
                if family:
                    if family not in configs:
                        raise ValueError(f"Family not configured in deployment: {family}")
                    payload["config"] = configs[family]
    if args.command == "list":
        result = list_metrics(
            args.domain, category=args.category, reference_kind=args.reference_kind
        )
    elif args.command == "doctor":
        from .doctor import doctor

        result = doctor(
            json.loads(Path(args.config).read_text(encoding="utf-8")) if args.config else None,
            args.verify_hashes,
        )
    elif args.command == "lock":
        from .deployment import create_deployment

        result = create_deployment(json.loads(Path(args.config).read_text(encoding="utf-8")))
    elif args.command == "verify":
        from .deployment import verify_deployment

        result = verify_deployment(args.deployment)
    elif args.command == "evaluate":
        from .models import evaluate

        result = evaluate(**payload)
    elif args.command == "batch":
        from .batch import evaluate_batch

        result = evaluate_batch(args.metric, **payload)
    else:
        result = run(args.metric, **payload)
    body = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if getattr(args, "output", None):
        Path(args.output).write_text(body, encoding="utf-8")
    else:
        print(body)
    if args.command == "run":
        return 0 if result.get("status") == "ok" else 2
    if args.command == "batch":
        return 0 if result.get("complete") and result.get("value") is not None else 2
    if args.command == "evaluate":
        return 0 if all(v.get("status") == "ok" for v in result.values()) else 2
    if args.command == "verify":
        return 0 if result.get("status") == "ok" else 2
    return 0


def main():
    try:
        return execute()
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(
            json.dumps(
                {"status": "invalid_request", "value": None, "reason": str(exc)},
                ensure_ascii=False,
                allow_nan=False,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
