# 指标卡与接口说明

每个条目对应实际注册 ID。完整真实结果、异常输入、上游对照和环境指纹见 `../validation/summary.json`。

## wer

词错误率

- 主分类：`recognition`；参考条件：transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：asr, ts_asr, tts, codec。
- 调用：`run('wer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## cer

字错误率

- 主分类：`recognition`；参考条件：transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：asr, ts_asr, tts, codec。
- 调用：`run('cer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## ts_wer

指定目标说话人的词错误率

- 主分类：`recognition`；参考条件：transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：asr, ts_asr。
- 调用：`run('ts_wer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## ts_cer

指定目标说话人的字错误率

- 主分类：`recognition`；参考条件：transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：asr, ts_asr。
- 调用：`run('ts_cer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## cpwer

全局说话人重排词错误率

- 主分类：`recognition`；参考条件：speaker_transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：mt_asr, meeting。
- 调用：`run('cpwer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## cpcer

全局说话人重排字错误率

- 主分类：`recognition`；参考条件：speaker_transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：mt_asr, meeting。
- 调用：`run('cpcer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## tcpwer

时间约束全局重排词错误率

- 主分类：`recognition`；参考条件：speaker_transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：mt_asr, meeting。
- 调用：`run('tcpwer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## tcpcer

时间约束全局重排字错误率

- 主分类：`recognition`；参考条件：speaker_transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：mt_asr, meeting。
- 调用：`run('tcpcer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## der

DER

- 主分类：`speaker_structure`；参考条件：speaker_annotation。
- 方向：`lower_is_better`；单位：`percent`；任务标签：diarization, meeting。
- 调用：`run('der', ...)`。
- 来源：https://github.com/pyannote/pyannote-metrics。
- 参数与口径：DER/JER使用pyannote.metrics，必须显式UEM、collar与skip_overlap，并确认真实语音活动标注。speaker_count是非空说话人标签基数的辅助误差；缺标签不等于模型真的少估一个人。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## jer

JER

- 主分类：`speaker_structure`；参考条件：speaker_annotation。
- 方向：`lower_is_better`；单位：`percent`；任务标签：diarization, meeting。
- 调用：`run('jer', ...)`。
- 来源：https://github.com/pyannote/pyannote-metrics。
- 参数与口径：DER/JER使用pyannote.metrics，必须显式UEM、collar与skip_overlap，并确认真实语音活动标注。speaker_count是非空说话人标签基数的辅助误差；缺标签不等于模型真的少估一个人。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## pesq_wb

PESQ 宽带 16 kHz

- 主分类：`perceptual_quality`；参考条件：aligned_waveform。
- 方向：`higher_is_better`；单位：`backend_score`；任务标签：enhancement, tse, separation, codec。
- 调用：`run('pesq_wb', ...)`。
- 来源：https://github.com/ludlows/PESQ。
- 参数与口径：PESQ WB=16k，NB=8k；其他输入率用soxr HQ重采样，不改增益或搜索延时。不是POLQA，需遵守上游实现许可证。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## pesq_nb

PESQ 窄带 8 kHz

- 主分类：`perceptual_quality`；参考条件：aligned_waveform。
- 方向：`higher_is_better`；单位：`backend_score`；任务标签：enhancement, tse, separation, codec。
- 调用：`run('pesq_nb', ...)`。
- 来源：https://github.com/ludlows/PESQ。
- 参数与口径：PESQ WB=16k，NB=8k；其他输入率用soxr HQ重采样，不改增益或搜索延时。不是POLQA，需遵守上游实现许可证。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## stoi

STOI 可懂度

- 主分类：`intelligibility`；参考条件：aligned_waveform。
- 方向：`higher_is_better`；单位：`backend_score`；任务标签：enhancement, tse, separation, codec。
- 调用：`run('stoi', ...)`。
- 来源：https://github.com/mpariente/pystoi。
- 参数与口径：pystoi 0.4.1，STOI/ESTOI分别extended=False/True，原生10kHz内部处理。输入同长度且无隐式对齐；短信号产生的后端警告不冒充有效分数。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## estoi

ESTOI 扩展可懂度

- 主分类：`intelligibility`；参考条件：aligned_waveform。
- 方向：`higher_is_better`；单位：`backend_score`；任务标签：enhancement, tse, separation, codec。
- 调用：`run('estoi', ...)`。
- 来源：https://github.com/mpariente/pystoi。
- 参数与口径：pystoi 0.4.1，STOI/ESTOI分别extended=False/True，原生10kHz内部处理。输入同长度且无隐式对齐；短信号产生的后端警告不冒充有效分数。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## si_sdr

尺度不变失真比

- 主分类：`signal_fidelity`；参考条件：aligned_waveform。
- 方向：`higher_is_better`；单位：`dB`；任务标签：enhancement, tse, separation, codec。
- 调用：`run('si_sdr', ...)`。
- 来源：https://github.com/fakufaku/fast_bss_eval。
- 参数与口径：SI-SDR采用fast-bss-eval，zero_mean=True；SI-SDRi再减同一clean-reference与mixture的SI-SDR。BSS SDR/SIR/SAR默认512点滤波、zero_mean=False、由上游选择排列；必须提供完整[source,samples]矩阵。非有限完美分数显式标记。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## si_sdri

相对输入混合音频的 SI-SDR 改善

- 主分类：`signal_fidelity`；参考条件：aligned_waveform。
- 方向：`higher_is_better`；单位：`dB`；任务标签：enhancement, tse, separation, codec。
- 调用：`run('si_sdri', ...)`。
- 来源：https://github.com/fakufaku/fast_bss_eval。
- 参数与口径：SI-SDR采用fast-bss-eval，zero_mean=True；SI-SDRi再减同一clean-reference与mixture的SI-SDR。BSS SDR/SIR/SAR默认512点滤波、zero_mean=False、由上游选择排列；必须提供完整[source,samples]矩阵。非有限完美分数显式标记。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## speaker_count

说话人数正确性、少估、多估与绝对误差；辅助诊断

- 主分类：`speaker_structure`；参考条件：speaker_annotation。
- 方向：`lower_is_better`；单位：`speakers`；任务标签：diarization, mt_asr, meeting。
- 调用：`run('speaker_count', ...)`。
- 来源：local explicit cardinality protocol。
- 参数与口径：DER/JER使用pyannote.metrics，必须显式UEM、collar与skip_overlap，并确认真实语音活动标注。speaker_count是非空说话人标签基数的辅助误差；缺标签不等于模型真的少估一个人。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## audiobox_aesthetics_ce

Content Enjoyment

- 主分类：`audio_aesthetics`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_rating`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('audiobox_aesthetics_ce', ...)`；模型家族 `audiobox_aesthetics`，选择输出 `CE`。
- 来源：https://github.com/facebookresearch/audiobox-aesthetics。
- 参数与口径：四个轴来自同一前向计算。CE=Content Enjoyment、CU=Content Usefulness、PC=Production Complexity、PQ=Production Quality。PC 是描述量；其余分数也不是人工听测 MOS。模型内部重采样 16k，并按有效片段长度加权。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## audiobox_aesthetics_cu

Content Usefulness

- 主分类：`audio_aesthetics`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_rating`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('audiobox_aesthetics_cu', ...)`；模型家族 `audiobox_aesthetics`，选择输出 `CU`。
- 来源：https://github.com/facebookresearch/audiobox-aesthetics。
- 参数与口径：四个轴来自同一前向计算。CE=Content Enjoyment、CU=Content Usefulness、PC=Production Complexity、PQ=Production Quality。PC 是描述量；其余分数也不是人工听测 MOS。模型内部重采样 16k，并按有效片段长度加权。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## audiobox_aesthetics_pc

Production Complexity

- 主分类：`audio_aesthetics`；参考条件：none。
- 方向：`descriptive`；单位：`predicted_rating`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('audiobox_aesthetics_pc', ...)`；模型家族 `audiobox_aesthetics`，选择输出 `PC`。
- 来源：https://github.com/facebookresearch/audiobox-aesthetics。
- 参数与口径：四个轴来自同一前向计算。CE=Content Enjoyment、CU=Content Usefulness、PC=Production Complexity、PQ=Production Quality。PC 是描述量；其余分数也不是人工听测 MOS。模型内部重采样 16k，并按有效片段长度加权。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## audiobox_aesthetics_pq

Production Quality

- 主分类：`audio_aesthetics`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_rating`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('audiobox_aesthetics_pq', ...)`；模型家族 `audiobox_aesthetics`，选择输出 `PQ`。
- 来源：https://github.com/facebookresearch/audiobox-aesthetics。
- 参数与口径：四个轴来自同一前向计算。CE=Content Enjoyment、CU=Content Usefulness、PC=Production Complexity、PQ=Production Quality。PC 是描述量；其余分数也不是人工听测 MOS。模型内部重采样 16k，并按有效片段长度加权。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## scoreq_natural_nr

SCOREQ natural nr

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('scoreq_natural_nr', ...)`；模型家族 `scoreq_natural_nr`，选择输出 `score`。
- 来源：https://github.com/alessandroragano/scoreq。
- 参数与口径：必须选 natural/synthetic 和 nr/ref 对应权重。NR 输出预测 MOS，REF 输出欧氏距离。natural REF 支持 matching/nonmatching；synthetic REF profile 使用 nonmatching。显式参考条件与模型权重共同确定实验口径。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## scoreq_natural_ref

SCOREQ natural ref

- 主分类：`perceptual_quality`；参考条件：nonmatching_waveform, matching_waveform。
- 方向：`lower_is_better`；单位：`embedding_distance`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('scoreq_natural_ref', ...)`；模型家族 `scoreq_natural_ref`，选择输出 `score`。
- 来源：https://github.com/alessandroragano/scoreq。
- 参数与口径：必须选 natural/synthetic 和 nr/ref 对应权重。NR 输出预测 MOS，REF 输出欧氏距离。natural REF 支持 matching/nonmatching；synthetic REF profile 使用 nonmatching。显式参考条件与模型权重共同确定实验口径。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。
- 语义性质：相同音频的相似度为1或参考距离为0，容差1e-5。

## scoreq_synthetic_nr

SCOREQ synthetic nr

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('scoreq_synthetic_nr', ...)`；模型家族 `scoreq_synthetic_nr`，选择输出 `score`。
- 来源：https://github.com/alessandroragano/scoreq。
- 参数与口径：必须选 natural/synthetic 和 nr/ref 对应权重。NR 输出预测 MOS，REF 输出欧氏距离。natural REF 支持 matching/nonmatching；synthetic REF profile 使用 nonmatching。显式参考条件与模型权重共同确定实验口径。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## scoreq_synthetic_ref

SCOREQ synthetic ref

- 主分类：`perceptual_quality`；参考条件：nonmatching_waveform。
- 方向：`lower_is_better`；单位：`embedding_distance`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('scoreq_synthetic_ref', ...)`；模型家族 `scoreq_synthetic_ref`，选择输出 `score`。
- 来源：https://github.com/alessandroragano/scoreq。
- 参数与口径：必须选 natural/synthetic 和 nr/ref 对应权重。NR 输出预测 MOS，REF 输出欧氏距离。natural REF 支持 matching/nonmatching；synthetic REF profile 使用 nonmatching。显式参考条件与模型权重共同确定实验口径。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## dnsmos_sig

DNSMOS SIG

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('dnsmos_sig', ...)`；模型家族 `dnsmos`，选择输出 `SIG`。
- 来源：https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS。
- 参数与口径：默认非 personalized 模型。SIG/BAK/OVRL 是多项式校准后预测，另保留三个 raw 头与独立 P808_MOS。soxr HQ 到16k后调用官方计算；短于9.01秒时重复填充、分窗与平均均沿用官方脚本。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## dnsmos_bak

DNSMOS BAK

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('dnsmos_bak', ...)`；模型家族 `dnsmos`，选择输出 `BAK`。
- 来源：https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS。
- 参数与口径：默认非 personalized 模型。SIG/BAK/OVRL 是多项式校准后预测，另保留三个 raw 头与独立 P808_MOS。soxr HQ 到16k后调用官方计算；短于9.01秒时重复填充、分窗与平均均沿用官方脚本。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## dnsmos_ovrl

DNSMOS OVRL

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('dnsmos_ovrl', ...)`；模型家族 `dnsmos`，选择输出 `OVRL`。
- 来源：https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS。
- 参数与口径：默认非 personalized 模型。SIG/BAK/OVRL 是多项式校准后预测，另保留三个 raw 头与独立 P808_MOS。soxr HQ 到16k后调用官方计算；短于9.01秒时重复填充、分窗与平均均沿用官方脚本。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## dnsmos_p808_mos

DNSMOS P808_MOS

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('dnsmos_p808_mos', ...)`；模型家族 `dnsmos`，选择输出 `P808_MOS`。
- 来源：https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS。
- 参数与口径：默认非 personalized 模型。SIG/BAK/OVRL 是多项式校准后预测，另保留三个 raw 头与独立 P808_MOS。soxr HQ 到16k后调用官方计算；短于9.01秒时重复填充、分窗与平均均沿用官方脚本。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## dnsmos_sig_raw

DNSMOS SIG_raw

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('dnsmos_sig_raw', ...)`；模型家族 `dnsmos`，选择输出 `SIG_raw`。
- 来源：https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS。
- 参数与口径：默认非 personalized 模型。SIG/BAK/OVRL 是多项式校准后预测，另保留三个 raw 头与独立 P808_MOS。soxr HQ 到16k后调用官方计算；短于9.01秒时重复填充、分窗与平均均沿用官方脚本。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## dnsmos_bak_raw

DNSMOS BAK_raw

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('dnsmos_bak_raw', ...)`；模型家族 `dnsmos`，选择输出 `BAK_raw`。
- 来源：https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS。
- 参数与口径：默认非 personalized 模型。SIG/BAK/OVRL 是多项式校准后预测，另保留三个 raw 头与独立 P808_MOS。soxr HQ 到16k后调用官方计算；短于9.01秒时重复填充、分窗与平均均沿用官方脚本。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## dnsmos_ovrl_raw

DNSMOS OVRL_raw

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('dnsmos_ovrl_raw', ...)`；模型家族 `dnsmos`，选择输出 `OVRL_raw`。
- 来源：https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS。
- 参数与口径：默认非 personalized 模型。SIG/BAK/OVRL 是多项式校准后预测，另保留三个 raw 头与独立 P808_MOS。soxr HQ 到16k后调用官方计算；短于9.01秒时重复填充、分窗与平均均沿用官方脚本。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## nisqa_mos

NISQA Overall quality

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_rating`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('nisqa_mos', ...)`；模型家族 `nisqa`，选择输出 `mos`。
- 来源：https://github.com/gabrielmittag/NISQA。
- 参数与口径：多维 nisqa.tar：MOS、NOI、DIS、COL、LOUD 都是质量评分，NOI 越高表示噪声问题越少，不是噪声能量越大。MOS-only/TTS 权重不冒充五维模型。内部特征与时间池化由原始 NISQA 实现负责。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## nisqa_noi

NISQA Noisiness quality

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_rating`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('nisqa_noi', ...)`；模型家族 `nisqa`，选择输出 `noi`。
- 来源：https://github.com/gabrielmittag/NISQA。
- 参数与口径：多维 nisqa.tar：MOS、NOI、DIS、COL、LOUD 都是质量评分，NOI 越高表示噪声问题越少，不是噪声能量越大。MOS-only/TTS 权重不冒充五维模型。内部特征与时间池化由原始 NISQA 实现负责。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## nisqa_dis

NISQA Discontinuity quality

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_rating`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('nisqa_dis', ...)`；模型家族 `nisqa`，选择输出 `dis`。
- 来源：https://github.com/gabrielmittag/NISQA。
- 参数与口径：多维 nisqa.tar：MOS、NOI、DIS、COL、LOUD 都是质量评分，NOI 越高表示噪声问题越少，不是噪声能量越大。MOS-only/TTS 权重不冒充五维模型。内部特征与时间池化由原始 NISQA 实现负责。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## nisqa_col

NISQA Coloration quality

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_rating`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('nisqa_col', ...)`；模型家族 `nisqa`，选择输出 `col`。
- 来源：https://github.com/gabrielmittag/NISQA。
- 参数与口径：多维 nisqa.tar：MOS、NOI、DIS、COL、LOUD 都是质量评分，NOI 越高表示噪声问题越少，不是噪声能量越大。MOS-only/TTS 权重不冒充五维模型。内部特征与时间池化由原始 NISQA 实现负责。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## nisqa_loud

NISQA Loudness quality

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_rating`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('nisqa_loud', ...)`；模型家族 `nisqa`，选择输出 `loud`。
- 来源：https://github.com/gabrielmittag/NISQA。
- 参数与口径：多维 nisqa.tar：MOS、NOI、DIS、COL、LOUD 都是质量评分，NOI 越高表示噪声问题越少，不是噪声能量越大。MOS-only/TTS 权重不冒充五维模型。内部特征与时间池化由原始 NISQA 实现负责。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## utmos

UTMOS22 strong

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('utmos', ...)`；模型家族 `utmos`，选择输出 `mos`。
- 来源：https://github.com/tarepan/SpeechMOS。
- 参数与口径：使用 SpeechMOS 转换的 UTMOS22 strong，保留原始时间平均与 2*x+3 映射；不是 UTMOSv2。权重及源代码 SHA 固定，原生 torchaudio 重采样。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。

## sheet_ssqa

SHEET SSL-MOS (model/config must be identified)

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('sheet_ssqa', ...)`；模型家族 `sheet_ssqa`，选择输出 `mos`。
- 来源：https://github.com/unilight/sheet。
- 参数与口径：SHEET 是工具箱，这里验证的是 all7-sslmos-mdf-2337 checkpoint-86000steps、mean_net 模式。配置文件、SSL 权重与 MOS 权重共同固定模型身份；不声称其他所有 SHEET 模型均已验收。soxr HQ 到16k，原始 Predictor 接受 tensor。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。

## speaker_similarity

RawNet3 embedding cosine

- 主分类：`speaker_identity`；参考条件：speaker_reference。
- 方向：`higher_is_better`；单位：`cosine`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('speaker_similarity', ...)`；模型家族 `speaker_similarity`，选择输出 `cosine`。
- 来源：https://huggingface.co/espnet/voxcelebs12_rawnet3。
- 参数与口径：ESPnet voxcelebs12 RawNet3，16k，输出嵌入余弦；理论范围[-1,1]，不截为[0,1]，不能直接当说话人识别准确率或 EER。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 语义性质：相同音频的相似度为1或参考距离为0，容差1e-5。

## phoneme_similarity

1 minus character edit rate of decoded IPA (not PER)

- 主分类：`content_similarity`；参考条件：matching_waveform。
- 方向：`higher_is_better`；单位：`ratio`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('phoneme_similarity', ...)`；模型家族 `phoneme_similarity`，选择输出 `similarity`。
- 来源：https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft。
- 参数与口径：复现旧评测定义：wav2vec2 预测 IPA 字符串，去空格后按 Unicode 字符算 1-edit/N。不是音素 token PER，可能为负数，不裁剪到0。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 语义性质：相同音频的相似度为1或参考距离为0，容差1e-5。

## visqol_speech

ViSQOL speech 16 kHz

- 主分类：`perceptual_quality`；参考条件：aligned_waveform。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('visqol_speech', ...)`；模型家族 `visqol_speech`，选择输出 `mos`。
- 来源：https://github.com/google/visqol。
- 参数与口径：speech 16k 使用 lattice TFLite，audio 48k 使用 SVR。soxr HQ、PCM16、严格同长度同原始采样率；不暗中裁剪或峰值归一。输入幅值必须在[-1,1]。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。

## visqol_audio

ViSQOL audio 48 kHz

- 主分类：`perceptual_quality`；参考条件：aligned_waveform。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('visqol_audio', ...)`；模型家族 `visqol_audio`，选择输出 `mos`。
- 来源：https://github.com/google/visqol。
- 参数与口径：speech 16k 使用 lattice TFLite，audio 48k 使用 SVR。soxr HQ、PCM16、严格同长度同原始采样率；不暗中裁剪或峰值归一。输入幅值必须在[-1,1]。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。

## speechbert_precision

SpeechBERTScore precision; HuBERT layer 8 default

- 主分类：`content_similarity`；参考条件：matching_waveform。
- 方向：`higher_is_better`；单位：`cosine`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('speechbert_precision', ...)`；模型家族 `speechbert`，选择输出 `precision`。
- 来源：https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics。
- 参数与口径：HuBERT base、hidden layer 8，原始 SpeechBERTScore 的逐帧最大余弦匹配。分别返回 precision、recall、调和 F1，不只返回 precision。不是逐时间点对齐误差。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 语义性质：相同音频的相似度为1或参考距离为0，容差1e-5。

## speechbert_recall

SpeechBERTScore recall; HuBERT layer 8 default

- 主分类：`content_similarity`；参考条件：matching_waveform。
- 方向：`higher_is_better`；单位：`cosine`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('speechbert_recall', ...)`；模型家族 `speechbert`，选择输出 `recall`。
- 来源：https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics。
- 参数与口径：HuBERT base、hidden layer 8，原始 SpeechBERTScore 的逐帧最大余弦匹配。分别返回 precision、recall、调和 F1，不只返回 precision。不是逐时间点对齐误差。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 语义性质：相同音频的相似度为1或参考距离为0，容差1e-5。

## speechbert_f1

SpeechBERTScore f1; HuBERT layer 8 default

- 主分类：`content_similarity`；参考条件：matching_waveform。
- 方向：`higher_is_better`；单位：`cosine`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('speechbert_f1', ...)`；模型家族 `speechbert`，选择输出 `f1`。
- 来源：https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics。
- 参数与口径：HuBERT base、hidden layer 8，原始 SpeechBERTScore 的逐帧最大余弦匹配。分别返回 precision、recall、调和 F1，不只返回 precision。不是逐时间点对齐误差。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 语义性质：相同音频的相似度为1或参考距离为0，容差1e-5。

## whisper_wer

Whisper ASR WER against ground-truth text

- 主分类：`recognition`；参考条件：transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('whisper_wer', ...)`；模型家族 `whisper_wer`，选择输出 `wer`。
- 来源：https://github.com/huggingface/transformers。
- 参数与口径：Whisper large-v3，英语，beam=5，无采样，片段<=30s。WER 对人工文本，dWER 对干净音频的 ASR 文本。Whisper EnglishTextNormalizer({}) 后使用共享清洗与 MeetEval。测试音频文本 fixture 仅检查接口，不作为真实 ASR 水平结论。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。

## whisper_dwer

Whisper ASR WER against ASR transcript of clean reference; not ground-truth WER

- 主分类：`recognition`；参考条件：matching_waveform。
- 方向：`lower_is_better`；单位：`percent`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('whisper_dwer', ...)`；模型家族 `whisper_dwer`，选择输出 `wer`。
- 来源：https://github.com/huggingface/transformers。
- 参数与口径：Whisper large-v3，英语，beam=5，无采样，片段<=30s。WER 对人工文本，dWER 对干净音频的 ASR 文本。Whisper EnglishTextNormalizer({}) 后使用共享清洗与 MeetEval。测试音频文本 fixture 仅检查接口，不作为真实 ASR 水平结论。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。

## orcwer

orcwer

- 主分类：`recognition`；参考条件：speaker_transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：multispeaker_asr。
- 调用：`run('orcwer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## tcorcwer

tcorcwer

- 主分类：`recognition`；参考条件：speaker_transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：multispeaker_asr。
- 调用：`run('tcorcwer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## mimower

mimower

- 主分类：`recognition`；参考条件：speaker_transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：multispeaker_asr。
- 调用：`run('mimower', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## tcmimower

tcmimower

- 主分类：`recognition`；参考条件：speaker_transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：multispeaker_asr。
- 调用：`run('tcmimower', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## greedy_dicpwer

greedy_dicpwer

- 主分类：`recognition`；参考条件：speaker_transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：multispeaker_asr。
- 调用：`run('greedy_dicpwer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## greedy_ditcpwer

greedy_ditcpwer

- 主分类：`recognition`；参考条件：speaker_transcript。
- 方向：`lower_is_better`；单位：`percent`；任务标签：multispeaker_asr。
- 调用：`run('greedy_ditcpwer', ...)`。
- 来源：https://github.com/fgnt/meeteval。
- 参数与口径：MeetEval 0.4.3；归一化、参考单位、录音级重排、时间插值与容差必须同时记录。ORC允许utterance重分配，MIMO与cp有不同结构约束；DI前缀明确为greedy算法，不声称是精确最优。中文用CER，TS固定目标，不按参考挑最好通道。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## bss_sdr

bss_sdr

- 主分类：`signal_fidelity`；参考条件：aligned_multisource_waveform。
- 方向：`higher_is_better`；单位：`dB`；任务标签：separation, tse。
- 调用：`run('bss_sdr', ...)`。
- 来源：https://github.com/fakufaku/fast_bss_eval。
- 参数与口径：SI-SDR采用fast-bss-eval，zero_mean=True；SI-SDRi再减同一clean-reference与mixture的SI-SDR。BSS SDR/SIR/SAR默认512点滤波、zero_mean=False、由上游选择排列；必须提供完整[source,samples]矩阵。非有限完美分数显式标记。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## bss_sir

bss_sir

- 主分类：`signal_fidelity`；参考条件：aligned_multisource_waveform。
- 方向：`higher_is_better`；单位：`dB`；任务标签：separation, tse。
- 调用：`run('bss_sir', ...)`。
- 来源：https://github.com/fakufaku/fast_bss_eval。
- 参数与口径：SI-SDR采用fast-bss-eval，zero_mean=True；SI-SDRi再减同一clean-reference与mixture的SI-SDR。BSS SDR/SIR/SAR默认512点滤波、zero_mean=False、由上游选择排列；必须提供完整[source,samples]矩阵。非有限完美分数显式标记。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## bss_sar

bss_sar

- 主分类：`signal_fidelity`；参考条件：aligned_multisource_waveform。
- 方向：`higher_is_better`；单位：`dB`；任务标签：separation, tse。
- 调用：`run('bss_sar', ...)`。
- 来源：https://github.com/fakufaku/fast_bss_eval。
- 参数与口径：SI-SDR采用fast-bss-eval，zero_mean=True；SI-SDRi再减同一clean-reference与mixture的SI-SDR。BSS SDR/SIR/SAR默认512点滤波、zero_mean=False、由上游选择排列；必须提供完整[source,samples]矩阵。非有限完美分数显式标记。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## plcc

plcc

- 主分类：`rating_agreement`；参考条件：paired_subjective_ratings。
- 方向：`higher_is_better`；单位：`correlation`；任务标签：quality_prediction。
- 调用：`run('plcc', ...)`。
- 来源：https://docs.scipy.org/doc/scipy/reference/stats.html。
- 参数与口径：SciPy直接计算原始配对评分：PLCC=Pearson，SRCC=Spearman，Kendall=tau-b。>=3对、有限、非恒定；不做隐式非线性拟合，不平均相关系数。p值仅是上游检验输出，不能替代对实验独立性假设的检查。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## srcc

srcc

- 主分类：`rating_agreement`；参考条件：paired_subjective_ratings。
- 方向：`higher_is_better`；单位：`correlation`；任务标签：quality_prediction。
- 调用：`run('srcc', ...)`。
- 来源：https://docs.scipy.org/doc/scipy/reference/stats.html。
- 参数与口径：SciPy直接计算原始配对评分：PLCC=Pearson，SRCC=Spearman，Kendall=tau-b。>=3对、有限、非恒定；不做隐式非线性拟合，不平均相关系数。p值仅是上游检验输出，不能替代对实验独立性假设的检查。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## ktau

ktau

- 主分类：`rating_agreement`；参考条件：paired_subjective_ratings。
- 方向：`higher_is_better`；单位：`correlation`；任务标签：quality_prediction。
- 调用：`run('ktau', ...)`。
- 来源：https://docs.scipy.org/doc/scipy/reference/stats.html。
- 参数与口径：SciPy直接计算原始配对评分：PLCC=Pearson，SRCC=Spearman，Kendall=tau-b。>=3对、有限、非恒定；不做隐式非线性拟合，不平均相关系数。p值仅是上游检验输出，不能替代对实验独立性假设的检查。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## vad_error

vad_error

- 主分类：`speech_activity`；参考条件：speaker_annotation。
- 方向：`lower_is_better`；单位：`percent`；任务标签：vad, diarization。
- 调用：`run('vad_error', ...)`。
- 来源：https://github.com/pyannote/pyannote-metrics。
- 参数与口径：用pyannote.metrics计算时间覆盖分量；不考虑说话人标签身份。UEM、collar、overlap策略必须明确。micro按持续时间分量累计。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## vad_precision

vad_precision

- 主分类：`speech_activity`；参考条件：speaker_annotation。
- 方向：`higher_is_better`；单位：`percent`；任务标签：vad, diarization。
- 调用：`run('vad_precision', ...)`。
- 来源：https://github.com/pyannote/pyannote-metrics。
- 参数与口径：用pyannote.metrics计算时间覆盖分量；不考虑说话人标签身份。UEM、collar、overlap策略必须明确。micro按持续时间分量累计。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## vad_recall

vad_recall

- 主分类：`speech_activity`；参考条件：speaker_annotation。
- 方向：`higher_is_better`；单位：`percent`；任务标签：vad, diarization。
- 调用：`run('vad_recall', ...)`。
- 来源：https://github.com/pyannote/pyannote-metrics。
- 参数与口径：用pyannote.metrics计算时间覆盖分量；不考虑说话人标签身份。UEM、collar、overlap策略必须明确。micro按持续时间分量累计。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## vad_accuracy

vad_accuracy

- 主分类：`speech_activity`；参考条件：speaker_annotation。
- 方向：`higher_is_better`；单位：`percent`；任务标签：vad, diarization。
- 调用：`run('vad_accuracy', ...)`。
- 来源：https://github.com/pyannote/pyannote-metrics。
- 参数与口径：用pyannote.metrics计算时间覆盖分量；不考虑说话人标签身份。UEM、collar、overlap策略必须明确。micro按持续时间分量累计。
- 验证：实际标准库调用；解析fixture或独立上游数值对照。

## scoreq

Deprecated alias for scoreq_natural_ref; use explicit metric ID

- 主分类：`perceptual_quality`；参考条件：nonmatching_waveform, matching_waveform。
- 方向：`lower_is_better`；单位：`embedding_distance`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('scoreq', ...)`；模型家族 `scoreq_natural_ref`，选择输出 `score`。
- 来源：https://github.com/alessandroragano/scoreq。
- 参数与口径：必须选 natural/synthetic 和 nr/ref 对应权重。NR 输出预测 MOS，REF 输出欧氏距离。natural REF 支持 matching/nonmatching；synthetic REF profile 使用 nonmatching。显式参考条件与模型权重共同确定实验口径。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。
- 兼容别名：新实验请使用 `scoreq_natural_ref`。

## dnsmos

Deprecated alias for dnsmos_ovrl; use explicit metric ID

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('dnsmos', ...)`；模型家族 `dnsmos`，选择输出 `OVRL`。
- 来源：https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS。
- 参数与口径：默认非 personalized 模型。SIG/BAK/OVRL 是多项式校准后预测，另保留三个 raw 头与独立 P808_MOS。soxr HQ 到16k后调用官方计算；短于9.01秒时重复填充、分窗与平均均沿用官方脚本。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。
- 兼容别名：新实验请使用 `dnsmos_ovrl`。

## nisqa

Deprecated alias for nisqa_mos; use explicit metric ID

- 主分类：`perceptual_quality`；参考条件：none。
- 方向：`higher_is_better`；单位：`predicted_rating`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('nisqa', ...)`；模型家族 `nisqa`，选择输出 `mos`。
- 来源：https://github.com/gabrielmittag/NISQA。
- 参数与口径：多维 nisqa.tar：MOS、NOI、DIS、COL、LOUD 都是质量评分，NOI 越高表示噪声问题越少，不是噪声能量越大。MOS-only/TTS 权重不冒充五维模型。内部特征与时间池化由原始 NISQA 实现负责。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 独立对照：直接初始化上游原生对象，绝对误差 < 1e-5。
- 兼容别名：新实验请使用 `nisqa_mos`。

## speechbert_score

Deprecated alias for speechbert_precision; use explicit metric ID

- 主分类：`content_similarity`；参考条件：matching_waveform。
- 方向：`higher_is_better`；单位：`cosine`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('speechbert_score', ...)`；模型家族 `speechbert`，选择输出 `precision`。
- 来源：https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics。
- 参数与口径：HuBERT base、hidden layer 8，原始 SpeechBERTScore 的逐帧最大余弦匹配。分别返回 precision、recall、调和 F1，不只返回 precision。不是逐时间点对齐误差。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 兼容别名：新实验请使用 `speechbert_precision`。

## visqol

Deprecated alias for visqol_speech; use explicit metric ID

- 主分类：`perceptual_quality`；参考条件：aligned_waveform。
- 方向：`higher_is_better`；单位：`predicted_mos`；任务标签：enhancement, tse, separation, codec, tts, voice_conversion。
- 调用：`run('visqol', ...)`；模型家族 `visqol_speech`，选择输出 `mos`。
- 来源：https://github.com/google/visqol。
- 参数与口径：speech 16k 使用 lattice TFLite，audio 48k 使用 SVR。soxr HQ、PCM16、严格同长度同原始采样率；不暗中裁剪或峰值归一。输入幅值必须在[-1,1]。
- 验证：真实LibriMix语音及可控噪声；短音频/立体声/静音/缺文件全部拒绝，无虚假数值。
- 兼容别名：新实验请使用 `visqol_speech`。

## `speechbert_mhubert_precision`

多语言 SpeechBERTScore precision

| Property | Contract |
|---|---|
| Measurement | content_similarity |
| Reference | matching_waveform |
| Output | cosine; higher_is_better |
| Implementation | DiscreteSpeechMetrics algorithm with utter-project/mHuBERT-147 |
| Source | [Upstream](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) |
| Required | reference and hypothesis audio paths; local mHuBERT-147 model_dir; official DiscreteSpeechMetrics source_dir; layer=8; mono; >=1 second |

Different encoder from HuBERT-base SBS; scores are not interchangeable. Full precision, recall and F1 retained.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `speechbert_mhubert_recall`

多语言 SpeechBERTScore recall

| Property | Contract |
|---|---|
| Measurement | content_similarity |
| Reference | matching_waveform |
| Output | cosine; higher_is_better |
| Implementation | DiscreteSpeechMetrics algorithm with utter-project/mHuBERT-147 |
| Source | [Upstream](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) |
| Required | reference and hypothesis audio paths; local mHuBERT-147 model_dir; official DiscreteSpeechMetrics source_dir; layer=8; mono; >=1 second |

Different encoder from HuBERT-base SBS; scores are not interchangeable. Full precision, recall and F1 retained.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `speechbert_mhubert_f1`

多语言 SpeechBERTScore f1

| Property | Contract |
|---|---|
| Measurement | content_similarity |
| Reference | matching_waveform |
| Output | cosine; higher_is_better |
| Implementation | DiscreteSpeechMetrics algorithm with utter-project/mHuBERT-147 |
| Source | [Upstream](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) |
| Required | reference and hypothesis audio paths; local mHuBERT-147 model_dir; official DiscreteSpeechMetrics source_dir; layer=8; mono; >=1 second |

Different encoder from HuBERT-base SBS; scores are not interchangeable. Full precision, recall and F1 retained.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `speaker_similarity_wavlm`

WavLM-base-plus-SV 说话人余弦相似度

| Property | Contract |
|---|---|
| Measurement | speaker_identity |
| Reference | speaker_reference |
| Output | cosine; higher_is_better |
| Implementation | Transformers WavLMForXVector |
| Source | [Upstream](https://huggingface.co/microsoft/wavlm-base-plus-sv) |
| Required | reference speaker audio and hypothesis audio; local WavLM-base-plus-SV model_dir; mono; >=1 second |

Cosine is in [-1,1], not calibrated probability or EER. Not interchangeable with RawNet3 or WavLM-large ECAPA.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `lps_phone`

LPS 音素 token 相似度

| Property | Contract |
|---|---|
| Measurement | content_similarity |
| Reference | matching_waveform |
| Output | ratio; higher_is_better |
| Implementation | wav2vec2-lv-60-espeak-cv-ft + phone-token Levenshtein |
| Source | [Upstream](https://github.com/urgent-challenge/urgent2026_challenge_track1/blob/main/evaluation_metrics/calculate_phoneme_similarity.py) |
| Required | hypothesis audio file; explicit local deployment config; reference |

1 - edit_distance / reference phone count; may be negative. Different from legacy IPA Unicode-character phoneme_similarity. Empty reference recognition is a failure; model-derived phones are not manual labels.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `plcmos_v2`

PLCMOS v2 final 模型

| Property | Contract |
|---|---|
| Measurement | perceptual_quality |
| Reference | none |
| Output | predicted_mos; higher_is_better |
| Implementation | Microsoft SpeechMOS 0.0.1.1 PLCMOS.get_mos |
| Source | [Upstream](https://pypi.org/project/speechmos/0.0.1.1/) |
| Required | hypothesis audio path; official SpeechMOS plcmos.py source_file; matching local ONNX checkpoint; seed=0; embed_rounds=15; mono; >=1 second; CPU |

Packet-loss-concealment MOS predictor; not established for arbitrary distortions. Final and validation checkpoints have different training/holdout scope. Seeded finite-rater sampling; scores depend on seed and repetition count.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `plcmos_v2_val`

PLCMOS v2 validation 模型

| Property | Contract |
|---|---|
| Measurement | perceptual_quality |
| Reference | none |
| Output | predicted_mos; higher_is_better |
| Implementation | Microsoft SpeechMOS 0.0.1.1 PLCMOS.get_mos |
| Source | [Upstream](https://pypi.org/project/speechmos/0.0.1.1/) |
| Required | hypothesis audio path; official SpeechMOS plcmos.py source_file; matching local ONNX checkpoint; seed=0; embed_rounds=15; mono; >=1 second; CPU |

Packet-loss-concealment MOS predictor; not established for arbitrary distortions. Final and validation checkpoints have different training/holdout scope. Seeded finite-rater sampling; scores depend on seed and repetition count.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `lsd_urgent`

URGENT 增益拟合自然对数谱距离

| Property | Contract |
|---|---|
| Measurement | signal_fidelity |
| Reference | aligned_waveform |
| Output | natural_log_power_ratio; lower_is_better |
| Implementation | librosa STFT |
| Source | [Upstream](https://github.com/urgent-challenge/urgent2025_challenge/tree/main/evaluation_metrics) |
| Required | reference; hypothesis; sample_rate; equal-length finite non-silent mono audio |

Frame, gain, log-base and coefficient conventions are part of the metric ID. MCD uses DTW; neither MCD nor magnitude LSD directly measures timing or phase fidelity.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `lsd_db`

无增益拟合的 dB 谱距离

| Property | Contract |
|---|---|
| Measurement | signal_fidelity |
| Reference | aligned_waveform |
| Output | dB; lower_is_better |
| Implementation | librosa STFT |
| Source | [Upstream](https://github.com/urgent-challenge/urgent2025_challenge/tree/main/evaluation_metrics) |
| Required | reference; hypothesis; sample_rate; equal-length finite non-silent mono audio |

Frame, gain, log-base and coefficient conventions are part of the metric ID. MCD uses DTW; neither MCD nor magnitude LSD directly measures timing or phase fidelity.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `mcd_urgent`

URGENT MCD：增益拟合、含 c0

| Property | Contract |
|---|---|
| Measurement | signal_fidelity |
| Reference | aligned_waveform |
| Output | dB; lower_is_better |
| Implementation | pysptk mcep + fastdtw |
| Source | [Upstream](https://github.com/urgent-challenge/urgent2025_challenge/tree/main/evaluation_metrics) |
| Required | reference; hypothesis; sample_rate; equal-length finite non-silent mono audio |

Frame, gain, log-base and coefficient conventions are part of the metric ID. MCD uses DTW; neither MCD nor magnitude LSD directly measures timing or phase fidelity.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `mcd_dtw_c1`

SPTK MCD：DTW、不含 c0、不拟合增益

| Property | Contract |
|---|---|
| Measurement | signal_fidelity |
| Reference | aligned_waveform |
| Output | dB; lower_is_better |
| Implementation | pysptk mcep + fastdtw |
| Source | [Upstream](https://github.com/urgent-challenge/urgent2025_challenge/tree/main/evaluation_metrics) |
| Required | reference; hypothesis; sample_rate; equal-length finite non-silent mono audio |

Frame, gain, log-base and coefficient conventions are part of the metric ID. MCD uses DTW; neither MCD nor magnitude LSD directly measures timing or phase fidelity.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `aecmos_16k_echo`

微软 aecmos_16k：echo_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `aecmos_16k_deg`

微软 aecmos_16k：deg_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `aecmos_16k_scenarioless_echo`

微软 aecmos_16k_scenarioless：echo_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `aecmos_16k_scenarioless_deg`

微软 aecmos_16k_scenarioless：deg_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `aecmos_48k_echo`

微软 aecmos_48k：echo_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `aecmos_48k_deg`

微软 aecmos_48k：deg_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `erle`

明确远端单讲区间的回声返回损耗增强

- Dimension: `echo_attenuation`; reference: `echo_or_farend_only_microphone`.
- Output: `dB`, `higher_is_better`; scope: `recording`.
- Required: `reference`, `hypothesis`, `sample_rate`, `farend_only_regions`, `signal_definition`.
- [Upstream source](https://www.microsoft.com/en-us/research/publication/aecmos-a-speech-quality-assessment-metric-for-echo-impairment/); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Not defined as an echo-only measure during double-talk. Microphone-based ERLE includes noise; label this signal definition explicitly. Batches pool energies, not per-recording dB. Zero residual returns infinite_result and null.

## `eer`

并列分数组合后的插值等错误率

- Dimension: `speaker_identity`; reference: `trial_labels`.
- Output: `percent`, `lower_is_better`; scope: `dataset`.
- Required: `scores`, `labels`.
- [Upstream source](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Whole trial list, both classes required; never average per-utterance EER/minDCF. Labels 1=target and 0=nontarget. Score direction is explicit. Ties share one operating point. EER uses linear ROC interpolation, which can differ from closest empirical-point conventions.

## `min_dcf`

显式先验下的最小检测代价

- Dimension: `speaker_identity`; reference: `trial_labels`.
- Output: `normalized_cost_or_cost`, `lower_is_better`; scope: `dataset`.
- Required: `scores`, `labels`, `p_target`.
- [Upstream source](https://www.nist.gov/document/nistsre10evalplan-r6pdf); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Whole trial list, both classes required; never average per-utterance EER/minDCF. Labels 1=target and 0=nontarget. Score direction is explicit. Ties share one operating point. Default costs 1/1; normalized=True. p_target is mandatory; minDCF is an oracle sweep, not deployment-threshold actual DCF.
