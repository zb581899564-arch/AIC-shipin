"""Invert the installed processor's documented patch ordering, not its resize."""
import torch


def unpack(pixels, grid, patch=16, temporal=2, merge=2):
    gt, gh, gw = map(int, grid)
    assert pixels.shape == (gt * gh * gw, 3 * temporal * patch * patch)
    shaped = pixels.reshape(gt, gh // merge, gw // merge, merge, merge, 3, temporal, patch, patch)
    return shaped.permute(0, 6, 5, 1, 3, 7, 2, 4, 8).reshape(gt * temporal, 3, gh * patch, gw * patch)


def pack(frames, grid, patch=16, temporal=2, merge=2):
    gt, gh, gw = map(int, grid)
    shaped = frames.reshape(gt, temporal, 3, gh // merge, merge, patch, gw // merge, merge, patch)
    return shaped.permute(0, 3, 6, 4, 7, 2, 1, 5, 8).reshape(gt * gh * gw, 3 * temporal * patch * patch)


def recover_uint8(pixels, grid, processor):
    normalized = unpack(pixels, grid)
    assert torch.equal(pack(normalized, grid), pixels)
    assert normalized.shape[0] == 2 and torch.equal(normalized[0], normalized[1])
    mean = torch.tensor(processor['image_mean']).reshape(1, 3, 1, 1)
    std = torch.tensor(processor['image_std']).reshape(1, 3, 1, 1)
    scale = processor['rescale_factor']
    values = (normalized * std + mean) / scale
    error = float((values - values.round()).abs().max())
    assert error < 1e-3 and values.min() >= -1e-3 and values.max() <= 255.001
    integers = values.round().to(torch.uint8)
    reconstructed = (integers.float() * scale - mean) / std
    normalize_error = float((reconstructed - normalized).abs().max())
    assert normalize_error < 2e-6
    return integers[0].permute(1, 2, 0).contiguous().numpy(), error, normalize_error
