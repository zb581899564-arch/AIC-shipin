"""Pure mappings from accepted image observations to paired video inputs.

The old occupied-cell index is the time authority. Pairing observations never
adds a native frame or changes its cell boundary, including an odd final cell.
"""
from fractions import Fraction
from numbers import Integral
from typing import Sequence

import numpy as np
import torch


def _integer(value, name: str, minimum: int = 0) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    value = int(value)
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _indices(values, name: str) -> np.ndarray:
    result = np.asarray(values)
    if result.ndim != 1 or (result.size and result.dtype.kind not in "iu"):
        raise ValueError(f"{name} must be a one-dimensional integer sequence")
    if result.size and (np.any(result < 0) or np.any(result > np.iinfo(np.int64).max)):
        raise ValueError(f"{name} must contain nonnegative int64 values")
    return result.astype(np.int64, copy=False)


def pair_image_pixels(
    frames: Sequence[torch.Tensor],
    grid_hw: Sequence[int],
    patch_size: int = 16,
    temporal_patch: int = 2,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Pair accepted image patches without decoding or processing pixels again.

    Each image row is [channel, temporal, patch_y, patch_x] flattened, and its
    two temporal slices must be identical. Video rows use the first slice of
    consecutive images in that same layout. An odd last image is paired with
    itself. The returned int64 video grid has shape (3,): [ceil(N/2), h, w].
    Inputs keep their values, dtype and device; no input tensor is modified.
    """
    patch_size = _integer(patch_size, "patch_size", 1)
    temporal_patch = _integer(temporal_patch, "temporal_patch", 1)
    if temporal_patch != 2:
        raise ValueError("Only the accepted temporal_patch=2 image layout is supported")
    if len(grid_hw) != 2:
        raise ValueError("grid_hw must contain exactly height and width")
    height, width = (_integer(value, "grid dimension", 1) for value in grid_hw)
    if not len(frames):
        raise ValueError("At least one accepted image observation is required")
    expected_shape = (height * width, 3 * temporal_patch * patch_size * patch_size)
    layout = []
    first = frames[0]
    if not isinstance(first, torch.Tensor):
        raise ValueError("Every frame must be a torch.Tensor")
    for frame in frames:
        if not isinstance(frame, torch.Tensor) or tuple(frame.shape) != expected_shape:
            raise ValueError(f"Every image pixel tensor must have shape {expected_shape}")
        if frame.dtype != first.dtype or frame.device != first.device:
            raise ValueError("All image pixels must share dtype and device")
        view = frame.reshape(height * width, 3, 2, patch_size, patch_size)
        if not torch.equal(view[:, :, 0], view[:, :, 1]):
            raise ValueError("Accepted image temporal slices must be exactly equal")
        layout.append(view)
    paired = []
    for index in range(0, len(layout), 2):
        left = layout[index][:, :, 0]
        right = layout[min(index + 1, len(layout) - 1)][:, :, 0]
        paired.append(torch.stack((left, right), dim=2).reshape(expected_shape))
    pixels = torch.cat(paired, dim=0)
    grid = torch.tensor([(len(frames) + 1) // 2, height, width], dtype=torch.int64, device=first.device)
    return pixels, grid


def window_schedule(cell_count: int, window: int = 64, stride: int = 32) -> list[tuple[int, int]]:
    """Return half-open observation windows on fixed even starting indices.

    Stop at the first window reaching the last observation. The last window
    may be short; no shifted ``cell_count - window`` tail is inserted.
    """
    cell_count = _integer(cell_count, "cell_count")
    window = _integer(window, "window", 2)
    stride = _integer(stride, "stride", 2)
    if window % 2 or stride % 2 or stride > window:
        raise ValueError("window and stride must be even, with stride <= window")
    windows = []
    for start in range(0, cell_count, stride):
        end = min(start + window, cell_count)
        windows.append((start, end))
        if end == cell_count:
            break
    return windows


def build_native_groups(old_native_groups, cell_count: int) -> np.ndarray:
    """Map each original native frame to old occupied cell index // 2.

    The old map must be ordered and cover exactly every cell in 0..N-1.
    Repeated labels are expected for native frames in the same cell. The
    returned int64 array has exactly the input native-frame length.
    """
    cell_count = _integer(cell_count, "cell_count")
    old = _indices(old_native_groups, "old_native_groups")
    if old.size and np.any(old[1:] < old[:-1]):
        raise ValueError("Old native groups must follow native-frame order")
    if not np.array_equal(np.unique(old), np.arange(cell_count, dtype=np.int64)):
        raise ValueError("Old native groups must cover every occupied cell exactly as a domain")
    return old // 2


def merge_window_features(windows, group_count: int) -> tuple[np.ndarray, np.ndarray]:
    """Mean overlapping window features by global paired-cell group ID.

    ``windows`` contains (one-dimensional global_group_ids, [rows, features])
    pairs. A group may appear once per window, and must appear in at least one
    window. Accumulation uses float64; output is at least float32 and retains
    float64 inputs. Counts are int64. Empty input is valid only for zero groups.
    """
    group_count = _integer(group_count, "group_count")
    prepared = []
    dimension = None
    dtypes = [np.dtype(np.float32)]
    for group_ids, features in windows:
        ids = _indices(group_ids, "global_group_ids")
        values = np.asarray(features)
        if values.ndim != 2 or values.shape[0] != len(ids) or values.dtype.kind not in "fiu":
            raise ValueError("Each feature array must be real numeric [groups, features]")
        if values.shape[1] < 1 or not np.all(np.isfinite(values)):
            raise ValueError("Features must have a positive dimension and finite values")
        if len(ids) == 0:
            raise ValueError("A feature window cannot be empty")
        if np.any(ids >= group_count) or len(np.unique(ids)) != len(ids):
            raise ValueError("Each window must contain unique in-range global group IDs")
        if dimension is None:
            dimension = values.shape[1]
        elif dimension != values.shape[1]:
            raise ValueError("All windows must share one feature dimension")
        dtypes.append(values.dtype)
        prepared.append((ids, values))
    counts = np.zeros(group_count, dtype=np.int64)
    if dimension is None:
        if group_count:
            raise ValueError("Every global group must have at least one feature")
        return np.empty((0, 0), dtype=np.float32), counts
    sums = np.zeros((group_count, dimension), dtype=np.float64)
    for ids, values in prepared:
        sums[ids] += values
        counts[ids] += 1
    if np.any(counts == 0):
        raise ValueError("Every global group must have at least one feature")
    means = sums / counts[:, None]
    if not np.all(np.isfinite(means)):
        raise ValueError("Merged features must be finite")
    return means.astype(np.result_type(*dtypes)), counts


def group_centers(sample_ordinals, pts, start: int, end: int) -> list[Fraction]:
    """Return exact paired sample-PTS centers for an even-start cell window.

    ``pts`` is the full native-frame clock (Fraction, exact string or integer),
    indexed by the accepted observation ``sample_ordinals``. An odd final
    observation is repeated for its center only. Float clocks are rejected so
    no inferred frame rate or binary float is used as the time authority.
    """
    samples = _indices(sample_ordinals, "sample_ordinals")
    start = _integer(start, "start")
    end = _integer(end, "end")
    if start % 2 or not start <= end <= len(samples):
        raise ValueError("Window must have an even start and lie in sample_ordinals")
    if samples.size and (np.any(samples[1:] <= samples[:-1]) or samples[-1] >= len(pts)):
        raise ValueError("Sample ordinals must be unique, ordered and inside the native clock")
    selected = []
    for ordinal in samples[start:end]:
        value = pts[int(ordinal)]
        if isinstance(value, (bool, np.bool_, float, np.floating)):
            raise ValueError("PTS must use exact fractions, strings or integers")
        try:
            value = Fraction(int(value)) if isinstance(value, Integral) else Fraction(value)
        except (TypeError, ValueError, ZeroDivisionError) as error:
            raise ValueError("Invalid exact native PTS") from error
        selected.append(value)
    if any(value < 0 for value in selected) or any(right <= left for left, right in zip(selected, selected[1:])):
        raise ValueError("Selected native PTS must be nonnegative and strictly increasing")
    return [(selected[index] + selected[min(index + 1, len(selected) - 1)]) / 2
            for index in range(0, len(selected), 2)]
