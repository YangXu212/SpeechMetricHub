# SpeechMetricHub · 语音评测指标集成库

<p align="center"><a href="README.md">English</a> · <b>简体中文</b> · <a href="docs/README.md">完整文档</a> · <a href="docs/METRICS.zh-CN.md">中文指标卡</a> · <a href="validation/README.zh-CN.md">验证记录</a> · <a href="CHANGELOG.md">更新日志</a></p>

**SpeechMetricHub** 将主流语音评测计分器与预训练神经评测模型整合到同一套 Python / CLI 接口中，在返回分数的同时显式记录参考条件、预处理方式、模型指纹、分数方向与汇总口径。

适用于语音识别（ASR / MT-ASR / TS-ASR）、说话人日志、语音质量、可懂度、信号保真、基频与清浊音、回声消除、说话人身份及内容一致性研究。

> **102 个独立指标变体 · 5 个兼容别名 · 11 个测量维度 · 34 个模型家族。**
> **使用同一个库不等于所有论文使用同一评测协议**——本库固定并公开具体口径，历史版本变更详见 [CHANGELOG.md](CHANGELOG.md)。

## 核心特性

- **完整输出头与明确方向**：保留 Audiobox CE/CU/PC/PQ、SCOREQ 四种域/模式、NISQA 五维、DNSMOS 校准与原始输出头、SpeechBERTScore P/R/F1、AECMOS 三模型 ECHO/DEG 等全部输出。
- **可追溯的锁版本协议**：通过部署锁（`deployment.locked.json`）与 `MetricHub` 固定代码、依赖版本、归一化规则及权重 SHA-256 指纹；不自动联网下载模型。
- **失败显式可见**：缺依赖、非法输入、解码截断或批量缺项均显式报错与留痕，绝不静默填 0 或从均值中隐藏；`compare_recognition` 显式区分完整语料与条件公共子集。
- **复用上游算法**：底层计算直接调用 MeetEval、pyannote.metrics、fast-bss-eval、OpenAI Whisper、Transformers、ESPnet、S3PRL、PyWorld、Parselmouth 及各原论文实现。

## 指标维度总览

主分类按“测量什么”组织，参考条件与任务标签（`enhancement`、`tse`、`codec`、`tts` 等）独立标注。

| 测量维度 | 可调用指标 |
|---|---|
| 识别准确性 `recognition` | WER/CER、TS-WER/CER、cpWER/cpCER、tcpWER/tcpCER、ORC/tcORC、MIMO/tcMIMO、greedy DI-cp/DI-tcp；OpenAI Whisper WER/dWER（`whisper_wer_en_openai`、`whisper_dwer_en_openai`）、升级版 HF Whisper v3（`whisper_wer_hf_v3`、`whisper_dwer_hf_v3`）、兼容版 Whisper WER/dWER；Cohere Transcribe WER/CER/dWER/dCER 及显式英/中文口径 |
| 说话人结构 `speaker_structure` | DER、JER、说话人数误差及人数命中诊断 |
| 语音活动 `speech_activity` | 检测错误率、precision、recall、accuracy |
| 感知质量 `perceptual_quality` | PESQ WB/NB、ViSQOL speech/audio、DNSMOS 校准与原始输出头及 P.808、NISQA 5 维、SCOREQ 4 种组合、UTMOS22 strong、SHEET SSL-MOS、PLCMOS v2/final 与 validation、AECMOS 三模型 ECHO/DEG |
| 可懂度 `intelligibility` | STOI、ESTOI |
| 信号保真 `signal_fidelity` | SI-SDR、SI-SDRi、BSS SDR/SIR/SAR；显式 LSD/MCD 口径；V/UV F1 与 F0 RMSE（WORLD、Amphion、ESPnet log-F0） |
| 说话人身份 `speaker_identity` | RawNet3、WavLM-base-plus-SV、UniSpeech WavLM-Large-ECAPA 说话人相似度；完整 trials 的 EER / minDCF |
| 回声衰减 `echo_attenuation` | 明确远端单讲区间的 ERLE（按能量汇总） |
| 内容相似度 `content_similarity` | IPA 字符相似度；HuBERT / mHuBERT SpeechBERTScore P/R/F1；字符级与音素 token 级 LPS |
| 音频美学 `audio_aesthetics` | Audiobox CE、CU、PC、PQ |
| 评分一致性 `rating_agreement` | PLCC、SRCC、Kendall tau-b |

完整参数与局限见 [中文指标卡](docs/METRICS.zh-CN.md) 与 [English Metric Catalog](docs/METRICS.md)。

## 快速开始

### 安装

