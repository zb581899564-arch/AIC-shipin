"""PTS-aligned streaming audio DSP; this module never decodes video.

An extraction is an explicit, separately registered operation. Importing this
module only defines functions. Samples are transient: persisted data contain
quarter-second DSP features, validity masks, exact coverage and decode evidence.
The first audio stream by container index is the fixed, label-free stream rule.
"""
from bisect import bisect_right
from fractions import Fraction as F
import datetime as dt
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import traceback
import uuid

import numpy as np


SCHEMA = 'PTS_AUDIO_DSP_V1'
RATE = 16000
BIN = F(1, 4)
FEATURE_NAMES = ('log_rms', 'normalized_positive_spectral_flux', 'positive_log_energy_change')


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def _json_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode('utf8')).hexdigest()


def _clock(clock):
    """Require observed original video PTS, never a container-start estimate."""
    pts = list(map(F, clock['normalized_exact_pts']))
    original = list(map(F, clock.get('original_exact_pts', [])))
    _require(pts and len(original) == len(pts),
             'Audio alignment requires full observed original_exact_pts; no origin fallback')
    origin = original[0]
    _require(pts[0] == 0 and all(a < b for a, b in zip(pts, pts[1:])),
             'Strict normalized native video PTS starting at zero required')
    _require(all(a-b == origin for a, b in zip(original, pts)),
             'Original/normalized video clocks must have one exact observed translation')
    if 'first_original_pts_exact' in clock:
        _require(F(clock['first_original_pts_exact']) == origin,
                 'Observed original video PTS0 fields disagree')
    end = F(clock['physical_end_exact'])
    _require(pts[-1] < end, 'Positive exact final native video frame duration required')
    binding = dict(original_exact_pts=list(map(str, original)),
                   normalized_exact_pts=list(map(str, pts)), physical_end_exact=str(end),
                   source_sha256=clock.get('source_sha256'), source_bytes=clock.get('source_bytes'))
    return pts, origin, end, _json_sha(binding)


def _paths(prefix):
    prefix = Path(prefix)
    return prefix, Path(str(prefix)+'.manifest.json'), Path(str(prefix)+'.features.npz')


def _load(prefix, verify_media=True):
    _, manifest_path, data_path = _paths(prefix)
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    _require(manifest['schema'] == SCHEMA and manifest['status'] == 'COMPLETE',
             'Only complete matching audio caches may be reused')
    _require(manifest['code_sha256'] == _sha(__file__), 'Audio cache code binding changed')
    if verify_media:
        media = Path(manifest['media_ref']['path'])
        _require(media.stat().st_size == manifest['media_ref']['bytes']
                 and _sha(media) == manifest['media_ref']['sha256'],
                 'Audio cache source media size/SHA binding changed')
    binding = manifest['features_ref']
    _require(data_path.stat().st_size == binding['bytes'] and _sha(data_path) == binding['sha256'],
             'Audio feature cache size/SHA binding changed')
    evidence_path = Path(str(prefix)+'.evidence.json.gz')
    binding = manifest['evidence_ref']
    _require(evidence_path.stat().st_size == binding['bytes']
             and _sha(evidence_path) == binding['sha256'],
             'Compressed audio frame evidence size/SHA binding changed')
    with np.load(data_path, allow_pickle=False) as data:
        arrays = {key: data[key].copy() for key in data.files}
    return dict(manifest=manifest, arrays=arrays)


def _append_interval(intervals, start, end):
    if end <= start:
        return
    if intervals and start <= intervals[-1][1]:
        intervals[-1][1] = max(intervals[-1][1], end)
    else:
        intervals.append([start, end])


