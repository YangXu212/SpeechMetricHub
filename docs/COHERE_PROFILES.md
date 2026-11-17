# Explicit Cohere recognition profiles

These additive profiles make text normalization and bounded-generation scoring
explicit. The four existing `cohere_wer`, `cohere_cer`, `cohere_dwer` and
`cohere_dcer` defaults remain unchanged; see [their protocol](COHERE_ASR.md).
All error rates are percentages, calculated as `100 * (S + D + I) / N`.

| Metric | Reference | Text processing and units |
|---|---|---|
| `cohere_wer_en_whisper` | English transcript | Whisper English normalization; whitespace words |
| `cohere_dwer_en_whisper` | Clean English audio | Same normalization; words from two ASR transcripts |
| `cohere_cer_zh_basic` | Chinese transcript | Whisper basic normalization; non-whitespace Unicode code points |
| `cohere_dcer_zh_basic` | Clean Chinese audio | Same normalization; characters from two ASR transcripts |

```python
from speechmetrichub import run

result = run(
    "cohere_wer_en_whisper",
    reference="The complete reference transcript.",
    hypothesis="generated.wav",
    config={
        "model_dir": "/opt/models/cohere-transcribe-03-2026",
        "python": "/opt/venvs/cohere/bin/python",
        "device": "cuda:0",
    },
)
print(result["value"], result["N"], result["S"], result["D"], result["I"])
```

The new profiles default to the language in their name, punctuation disabled,
`truncation_policy="score"`, and `audio_frontend="float64_downmix"`.
That frontend reads soundfile float64, averages channels when necessary,
resamples with soxr HQ, then converts to contiguous float32. Native processor
chunking is retained. Beam size 1, a 256-token generation budget per chunk, and
chunk batches of 1 remain configurable operational defaults. The library adds
no task-specific time cuts, short-tail removal, VAD, automatic retry or clipping.
Language, punctuation, generation budget, precision, frontend and normalization
are recorded in the protocol. The requested budget must fit the model's actual
decoder capacity including its prompt; 512 is not a universal architectural cap.

## Normalization and compatibility

The English profile invokes ESPnet's public `TextCleaner("whisper_en")`, which
delegates to OpenAI Whisper's `EnglishTextNormalizer`. It includes English
number, contraction and spelling rules. Counts use `Levenshtein.opcodes`, with
the hypothesis span for insertions and reference spans for other operations.
No second generic normalizer is applied. This reproduces that specific scoring
algorithm and its alignment tie policy. It does not assert equivalence to every
Cohere benchmark or to historical inference batches of eight utterances.
The validation script can compare an explicitly authorized original evaluator
in place, using its actual functions with one utterance per call.

The Chinese profile uses `TextCleaner("whisper_basic")`, delegating to Whisper's
`BasicTextNormalizer`. It applies lowercasing and Unicode/symbol cleanup and
removes bracketed or parenthesized annotations. It does **not** equate Arabic
and Chinese-written numbers, convert traditional/simplified characters, or
segment Chinese words. This is a named basic CER protocol, not a universal
Mandarin scoring standard. Mixed Chinese/English text counts Latin letters
individually here. For comparison, WeNet's `--char=1` tokenizer groups contiguous
ASCII text, so its mixed-language counts need not match this CER.

Normalization versions and source identities matter. The tested worker uses
`openai-whisper==20250625` and `Levenshtein==0.27.3`; complete dependency versions
and public normalizer source hashes are captured by the validator. English
spelling mappings also come from Whisper's packaged `english.json`.

