"""Bounded, immutable source RGB union and one read-only native64 view.

Pure data logic only: no file I/O, decoder, NumPy, processor, model or launcher.
The caller supplies already decoded RGB buffers and a previously bound clock.
Limits count RGB payload bytes, not process RSS or processor/IPC overhead.
Drop derived consumers before leaving view64(); no view may escape its lease.
"""
from bisect import bisect_left
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import re


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _exact(value):
    _require(type(value) in (str, int, Fraction), 'Exact integer/rational PTS required; floats and bools are rejected')
    return Fraction(value)


def _integer(value, minimum, message):
    _require(type(value) is int and value >= minimum, message)
    return value


def _digest(value):
    _require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value), 'Explicit lowercase source/clock/pixel SHA256 required')
    return value


@dataclass(frozen=True)
class SourceIdentity:
    source_sha256: str
    clock_sha256: str
    width: int
    height: int
    total_frames: int

    def __post_init__(self):
        _digest(self.source_sha256); _digest(self.clock_sha256)
        _integer(self.width, 1, 'Positive original width required')
        _integer(self.height, 1, 'Positive original height required')
        _integer(self.total_frames, 1, 'Positive complete-clock frame count required')

    @property
    def frame_rgb_bytes(self):
        return self.width*self.height*3


def payload_requirements(identity, wanted_count, view_copies=1, decode_frame_copies=1):
    """Exact RGB byte arithmetic, excluding Python/decoder/processor/IPC costs.

    A production controller must separately measure/reserve those extra costs
    against current shared resources. This result is never an admission gate.
    """
    _require(isinstance(identity, SourceIdentity), 'Explicit source identity required')
    _integer(wanted_count, 1, 'Positive wanted-ordinal count required')
    _require(wanted_count <= identity.total_frames, 'Wanted union exceeds the complete source')
    _integer(view_copies, 0, 'Nonnegative simultaneous RGB view-copy count required')
    _integer(decode_frame_copies, 0, 'Nonnegative live decoder-frame copy count required')
    frame = identity.frame_rgb_bytes
    return dict(frame_rgb_bytes=frame, union_rgb_bytes=wanted_count*frame, one_native64_rgb_bytes=64*frame,
        requested_view_copy_rgb_bytes=view_copies*64*frame, requested_decode_frame_rgb_bytes=decode_frame_copies*frame,
        combined_rgb_payload_bytes=(wanted_count+64*view_copies+decode_frame_copies)*frame,
        includes_processor_IPC_Python_or_RSS_overhead=False, production_admitted=False)


@dataclass(frozen=True)
class ReadOnly64:
    source: SourceIdentity
    ordinals: tuple
    sample_exact_pts: tuple
    pixel_sha256: tuple
    window_start: str
    window_end: str
    rgb: memoryview

    def metadata(self):
        return dict(source=asdict(self.source), source_frame_ordinals=list(self.ordinals),
            sample_exact_pts=list(self.sample_exact_pts), pixel_sha256=list(self.pixel_sha256),
            window_start=self.window_start, window_end=self.window_end, physical_frames=64,
            shape=[64, self.source.height, self.source.width, 3], dtype='uint8',
            rgb_payload_bytes=self.rgb.nbytes, readonly=self.rgb.readonly, RGB_persisted=False)


