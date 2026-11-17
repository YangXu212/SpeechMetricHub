"""Compare recognition results without hiding model-dependent scoring failures.

This module never runs ASR and never chooses a winning system. Pass rows returned
by evaluate_batch, or equivalent {id, result} rows. A common valid subset is an
explicitly conditional diagnostic, not a replacement for the intended corpus.
"""

from collections import Counter
import hashlib
import json


_COUNTS = ("N", "S", "D", "I", "errors")
_ACCEPTED = ("ok", "undefined_reference")


def _json(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def _digest(value):
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _ids(values, name):
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable of IDs, not a single string")
    values = list(values)
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"{name} must contain nonempty string IDs")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate IDs in {name}")
    return values


def _unit(result):
    if result.get("scoring_unit") in ("word", "char"):
        return result["scoring_unit"]
    metric = result.get("metric", "")
    if isinstance(metric, str):
        if metric.endswith("wer"):
            return "word"
        if metric.endswith("cer"):
            return "char"
    unit = result.get("unit")
    return unit if unit in ("word", "char") else None


def _count_result(result):
    details = result.get("details") or {}
    fallback = details.get(_unit(result), details) if isinstance(details, dict) else {}
    if not isinstance(fallback, dict):
        fallback = {}
    counts = {key: result.get(key, fallback.get(key)) for key in _COUNTS}
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in counts.values()):
        raise ValueError("N/S/D/I/errors must be nonnegative integers")
    if counts["errors"] != counts["S"] + counts["D"] + counts["I"]:
        raise ValueError("errors must equal S + D + I")
    if counts["S"] + counts["D"] > counts["N"]:
        raise ValueError("S + D exceeds the reference length")
    if result.get("status") == "undefined_reference" and counts["N"]:
        raise ValueError("undefined_reference requires N = 0")
    return counts


def _truncation(result):
    details = result.get("details") or {}
    flags = {}
    for side in ("reference", "hypothesis"):
        decode = details.get(f"{side}_decode") if isinstance(details, dict) else None
        flags[side] = isinstance(decode, dict) and decode.get("complete") is False
    explicit = result.get("status") == "generation_truncated"
    if isinstance(details, dict):
        explicit = (
            explicit
            or details.get("generation_truncated") is True
            or details.get("scored_truncated_generation") is True
            or details.get("generation_complete") is False
            or details.get("decode_complete") is False
        )
    explicit = (
        explicit
        or result.get("generation_truncated") is True
        or result.get("decode_complete") is False
    )
    flags["any"] = explicit or flags["reference"] or flags["hypothesis"]
    return flags


def _protocol(result):
    protocol, backend = result.get("protocol"), result.get("backend")
    if not isinstance(protocol, dict) or not protocol:
        return None
    # Native text scorers carry their backend inside protocol.
    backend = backend or protocol.get("backend")
    if not isinstance(backend, dict) or not backend or _unit(result) is None:
        return None
    value_unit = result.get("value_unit", "percent")
    if value_unit != "percent":
        return None
    return _json(
        {
            "metric": result.get("metric"),
            "unit": _unit(result),
            "value_unit": value_unit,
            "protocol": protocol,
            "backend": backend,
        }
    )


def _reference(row, unit):
    """Return identity evidence, never infer identity merely from equal lengths."""
    result = row["result"]
    details = result.get("details") or {}
    protocol = result.get("protocol")
    protocol = protocol if isinstance(protocol, dict) else {}
    normalization = protocol.get("normalization")
    normalization = normalization.get("id") if isinstance(normalization, dict) else normalization
    if isinstance(details, dict) and isinstance(details.get("reference_text"), str):
        if normalization == "nfkc-casefold-v1" and unit in ("word", "char"):
            from .transcription import tokenize

            tokens = tokenize(details["reference_text"], unit)
            return ("normalized_reference_tokens", _digest(tokens)), len(tokens)
    if isinstance(details, dict):
        fingerprint = details.get("reference_fingerprint")
        if isinstance(fingerprint, dict):
            fingerprint = fingerprint.get(unit)
        if isinstance(fingerprint, str) and fingerprint:
            return ("supplied_reference_fingerprint", fingerprint), None
    identity = row.get("reference_id")
    if isinstance(identity, str) and identity:
        # An explicit caller assertion (e.g. annotation version + record ID).
        # The report distinguishes it from verified normalized text identity.
        return ("caller_reference_id", identity), None
    return None, None


