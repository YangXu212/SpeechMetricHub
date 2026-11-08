"""Dataset-level speaker verification with tie-aware ROC operating points."""

from importlib.metadata import version
import hashlib
import json


def verification_metric(
    *,
    metric,
    scores,
    labels,
    trial_ids=None,
    score_direction="higher_is_target",
    p_target=None,
    c_miss=1.0,
    c_fa=1.0,
    normalized=True,
):
    import numpy as np
    from sklearn.metrics import roc_curve

    protocol = {
        "profile": "speaker-verification-v1",
        "scope": "dataset",
        "score_direction": score_direction,
        "ties": "group_identical_scores",
        "roc": "sklearn.roc_curve(drop_intermediate=False)",
        "decision_rule": ">= threshold"
        if score_direction == "higher_is_target"
        else "<= threshold",
        "sample_weight": "uniform",
        "aggregation": "whole_trial_list",
    }

    def invalid(reason):
        return {
            "metric": metric,
            "status": "invalid_input",
            "value": None,
            "reason": reason,
            "protocol": protocol,
        }

    try:
        x, y = np.asarray(scores, dtype=np.float64), np.asarray(labels)
        if x.ndim != 1 or y.ndim != 1 or len(x) != len(y) or not len(x):
            return invalid("scores and labels must be nonempty equal-length vectors")
        if not np.isfinite(x).all() or not np.isin(y, [0, 1]).all():
            return invalid("Scores must be finite; labels must be numeric 0=nontarget, 1=target")
        if len(np.unique(y)) != 2:
            return invalid("Both target and nontarget trials are required")
        if score_direction not in ("higher_is_target", "lower_is_target"):
            return invalid("Specify higher_is_target or lower_is_target")
        if trial_ids is not None and (
            len(trial_ids) != len(x)
            or not all(isinstance(t, str) and t for t in trial_ids)
            or len(set(trial_ids)) != len(x)
        ):
            return invalid("trial_ids must be unique nonempty strings, one per score")
        if metric == "min_dcf":
            params = (p_target, c_miss, c_fa)
            if any(
                isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v)
                for v in params
            ):
                return invalid("Explicit finite p_target and positive costs are required")
            if not 0 < p_target < 1 or c_miss <= 0 or c_fa <= 0 or not isinstance(normalized, bool):
                return invalid("Require 0<p_target<1, positive costs, and boolean normalized")
            protocol.update(p_target=p_target, c_miss=c_miss, c_fa=c_fa, normalized=normalized)
        signed = x if score_direction == "higher_is_target" else -x
        fpr, tpr, thresholds = roc_curve(y, signed, pos_label=1, drop_intermediate=False)
        fnr = 1 - tpr
        actual_thresholds = thresholds if score_direction == "higher_is_target" else -thresholds

        def threshold(i):
            return float(actual_thresholds[i]) if np.isfinite(actual_thresholds[i]) else None

        details = {
            "n_trials": len(x),
            "n_target": int(np.sum(y == 1)),
            "n_nontarget": int(np.sum(y == 0)),
        }
        if metric == "eer":
            delta = fpr - fnr
            right = int(np.flatnonzero(delta >= 0)[0])
            if delta[right] == 0:
                value = float(fpr[right])
                details.update(threshold=threshold(right), interpolated=False)
            else:
                left = right - 1
                weight = float(-delta[left] / (delta[right] - delta[left]))
                value = float(fpr[left] + weight * (fpr[right] - fpr[left]))
                details.update(
                    threshold=None,
                    interpolated=True,
                    threshold_bracket=[threshold(left), threshold(right)],
                    interpolation_weight=weight,
                )
            protocol["eer_convention"] = (
                "linear ROC crossing of FPR=FNR; no fabricated deterministic threshold"
            )
            value *= 100
            unit = "percent"
        elif metric == "min_dcf":
            costs = c_miss * p_target * fnr + c_fa * (1 - p_target) * fpr
            index = int(np.argmin(costs))
            raw = float(costs[index])
            default = min(c_miss * p_target, c_fa * (1 - p_target))
            value = raw / default if normalized else raw
            unit = "normalized_cost" if normalized else "cost"
            details.update(
                raw_min_dcf=raw,
                normalized_min_dcf=raw / default,
                normalization_constant=default,
                threshold=threshold(index),
                decision="reject_all" if index == 0 else "score_threshold",
                p_miss=float(fnr[index]),
                p_false_alarm=float(fpr[index]),
            )
            protocol["minimum_tie_break"] = "first ROC point; most restrictive acceptance threshold"
        else:
            return invalid("Unknown verification metric")
        signature = json.dumps(
            {"scores": x.tolist(), "labels": y.astype(int).tolist(), "trial_ids": trial_ids},
            sort_keys=True,
        ).encode()
        return {
            "metric": metric,
            "status": "ok",
            "value": float(value),
            "value_unit": unit,
            "direction": "lower_is_better",
            "protocol": protocol,
            "details": details,
            "input_sha256": hashlib.sha256(signature).hexdigest(),
            "backend": {"scikit-learn": version("scikit-learn"), "numpy": version("numpy")},
        }
    except (ValueError, TypeError, OverflowError) as exc:
        return invalid(str(exc))
