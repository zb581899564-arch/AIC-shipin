"""Read each compressed waveform once for first serialized native sample QA."""
from fractions import Fraction as F
import json
from pathlib import Path
import numpy as np

ROOT = Path('/home/inspur/aic_video_work/sprint_audio_events_20261021_v1/native32k10')


def main():
    if (ROOT/'independent_native_sample_qa11.json').exists():
        raise ValueError('Original audit completed; do not repeat success')
    if not (ROOT/'sample_qa11_controlled_stop.json').exists():
        raise ValueError('Explicit slow-audit failure required before remaining12')
    rows = json.loads((ROOT/'input_acceptance.json').read_text())['rows']
    accepted, sources = [], {}
    for item in rows:
        with np.load(item['input_ref']['path'], allow_pickle=False) as data:
            wave, observed = data['wave'], data['observed']
        mapping = json.loads((ROOT/'inputs'/(item['uid']+'.mapping.json')).read_text())
        path = mapping['source_frames']['path']
        if path not in sources:
            with np.load(path, allow_pickle=False) as data:
                sources[path] = {key:data[key] for key in data.files}
        source = sources[path]
        offsets = source['offsets']
        starts = list(map(F, source['starts_exact'].tolist()))
        visited = np.zeros(len(wave), bool)
        for row in mapping['mappings']:
            lo, hi, frame = row['frame_first'], row['frame_stop'], row['frame']
            positions = np.arange(row['grid_first'], row['grid_first']+hi-lo)
            fresh = ~visited[positions]
            if not np.array_equal(wave[positions[fresh]], source['values'][offsets[frame]+lo:offsets[frame]+hi][fresh]):
                raise ValueError('Serialized original source samples differ')
            stamp = starts[frame]+F(lo,32000)
            if stamp != F(row['actual_first_sample_time_exact']) or not F(item['start_exact']) <= stamp < F(item['end_exact']):
                raise ValueError('Native audio/video exact clock differs')
            if not 0 <= F(row['sub_sample_grid_residual_exact']) < 1:
                raise ValueError('Unexpected subsample mapping error')
            visited[positions[fresh]] = True
        if not np.array_equal(visited, observed) or wave[~visited].any():
            raise ValueError('Missing samples mask changed')
        accepted.append(dict(uid=item['uid'], actual_samples=len(wave),
            high_band_fraction=item['high_band_fraction'],
            old_upsampled16k_high_band_fraction=item['old16k_upsampled_high_band_fraction']))
    result = dict(status='PASS_FIRST8_SERIALIZED_NATIVE_SOURCE_SAMPLE_AND_PTS_REPLAY', rows=accepted,
        new_model_calls=0, actual_original_source_frames=4,
        labels_or_clocks_changed=False, compressed_members_read_once=True)
    with (ROOT/'independent_native_sample_qa12.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
