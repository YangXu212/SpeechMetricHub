# 部署与复现

核心环境安装 `pip install 'numpy<2' '.[transcription,quality,separation,diarization]'`。模型基础安装 `.[models]`，再按需选择 aesthetics、scoreq、dnsmos、sheet、speaker extras。SCOREQ 1.0.0 固定 ONNX Runtime 1.16.3，不要混装 CPU/GPU 发行包。

官方代码与权重独立保存，使用验收清单中的提交和 SHA-256。路径通过配置传入，不修改库源码。`speech-eval doctor --config deployment.local.json --verify-hashes` 检查文件；`expected_hashes` 可要求运行时拒绝不同权重和代码。源代码式上游的依赖在模型环境安装；可按 family 指定 `python` 解释器。

| family | 必要配置 |
|---|---|
| audiobox_aesthetics | checkpoint：官方四头 checkpoint.pt |
| scoreq_natural_nr/ref、scoreq_synthetic_nr/ref | checkpoint：对应 adapt_nr_telephone / fixed_nmr_telephone / adapt_nr_synthetic / fixed_nmr_synthetic.onnx；REF 指定 reference_kind |
| dnsmos | source_file：官方 dnsmos_local.py；primary_model：sig_bak_ovr.onnx；p808_model：model_v8.onnx |
| nisqa | source_dir：NISQA repo；checkpoint：多维 nisqa.tar |
| utmos | source_dir：SpeechMOS repo；checkpoint：utmos22_strong_step7459_v1.pt |
| sheet_ssqa | source_dir：SHEET；config_file：SSLMOS config；checkpoint：MOS 权重；ssl_checkpoint：wav2vec_small.pt |
| speechbert | source_dir：DiscreteSpeechMetrics；model_dir：HuBERT base；layer：验证为 8 |
| phoneme_similarity | model_dir：facebook/wav2vec2-lv-60-espeak-cv-ft 完整目录 |
| speaker_similarity | config_file：ESPnet RawNet3 训练配置；checkpoint：40epoch.pth |
| visqol_speech/audio | binary：官方 ViSQOL；checkpoint：speech lattice TFLite / audio SVR |
| whisper_wer/dwer | model_dir：Whisper large-v3 HF；language：english；beam_size：5 |

公共字段：device 默认 cpu，或显式 cuda:N；threads 默认 2；timeout 秒；python 指定模型解释器；trusted_checkpoint=true 允许可信 PyTorch 文件；expected_hashes 映射文件字段名到 SHA-256。v0.2/v0.4 重模型记录主要为 CPU；v0.5 的 AECMOS 有独立 CPU/GPU 验收，不能外推到其他模型。DNSMOS 目前只支持 CPU。

重模型由独立子进程执行，超时终止本次进程。不需要常驻终端。工作台由原计划任务维护。

模型与代码指纹参与批量协议一致性检查；输入指纹只用于逐条追踪。复制配置不等于新机器已验收。质量模型在语言、自然/合成语音和失真类型上的效度不同，接口验证不能代替领域效度研究。

旧名 scoreq/dnsmos/nisqa/speechbert_score/visqol 分别指 natural_ref/OVRL/overall MOS/precision/speech；新实验用显式 ID。

`docker build -t speech-eval .` 构建核心镜像，数据只读挂载，模型环境按可选依赖扩展，权重不烘焙进镜像。Dockerfile 不代表 Docker runtime 已验收。

## v0.5 AEC / verification and deployment locks

See [AECMOS, ERLE, EER and minDCF profiles](AEC_VERIFICATION.md) and [locked worker deployment](DEPLOYMENT_LOCKS.md).
