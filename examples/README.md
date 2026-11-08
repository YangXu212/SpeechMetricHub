# Examples

From an installed checkout:

```bash
speechmetrichub run tcpwer --input examples/tcpwer.json --output result.json
speechmetrichub batch ts_wer --input examples/batch_ts_asr.json --output report.json
```

These text-only examples do not need model weights. For models:

1. Copy `deployment.example.json` to a private `deployment.local.json`.
2. Fill only the families you need with local official artifacts and their hashes.
3. Inspect with `speechmetrichub doctor --config deployment.local.json --verify-hashes`.
4. Adapt `model_evaluation.json` to your audio and configuration, then run `speechmetrichub evaluate --input ...`.

The paths in model examples are placeholders, not downloadable assets or an indication that models are installed. The public repository contains no audio datasets or pretrained checkpoints.

`scripts/validate_models.py --help` describes the real-model validation entry point. It accepts clean and nonmatching references separately, as well as reference text for Whisper WER.
