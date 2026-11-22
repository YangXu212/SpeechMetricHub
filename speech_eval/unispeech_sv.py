"""Microsoft UniSpeech WavLM-Large ECAPA-TDNN speaker embedding extractor.

Adapted from the public Microsoft UniSpeech speaker verification recipe
(https://github.com/microsoft/UniSpeech/tree/main/downstreams/speaker_verification)
and ECAPA-TDNN backbone (https://github.com/lawlict/ECAPA-TDNN). No weights are
bundled or downloaded; both the WavLM-Large SSL checkpoint and the fine-tuned
ECAPA-TDNN checkpoint must be provisioned locally.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class Res2Conv1dReluBn(nn.Module):
    def __init__(
        self,
        channels: int,
        kernel_size: int = 1,
        stride: int = 1,
        padding: int = 0,
        dilation: int = 1,
        bias: bool = True,
        scale: int = 4,
    ):
        super().__init__()
        if channels % scale != 0:
            raise ValueError(f"channels ({channels}) must be divisible by scale ({scale})")
        self.scale = scale
        self.width = channels // scale
        self.nums = scale if scale == 1 else scale - 1
        self.convs = nn.ModuleList(
            [
                nn.Conv1d(
                    self.width,
                    self.width,
                    kernel_size,
                    stride,
                    padding,
                    dilation,
                    bias=bias,
                )
                for _ in range(self.nums)
            ]
        )
        self.bns = nn.ModuleList([nn.BatchNorm1d(self.width) for _ in range(self.nums)])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = []
        spx = torch.split(x, self.width, 1)
        sp = spx[0]
        for i in range(self.nums):
            sp = spx[i] if i == 0 else sp + spx[i]
            sp = self.bns[i](F.relu(self.convs[i](sp)))
            out.append(sp)
        if self.scale != 1:
            out.append(spx[self.nums])
        return torch.cat(out, dim=1)


class Conv1dReluBn(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 1,
        stride: int = 1,
        padding: int = 0,
        dilation: int = 1,
        bias: bool = True,
    ):
        super().__init__()
        self.conv = nn.Conv1d(
            in_channels, out_channels, kernel_size, stride, padding, dilation, bias=bias
        )
        self.bn = nn.BatchNorm1d(out_channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.bn(F.relu(self.conv(x)))


class SEConnect(nn.Module):
    def __init__(self, channels: int, se_bottleneck_dim: int = 128):
        super().__init__()
        self.linear1 = nn.Linear(channels, se_bottleneck_dim)
        self.linear2 = nn.Linear(se_bottleneck_dim, channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = x.mean(dim=2)
        out = F.relu(self.linear1(out))
        out = torch.sigmoid(self.linear2(out))
        return x * out.unsqueeze(2)


class SERes2Block(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        stride: int,
        padding: int,
        dilation: int,
        scale: int,
        se_bottleneck_dim: int,
    ):
        super().__init__()
        self.Conv1dReluBn1 = Conv1dReluBn(in_channels, out_channels, kernel_size=1, padding=0)
        self.Res2Conv1dReluBn = Res2Conv1dReluBn(
            out_channels, kernel_size, stride, padding, dilation, scale=scale
        )
        self.Conv1dReluBn2 = Conv1dReluBn(out_channels, out_channels, kernel_size=1, padding=0)
        self.SE_Connect = SEConnect(out_channels, se_bottleneck_dim)
        self.shortcut = (
            nn.Conv1d(in_channels=in_channels, out_channels=out_channels, kernel_size=1)
            if in_channels != out_channels
            else None
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.shortcut(x) if self.shortcut is not None else x
        x = self.Conv1dReluBn1(x)
        x = self.Res2Conv1dReluBn(x)
        x = self.Conv1dReluBn2(x)
        x = self.SE_Connect(x)
        return x + residual


class AttentiveStatsPool(nn.Module):
    def __init__(
        self, in_dim: int, attention_channels: int = 128, global_context_att: bool = False
    ):
        super().__init__()
        self.global_context_att = global_context_att
        in_channels = in_dim * 3 if global_context_att else in_dim
        self.linear1 = nn.Conv1d(in_channels, attention_channels, kernel_size=1)
        self.linear2 = nn.Conv1d(attention_channels, in_dim, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.global_context_att:
            context_mean = torch.mean(x, dim=-1, keepdim=True).expand_as(x)
            context_std = torch.sqrt(torch.var(x, dim=-1, keepdim=True) + 1e-10).expand_as(x)
            x_in = torch.cat((x, context_mean, context_std), dim=1)
        else:
            x_in = x
        alpha = torch.tanh(self.linear1(x_in))
        alpha = torch.softmax(self.linear2(alpha), dim=2)
        mean = torch.sum(alpha * x, dim=2)
        residuals = torch.sum(alpha * (x**2), dim=2) - mean**2
        std = torch.sqrt(residuals.clamp(min=1e-9))
        return torch.cat([mean, std], dim=1)


class UniSpeechWavLMEcapa(nn.Module):
    """ECAPA-TDNN-SMALL head over frozen/fine-tuned S3PRL WavLM-Large hidden states."""

    def __init__(
        self,
        feature_extract: nn.Module,
        *,
        feat_dim: int = 1024,
        channels: int = 512,
        emb_dim: int = 256,
        sr: int = 16000,
        feature_selection: str = "hidden_states",
        global_context_att: bool = False,
    ):
        super().__init__()
        self.sr = sr
        self.feature_selection = feature_selection
        self.feature_extract = feature_extract
        self.feat_num = self._probe_feat_num()
        self.feature_weight = nn.Parameter(torch.zeros(self.feat_num))
        self.instance_norm = nn.InstanceNorm1d(feat_dim)
        self.channels = [channels] * 4 + [1536]
        self.layer1 = Conv1dReluBn(feat_dim, self.channels[0], kernel_size=5, padding=2)
        self.layer2 = SERes2Block(
            self.channels[0],
            self.channels[1],
            kernel_size=3,
            stride=1,
            padding=2,
            dilation=2,
            scale=8,
            se_bottleneck_dim=128,
        )
        self.layer3 = SERes2Block(
            self.channels[1],
            self.channels[2],
            kernel_size=3,
            stride=1,
            padding=3,
            dilation=3,
            scale=8,
            se_bottleneck_dim=128,
        )
        self.layer4 = SERes2Block(
            self.channels[2],
            self.channels[3],
            kernel_size=3,
            stride=1,
            padding=4,
            dilation=4,
            scale=8,
            se_bottleneck_dim=128,
        )
        self.conv = nn.Conv1d(channels * 3, self.channels[-1], kernel_size=1)
        self.pooling = AttentiveStatsPool(
            self.channels[-1], attention_channels=128, global_context_att=global_context_att
        )
        self.bn = nn.BatchNorm1d(self.channels[-1] * 2)
        self.linear = nn.Linear(self.channels[-1] * 2, emb_dim)

    def _probe_feat_num(self) -> int:
        self.feature_extract.eval()
        params = list(self.feature_extract.parameters())
        device = params[0].device if params else torch.device("cpu")
        with torch.no_grad():
            features = self.feature_extract([torch.zeros(self.sr, device=device)])
        selected = features[self.feature_selection]
        return len(selected) if isinstance(selected, (list, tuple)) else 1

    def get_feat(self, x: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            feats = self.feature_extract([sample for sample in x])[self.feature_selection]
        stacked = torch.stack(feats, dim=0) if isinstance(feats, (list, tuple)) else feats[None]
        weights = F.softmax(self.feature_weight, dim=-1).view(-1, 1, 1, 1)
        weighted = (weights * stacked).sum(dim=0).transpose(1, 2) + 1e-6
        return self.instance_norm(weighted)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.get_feat(x)
        out1 = self.layer1(feat)
        out2 = self.layer2(out1)
        out3 = self.layer3(out2)
        out4 = self.layer4(out3)
        cat = torch.cat([out2, out3, out4], dim=1)
        out = F.relu(self.conv(cat))
        out = self.bn(self.pooling(out))
        return self.linear(out)


def load_unispeech_wavlm_model(ssl_checkpoint: str, checkpoint: str, *, device: str = "cpu"):
    """Load WavLM-Large upstream and fine-tuned UniSpeech ECAPA-TDNN weights."""
    from s3prl.upstream.wavlm.expert import UpstreamExpert as WavLMUpstream

    upstream = WavLMUpstream(ssl_checkpoint)
    model = UniSpeechWavLMEcapa(upstream, feat_dim=1024, channels=512, emb_dim=256, sr=16000)
    raw = torch.load(checkpoint, map_location="cpu", weights_only=False)
    state = raw["model"] if isinstance(raw, dict) and "model" in raw else raw
    missing, _ = model.load_state_dict(state, strict=False)
    if missing:
        raise ValueError(f"UniSpeech WavLM checkpoint is missing model keys: {missing[:5]}")
    model = model.to(device).eval()
    for param in model.parameters():
        param.requires_grad = False
    return model
