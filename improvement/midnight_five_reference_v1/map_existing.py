"""Adopt complete successful old JSON evidence; emit reference-free new inputs.

Reads metadata only. It never deserializes a tensor, opens reference labels,
replays QA, decodes media, calls a processor or changes the old comparison.
"""
import argparse
from bisect import bisect_left
from collections import Counter
from fractions import Fraction as F
import hashlib
from pathlib import Path

from reference_common import HOME, checked, merged, read, ref, require, save, serialized

CACHE_FORMAT = 'TORCH_SAVE_GZIP_LOSSLESS_LEVEL1'


def index_receipts(completion, key, prefix):
    rows = completion[key]
    require(completion['calls'] == len(rows), 'Incomplete old '+prefix+' denominator')
    result = {row['case_id']: row for row in rows}
    require(len(result) == len(rows), 'Repeated old '+prefix+' case')
    return result


def old_path(row, prefix):
    return checked(dict(path=row[prefix+'_path'], sha256=row[prefix+'_sha256']))


def map_existing(prior, group, output, protocol):
    prior, output = prior.resolve(), output.resolve()
    require(prior.is_relative_to(HOME) and output.is_relative_to(HOME) and not output.exists(), 'Distinct new Linux-only output required')
    protocol_ref = ref(protocol)
    # The protocol must be frozen before the first new prompt/model call.
    from reference_common import validate_gates
    validate_gates(read(checked(protocol_ref)))
    cpu_path = prior/('cpu_acceptance_'+group+'.json'); cpu = read(cpu_path)
    require(cpu['status'] == 'PASS_ALL_RECALL_REAL_CPU_INPUTS_NOT_GPU_ADMISSION' and cpu['group'] == group
        and cpu['CPU_only'] is True and cpu['CUDA_initialized'] is False, 'Complete old real CPU admission required')
    b0path = prior/group/'B0/gpu_01/completion.json'; b0qa_path = prior/group/'B0/replay_01/completion.json'
    vpath = prior/group/'VERIFY/gpu_01/completion.json'; vqa_path = prior/group/'VERIFY/replay_01/completion.json'
    b0, b0qa, verify, vqa = map(read, (b0path, b0qa_path, vpath, vqa_path))
    for stage, complete, qa, path in (('B0', b0, b0qa, b0path), ('VERIFY', verify, vqa, vpath)):
        require(complete['status'] == 'PASS_ALL_RECALL_'+stage+'_CALLS_NOT_QUALITY'
            and qa['status'] == 'PASS_ALL_RECALL_'+stage+'_INDEPENDENT_REPLAYS_NOT_QUALITY'
            and complete['calls'] == qa['calls'] and qa['gpu_completion_sha256'] == ref(path)['sha256']
            and qa['CPU_only'] is True and qa['CUDA_initialized'] is False, 'Original completed first QA required')
    by_b0, by_b0qa = index_receipts(b0, 'entries', 'B0'), index_receipts(b0qa, 'proofs', 'B0 QA')
    by_v, by_vqa = index_receipts(verify, 'entries', 'VERIFY'), index_receipts(vqa, 'proofs', 'VERIFY QA')
    require([e['case_id'] for e in cpu['entries']] == list(by_b0) == list(by_b0qa), 'Complete original CPU/B0 order differs')
    export_path = prior/group/'VERIFY/verification_export.json'; export = read(export_path)
    require(export['status'] == 'PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY'
        and export['independent_replay_completion_sha256'] == ref(vqa_path)['sha256']
        and len(export['events']) == len(by_v) == len(by_vqa), 'Complete old VERIFY export required')
    inputs = {}; sources = {}; old_events = {}; selected = {}; pair_seen = set()
    for row in cpu['entries']:
        case = row['case_id']; mp, pp = old_path(row, 'input'), old_path(row, 'proof')
        meta, proof = read(mp), read(pp)
        dp, qp = old_path(by_b0[case], 'done'), old_path(by_b0qa[case], 'proof')
        done, qa = read(dp), read(qp)
        require(case == meta['case_id'] == proof['case_id'] == done['case_id'] == qa['case_id']
            and proof['input_sha256'] == row['input_sha256'] and qa['done_sha256'] == ref(dp)['sha256']
            and qa['segments'] == done['segments'] and qa['native_ranges'] == done['native_ranges']
            and done['source_sha256'] == meta['source_sha256']
            and proof['input_evidence'] == done['input_evidence'], 'Adopted CPU/B0/first-QA binding differs')
        ordinals, pts = meta['source_frame_ordinals'], meta['sample_exact_pts']
        require(len(ordinals) == len(pts) == 64 and len(set(ordinals)) == 64 and ordinals == sorted(ordinals)
            and [meta['all_source_exact_pts'][i] for i in ordinals] == pts
            and proof['encoded_tensor_format'] == CACHE_FORMAT and meta['reference_available_to_inference'] is False
            and meta['audio_observed'] is False, 'Original complete silent native64 observation required')
        cache = Path(proof['encoded_tensor_path'])
        require(cache.is_relative_to(prior), 'Original accepted visual cache escaped old root')
        old_request_path = dp.parent/'request.json'; old_request = read(old_request_path)
        require(done['request_sha256'] == ref(old_request_path)['sha256'] and
            hashlib.sha256(old_request['prompt'].encode()).hexdigest() == proof['input_evidence']['prompt_sha256'],
            'Original full-cache prompt differs')
        name = meta['source_name']; sources.setdefault(name, dict(source_name=name, source_id=meta['video_id'],
            source_sha256=meta['source_sha256'], source_bytes=meta['source_bytes'],
            clock_ref=dict(path=meta['original_clock_path'], sha256=meta['original_clock_sha256'])))
        require(sources[name]['source_sha256'] == meta['source_sha256'], 'Crossed source bytes')
        inputs[case] = dict(case_id=case, source_name=name, source_id=meta['video_id'], source_sha256=meta['source_sha256'],
            source_ordinals=ordinals, exact_pts=pts, window_exact=[meta['window_start'], meta['window_end']],
            view_roles=meta.get('view_roles', [meta['window_role']]), original_input_ref=ref(mp), original_cpu_proof_ref=ref(pp),
            original_cache_ref=dict(path=str(cache), sha256=proof['encoded_tensor_sha256']), cache_codec=CACHE_FORMAT,
            input_kind='FULL_GZIP', cache_ref=dict(path=str(cache), sha256=proof['encoded_tensor_sha256']),
            original_prompt=old_request['prompt'], original_cache_bytes=proof['encoded_tensor_bytes'],
            window_native_end_ordinal=bisect_left(list(map(F, meta['all_source_exact_pts'])), F(meta['window_end'])),
            window_native_end_exact=meta['window_end'], original_B0_request_ref=ref(old_request_path),
            original_input_evidence=proof['input_evidence'], original_B0_done_ref=ref(dp), original_first_QA_ref=ref(qp),
            original_prompt_sha256=proof['input_evidence']['prompt_sha256'], candidate_events=[])
        old_events[case] = done['segments']
    for event in export['events']:
        case = event['original_case_id']; index = event['original_segment_index']; pair = (case, index)
        require(pair not in pair_seen and case in inputs and 0 <= index < len(old_events[case]), 'Repeated/foreign old candidate')
        pair_seen.add(pair); item = inputs[case]; a, b = map(F, event['original_interval_exact']); lo, hi = map(F, item['window_exact'])
        require([str(lo+F(str(t))) for t in old_events[case][index]] == event['original_interval_exact'], 'Old native candidate endpoint changed')
        decision = event['decision_result']; request = decision['request_id']
        vd = read(old_path(by_v[request], 'done')); vq = read(old_path(by_vqa[request], 'proof'))
        require(event['event_id'] == decision['event_id'] and event['source_sha256'] == item['source_sha256']
            and vd['decision_result'] == vq['decision_result'] == decision
            and vq['done_sha256'] == by_v[request]['done_sha256'] and decision['successful_model_call_required'] is True
            and decision['decision'] in ('KEEP', 'UNKNOWN', 'DROP') and lo <= a < b <= hi, 'Old successful VERIFY decision differs')
        if 'baseline' in item['view_roles']:
            contribution = [max(lo, a-F(3, 4)), min(hi, b+F(1, 2)+(F(1, 4) if b-a >= 8 else F(0)))]
            candidate = dict(event_id=event['event_id'], original_interval_exact=event['original_interval_exact'],
                selected_interval_exact=[str(v) for v in contribution], decision=decision['decision'],
                original_segment_index=index, old_VERIFY_done_ref=ref(old_path(by_v[request], 'done')),
                old_VERIFY_first_QA_ref=ref(old_path(by_vqa[request], 'proof')))
            selected.setdefault(item['source_name'], []).append((case, candidate))
    require(pair_seen == {(case, i) for case, segments in old_events.items() for i in range(len(segments))}, 'Full original candidate denominator differs')
    for name, values in selected.items():
        kept = [(case, event) for case, event in values if event['decision'] != 'DROP']
        fallback = not kept
        for case, event in (values if fallback else kept):
            event['original_baseline_source_empty_guard'] = fallback
            inputs[case]['candidate_events'].append(event)
    entries = [item for item in inputs.values() if item['candidate_events']]
    require(len(sources) == 4 and set(selected) == set(sources), 'Full frozen four-source denominator required')
    for entry in entries:
        entry['candidate_events'].sort(key=lambda event: event['original_segment_index'])
        cache = Path(entry['cache_ref']['path'])
        require(cache.is_file() and cache.stat().st_size == entry['original_cache_bytes'],
                'Required original baseline visual cache missing or changed size')
    pointer_path = prior/('reference_completion_'+group+'.json'); reference_path = checked(read(pointer_path)); reference_receipt = read(reference_path)
    reference_rows = {row['video_id']: row for row in reference_receipt['accepted']}
    require(set(reference_rows) == set(sources) and len(reference_rows) == 4, 'Complete original reference pointers required')
    for name, source in sources.items():
        row = reference_rows[name]
        require(row['media']['sha256'] == source['source_sha256'] and source['clock_ref'] ==
            dict(path=row['clock_path'], sha256=row['clock_sha256']), 'Reference source byte/clock identity differs')
        source['reference_ref'] = dict(path=row['reference_path'], sha256=row['reference_sha256'])
        source['baseline_spans'] = serialized([event['selected_interval_exact'] for entry in entries
            if entry['source_name'] == name for event in entry['candidate_events']])
    summary = dict(original_CPU_view_count=len(inputs), original_B0_calls=len(by_b0), original_VERIFY_calls=len(by_v),
        new_decision_view_count=len(entries), new_baseline_event_count=sum(len(e['candidate_events']) for e in entries),
        original_roles=dict(Counter(','.join(e['view_roles']) for e in inputs.values())), source_count=4)
    output.mkdir(parents=True, exist_ok=False)
    inference = dict(schema='MIDNIGHT_DELETE_INPUT_ENTRIES_V1', group=group, entries=entries, denominator=summary,
        protocol_ref=protocol_ref, all_sources_previously_exposed=(group == 'dev'), reference_labels_read=False,
        model_calls=0, processor_calls=0, media_decodes=0, old_QA_repeated=0)
    save(output/'inference_entries.json', inference)
    save(output/'evaluation_manifest.json', dict(schema='MIDNIGHT_DELETE_REFERENCE_V1', group=group,
        exposure_label='development_previously_exposed' if group == 'dev' else 'confirmation_requires_separate_fresh_admission',
        protocol_ref=protocol_ref, inputs_ref=ref(output/'inference_entries.json'), sources=list(sources.values()),
        prior_root=str(prior), denominator=summary, reference_completion_ref=ref(reference_path),
        prior_bindings={str(path): ref(path) for path in (cpu_path, b0path, b0qa_path, vpath, vqa_path, export_path)},
        reference_labels_read_during_mapping=False, old_QA_repeated=0))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prior-root', type=Path, required=True)
    parser.add_argument('--group', choices=('dev',), default='dev')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    print(map_existing(args.prior_root, args.group, args.output, args.protocol))
