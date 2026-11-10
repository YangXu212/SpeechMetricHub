# Upstream implementations and artifacts

This library does not create a universal benchmark standard. It integrates existing implementations and records the exact local evaluation protocol. Dataset/challenge rules still determine normalization, scoring regions, reference quality and aggregation.

| Implementation | Role | Upstream |
|---|---|---|
| MeetEval | WER/CER, speaker-permutation and time-constrained/multistream errors | https://github.com/fgnt/meeteval |
| kaldialign | Alignment display and IPA character edit distance | https://github.com/csukuangfj/kaldialign |
| pyannote.metrics | Diarization and speech activity | https://github.com/pyannote/pyannote-metrics |
| fast-bss-eval | SI-SDR and BSS SDR/SIR/SAR | https://github.com/fakufaku/fast_bss_eval |
| PESQ, pystoi | Perceptual quality / intelligibility | https://github.com/ludlows/PESQ ; https://github.com/mpariente/pystoi |
| ViSQOL | Speech and general audio quality | https://github.com/google/visqol |
| Audiobox Aesthetics | CE, CU, PC, PQ | https://github.com/facebookresearch/audiobox-aesthetics |
| SCOREQ | Natural/synthetic, reference/no-reference | https://github.com/alessandroragano/scoreq |
| DNSMOS | SIG, BAK, OVRL, P808_MOS and raw heads | https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS |
| NISQA | Overall/noisiness/discontinuity/coloration/loudness | https://github.com/gabrielmittag/NISQA |
| SpeechMOS | UTMOS22 strong converted model | https://github.com/tarepan/SpeechMOS |
| SHEET | Configurable SSL-MOS inference | https://github.com/unilight/sheet |
| DiscreteSpeechMetrics | SpeechBERTScore precision/recall/F1 | https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics |
| ESPnet RawNet3 | Speaker embedding cosine | https://huggingface.co/espnet/voxcelebs12_rawnet3 |
| Transformers | Whisper and phoneme recognizer execution | https://github.com/huggingface/transformers |

Model weights, upstream source and executables are not redistributed in this wheel. Check their separate licenses before redistribution or commercial use. In particular, Audiobox code/weights and PESQ have their own conditions; this project's MIT license does not override them. Source revisions and artifact SHA-256 values used in validation are in the deployment manifest and detailed reports.

The compatibility loader for SHEET injects a local SSL checkpoint only; its network and forward computation are upstream. SCOREQ uses the official preprocessing/predict methods with an explicit ONNX session. SpeechBERTScore uses the official feature matching and pooling with a local HuBERT model. DNSMOS receives a 16 kHz float WAV so its historical librosa resampling API is not invoked. These initialization/I/O choices are included in result metadata.

## v0.4 sources

