"""Clip-local speaker cardinality, independent of text alignment/permutation."""

from .transcription import tokenize


def _labels(segments):
    labels = set()
    missing = 0
    for segment in segments or []:
        if not tokenize(segment.get("text", ""), "char"):
            continue
        label = segment.get("speaker")
        if label is None or not str(label).strip():
            missing += 1
        else:
            labels.add(str(label))
    return sorted(labels), missing


def evaluate_speaker_count(reference, hypothesis, *, has_reference=True, boundary_note=""):
    refs, ref_missing = _labels(reference)
    hyps, hyp_missing = _labels(hypothesis)
    ref_count = len(refs) if has_reference and not ref_missing else None
    hyp_count = len(hyps) if not hyp_missing else None
    available = has_reference and not ref_missing and not hyp_missing
    delta = hyp_count - ref_count if available else None
    status = (
        ("equal" if delta == 0 else "under" if delta < 0 else "over")
        if available
        else "unavailable"
    )
    reasons = []
    if not has_reference:
        reasons.append("没有参考标注，不能判断人数是否正确。")
    if ref_missing:
        reasons.append(f"参考有 {ref_missing} 个非空转写分段缺少说话人标签。")
    if hyp_missing:
        reasons.append(f"模型有 {hyp_missing} 个非空转写分段缺少说话人标签。")
    if boundary_note:
        reasons.append(
            "参考未覆盖切片边界残句，人数仅相对于现有标注，不保证覆盖所有可听见的说话人。"
        )
    return {
        "version": "speaker-count-v1",
        "available": bool(available),
        "status": status,
        "reference_count": ref_count,
        "hypothesis_count": hyp_count,
        "signed_error": delta,
        "absolute_error": abs(delta) if available else None,
        "correct": delta == 0 if available else None,
        "reference_is_multi_speaker": ref_count >= 2 if ref_count is not None else None,
        "reference_labels": refs if has_reference else [],
        "hypothesis_labels": hyps,
        "reference_missing_labels": ref_missing if has_reference else 0,
        "hypothesis_missing_labels": hyp_missing,
        "reference_boundary_incomplete": bool(boundary_note) if has_reference else None,
        "warnings": reasons,
        "scope": "当前片段中，归一化后含有效文字的不同说话人标签数；不计空白/纯标点分段，不是整段源录音人数。",
        "interpretation": "编号改名不影响人数；人数一致不代表身份、说话人归属或时间正确。少估/多估描述数量差，不直接断言漏检/合并/拆分原因。",
    }
