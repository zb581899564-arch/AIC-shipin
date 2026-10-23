"""Inference port of the frozen author's ROI/ROD forward kernels.

Preserves the legacy +1 endpoint, extrapolation at the last pixel, inclusive
discard mask, and (height-1.001) grid. Modern ROIAlign is not substituted.
"""
import torch
from torch import nn
from torch.nn import functional as F


def _validate(features, rois, height, width):
    if features.ndim != 4 or min(features.shape[-2:]) < 2 or rois.ndim != 2 or rois.shape[1] != 5:
        raise ValueError('Legacy alignment requires NCHW and Kx5 ROIs')
    if features.dtype != torch.float32 or rois.dtype != torch.float32 or features.device != rois.device:
        raise ValueError('Original alignment is float32 on one device')
    if height < 2 or width < 2 or not torch.isfinite(rois).all():
        raise ValueError('Finite ROI and at least2x2 sampling grid required')
    batch = rois[:, 0]
    if not ((batch == batch.floor()) & (batch >= 0) & (batch < features.shape[0])).all():
        raise ValueError('Invalid ROI batch identity')


def _sample(features, batch, y, x):
    count, channels = len(batch), features.shape[1]
    h, w = features.shape[-2:]
    yy, xx = torch.broadcast_tensors(y[:, :, None], x[:, None, :])
    valid = (yy >= 0) & (yy < h) & (xx >= 0) & (xx < w)
    top = yy.floor().long().clamp(0, h - 2)
    left = xx.floor().long().clamp(0, w - 2)
    dy, dx = (yy - top).reshape(count, 1, -1), (xx - left).reshape(count, 1, -1)
    source = features[batch].reshape(count, channels, h * w)

    def gather(offset):
        index = (top * w + left + offset).reshape(count, 1, -1).expand(count, channels, -1)
        return source.gather(2, index)

    values = (gather(0) * (1 - dy) * (1 - dx) + gather(1) * (1 - dy) * dx +
              gather(w) * dy * (1 - dx) + gather(w + 1) * dy * dx)
    return values.reshape(count, channels, yy.shape[1], yy.shape[2]), valid, yy, xx


def legacy_align(features, rois, aligned_height, aligned_width, spatial_scale, mode):
    _validate(features, rois, aligned_height, aligned_width)
    if mode not in ('roi', 'rod'):
        raise ValueError('Unknown original alignment mode')
    count = rois.shape[0]
    if count == 0:
        return features.new_empty((0, features.shape[1], aligned_height, aligned_width))
    bounds = rois[:, 1:] * spatial_scale
    rows = torch.arange(aligned_height, device=features.device, dtype=torch.float32)
    columns = torch.arange(aligned_width, device=features.device, dtype=torch.float32)
    if mode == 'roi':
        y = bounds[:, 1, None] + rows * ((bounds[:, 3] - bounds[:, 1] + 1).clamp_min(0) / (aligned_height - 1))[:, None]
        x = bounds[:, 0, None] + columns * ((bounds[:, 2] - bounds[:, 0] + 1).clamp_min(0) / (aligned_width - 1))[:, None]
    else:
        step_y = features.new_tensor(features.shape[-2] - 1.001) / (aligned_height - 1)
        step_x = features.new_tensor(features.shape[-1] - 1.001) / (aligned_width - 1)
        y = (rows * step_y).expand(count, -1)
        x = (columns * step_x).expand(count, -1)
    output, valid, yy, xx = _sample(features, rois[:, 0].long(), y, x)
    if mode == 'rod':
        inside = ((yy >= bounds[:, 1, None, None]) & (yy <= bounds[:, 3, None, None]) &
                  (xx >= bounds[:, 0, None, None]) & (xx <= bounds[:, 2, None, None]))
        valid = valid & ~inside
    return output * valid[:, None]


class LegacyAlign(nn.Module):
    def __init__(self, height, width, scale, mode, average=False):
        super().__init__()
        self.height, self.width, self.scale = int(height), int(width), float(scale)
        self.mode, self.average = mode, average

    def forward(self, features, rois):
        extra = int(self.average)
        output = legacy_align(features, rois, self.height + extra, self.width + extra, self.scale, self.mode)
        return F.avg_pool2d(output, 2, 1) if self.average else output
