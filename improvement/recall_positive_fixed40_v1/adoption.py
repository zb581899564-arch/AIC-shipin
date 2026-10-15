"""Exact-identity successful evidence adoption; no successful stage is rerun."""
from fractions import Fraction as F
from pathlib import Path
import facts_common as io
from registration import bound


def adopt(row, view, source, clock, required):
    io.require(row['mode'] == 'ADOPT', 'Explicit successful exact-identity adoption required')
    evidence = row['evidence']
    keys = ('input_ref','primary_proof_ref','first_input_QA_ref','done_ref','output_QA_ref',
        'gpu_completion_ref','output_QA_completion_ref','gpu_admission_ref','model_identity_ref','resource_ref')
    docs = {}
    for key in keys:
        path = bound(evidence[key]); io.require(required.get(str(path)) == evidence[key]['sha256'], 'Every adopted artifact must be frozen in new registration')
        docs[key] = io.read(path)
    meta, proof, first, done, qa = [docs[key] for key in keys[:5]]
    source_keys = ('source_name','source_sha256','window_start','window_end','source_frame_ordinals','sample_exact_pts','window_role','view_roles')
    io.require(meta['case_id'] == row['case_id'] == view['case_id'] and all(meta[k] == view[k] for k in source_keys) and
        meta['original_clock_sha256'] == source['clock_sha256'] and meta['all_source_exact_pts'] == clock['original_exact_pts'] and
        meta['physical_end_exact'] == clock['physical_end_exact'] and meta['audio_observed'] is False and
        meta['reference_available_to_inference'] is False and proof['input_sha256'] == evidence['input_ref']['sha256'] and
        proof['input_evidence']['prompt_sha256'] == io.PROMPT_SHA and
        proof['input_evidence'] == first['input_evidence'] == done['input_evidence'],
        'Adoption requires exact full original source/clock/native64/tensor/prompt identity, not a similar window')
    for pathkey, shakey in (('encoded_tensor_path','encoded_tensor_sha256'),):
        io.require(required.get(proof[pathkey]) == proof[shakey], 'Adopted exact tensor cache missing from lock')
        io.checked(proof[pathkey],proof[shakey])
    io.require(first['CPU_only'] is True and first['new_model_calls'] == 0 and
        first['status'] in ('PASS_FIRST_INDEPENDENT_POSITIVE_FIXED40_INPUT_QA_PRE_GPU',
            'PASS_INDEPENDENT_FIXED40_B0_TENSOR_TOKEN_GRAMMAR_PARSER_NATIVE_REPLAY'), 'Actual successful independent original input QA required')
    io.require(qa['status'] in ('PASS_POSITIVE_FIXED40_B0_OUTPUT_TOKEN_GRAMMAR_PARSER_NATIVE_QA',
        'PASS_INDEPENDENT_FIXED40_B0_TENSOR_TOKEN_GRAMMAR_PARSER_NATIVE_REPLAY') and qa['CPU_only'] is True and
        qa['new_model_calls'] == 0 and qa['case_id'] == done['case_id'] == meta['case_id'] and
        qa['done_sha256'] == evidence['done_ref']['sha256'] and qa['segments'] == done['segments'] and
        qa['native_ranges'] == done['native_ranges'], 'Actual untouched B0 raw/parser/native output QA required for adoption')
    raw_path = io.checked(done['raw_path'], done['raw_sha256']); request_path = Path(evidence['done_ref']['path']).parent/'request.json'
    io.checked(request_path, done['request_sha256']); request = io.read(request_path); raw = io.read(raw_path)
    io.require(required.get(str(raw_path)) == done['raw_sha256'] and required.get(str(request_path)) == done['request_sha256'] and
        request['prompt'] and __import__('hashlib').sha256(request['prompt'].encode()).hexdigest() == io.PROMPT_SHA and
        request['input_sha256'] == evidence['input_ref']['sha256'] and
        request['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'] and request['input_evidence'] == raw['input_evidence'] == done['input_evidence'] and
        request['reference_labels_read'] is False and request['audio_observed'] is False and qa['raw_sha256'] == done['raw_sha256'],
        'Adopted actual raw/request/cache must match the successful original input and first QA')
    io.output_tokens(raw,done); io.verify_identity(docs['model_identity_ref']['identity'])
    gate, complete, completed_qa = docs['gpu_admission_ref'], docs['gpu_completion_ref'], docs['output_QA_completion_ref']
    resource, resource_sha = io.terminal(gate)
    io.require(resource_sha == evidence['resource_ref']['sha256'] and resource == docs['resource_ref'] and
        complete['status'] in ('PASS_ALL_FIXED40_B0_CALLS_NOT_QUALITY','PASS_POSITIVE_FIXED40_B0_NEW_CALLS_NOT_FACT_QUALITY') and
        completed_qa['status'] in ('PASS_ALL_FIXED40_B0_INDEPENDENT_REPLAYS_NOT_QUALITY','PASS_POSITIVE_FIXED40_B0_NEW_OUTPUT_QA_NOT_FACT_QUALITY') and
        complete['admission_sha256'] == evidence['gpu_admission_ref']['sha256'] and
        complete['model_identity_sha256'] == evidence['model_identity_ref']['sha256'] and
        complete['calls'] == len(complete['entries']) == completed_qa['calls'] == len(completed_qa['proofs']) and
        completed_qa['gpu_completion_sha256'] == evidence['gpu_completion_ref']['sha256'] and
        completed_qa['resource_terminal_sha256'] == resource_sha and completed_qa['CPU_only'] is True and
        completed_qa['CUDA_initialized'] is False,
        'Actual complete original model/QA/natural shared-ledger terminal must support exact adoption')
    journal_path=Path(evidence['gpu_completion_ref']['path']).parent/'attempts.jsonl'
    io.require(required.get(str(journal_path)) == complete['attempts_sha256'], 'Adopted actual unique call journal must be frozen')
    io.checked(journal_path,complete['attempts_sha256']);journal=io.rows(journal_path)
    io.require(len(journal)==2*complete['calls'] and len({item['case_id'] for item in complete['entries']})==complete['calls'],
        'Adopted original actual call denominator must be complete and unique')
    for index,item in enumerate(complete['entries'],1):
        begin,accepted=journal[2*(index-1):2*index]
        io.require(begin['event']=='BEGIN' and accepted['event']=='ACCEPTED' and begin['call_id']==accepted['call_id']==index and
            begin['case_id']==accepted['case_id']==item['case_id'] and accepted['done_sha256']==item['done_sha256'],
            'Adopted original journal/call identity differs')
    io.require(any(item.get('done_sha256') == evidence['done_ref']['sha256'] and item['case_id'] == meta['case_id'] for item in complete['entries']) and
        any(item.get('proof_sha256') == evidence['output_QA_ref']['sha256'] and item['case_id'] == meta['case_id'] for item in completed_qa['proofs']),
        'Adopted case absent from complete successful original execution/QA denominator')
    return dict(case_id=meta['case_id'], source_name=meta['source_name'], segments=done['segments'],
        native_ranges=done['native_ranges'], source_start_exact=done['source_start_exact'], evidence=evidence, adopted=True)