核心计分器建议使用 Python 3.10 或 3.11（Windows 编译说明见 [WINDOWS_BUILD.md](WINDOWS_BUILD.md)）：

```bash
git clone https://github.com/YangXu212/SpeechMetricHub.git
cd SpeechMetricHub
python -m venv .venv
source .venv/bin/activate
python -m pip install "numpy<2" ".[transcription,quality,separation,diarization,spectral,pitch]"
```

完整固定环境与集群共享部署请参考 [安装说明](docs/INSTALLATION.md) 与 [共享部署指南](docs/SHARED_DEPLOYMENT.md)。

### Python 与 CLI 调用

```python
from speechmetrichub import run, evaluate, MetricHub

# 文本 / 波形标准指标
run("ts_wer", reference="hello world", hypothesis="hello word")
run("estoi", reference=clean_wave, hypothesis=predicted_wave, sample_rate=16000)
run("tcpwer", reference=reference_segments, hypothesis=predicted_segments, collar=5)

# 共享锁定部署调用预训练模型
hub = MetricHub("/path/to/deployment.locked.json")
res = hub.run("whisper_wer_en_openai", reference="hello world", hypothesis="enh.wav")
```

```bash
speechmetrichub list --category perceptual_quality
speechmetrichub list --task tse --reference-kind none
speechmetrichub run tcpwer --input examples/tcpwer.json --output result.json
speechmetrichub batch ts_wer --input examples/batch_ts_asr.json --output report.json
speechmetrichub doctor --config deployment.local.json --verify-hashes
```

## 预训练模型与口径选型建议

所有神经评测模型均在独立子进程中离线运行，只加载显式配置的本地文件；同一次 `evaluate()` 请求同一模型家族的多个输出头会复用一次前向计算。

- **Whisper ASR 选型**：复现语音增强 / TSE 论文（如 StuPASE、URGENT、ESPnet 评测流程）时，**推荐优先使用 `whisper_wer_en_openai` / `whisper_dwer_en_openai`**（对应官方 `openai-whisper` + `beam_size=5` + `hallucination_silence_threshold=2.0` + `TextCleaner("whisper_en")` 调用方式），或使用 Cohere 英文口径 `cohere_wer_en_whisper` / `cohere_dwer_en_whisper`。升级版 `whisper_wer_hf_v3` / `whisper_dwer_hf_v3` 已在 Transformers 侧补齐时间戳、温度回退与 `>30s` 长音频解码；旧 `whisper_wer` / `whisper_dwer` 仅为兼容历史锁文件保留。详见 [Whisper ASR 协议说明](docs/WHISPER_ASR.md) 与 [Cohere 协议说明](docs/COHERE_PROFILES.md)。
- **说话人相似度选型**：按实验目标显式选择 `speaker_similarity`（RawNet3）、`speaker_similarity_wavlm`（WavLM-base-plus-SV）或 `speaker_similarity_unispeech_wavlm`（UniSpeech WavLM-Large-ECAPA），三者不可混比。
- **方向与语义注意**：SCOREQ NR 越高越好，SCOREQ REF 为嵌入距离越低越好；Audiobox PC 为制作复杂度描述量；`*_dwer` / `*_dcer` 衡量与干净音频 ASR 转写的一致性，不是真值错误率。

## 结果与汇总边界

- WER/CER/Whisper/Cohere 按语料累计 `N/S/D/I` 计算 micro 错误率；DER/VAD 按时长分量累计；JER 按参考说话人数累计；V/UV F1 与 F0 RMSE 汇总充分统计量；ERLE 按能量汇总；质量类指标按样本宏平均；相关系数在完整评分数组上计算。
- 批量存在缺项或失败时，`value` 为空，同时单独报告 `valid_subset_value` 与 `coverage`。
- MT/TS-ASR 固定 MeetEval 0.4.3 与 `nfkc-casefold-v1` 口径；DER/JER 必须提供 UEM 与真实语音活动标注。

## 文档与版本记录

- 中文资料：[指标卡](docs/METRICS.zh-CN.md) · [部署说明](docs/DEPLOYMENT.md) · [验证记录](validation/README.zh-CN.md)
- 协议与架构：[文档总目录](docs/README.md) · [Whisper 协议](docs/WHISPER_ASR.md) · [Cohere 协议](docs/COHERE_PROFILES.md) · [基频与清浊音](docs/PITCH.md) · [AEC 与声纹](docs/AEC_VERIFICATION.md) · [模型配置](docs/MODELS.md) · [共享部署](docs/SHARED_DEPLOYMENT.md)
- 版本与许可：[更新日志](CHANGELOG.md) · [上游与许可证](THIRD_PARTY.md) · [安全边界](SECURITY.md) · [贡献指南](CONTRIBUTING.md)
