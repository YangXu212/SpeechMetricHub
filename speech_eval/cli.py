import argparse
import json
from pathlib import Path
from .registry import list_metrics, run


def main():
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
    args = p.parse_args()
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
    elif args.command == "evaluate":
        from .models import evaluate

        result = evaluate(**json.loads(Path(args.input).read_text(encoding="utf-8")))
    elif args.command == "batch":
        from .batch import evaluate_batch

        result = evaluate_batch(
            args.metric, **json.loads(Path(args.input).read_text(encoding="utf-8"))
        )
    else:
        result = run(args.metric, **json.loads(Path(args.input).read_text(encoding="utf-8")))
    body = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if getattr(args, "output", None):
        Path(args.output).write_text(body, encoding="utf-8")
    else:
        print(body)
    if args.command == "run":
        return 0 if result.get("status") == "ok" else 2
    if args.command == "batch":
        return 0 if result.get("complete") else 2
    if args.command == "evaluate":
        return 0 if all(v.get("status") == "ok" for v in result.values()) else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
