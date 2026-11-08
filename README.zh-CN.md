# SpeechMetricHub · 语音指标集成库

公开版本 **0.4.0**；沿用 v0.2 的指标集成与真实模型验收基线。将标准计分器和预训练评测模型整合为同一套 Python / CLI 接口，保留各自的参考条件、预处理、分数方向和模型身份。重点支持 MT-ASR / TS-ASR，也可用于质量、可懂度、分离和内容保持研究。

**使用同一个库，不等于所有论文使用同一评测协议。** 本项目固定并公开协议，不宣称存在唯一官方清洗或容差。工作台已有 `speech-eval-mt-v1.0` 协议保持不变。

## v0.4 新增与口径修正

当前提供 **75 个独立指标变体、5 个兼容别名、10 个测量维度、20 个模型家族**。新增 11 个接口：mHuBERT-147 多语言 SBS 三项输出、音素 token 版 LPS、WavLM 话者相似度、PLCMOS 的 final/validation 两个模型，以及四种明确命名的 LSD/MCD 口径。

先完成[调研与接入计划](docs/EXPANSION_PLAN.md)，再实现并验证。详细[口径说明](docs/EXPANSION_PROFILES.md)和[本轮验证结果](validation/expansion-v0.4.json)随版本保留。旧的 IPA 字符相似度不替换为音素 token 相似度；旧实验数值仍可复现。

## 指标组织

主分类按“测量什么”，参考条件与任务标签独立存储。这是项目的工程分类，不冒称标准组织的唯一分类。

| 测量维度 | 可调用指标 |
|---|---|
| 识别准确性 `recognition` | WER/CER、TS-WER/CER、cpWER/cpCER、tcpWER/tcpCER、ORC/tcORC、MIMO/tcMIMO、greedy DI-cp/DI-tcp、Whisper WER/dWER |
| 说话人结构 `speaker_structure` | DER、JER、说话人数误差及人数命中诊断 |
| 语音活动 `speech_activity` | 检测错误率、precision、recall、accuracy |
| 感知质量 `perceptual_quality` | PESQ WB/NB、ViSQOL speech/audio、DNSMOS 4 项校准输出及 3 项原始输出、NISQA 5 维、SCOREQ 4 种组合、UTMOS22 strong、SHEET SSL-MOS |
| 可懂度 `intelligibility` | STOI、ESTOI |
| 信号保真 `signal_fidelity` | SI-SDR、SI-SDRi、BSS SDR/SIR/SAR |
| 说话人身份 `speaker_identity` | RawNet3 embedding cosine |
| 内容相似度 `content_similarity` | IPA 字符相似度、SpeechBERTScore precision/recall/F1 |
| 音频美学 `audio_aesthetics` | Audiobox CE、CU、PC、PQ |
| 评分一致性 `rating_agreement` | PLCC、SRCC、Kendall tau-b |

`enhancement`、`tse`、`codec` 等只是任务标签，不能证明模型在该任务上的有效性。参考条件包括无参考、对齐波形、匹配/非匹配波形、目标说话人参考、文本、语音活动标注、成对主观评分。

完整参数与局限见 [中文指标卡](docs/METRICS.zh-CN.md)。实际验证见 [验收报告](validation/README.md) 和 `validation/summary.json`。5 个兼容旧名的别名不计作新增指标。

