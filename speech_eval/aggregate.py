"""Never present a partial subset as a complete benchmark score."""


def aggregate(items, metric):
    items = list(items)
    available = []
    eligible = []
    failures = []
    versions = set()
    for item in items:
        evaluation = item.get("evaluation", {})
        p = evaluation.get("protocol", {})
        import json

        versions.add(json.dumps(p, sort_keys=True, ensure_ascii=False))
        m = evaluation.get("metrics", {}).get(metric)
        if m is not None:
            available.append(m)
        if m is not None and m.get("eligible", False):
            eligible.append(m)
        else:
            failures.append(
                {
                    "name": item.get("name"),
                    "reasons": evaluation.get("warnings") or ["missing metric/cache/reference"],
                }
            )
    if len(versions) > 1:
        raise ValueError("Cannot aggregate different scoring protocols/backends")

    def totals(rows):
        sums = {k: sum(m[k] for m in rows) for k in ["errors", "N", "S", "D", "I"]}
        return {**sums, "rate": 100 * sums["errors"] / sums["N"] if sums["N"] else None}

    complete = bool(items) and not failures
    return {
        "metric": metric,
        "expected": len(items),
        "scored": len(available),
        "eligible": len(eligible),
        "coverage": len(eligible) / len(items) if items else None,
        "complete": complete,
        "complete_set_rate": totals(eligible)["rate"] if complete else None,
        "eligible_subset": totals(eligible),
        "parsed_diagnostic_subset": totals(available),
        "failures": failures,
        "aggregation": "micro: sum(S+D+I)/sum(N); no imputed score for failures",
    }
