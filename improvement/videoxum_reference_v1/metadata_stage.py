"""Acquire the pinned author annotation file once; select without prediction access."""
import datetime
import hashlib
import json
import math
import os
import re
import socket
import traceback
import urllib.request
from pathlib import Path


BASE = Path('/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, obj):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)


def main():
    if socket.gethostname() != 'inspur-NP5570M5':
        raise RuntimeError('Unexpected host')
    registration = json.loads((BASE / 'metadata_registration_01.json').read_text())
    stage = BASE / 'metadata_01'
    stage.mkdir(exist_ok=False)
    write_new(stage / 'launch_claim.json', {
        'pid': os.getpid(), 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'registration_sha256': digest((BASE / 'metadata_registration_01.json').read_bytes()),
        'new_model_calls': 0, 'new_CPU_decodes': 0,
    })
    try:
        target = stage / 'val_videoxum.json'
        partial = target.with_suffix('.json.partial')
        item = registration['annotation_file']
        hasher = hashlib.sha256()
        count = 0
        with urllib.request.urlopen(item['url'], timeout=45) as response, partial.open('xb') as stream:
            while block := response.read(1024 * 1024):
                count += len(block)
                if count > item['bytes']:
                    raise RuntimeError('Author file exceeds registered size')
                hasher.update(block)
                stream.write(block)
        if count != item['bytes'] or hasher.hexdigest() != item['sha256']:
            raise RuntimeError('Author file size/SHA does not match pinned Hugging Face LFS object')
        partial.rename(target)
        data = json.loads(target.read_bytes())
        if not isinstance(data, list) or len(data) != 2001:
            raise RuntimeError('Expected the original author validation list of 2001 records')
        exclusions = json.loads((BASE / 'known_source_exclusions_01.json').read_text())
        excluded = set(exclusions['youtube_ids'])
        eligible = []
        ids = set()
        excluded_rows = []
        for row in data:
            vid = row['video_id']
            if not re.fullmatch(r'v_[A-Za-z0-9_-]{11}', vid) or vid in ids:
                raise RuntimeError('Invalid or duplicate original source ID')
            ids.add(vid)
            # Only ID and source duration choose this split. No vsum, text or model result is used.
            duration = row['duration']
            if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
                raise RuntimeError('Invalid source duration')
            if vid[2:] in excluded:
                excluded_rows.append(vid)
            elif registration['min_duration_seconds'] <= duration <= registration['max_duration_seconds']:
                eligible.append({'video_id': vid, 'youtube_id': vid[2:], 'duration_seconds': duration,
                                 'selection_hash': digest((registration['selection_salt'] + vid).encode())})
        eligible.sort(key=lambda row: (row['selection_hash'], row['video_id']))
        needed = registration['screen_sources'] + registration['confirm_sources']
        selected = eligible[:needed]
        if len(selected) != needed:
            raise RuntimeError('Insufficient eligible source identities')
        for i, row in enumerate(selected):
            row['group'] = 'screen' if i < registration['screen_sources'] else 'confirm'
        registry = {
            'status': 'SOURCE_IDS_FROZEN_BEFORE_MEDIA_OR_MODEL_RESULTS',
            'source_annotation_sha256': item['sha256'], 'selection': selected,
            'ordered_media_replacements': eligible[needed:needed + registration['reserve_sources']],
            'excluded_known_identity_rows': excluded_rows,
            'eligible_count': len(eligible), 'original_validation_count': len(data),
            'selection_uses_annotations_or_predictions': False,
            'replacement_policy': registration['replacement_policy'],
            'known_source_exclusions_sha256': digest((BASE / 'known_source_exclusions_01.json').read_bytes()),
        }
        write_new(stage / 'source_registration_01.json', registry)
        by_id = {row['video_id']: row for row in data}
        diagnostics = []
        references = []
        for source in selected:
            row = by_id[source['video_id']]
            events = row['vsum']
            if not isinstance(events, list) or not events:
                raise RuntimeError('Missing original manually selected summary intervals')
            annotators = [[] for _ in range(10)]
            for event in events:
                if len(event) != 10:
                    raise RuntimeError('Expected all ten annotators for each event')
                for i, span in enumerate(event):
                    if len(span) != 2 or not all(isinstance(x, (float, int)) and math.isfinite(x) for x in span):
                        raise RuntimeError('Invalid original summary interval')
                    start, end = span
                    if not (0 <= start < end <= row['duration']):
                        # Never fix, truncate, stretch or replace invalid author labels.
                        raise RuntimeError('Author interval violates original source duration: ' + row['video_id'])
                    annotators[i].append(span)
            onehot = row['vsum_onehot']
            if len(onehot) != 10 or any(len(values) != row['sampled_frames'] for values in onehot):
                raise RuntimeError('Original one-second summary matrix dimension mismatch')
            diagnostics.append({'video_id': source['video_id'], 'events': len(events),
                                'annotators': 10, 'author_sampled_frames': row['sampled_frames'],
                                'native_frame_mapping': 'NOT_RUN', 'annotation_limits': 'caption-conditioned human summary proxy'})
            references.append({**source, 'annotator_intervals_seconds': annotators,
                               'original_vsum': events, 'original_onehot': onehot,
                               'author_sampled_frames': row['sampled_frames']})
        # References stay isolated from future model request documents; no captions are exported.
        write_new(stage / 'selected_human_references_01.json', references)
        write_new(stage / 'schema_acceptance_01.json', {
            'status': 'PASS_PINNED_AUTHOR_METADATA_AND_TEN_ORIGINAL_INTERVALS_SCHEMA_ONLY',
            'sources': diagnostics, 'new_media_files': 0, 'native_mapping_pass': False,
            'candidate_quality_pass': False, 'new_model_calls': 0, 'new_optimizer_updates': 0,
        })
        write_new(stage / 'completion.json', {
            'status': 'METADATA_AND_PREDICTION_FREE_SOURCE_SELECTION_COMPLETE',
            'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'downloaded_bytes': count, 'sha256': hasher.hexdigest(),
            'sources': needed, 'screen': registration['screen_sources'], 'confirm': registration['confirm_sources'],
            'new_media_files': 0, 'new_CPU_decodes': 0, 'new_model_calls': 0,
            'next': 'Original-source media admission and native time mapping; no GPU launch permitted by this receipt.',
        })
        print(json.dumps(json.loads((stage / 'completion.json').read_text())))
    except BaseException:
        write_new(stage / 'failure.json', {'status': 'FAILED_METADATA_STAGE_PRESERVED_NO_AUTOMATIC_RETRY',
                                        'traceback': traceback.format_exc(),
                                        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
        raise


if __name__ == '__main__':
    main()