[English](README.md) · [完整文档](docs/README.md) · [GitHub Releases](https://github.com/YangXu212/SpeechMetricHub/releases)

## 快速调用

核心算法建议 Python 3.10/3.11；神经模型已验证 Linux / Python 3.10 / CPU。Windows MeetEval 编译与隔离包见 [WINDOWS_BUILD.md](WINDOWS_BUILD.md)。

```sh
git clone https://github.com/YangXu212/SpeechMetricHub.git
cd SpeechMetricHub
python -m venv .venv
# 激活虚拟环境后：
python -m pip install 'numpy<2' '.[transcription,quality,separation,diarization]'
speechmetrichub list --category perceptual_quality
speechmetrichub list --task tse --reference-kind none
speechmetrichub run tcpwer --input examples/tcpwer.json --output result.json
speechmetrichub doctor
```

```python
from speechmetrichub import run, list_metrics, evaluate
run('ts_wer', reference='hello world', hypothesis='hello word')
run('estoi', reference=clean_wave, hypothesis=predicted_wave, sample_rate=16000)
run('tcpwer', reference=reference_segments, hypothesis=predicted_segments, collar=5)
```

分段格式：`{"speaker":"A", "text":"hello", "start":0.0, "end":1.0}`。一次调用对应完整录音，说话人重排不能逐句重置。TS-ASR 必须提前选定目标，不允许按答案挑选最好的一路。

## 模型接口

只加载显式配置的本地文件，评分时不自动下载；`doctor` 不加载模型。模型在独立进程运行，默认 CPU、2 线程、超时 600 秒。可通过 `python` 配置指定独立模型环境。

```python
results = evaluate(
    ['audiobox_aesthetics_ce', 'audiobox_aesthetics_cu',
     'audiobox_aesthetics_pc', 'audiobox_aesthetics_pq'],
    hypothesis='/audio/example.wav',
    configs={'audiobox_aesthetics': {
        'checkpoint': '/models/audiobox/checkpoint.pt',
        'trusted_checkpoint': True, 'device': 'cpu', 'threads': 2,
    }},
)
```

同一次 `evaluate` 的多个输出共用一次前向计算。不同录音目前重新启动进程并加载模型；这版优先依赖隔离，不宣称是持久化高吞吐服务。

SCOREQ 使用 `scoreq_natural_nr/ref`、`scoreq_synthetic_nr/ref` 四个明确名称。REF 必须声明 `reference_kind`；synthetic 按上游建议使用 nonmatching 参考。NR 是越高越好的预测 MOS；REF 是越低越好的距离。AE 的 PC 是制作复杂度，不能作为音质排行榜的“越高越好”。

```sh
speechmetrichub evaluate --input examples/model_evaluation.json --output model-results.json
speechmetrichub doctor --config deployment.local.json --verify-hashes
```

配置与依赖见 [部署说明](docs/DEPLOYMENT.md)，模型归属见 [上游与许可证](THIRD_PARTY.md)。权重不随 wheel 分发。

## 结果与汇总

- 成功返回 `status="ok"`、有限 `value`、单位、协议、版本；模型另有输入/权重/代码 SHA-256、完整输出、设备和耗时。
- 缺依赖、非法输入、模型错误、超时均保留原因，不填 0。参数错误可能抛出 `ValueError`，批量接口捕获并保留。JSON 不输出 NaN/Infinity。
- WER/CER/Whisper 累计 N/S/D/I；DER/VAD 累计时长分量；JER 按参考说话人数累计；波形质量按录音宏平均。相关系数在完整评分数组上算，不平均相关系数。
- 缺项时完整集分数为空，子集分数单列，同时报告 expected/scored/coverage。不同协议、权重或清洗版本不能合并。
- WER 空参考保留插入数。BSS 完美重建导致无限值时显式标记，不静默截断到任意 dB。
- 传统侵入式指标要求同率、同长度、有限单声道，不暗中裁剪/延时搜索/增益拟合。模型部署协议拒绝静音、短于 1 秒和立体声；这些是本 profile 的限制，不声称是全部原论文的限制。

```sh
speechmetrichub batch ts_wer --input examples/batch_ts_asr.json --output report.json
python -m unittest discover -s tests -v
python -m build
```

CLI 成功退出 0；评分失败/批量缺项退出 2。`doctor` 不能代替真实调用。

## MT/TS-ASR 协议

固定 MeetEval 0.4.3、kaldialign 0.12.0。NFKC/casefold 保留重复、口头词、数字原写法和词内撇号。中文按字符 CER。tcp 使用字符比例伪词时间：参考 character_based、假设 character_based_points，容差显式配置。句级插值不等价于人工词级时间戳。

DER/JER 必须提供 UEM 与确认的语音活动标注，转写句段不能冒充真值。说话人数是辅助诊断，不能替代 DER 或 cpWER。

## 范围

这是具有真实接口验收的研究集成版本，不是完整排行榜复现。GPU、所有平台/语言、所有 SHEET 模型和失真类型没有穷尽验证。Dockerfile 与 CI 是否实际执行，以验收报告为准。未实现候选项单列于 [扩展路线](docs/ROADMAP.md)，不混入可调用目录。扩展要求见 [CONTRIBUTING.md](CONTRIBUTING.md)。