- Microsoft [SpeechMOS 0.0.1.1](https://pypi.org/project/speechmos/0.0.1.1/): PLCMOS preprocessing/inference, loaded from an explicitly supplied public source file. This is a different project from tarepan/SpeechMOS (UTMOS).
- [URGENT 2025](https://github.com/urgent-challenge/urgent2025_challenge/tree/main/evaluation_metrics): mathematical LSD and MCD conventions; upstream functions are independently invoked in validation.
- [URGENT 2026](https://github.com/urgent-challenge/urgent2026_challenge_track1/blob/main/evaluation_metrics/calculate_phoneme_similarity.py) and the [LPS authors](https://git.rz.tu-bs.de/ifn-public/LPS): phone-token LPS definition.
- [pysptk](https://github.com/r9y9/pysptk) and [fastdtw](https://github.com/slaypni/fastdtw): mel-cepstral analysis and alignment. The public SPTK/ESPnet-derived reference script credits Wen-Chin Huang and Tomoki Hayashi under Apache-2.0; it is used as an external validation reference, not vendored here.
- [mHuBERT-147](https://huggingface.co/utter-project/mHuBERT-147) and [WavLM-base-plus-SV](https://huggingface.co/microsoft/wavlm-base-plus-sv): independently provisioned pretrained encoders, each with its own model-card terms.

No internal lab code tree or model weights are included in this repository. Public source hashes and artifact fingerprints accompany the validation report. New adapters do not grant redistribution rights to upstream materials.

## v0.5 AEC and verification

- [Microsoft speechmos / AECMOS](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local): upstream three-signal frontend and three checkpoints, ECHO/DEG outputs; public package 0.0.1.1. Source and weights are provisioned separately, not redistributed here.
- [scikit-learn ROC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html): complete tie-aware operating points, version 1.5.2. EER interpolation and NIST-style minDCF reductions are explicitly defined in our profile.
- [NIST SRE detection-cost construction](https://www.nist.gov/document/nistsre10evalplan-r6pdf): costs and prior must be reported; no claim of one universal NIST trial protocol.
- [ONNX Runtime CUDA](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html): isolated execution and provider profiling. AECMOS pins 1.16.3 for original-checkpoint compatibility.

## v0.7 pitch and voicing

The pitch adapter contains adaptations of the following public computational recipes. Unlike the separately provisioned model-source trees described above, these small algorithm adaptations are distributed in `speech_eval/pitch.py`; their copyright and license notices are retained below. The independent upstream validation scripts are not bundled in the wheel.

- **Amphion**, copyright (c) 2023 Amphion, MIT: revision [`26f6883110181f1dbfe95c70a7c7dbaf4de5f42a`](https://github.com/open-mmlab/Amphion/tree/26f6883110181f1dbfe95c70a7c7dbaf4de5f42a), `evaluation/metrics/f0/v_uv_f1.py`, `evaluation/metrics/f0/f0_rmse.py`, and `utils/f0.py`. The named adapters retain the Parselmouth extraction, F0 cut/DTW alignment, confusion counts and all-frame RMSE definitions. Unsupported median-centered mode and explicit undefined-result behavior are described in [PITCH.md](docs/PITCH.md).
- **ESPnet**, copyright 2021 Wen-Chin Huang and Tomoki Hayashi, Apache-2.0: revision [`c573dfed21a3d64ce491a6f53748cc6b596097e5`](https://github.com/espnet/espnet/blob/c573dfed21a3d64ce491a6f53748cc6b596097e5/egs2/TEMPLATE/asr1/pyscripts/utils/evaluate_f0.py). The named adapter retains int16 decoding, WORLD Harvest/CheapTrick, pysptk mel-cepstra, FastDTW and jointly voiced natural-log RMSE. Cross-rate resampling and invalid/undefined cases have a narrower explicit contract; these are not undocumented substitutions.
- [WORLD](https://github.com/mmorise/World) and [PyWorld](https://github.com/JeremyCCHsu/Python-Wrapper-for-World-Vocoder): F0 and spectral-envelope extraction; PyWorld 0.3.5 in the validated environment. WORLD's upstream BSD-style license applies separately.
- [Praat/Parselmouth](https://github.com/YannickJadoul/Parselmouth): optional `praat-parselmouth` 0.4.7 dependency for Amphion profiles. Parselmouth is GPL-3.0-or-later and embeds Praat under its own license; this project's MIT license does not relicense those dependencies. No Parselmouth binary is copied into the SpeechMetricHub wheel.
- [librosa](https://github.com/librosa/librosa), [resampy](https://github.com/bmcfee/resampy), [pysptk](https://github.com/r9y9/pysptk), and [fastdtw](https://github.com/slaypni/fastdtw): explicit audio loading/resampling, pitch-contour alignment, mel-cepstral analysis and spectral alignment. Their versions appear in results and the environment lock.

The unqualified `vuv_f1` and `f0_rmse` interfaces use the separately documented SpeechMetricHub synchronized-reconstruction protocol. They are not labeled as Amphion/ESPnet or as a universal official benchmark. The direct-upstream numerical validation, source file hashes and boundary-policy differences are recorded in [validation/pitch-v0.7.json](validation/pitch-v0.7.json).

### Amphion MIT license notice

MIT License

Copyright (c) 2023 Amphion

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


### ESPnet Apache License 2.0

                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright 2017 Johns Hopkins University (Shinji Watanabe)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
