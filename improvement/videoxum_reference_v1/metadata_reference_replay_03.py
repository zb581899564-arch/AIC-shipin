"""Complete original references from the successful download; preserve the frozen split."""
import datetime
import hashlib
import json
import math
import os
import socket
import traceback
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

BASE = Path('/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def main():
    if socket.gethostname() != 'inspur-NP5570M5':
        raise RuntimeError('Unexpected host')
    out = BASE / 'metadata_03'
    out.mkdir(exist_ok=False)
    save(out / 'launch_claim.json', {'pid': os.getpid(), 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                   'recovery_contract_sha256': sha(BASE / 'metadata_schema_recovery_03.json')})
    try:
        contract = json.loads((BASE / 'metadata_schema_recovery_03.json').read_text())
        source = BASE / 'metadata_02/val_videoxum.json'
        registry_path = BASE / 'metadata_02/source_registration_01.json'
        if sha(source) != contract['annotation_sha256'] or source.stat().st_size != 9575564:
            raise RuntimeError('Retained successful author download changed')
        registry = json.loads(registry_path.read_text())
        data = json.loads(source.read_text(), parse_float=Decimal)
        by_id = {row['video_id']: row for row in data}
        if len(registry['selection']) != 20 or len(by_id) != 2001:
            raise RuntimeError('Original author/source denominator changed')
        references, diagnostics = [], []
        for selected in registry['selection']:
            row = by_id[selected['video_id']]
            nominal_duration = Fraction(row['duration'])
            if nominal_duration <= 0:
                raise RuntimeError('Invalid author duration metadata')
            labels = [[] for _ in range(10)]
            end_diagnostics = []
            for event_index, event in enumerate(row['vsum']):
                if len(event) != 10:
                    raise RuntimeError('Expected ten original summary references for each event')
                for reference_index, span in enumerate(event):
                    if len(span) != 2:
                        raise RuntimeError('Invalid original timestamp pair')
                    first, last = map(Fraction, span)
                    if not (0 <= first < last):
                        raise RuntimeError('Invalid original manual interval; never repair a label')
                    labels[reference_index].append([str(span[0]), str(span[1])])
                    if last > nominal_duration:
                        end_diagnostics.append({'event_index': event_index, 'reference_index': reference_index,
                                                'original_start_seconds': str(span[0]),
                                                'original_end_seconds': str(span[1]),
                                                'author_duration_raw': str(row['duration']),
                                                'end_minus_author_duration_exact': str(last - nominal_duration),
                                                'native_end_validation': 'REQUIRED_AFTER_ACTUAL_ORIGINAL_VIDEO_DECODE'})
            onehot = row['vsum_onehot']
            if (len(onehot) != 10 or any(len(values) != row['sampled_frames'] for values in onehot)
                    or any(v not in (0, 1) for values in onehot for v in values)):
                raise RuntimeError('Original one-second matrix schema invalid; do not resize it')
            references.append({**selected, 'author_duration_raw': str(row['duration']),
                               'annotator_intervals_exact_seconds': labels,
                               'original_onehot': onehot, 'author_sampled_frames': row['sampled_frames']})
            diagnostics.append({'video_id': selected['video_id'], 'group': selected['group'],
                                'references': 10, 'events': len(row['vsum']),
                                'author_duration_is_not_native_clock_end': True,
                                'end_diagnostics': end_diagnostics, 'native_mapping_pass': False})
        save(out / 'selected_human_references_01.json', references)
        save(out / 'schema_acceptance_03.json', {
            'status': 'PASS_ORIGINAL_MANUAL_INTERVAL_SCHEMA_PENDING_REAL_NATIVE_END_GATE',
            'sources': diagnostics, 'frozen_source_selection_sha256': sha(registry_path),
            'annotation_sha256': sha(source), 'raw_intervals_modified': False,
            'source_selection_modified': False, 'onehot_stretched_padded_or_truncated': False,
            'caption_text_exported': False, 'native_mapping_pass': False,
            'source_media_admission_pass': False, 'GPU_admitted': False,
            'new_downloads': 0, 'new_CPU_decodes': 0, 'new_model_calls': 0,
        })
        save(out / 'completion.json', {
            'status': 'PASS_TWENTY_RETAINED_AUTHOR_REFERENCE_SCHEMAS_NOT_NATIVE_OR_QUALITY_ACCEPTANCE',
            'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'sources': 20, 'screen': 12, 'confirm': 8,
            'retained_author_download_bytes': source.stat().st_size, 'annotation_sha256': sha(source),
            'original_source_registration_sha256': sha(registry_path),
            'reference_export_sha256': sha(out / 'selected_human_references_01.json'),
            'schema_acceptance_sha256': sha(out / 'schema_acceptance_03.json'),
            'original_metadata02_failure_preserved_sha256': sha(BASE / 'metadata_02/failure.json'),
            'new_downloads': 0, 'new_CPU_decodes': 0, 'new_model_calls': 0,
            'next': 'Original public media availability/rights, known identity and native-end gates. No GPU launch.',
        })
        print(json.dumps(json.loads((out / 'completion.json').read_text())))
    except BaseException:
        save(out / 'failure.json', {'status': 'FAILED_METADATA03_PRESERVED_NO_AUTOMATIC_RETRY',
                                   'traceback': traceback.format_exc()})
        raise


if __name__ == '__main__':
    main()
