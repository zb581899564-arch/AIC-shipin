"""Shared final accounting for explicit remaining controllers."""
import json
from common import ROOT, WORK, ref, read, write
from controller import RESOURCE, JOB, LEDGER


def complete():
    record = read(RESOURCE / f'{JOB}.resource.json')
    ledger = [json.loads(s) for s in LEDGER.read_text().splitlines() if s.strip()]
    assert record['status'] == 'completed' and record['exit_code'] == 0
    assert [r for r in ledger if r.get('name') == JOB] == [record]
    result = read(ROOT / 'review.json')
    baseline = WORK / 'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
    assert ref(baseline)['sha256'] == read(ROOT / 'protocol.json')['protected_sha256']
    identity = read(ROOT / 'model_acceptance.json')
    inference = read(ROOT / 'inference_completion.json')
    write(ROOT / 'completion.json', dict(status=result['status'], tests=result['tests'],
          source_macro_AP=result['source_macro_AP'], static_clip_macro=result['static_clip_macro'],
          parameters=identity['parameters'], combined_parameters=identity['with_protected_baseline'],
          charged_seconds=record['charged_seconds'], wrapper_sampled_peak_mib=record.get('sampled_peak_memory_mib'),
          peak_allocated_bytes=inference['peak_allocated_bytes'],
          video_forward_batches=inference['actual_video_forward_batches'],
          text_forward_batches=1, real_cells=512, reverse_cells=512,
          review=ref(ROOT / 'review.json'), audit=ref(ROOT / 'independent_cpu_audit.json'),
          baseline_unchanged=True, new_updates=0, new_zip=0, production_allowed=False))
