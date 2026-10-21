"""First remainingCPU arithmetic review after34 final JSON serialization failure.

No old completion is overwritten. All102 derivatives are adopted, never run.
Original end-memory freeze assertions are adopted by bound execution trace;
their un-emitted final hash values are not fabricated as raw logged evidence.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time
from metadata_json35 import native


def ref(path):
    p=Path(path).resolve(strict=True);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    import numpy as np
    import torch
    from safetensors.torch import load
    n=Path(__file__).resolve().parent;w=n.parent.parent;started=time.monotonic()
    reg=json.loads((n/'registration35.json').read_text());assert reg['code_ref']==ref(__file__)
    old=Path(reg['old_root']);assert old.is_relative_to(w)
    def read(r):
        p=Path(r['path']).resolve(strict=True);assert p.is_relative_to(w) and ref(p)==r
        return json.loads(p.read_text())
    protocol=read(reg['protocol_ref']);admission=read(reg['admission34_ref'])
    for rr in admission['code_bindings']+admission['old_code_bindings']:assert ref(rr['path'])==rr
    failure=read(reg['failure34_ref']);terminal=read(reg['terminal34_ref'])
    assert terminal['exit_code']==1 and failure['traceback'].endswith("TypeError: Object of type bool is not JSON serializable\n")
    code=Path(admission['code_ref']['path']).read_text()
    lines=code.splitlines();endline=next(i+1 for i,line in enumerate(lines)if "save(n/'gpu_completion34.json'"in line)
    assert ('line '+str(endline)+', in gpu')in failure['traceback']
    preceding='\n'.join(lines[endline-7:endline-1])
    assert 'base_after=canonical_frozen_hash' in preceding
    assert 'base_after==runtime.base_before' in preceding
    assert 'torch.equal(actual[k].view(torch.uint8),original[k].view(torch.uint8))'in preceding
    resource=read(reg['resource34_ref']);job='evidence_reset_coupled_source_gradient_20261021_v34'
    ledger=[json.loads(s)for s in(w/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()if s.strip()]
    assert resource['name']==job and resource['status']=='failed'and resource['exit_code']==1
    assert[v for v in ledger if v.get('name')==job]==[resource]
    events=[json.loads(s)for s in(old/'events34.jsonl').read_text().splitlines()if s.strip()]
    begins=[e for e in events if e['kind']=='BEGIN_FIRST_PROGRAM_DERIVATIVE34']
    raw=[e for e in events if e['kind']=='FIRST_DERIVATIVE_LP_RAW']
    accepted=[e for e in events if e['kind']=='FIRST_DERIVATIVE_ACCEPTED_RAM34']
    key=lambda e:(e['uid'],e['arm'],e['label'])
    assert len(begins)==len(raw)==len(accepted)==102
    assert len({key(e)for e in begins})==102 and {key(e)for e in begins}=={key(e)for e in raw}=={key(e)for e in accepted}
    assert all(e['logprob']==e['cached']for e in raw)
    assert sum(e['role']=='fit'for e in begins)==34 and sum(e['role']=='process'for e in begins)==68
    assert not any(e['kind']=='ADOPTED_IDENTICAL_SAME_THETA_RAM_DERIVATIVE'for e in events)
    fit=read(reg['fit_direction_ref']);artifact=fit['artifact_ref'];assert ref(artifact['path'])==artifact
    direction={k:v.numpy()for k,v in load(gzip.decompress(Path(artifact['path']).read_bytes())).items()}
    assert len(direction)==288 and sum(v.size for v in direction.values())==15335424
    assert all(v.dtype==np.float32 and np.isfinite(v).all()for v in direction.values())
    sys.path.insert(0,str(old));from coupled_gradient34_math import bounded_dot,decide
    norm=bounded_dot(direction,direction)
    assert all(math.isclose(norm[key],fit['stored_direction_norm2'][key],rel_tol=1e-12,abs_tol=1e-12)for key in ['value','radius','lower','upper'])
    process=[read(rr)for rr in reg['process_stat_refs']];assert {r['sid']for r in process}=={'S02','S06','S08'}
    decision=decide(process,protocol['unchanged_minimum_scale_removed_projection'])
    partial=(old/'gpu_completion34.json').read_text();partial_status=re.search(r'"status"\s*:\s*"([^"]+)"',partial)
    assert partial_status and partial_status[1]==decision['status'],'No gate outcome change during metadata repair'
    try:json.loads(partial)
    except json.JSONDecodeError:pass
    else:raise AssertionError('Expected preserved malformed original output')
    baseline=ref(w/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    assert baseline['bytes']==384630 and baseline['sha256']=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
    out=dict(status=decision['status'],decision=decision,process=process,fit=fit,
        original34_resource_status='FAILED_EXIT1_FINAL_NUMPY_BOOLEAN_SERIALIZATION',
        original34_resource_ref=reg['resource34_ref'],original_failure_ref=reg['failure34_ref'],
        original_partial_output_ref=ref(old/'gpu_completion34.json'),original_code_ref=admission['code_ref'],
        independent_QA='FIRST_REMAINING_CPU_DIRECTION_NORM_AND_SUFFICIENT_STAT_GATE_REPLAY_PASS',
        original_end_freeze_checks='Control-flow adoption: immutable code reached final save after original288 bit equality and BASEbefore==BASEafter assertions; raw final hash/counter fields were not serialized and are not claimed recovered.',
        actual_successful_derivative_events=102,successful_fit_derivative_events=34,successful_process_derivative_events=68,
        exact_cached_LP_checks=102,raw_final_runtime_counts='NOT_SERIALIZED;102 successful derivative events directly preserved',
        original_GPU_charged_seconds=resource['charged_seconds'],original_GPU_peak_mib=resource['sampled_peak_memory_mib'],
        CPU_seconds=time.monotonic()-started,new_model_calls=0,new_backwards=0,new_updates=0,
        scientific_thresholds_unchanged=True,protected_baseline_ref=baseline,automatic_update=False,production_admitted=False,new_ZIP=0,official_submissions=0)
    with(n/'remaining_completion35.json').open('x')as f:json.dump(native(out),f,indent=2,allow_nan=False)
    summary={k:v for k,v in out.items()if k not in ['process','fit']}
    summary['stored_direction_norm2']=fit['stored_direction_norm2'];summary['direction_ref']=artifact
    print(json.dumps(native(dict(completion_ref=ref(n/'remaining_completion35.json'),receipt=summary))))


if __name__=='__main__':main()