Sources: [ESPnet TextCleaner](https://github.com/espnet/espnet/blob/master/espnet2/text/cleaner.py),
[Whisper English normalizer](https://github.com/openai/whisper/blob/v20250625/whisper/normalizers/english.py),
[Whisper basic normalizer](https://github.com/openai/whisper/blob/v20250625/whisper/normalizers/basic.py),
[Levenshtein opcodes](https://rapidfuzz.github.io/Levenshtein/levenshtein.html#Levenshtein.opcodes),
[WeNet scoring](https://github.com/wenet-e2e/wenet/blob/main/tools/compute-wer.py).

## Truncation and fair comparisons

`truncation_policy="score"` scores the text actually generated when a chunk
reaches its budget without EOS. The result retains a warning, per-chunk decoding
diagnostics and `details.scored_truncated_generation`. Missing reference words
become deletions and repetitions become insertions. A high WER can therefore
represent recognizer instability; it is not silently discarded or capped.
`truncation_policy="reject"` instead returns `generation_truncated` without a
score. Both policies are explicit choices; neither establishes hallucination-free
recognition. Silence and noise are decoded normally.

Choose the policy before comparing systems. Independently excluding each
system's failures changes the evaluated samples and can bias rankings. A low
failure percentage alone cannot establish negligible bias. A common successful
intersection gives a matched **conditional** comparison, but still excludes
difficult cases and can change when another system is added. Report the expected
IDs, scored/excluded IDs, reasons and truncation rates alongside any subset score.
Infrastructure failures remain failures; no arbitrary zero or 100% error is
substituted. Corpus error rates pool counts rather than averaging utterance rates.

For audio-reference dWER/dCER, use the same frozen pseudo-reference transcripts
and normalization for every compared system. Reference token fingerprints must
match per ID; equal denominator lengths alone are insufficient. Changing the
clean-reference generation budget can change that reference and its denominator.
These metrics measure agreement with ASR pseudo-references, not transcription
accuracy against human ground truth. Empty references retain insertion counts
but have no defined per-utterance percentage.

## Comparing systems without hidden exclusions

Compatibility validation covers valid reference transcripts and short
utterances with one utterance per call. Historical batches of eight, or a
different batching of multiple native long-audio chunks, can change BF16
decoding and are not claimed bitwise equivalent. The caller must map unavailable
reference sentinels in its own dataset to explicit failures before scoring.

Use the public result rows from each system and the original intended IDs:

```python
from speechmetrichub import compare_recognition

report = compare_recognition(
    {"system_a": results_a, "system_b": results_b},
    expected_ids=original_recording_ids,
)
```

Each system is a list of `{"id": recording_id, "result": metric_result}` rows,
including failures. Results from `evaluate_batch(...)["rows"]` already have this
shape. Pass explicit expected IDs to detect omissions shared by every system.
Missing rows and unscored failures prevent a full-corpus score. Scored bounded
outputs remain included while their truncation count/rate is reported separately.

The helper checks the same metric, protocol, backend, reference lengths and
per-record reference identity. New Cohere results include normalized token
fingerprints; legacy generic normalized text can also be checked. An explicit
row `reference_id` is supported as a caller assertion, disclosed as such rather
than a verified token comparison. Equal `N` alone does not establish equality.

`common_subset` records its selected/excluded IDs and hash, has
`diagnostic_only=True`, and cannot silently replace the full set. There is no
automatic winner or rank. Empty-reference insertions remain in corpus counts.
The CLI accepts the same JSON arguments:

```bash
speechmetrichub compare-recognition --input comparison.json --output report.json
```

## Reproducing validation

Run in the isolated worker environment with the candidate package importable:

```bash
python scripts/validate_cohere_profiles.py \
  --model-dir /opt/models/cohere-transcribe-03-2026 \
  --manifest /path/to/uncut-real-pairs.json \
  --chinese-audio /path/to/chinese-example.wav \
  --device cuda:0 --limit 2 --output /tmp/cohere-profiles.json
```

The script executes real native inference, compares the English profiles' text
and exact S/D/I counts, exercises all four legacy interfaces, and tests actual
one-token generation with both scoring policies. With Chinese audio it checks
both Chinese interfaces against public upstream normalization and edit counts.
Without a supplied `--chinese-text`, Chinese transcript-reference validation is
explicitly an ASR self-transcript interface check, not an accuracy benchmark.
The audio-reference identity check is likewise a consistency test.
`--reference-script` optionally executes a locally authorized evaluator in place;
it does not copy or publish that evaluator's code. The JSON records coverage,
timings, versions, source hashes, diagnostics and every individual assertion.
For a smaller CPU parity run, combine `--reference-script` with
`--reference-only --limit 1 --device cpu`; the report explicitly records that
legacy, truncation and Chinese runtime cases were skipped in that run.