class MemoryRGBUnion:
    """One source, one immutable copy per wanted ordinal, one active view lease.

    add_frame accepts a C-contiguous uint8 buffer of shape (height,width,3).
    A NumPy uint8 frame is supported through its buffer protocol; importing
    NumPy is unnecessary. The stored bytes never alias the incoming buffer.
    """

    def __init__(self, identity, full_source_exact_pts, physical_end_exact,
                 wanted_ordinals, *, max_union_rgb_bytes):
        _require(isinstance(identity, SourceIdentity), 'Explicit source identity required')
        self.identity = identity
        self.points = tuple(_exact(point) for point in full_source_exact_pts)
        self.physical_end = _exact(physical_end_exact)
        _require(len(self.points) == identity.total_frames and self.points[0] == 0 and
            all(a < b for a, b in zip(self.points, self.points[1:])) and self.physical_end > self.points[-1],
            'Complete original zero-origin increasing clock and positive physical endpoint required')
        wanted = tuple(wanted_ordinals)
        _require(wanted and all(type(i) is int and 0 <= i < identity.total_frames for i in wanted) and
            len(set(wanted)) == len(wanted), 'Distinct in-domain wanted original ordinals required')
        self.wanted = tuple(sorted(wanted)); self._wanted = frozenset(wanted)
        _integer(max_union_rgb_bytes, 0, 'Explicit nonnegative RGB union byte limit required')
        self.union_rgb_bytes = len(wanted)*identity.frame_rgb_bytes
        _require(self.union_rgb_bytes <= max_union_rgb_bytes, 'Requested source RGB union exceeds the explicit payload allowance')
        self._frames, self._hashes = {}, {}
        self._sealed, self._closed, self._view_active = False, False, False

    def _source(self, source):
        _require(source == self.identity, 'RGB/source/clock/geometry identity differs')
        _require(not self._closed, 'This RAM union has been closed; no implicit recovery')

    def add_frame(self, source, ordinal, exact_pts, rgb, *, expected_pixel_sha256=None):
        self._source(source)
        _require(not self._sealed, 'Sealed successful union cannot be overwritten')
        _require(type(ordinal) is int and ordinal in self._wanted and ordinal not in self._frames,
                 'Unwanted, out-of-domain or duplicate original ordinal')
        _require(_exact(exact_pts) == self.points[ordinal], 'Decoded frame PTS differs from the bound complete clock')
        pixels = memoryview(rgb)
        _require(pixels.format == 'B' and pixels.itemsize == 1 and pixels.ndim == 3 and
            pixels.shape == (source.height, source.width, 3) and pixels.c_contiguous and
            pixels.nbytes == source.frame_rgb_bytes, 'C-contiguous original-size uint8 RGB24 buffer required')
        payload = pixels.tobytes()
        digest = hashlib.sha256(payload).hexdigest()
        if expected_pixel_sha256 is not None:
            _require(digest == _digest(expected_pixel_sha256), 'Actual decoded RGB pixel SHA differs')
        self._frames[ordinal] = payload; self._hashes[ordinal] = digest

    def seal(self):
        self._source(self.identity)
        _require(not self._sealed and set(self._frames) == self._wanted,
                 'Complete exact wanted union required; no missing frames or repeated success')
        _require(sum(map(len, self._frames.values())) == self.union_rgb_bytes, 'Actual RGB union payload size differs')
        self._sealed = True

    def manifest(self):
        self._source(self.identity)
        _require(self._sealed, 'Only a complete sealed original RGB union has a manifest')
        return dict(schema='RECALL_MEMORY_RGB_UNION_V1', source=asdict(self.identity),
            physical_end_exact=str(self.physical_end), union_rgb_payload_bytes=self.union_rgb_bytes,
            items=[dict(ordinal=i, exact_pts=str(self.points[i]), pixel_sha256=self._hashes[i]) for i in self.wanted],
            RGB_persisted=False, independent_processor_QA_completed=False, production_admitted=False)

    @contextmanager
    def view64(self, source, ordinals, sample_exact_pts, window_start, window_end, *, max_view_rgb_bytes):
        """Yield one immutable (64,H,W,3) buffer; no resampling or padding.

        The caller may construct a read-only NumPy view with frombuffer inside
        this context. All such derived RGB consumers must be dropped on exit.
        Persist tensor caches and genuine primary+independent QA receipts before
        closing the source union. This class does not execute or certify QA.
        """
        self._source(source)
        _require(self._sealed and not self._view_active, 'A complete union and no other active RGB view are required')
        start, stop = _exact(window_start), _exact(window_end)
        _require(0 <= start < stop <= self.physical_end and stop-start <= 15, 'Positive original-domain view of at most 15 seconds required')
        selected = tuple(ordinals); samples = tuple(_exact(point) for point in sample_exact_pts)
        _require(len(selected) == len(samples) == 64 and all(type(i) is int and i in self._wanted for i in selected) and
            len(set(selected)) == 64 and all(a < b for a, b in zip(selected, selected[1:])),
            'Exactly 64 ordered distinct wanted native frames required')
        first, limit = bisect_left(self.points, start), bisect_left(self.points, stop)
        _require(limit-first >= 64, 'Fewer than 64 native frames; do not pad or change the window')
        expected = tuple(first+j*(limit-first-1)//63 for j in range(64))
        _require(selected == expected and samples == tuple(self.points[i] for i in selected),
                 'Original first+j*(limit-first-1)//63 native sampling or exact PTS differs')
        _integer(max_view_rgb_bytes, 0, 'Explicit nonnegative view RGB payload allowance required')
        _require(64*source.frame_rgb_bytes <= max_view_rgb_bytes, 'Native64 RGB exceeds the explicit view payload allowance')
        _require(all(hashlib.sha256(self._frames[i]).hexdigest() == self._hashes[i] for i in selected), 'Stored source RGB pixel hash differs')
        self._view_active = True
        pixels = None
        try:
            payload = b''.join(self._frames[i] for i in selected)
            pixels = memoryview(payload).cast('B', shape=(64, source.height, source.width, 3))
            _require(pixels.readonly and pixels.nbytes == 64*source.frame_rgb_bytes, 'Native64 buffer is not immutable RGB24')
            yield ReadOnly64(source, selected, tuple(map(str, samples)), tuple(self._hashes[i] for i in selected),
                             str(start), str(stop), pixels)
        finally:
            if pixels is not None:
                pixels.release()
            self._view_active = False

    def close(self):
        self._source(self.identity)
        _require(not self._view_active, 'Do not release a source while its RGB view is active')
        self._frames.clear(); self._hashes.clear(); self._closed = True
