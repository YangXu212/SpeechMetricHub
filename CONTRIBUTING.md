# Contributing

An integration is complete only after a real upstream invocation succeeds. A registry row or subprocess mock is not runtime validation.

1. Add a lazy adapter. Reuse the original scorer; do not silently replace it with a similarly named approximation.
2. Add explicit registry metadata: measurement category, reference conditions, task tags, score direction, unit, canonical source and optional dependencies.
3. Define preprocessing, reference selection, empty/silent behavior, alignment, aggregation and all model variants/heads. Descriptive quantities need not have a better/worse direction.
4. Validate a real recording, directly compare with upstream where feasible, and test invalid input and at least one semantic property. Save versions, input and artifact hashes, platform, numerical tolerance and result.
5. Extend `validation/summary.json` and the metric cards. Distinguish runtime validation from dependency inspection. Do not mark untested devices or platforms as supported.
6. Run `python -m unittest discover -s tests -v` and build/install the wheel. Model integration tests need local licensed weights; ordinary CI tests the standard scorers and contracts.

Keep source and model artifacts outside the wheel. Configuration must not embed a developer's home directory. New official scorer versions or preprocessing changes require a new profile and a comparison report. Do not update an established research profile in place.
