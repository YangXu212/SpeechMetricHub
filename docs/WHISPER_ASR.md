# Whisper ASR evaluation profiles

SpeechMetricHub exposes three explicit Whisper `large-v3` profile families so
researchers can reproduce published benchmarks without silently altering older
deployment locks.

| Profile family | Metrics | Backend | Long-form (`>30s`) | Normalization & edit counts | Recommended use |
|---|---|---|---|---|---|
| **OpenAI Whisper** | `whisper_wer_en_openai`, `whisper_dwer_en_openai` | `openai-whisper==20250625` (`large-v3.pt`), `beam_size=5`, `hallucination_silence_threshold=2.0` | Native 30s sliding window | `espnet2.text.cleaner.TextCleaner("whisper_en")` + `Levenshtein.opcodes` | **Default choice** for speech enhancement / TSE paper reproduction (matches `calculate_wer_whisper.py` / URGENT / StuPASE evaluation pipelines) |
| **Upgraded HF Whisper** | `whisper_wer_hf_v3`, `whisper_dwer_hf_v3` | Hugging Face `transformers` (`Whisper_large_v3_HF`), `return_timestamps=True`, temperature fallback `(0.0..1.0)`, `condition_on_prev_tokens=False` | Sequential long-form (`truncation=False`, `padding="longest"`) | `WhisperTokenizer.normalize` (with `normalizer.json` spelling map) + `kaldialign` | Primary-environment Transformers alternative without requiring the separate OpenAI Whisper worker |
| **Legacy HF Whisper** | `whisper_wer`, `whisper_dwer` | Hugging Face `transformers`, `float32`, greedy/beam without timestamps or fallback | Rejected (`>30s` raises `ValueError`) | `EnglishTextNormalizer({})` + `nfkc-casefold-v1` + MeetEval | Preserved unchanged for v0.2–v0.9 lock compatibility only; avoid for new benchmarks |

## Why prefer `whisper_wer_en_openai` / `whisper_dwer_en_openai`?

Most speech enhancement, target speaker extraction, and generative speech
benchmarks (including StuPASE and ESPnet-style evaluation suites) invoke
OpenAI's official `whisper` package (`model.transcribe(..., task="transcribe",
language="en", beam_size=5, hallucination_silence_threshold=2.0)` followed by
ESPnet's `TextCleaner("whisper_en")`).

Even when Hugging Face Transformers Whisper is upgraded with
`return_timestamps=True` and temperature fallback (`whisper_*_hf_v3`), small
decoding differences remain between the two engines—especially on reverberant
speech and trailing silence segments. For direct comparability with published
Whisper tables, use **`whisper_wer_en_openai` / `whisper_dwer_en_openai`** (or
for Cohere Transcribe benchmarks, use [`cohere_wer_en_whisper` /
`cohere_dwer_en_whisper`](COHERE_PROFILES.md)).

## Usage

### OpenAI Whisper (`whisper_wer_en_openai` / `whisper_dwer_en_openai`)

```python
from speechmetrichub import run

result = run(
    "whisper_wer_en_openai",
    reference="The complete ground-truth transcript.",
    hypothesis="enhanced.wav",
    config={
        "checkpoint": "/models/openai-whisper/large-v3.pt",
        "python": "/opt/venvs/cohere/bin/python",
        "device": "cuda:0",
        "dtype": "float16",
        "trusted_checkpoint": True,
    },
)
print(result["value"], result["N"], result["S"], result["D"], result["I"])
```

- **CUDA memory optimization**: When `device="cuda:N"` and `dtype="float16"`
  (the CUDA default), weights are cast to `float16` on CPU while keeping
  `whisper.model.LayerNorm` parameters in `float32` before moving to GPU. This
  matches standard `fp16=True` matmuls while cutting peak VRAM from ~6.5 GB to
  ~3.5 GB.
- **CPU execution**: Use `device="cpu"` and `dtype="float32"` (the locked
  deployment default).
- **Audio frontend**: Defaults to `float64_downmix` (`soundfile` float64,
  channel mean, `soxr` HQ to 16 kHz, contiguous float32). On 16 kHz mono PCM16
  WAV files, the resulting float32 samples are bit-for-bit identical to
  `whisper.load_audio` without invoking `ffmpeg`.
- **Environment reuse**: The OpenAI Whisper profiles share the same isolated
  worker environment (`requirements-cohere.txt`, which pins
  `openai-whisper==20250625`, `espnet==202412`, and `Levenshtein==0.27.3`).

### Upgraded HF Whisper (`whisper_wer_hf_v3` / `whisper_dwer_hf_v3`)

```python
from speechmetrichub import run

result = run(
    "whisper_dwer_hf_v3",
    reference="clean.wav",
    hypothesis="enhanced.wav",
    config={
        "model_dir": "/models/Whisper_large_v3_HF",
        "device": "cuda:0",
        "dtype": "float16",
        "trusted_checkpoint": True,
    },
)
print(result["value"], result["details"]["hypothesis_text"])
```

Compared to legacy `whisper_wer` / `whisper_dwer`, the upgraded `hf_v3`
profiles:

1. Enable `return_timestamps=True` and `condition_on_prev_tokens=False` to
   prevent leading-sentence omissions and cross-window error drift.
2. Enable Whisper's standard fallback decoding thresholds
   (`temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)`,
   `compression_ratio_threshold=2.4`, `logprob_threshold=-1.0`,
   `no_speech_threshold=0.6`) to prevent infinite repetition loops on noisy or
   degraded audio.
3. Support recordings longer than 30 seconds (`max_audio_seconds=600.0`) via
   Hugging Face's sequential long-form decoding (`truncation=False`,
   `padding="longest"`).
4. Normalize English text with `WhisperTokenizer.normalize` (loading the full
   British-to-American spelling table from `normalizer.json` rather than an
   empty `{}` mapping) and compute word edit counts with `kaldialign` directly.

## Comparison and caveats

- Both `whisper_*_en_openai` and `whisper_*_hf_v3` emit `scoring_unit="word"`,
  top-level `N/S/D/I/errors`, empty-reference `undefined_reference` counts, and
  `details.reference_fingerprint`, making them directly compatible with
  `evaluate_batch` and `compare_recognition`.
- `whisper_dwer_*` scores agreement against the recognizer's own transcript of
  the clean reference waveform; it is a differential ASR consistency metric, not
  ground-truth WER.
- Never mix legacy `whisper_wer`, `whisper_wer_hf_v3`, and
  `whisper_wer_en_openai` numbers in the same comparison table without stating
  the exact profile ID.
- Real-audio parity and StuPASE benchmark verification are recorded in
  [validation/whisper-unispeech-v0.10.json](../validation/whisper-unispeech-v0.10.json).
