"""Keep legacy IPA-character and phone-token edit units explicit."""


def compare_decoded(reference, hypothesis):
    import kaldialign

    a, b = reference.replace(" ", ""), hypothesis.replace(" ", "")
    ref_phones, hyp_phones = reference.split(), hypothesis.split()
    if not a or not ref_phones:
        raise ValueError("Empty reference phoneme prediction")
    counts = kaldialign.edit_distance(list(a), list(b))
    phone_counts = kaldialign.edit_distance(ref_phones, hyp_phones)
    values = {
        "similarity": 1 - counts["total"] / len(a),
        "phone_similarity": 1 - phone_counts["total"] / len(ref_phones),
    }
    details = {
        "reference_ipa": a,
        "hypothesis_ipa": b,
        "counts": counts,
        "reference_phones": ref_phones,
        "hypothesis_phones": hyp_phones,
        "phone_counts": phone_counts,
    }
    return values, details