def _aggregate(ids, usable, *, compatible=True):
    counts = {key: sum(usable[item][key] for item in ids) for key in _COUNTS}
    value = 100 * counts["errors"] / counts["N"] if counts["N"] and compatible else None
    return {
        "counts": counts,
        "value": value,
        "value_unit": "percent",
        "aggregation": "micro_errors_over_reference_units",
    }


def compare_recognition(systems, *, expected_ids=None):
    """Compare full-corpus counts and a disclosed common-subset diagnostic.

    ``systems`` maps system names to iterable ``{id, result}`` rows, including
    failures. Supply the original ``expected_ids`` to detect items omitted from
    every system. Otherwise the union of observed IDs is used only for
    diagnostics: full-corpus values remain null and comparability remains false.
    Unexpected IDs and duplicate IDs are rejected. Missing expected rows remain
    failures. Scored partial generations (status ok) retain their errors; rejected
    generations do not receive invented counts or a fabricated full-corpus score.

    Cross-system comparison requires exactly matching metric, protocol and
    backend metadata, equal per-record reference lengths, and reference identity
    evidence. Known normalized reference text is checked directly. Otherwise use
    ``details.reference_fingerprint`` or an explicit row ``reference_id`` shared
    by systems; the latter is a caller assertion, not a text verification.
    """
    if not isinstance(systems, dict) or not systems:
        raise ValueError("systems must be a nonempty mapping of names to rows")
    indexed = {}
    for name, rows in systems.items():
        if not isinstance(name, str) or not name:
            raise ValueError("System names must be nonempty strings")
        rows = list(rows)
        if any(
            not isinstance(row, dict) or not isinstance(row.get("result"), dict) for row in rows
        ):
            raise ValueError(f"{name}: every row requires an id and result object")
        ids = _ids([row.get("id") for row in rows], f"system {name}")
        indexed[name] = dict(zip(ids, rows))
    observed = set().union(*(set(rows) for rows in indexed.values()))
    explicit = expected_ids is not None
    expected = _ids(expected_ids, "expected_ids") if explicit else sorted(observed)
    unexpected = observed - set(expected)
    if unexpected:
        raise ValueError(f"Rows outside expected_ids: {sorted(unexpected)}")
    reports, usable, fingerprints = {}, {}, {}
    for name, rows in indexed.items():
        valid, protocols, failures, truncated_ids, scored_truncated_ids = {}, set(), [], [], []
        reference_truncated, hypothesis_truncated = [], []
        for item in expected:
            row = rows.get(item)
            if row is None:
                failures.append(
                    {"id": item, "status": "missing_result", "reason": "Expected result is missing"}
                )
                continue
            result = row["result"]
            truncation = _truncation(result)
            if truncation["any"]:
                truncated_ids.append(item)
            if truncation["reference"]:
                reference_truncated.append(item)
            if truncation["hypothesis"]:
                hypothesis_truncated.append(item)
            if result.get("status") not in _ACCEPTED:
                failures.append(
                    {
                        "id": item,
                        "status": str(result.get("status", "missing_status")),
                        "reason": str(
                            result.get("reason") or "Result has no usable recognition counts"
                        ),
                        "reference_truncated": truncation["reference"],
                        "hypothesis_truncated": truncation["hypothesis"],
                    }
                )
                continue
            try:
                counts = _count_result(result)
                fingerprint = _protocol(result)
            except (ValueError, TypeError) as exc:
                failures.append({"id": item, "status": "invalid_result", "reason": str(exc)})
                continue
            valid[item] = counts
            protocols.add(fingerprint)
            if truncation["any"]:
                scored_truncated_ids.append(item)
        protocol_valid = len(protocols) == 1 and None not in protocols
        complete = explicit and bool(expected) and len(valid) == len(expected) and protocol_valid
        subset = _aggregate(list(valid), valid, compatible=protocol_valid)
        reports[name] = {
            "expected": len(expected),
            "present": len(rows),
            "scored": len(valid),
            "counts_complete": bool(expected) and len(valid) == len(expected),
            "expected_corpus_verified": explicit,
            "complete": complete,
            "coverage": len(valid) / len(expected) if expected else None,
            "value": subset["value"] if complete else None,
            "value_unit": "percent",
            "counts": subset["counts"],
            "aggregation": subset["aggregation"],
            "valid_subset_value": subset["value"],
            "valid_subset_diagnostic_only": True,
            "scored_ids": list(valid),
            "failures": failures,
            "failures_by_status": dict(Counter(r["status"] for r in failures)),
            "failures_by_reason": dict(Counter(r["reason"] for r in failures)),
            "truncated": len(truncated_ids),
            "truncation_rate": len(truncated_ids) / len(expected) if expected else None,
            "truncated_ids": truncated_ids,
            "scored_truncated": len(scored_truncated_ids),
            "scored_truncation_rate": len(scored_truncated_ids) / len(expected)
            if expected
            else None,
            "scored_truncated_ids": scored_truncated_ids,
            "reference_truncated_ids": reference_truncated,
            "hypothesis_truncated_ids": hypothesis_truncated,
            "reference_truncation_rate": len(reference_truncated) / len(expected)
            if expected
            else None,
            "hypothesis_truncation_rate": len(hypothesis_truncated) / len(expected)
            if expected
            else None,
            "protocol_consistent": protocol_valid,
            "protocols": [json.loads(p) for p in sorted(p for p in protocols if p is not None)],
        }
        usable[name], fingerprints[name] = valid, protocols
    common = [item for item in expected if all(item in valid for valid in usable.values())]
    all_protocols = set().union(*fingerprints.values())
    protocol_compatible = len(all_protocols) == 1 and None not in all_protocols
    reference_issues, evidence = [], {}
    for item in common:
        identities, lengths, bases = [], [], []
        for name, rows in indexed.items():
            row = rows[item]
            identity, token_count = _reference(row, _unit(row["result"]))
            n = usable[name][item]["N"]
            identities.append(identity)
            lengths.append(n)
            if identity is not None:
                bases.append(identity[0])
            if token_count is not None and token_count != n:
                reference_issues.append(
                    {"id": item, "system": name, "reason": "reference_tokens_disagree_with_N"}
                )
        if len(set(lengths)) != 1:
            reference_issues.append({"id": item, "reason": "reference_lengths_differ"})
        if any(identity is None for identity in identities):
            reference_issues.append({"id": item, "reason": "reference_identity_unverified"})
        elif len(set(identities)) != 1:
            reference_issues.append({"id": item, "reason": "reference_identities_differ"})
        evidence[item] = sorted(set(bases))
    common_comparable = bool(common) and protocol_compatible and not reference_issues
    issues = []
    if not explicit:
        # A shared omission is invisible in the observed union. Do not promote
        # conditional observed-set scores into full-corpus claims.
        corpus_scope = "observed_union; omissions shared by every system cannot be detected"
        issues.append("expected_corpus_unverified")
    else:
        corpus_scope = "explicit_expected_ids"
    if not all(
        report["counts_complete"] and report["protocol_consistent"] for report in reports.values()
    ):
        issues.append("incomplete_full_corpus_or_inconsistent_within_system_protocol")
    if not protocol_compatible:
        issues.append("incompatible_or_unverified_protocols")
    if reference_issues:
        issues.append("reference_identity_or_length_mismatch")
    if not expected:
        issues.append("empty_expected_corpus")
    full_comparable = bool(expected) and not issues and len(common) == len(expected)
    return {
        "expected_ids": expected,
        "expected_ids_sha256": _digest(expected),
        "expected_corpus_verified": explicit,
        "corpus_scope": corpus_scope,
        "systems": reports,
        "full_corpus_comparable": full_comparable,
        "comparability_issues": issues,
        "protocol_compatible": protocol_compatible,
        "reference_issues": reference_issues,
        "reference_identity_evidence": evidence,
        "common_subset": {
            "diagnostic_only": True,
            "selection": "intersection of usable counts; conditional on all systems being scoreable",
            "comparable_within_subset": common_comparable,
            "ids": common,
            "ids_sha256": _digest(common),
            "count": len(common),
            "excluded_ids": [item for item in expected if item not in common],
            "coverage": len(common) / len(expected) if expected else None,
            "systems": {
                name: _aggregate(common, valid, compatible=common_comparable)
                for name, valid in usable.items()
            },
        },
        "ranking": None,
    }