class _DSP:
    """At most one quarter-second of PCM retained between pushes."""
    def __init__(self, end):
        self.end = end
        self.coverage = []
        self.rows = []
        self.index = None
        self.pieces = []
        self.previous = None
        self.accepted_samples = 0
        self.overlap_samples_discarded = 0

    def _finish_bin(self):
        if not self.pieces:
            return
        runs = []
        for start, values in self.pieces:
            stop = start+F(len(values), RATE)
            if runs and start == runs[-1][1]:
                runs[-1][1] = stop
                runs[-1][2].append(values)
            else:
                runs.append([start, stop, [values]])
        samples = sum(len(v) for _, v in self.pieces)
        squared = sum(float(np.dot(v.astype(np.float64), v)) for _, v in self.pieces)
        energy = math.log(max(math.sqrt(squared/samples), 1e-12))
        spectrum = np.zeros(2049, np.float64)
        for _, _, chunks in runs:
            values = np.concatenate(chunks).astype(np.float64)
            window = np.hanning(len(values)) if len(values) > 2 else np.ones(len(values))
            magnitude = np.abs(np.fft.rfft(values*window, n=4096))
            norm = float(np.linalg.norm(magnitude))
            if norm > 0:
                spectrum += (len(values)/samples)*(magnitude/norm)
        norm = float(np.linalg.norm(spectrum))
        if norm > 0:
            spectrum /= norm
        contiguous = len(runs) == 1
        valid_change = (self.previous is not None and contiguous and self.previous['contiguous']
                        and self.previous['index']+1 == self.index
                        and self.previous['end'] == runs[0][0])
        flux = float(np.linalg.norm(np.maximum(spectrum-self.previous['spectrum'], 0))) if valid_change else 0.
        change = max(energy-self.previous['energy'], 0.) if valid_change else 0.
        self.rows.append((self.index, [energy, flux, change], [True, valid_change, valid_change], samples))
        self.previous = dict(index=self.index, end=runs[-1][1], contiguous=contiguous,
                             spectrum=spectrum, energy=energy)
        self.pieces = []

    def push(self, frame, origin, observed_start, observed_end):
        _require(frame.pts is not None and frame.time_base is not None,
                 'Resampled audio frame lacks actual PTS/time_base')
        _require(frame.sample_rate == RATE, 'Actual resampled audio rate must be16k')
        values = np.asarray(frame.to_ndarray(), dtype=np.float32).reshape(-1)
        _require(len(values) == frame.samples and np.isfinite(values).all(),
                 'Finite mono resampled samples required')
        start = F(frame.pts)*F(frame.time_base)-origin
        lo = max(F(0), observed_start)
        hi = min(self.end, observed_end)
        if self.coverage:
            lo = max(lo, self.coverage[-1][1])
        first = max(0, math.ceil((lo-start)*RATE))
        last = min(len(values), math.floor((hi-start)*RATE))
        self.overlap_samples_discarded += min(len(values), first)
        if last <= first:
            return
        values = values[first:last]
        start += F(first, RATE)
        stop = start+F(len(values), RATE)
        _append_interval(self.coverage, start, stop)
        self.accepted_samples += len(values)
        offset = 0
        while offset < len(values):
            current = start+F(offset, RATE)
            index = int(current//BIN)
            if self.index != index:
                self._finish_bin()
                self.index = index
            count = min(len(values)-offset, math.ceil(((index+1)*BIN-current)*RATE))
            _require(count > 0, 'Positive exact audio bin split')
            self.pieces.append((current, values[offset:offset+count].copy()))
            offset += count

    def arrays(self):
        self._finish_bin()
        bins = math.ceil(self.end/BIN)
        raw = np.zeros((bins, 3), np.float64)
        valid = np.zeros((bins, 3), bool)
        samples = np.zeros(bins, np.int64)
        for index, values, mask, count in self.rows:
            raw[index] = values
            valid[index] = mask
            samples[index] = count
        observed = [F(0) for _ in range(bins)]
        for start, stop in self.coverage:
            for index in range(int(start//BIN), min(bins, math.ceil(stop/BIN))):
                observed[index] += max(F(0), min(stop, (index+1)*BIN)-max(start, index*BIN))
        coverage = np.asarray([float(v/min(BIN, self.end-i*BIN)) for i, v in enumerate(observed)])
        z = np.zeros_like(raw)
        means = np.zeros(3)
        stds = np.ones(3)
        for column in range(3):
            mask = valid[:, column]
            if mask.any():
                weight = np.asarray([float(v) for v in observed])[mask]
                means[column] = np.average(raw[mask, column], weights=weight)
                std = float(np.sqrt(np.average((raw[mask, column]-means[column])**2, weights=weight)))
                stds[column] = std if std > 1e-8 else 1.
                z[mask, column] = (raw[mask, column]-means[column])/stds[column]
        _require(np.isfinite(z).all() and np.all((coverage >= 0) & (coverage <= 1)),
                 'Finite source-only normalized features and bounded observed coverage')
        return (dict(raw=raw, z=z, valid=valid, coverage=coverage, sample_count=samples),
                dict(mean=means.tolist(), std=stds.tolist(), label_free=True,
                     weighting='exact_observed_duration_per_bin'),
                [[i, str(value)] for i, value in enumerate(observed) if value > 0])


def extract_audio(media_path, clock, output_prefix):
    """Decode one fixed audio stream once, or reuse a fully bound success cache.

    Returns ``{'manifest': ..., 'arrays': ...}``. Per-frame evidence is stored in
    ``prefix.evidence.json.gz``; normal cache loading verifies it without inflation.
    Successful absence of any audio
    stream has ``manifest['no_audio'] == True``. Every other extraction failure
    raises and preserves a uniquely named JSON failure; use a new prefix for an
    explicitly registered recovery. Existing partial artifacts are never replaced.
    """
    prefix, manifest_path, data_path = _paths(output_prefix)
    evidence_path = Path(str(prefix)+'.evidence.json.gz')
    prefix.parent.mkdir(parents=True, exist_ok=True)
    evidence = dict(schema=SCHEMA, media_path=str(Path(media_path).resolve()),
                    explicit_video_decode_calls=0, decoded_frames=[], resampled_frames=[])
    try:
        _, origin, end, clock_sha = _clock(clock)
        media = Path(media_path).resolve()
        before = media.stat()
        binding = dict(path=str(media), bytes=before.st_size, sha256=_sha(media))
        _require(clock.get('source_sha256') == binding['sha256']
                 and clock.get('source_bytes') == binding['bytes'],
                 'Observed video clock must bind this exact media source size/SHA')
        code_sha = _sha(__file__)
        evidence.update(media_ref=binding, clock_sha256=clock_sha, original_video_pts0_exact=str(origin))
        if manifest_path.exists():
            cache = _load(prefix, verify_media=False)
            manifest = cache['manifest']
            _require(manifest['media_ref'] == binding and manifest['clock_sha256'] == clock_sha
                     and manifest['code_sha256'] == code_sha,
                     'Completed audio cache does not match current media/clock/code bindings')
            return cache
        _require(not data_path.exists() and not evidence_path.exists()
                 and not list(prefix.parent.glob(prefix.name+'.failure.*.json')),
                 'Incomplete/failed audio prefix requires explicit recovery with a new prefix')
        import av
        dsp = _DSP(end)
        input_coverage = []
        input_gaps = []
        evidence['input_timestamp_discontinuities'] = input_gaps
        raw_samples = 0
        resampled_frames = 0
        resampled_samples = 0
        previous_start = previous_end = None
        run_start = run_end = None
        resampler = None

        def consume(frames):
            nonlocal resampled_frames, resampled_samples
            for audio in frames:
                resampled_frames += 1
                resampled_samples += int(audio.samples)
                actual = None if audio.pts is None or audio.time_base is None else F(audio.pts)*F(audio.time_base)
                evidence['resampled_frames'].append(dict(pts=None if audio.pts is None else int(audio.pts),
                    time_base=None if audio.time_base is None else str(audio.time_base),
                    normalized_start_exact=None if actual is None else str(actual-origin),
                    samples=int(audio.samples), rate=int(audio.sample_rate)))
                dsp.push(audio, origin, run_start, run_end)

        with av.open(str(media), mode='r') as container:
            headers = []
            for stream in container.streams:
                context = stream.codec_context
                item = dict(index=stream.index, type=stream.type, codec=None if context is None else context.name,
                            time_base=None if stream.time_base is None else str(stream.time_base),
                            duration_units=stream.duration)
                if stream.type == 'audio':
                    _require(context is not None, 'Actual audio stream lacks codec context')
                    item.update(sample_rate=context.sample_rate, channels=context.channels)
                headers.append(item)
            audio_streams = sorted(container.streams.audio, key=lambda stream: stream.index)
            evidence.update(headers=headers, header_sha256=_json_sha(headers), pyav_version=av.__version__,
                            selected_audio_stream=None if not audio_streams else audio_streams[0].index)
            if audio_streams:
                stream = audio_streams[0]
                for frame in container.decode(stream):
                    _require(frame.pts is not None and frame.time_base is not None,
                             'Decoded audio frame lacks actual PTS/time_base; cannot align')
                    _require(frame.sample_rate > 0 and frame.samples > 0,
                             'Decoded audio frame must have actual samples and rate')
                    absolute = F(frame.pts)*F(frame.time_base)
                    start = absolute-origin
                    stop = start+F(frame.samples, frame.sample_rate)
                    _require(previous_start is None or start > previous_start,
                             'Non-increasing actual decoded audio frame PTS')
                    evidence['decoded_frames'].append(dict(pts=int(frame.pts), time_base=str(frame.time_base),
                        absolute_start_exact=str(absolute), normalized_start_exact=str(start),
                        normalized_end_exact=str(stop), samples=int(frame.samples), rate=int(frame.sample_rate)))
                    raw_samples += int(frame.samples)
                    _append_interval(input_coverage, max(F(0), start), min(end, stop))
                    if previous_end is not None and start != previous_end:
                        input_gaps.append(dict(previous_end_exact=str(previous_end), next_start_exact=str(start),
                                               delta_exact=str(start-previous_end), kind='gap' if start > previous_end else 'overlap'))
                        consume(resampler.resample(None))
                        resampler = None
                    if resampler is None:
                        resampler = av.AudioResampler(format='fltp', layout='mono', rate=RATE)
                        run_start = start
                    run_end = stop
                    consume(resampler.resample(frame))
                    previous_start, previous_end = start, stop
                _require(evidence['decoded_frames'], 'Audio stream exists but yielded no decoded samples')
                consume(resampler.resample(None))
        after = media.stat()
        _require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
                 'Media size/mtime changed during audio extraction')
        arrays, normalization, observed_bins = dsp.arrays()
        no_audio = not audio_streams
        coverage = [[str(a), str(b)] for a, b in dsp.coverage]
        gaps = []
        cursor = F(0)
        for a, b in dsp.coverage:
            if cursor < a:
                gaps.append([str(cursor), str(a)])
            cursor = b
        if cursor < end:
            gaps.append([str(cursor), str(end)])
        evidence.update(decoded_frame_count=len(evidence['decoded_frames']), decoded_sample_count=raw_samples,
            resampled_frame_count=resampled_frames, resampled_sample_count=resampled_samples,
            accepted_resampled_samples=dsp.accepted_samples, cropped_leading_or_overlapping_samples=dsp.overlap_samples_discarded,
            decoded_input_coverage_exact=[[str(a), str(b)] for a, b in input_coverage],
            input_timestamp_discontinuities=input_gaps)
        with data_path.open('xb') as stream:
            np.savez_compressed(stream, **arrays)
        # Keep the in-memory evidence intact until the whole cache commits: a
        # later write failure must still preserve the complete original diagnosis.
        frame_evidence = dict(schema=SCHEMA, decoded_frames=evidence['decoded_frames'],
                              resampled_frames=evidence['resampled_frames'])
        with evidence_path.open('xb') as stream:
            with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding='utf8', newline='\n') as text:
                    json.dump(frame_evidence, text, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        evidence_summary = {key: value for key, value in evidence.items()
                            if key not in ('decoded_frames', 'resampled_frames')}
        manifest = dict(schema=SCHEMA, status='COMPLETE', no_audio=no_audio,
            audio_observed=bool(dsp.accepted_samples),
            audio_outside_video_only=bool(not no_audio and not dsp.accepted_samples),
            utc=dt.datetime.now(dt.timezone.utc).isoformat(), media_ref=binding, clock_sha256=clock_sha,
            code_sha256=code_sha, original_video_pts0_exact=str(origin), physical_video_end_exact=str(end),
            sample_rate=RATE, bin_duration_exact=str(BIN), feature_names=list(FEATURE_NAMES),
            features_ref=dict(path=str(data_path.resolve()), bytes=data_path.stat().st_size, sha256=_sha(data_path)),
            evidence_ref=dict(path=str(evidence_path.resolve()), bytes=evidence_path.stat().st_size,
                              sha256=_sha(evidence_path), compression='gzip', gzip_mtime=0),
            observed_coverage_exact=coverage, unobserved_intervals_exact=gaps,
            observed_bin_durations_exact=observed_bins, normalization=normalization, raw_evidence=evidence_summary,
            alignment='resampled_frame.pts * resampled_frame.time_base - observed_original_video_pts0',
            missing_policy='No synthesis/interpolation across missing coverage; separate feature validity masks',
            stream_selection='first_audio_stream_by_container_index', pcm_persisted=False)
        with manifest_path.open('x', encoding='utf8') as stream:
            json.dump(manifest, stream, ensure_ascii=False, indent=2, allow_nan=False)
        return dict(manifest=manifest, arrays=arrays)
    except BaseException as error:
        evidence.update(status='FAILED', error=repr(error), traceback=traceback.format_exc())
        if 'dsp' in locals():
            evidence.update(accepted_samples_at_failure=dsp.accepted_samples,
                observed_coverage_at_failure_exact=[[str(a), str(b)] for a, b in dsp.coverage])
        failure = Path(str(prefix)+'.failure.'+uuid.uuid4().hex+'.json')
        with failure.open('x', encoding='utf8') as stream:
            json.dump(evidence, stream, ensure_ascii=False, indent=2, allow_nan=False)
        raise


def proposal_audio_features(cache, clock, baseline, candidates):
    """Pool observed *new native-frame PTS* into eight DSP/coverage features.

    Columns: energy-z mean/std/max, flux-z mean/max, positive-energy-change-z
    mean/max, fraction of new native-frame timestamps with measured audio.
    Statistics exclude unobserved/invalid values. Missing statistics are zero,
    accompanied by coverage (and the persisted per-feature validity masks).
    """
    if isinstance(cache, (str, Path)):
        cache = _load(cache)
    manifest, arrays = cache['manifest'], cache['arrays']
    pts, _, end, clock_sha = _clock(clock)
    _require(manifest['schema'] == SCHEMA and manifest['status'] == 'COMPLETE'
             and manifest['clock_sha256'] == clock_sha, 'Audio proposal/native clock binding')
    baseline = np.asarray(baseline)
    _require(baseline.dtype == np.bool_ and baseline.shape == (len(pts),),
             'Full native boolean baseline required for audio proposal pooling')
    result = np.zeros((len(candidates), 8), np.float64)
    z, valid = arrays['z'], arrays['valid']
    _require(z.shape == valid.shape == (math.ceil(end/BIN), 3) and np.isfinite(z).all(),
             'Bounded valid audio cache feature domain')
    if manifest['no_audio']:
        _require(not valid.any() and not manifest['observed_coverage_exact'],
                 'No-audio success cannot contain observed audio')
        return result
    intervals = [(F(a), F(b)) for a, b in manifest['observed_coverage_exact']]
    starts = [a for a, _ in intervals]
    for row, candidate in enumerate(candidates):
        left, right = int(candidate['left']), int(candidate['right'])
        _require(0 <= left < right <= len(pts), 'Proposal native ordinal bounds')
        indices = np.flatnonzero(~baseline[left:right])+left
        _require(len(indices) > 0 and len(indices) == int(candidate['added_frames']),
                 'Proposal actual newly added native frame count')
        observed_bins = []
        for ordinal in indices:
            point = pts[int(ordinal)]
            interval = bisect_right(starts, point)-1
            if interval >= 0 and point < intervals[interval][1]:
                observed_bins.append(int(point//BIN))
        result[row, 7] = len(observed_bins)/len(indices)
        if not observed_bins:
            continue
        bins = np.asarray(observed_bins, np.int64)
        for column, output in [(0, 0), (1, 3), (2, 5)]:
            values = z[bins, column][valid[bins, column]]
            if len(values):
                result[row, output] = values.mean()
                if column == 0:
                    result[row, 1] = values.std()
                    result[row, 2] = values.max()
                else:
                    result[row, output+1] = values.max()
    _require(np.isfinite(result).all(), 'Finite eight-dimensional observed audio descriptor')
    return result
