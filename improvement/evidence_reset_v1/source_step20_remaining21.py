"""First remaining scalar metadata/objective QA after real20 review failure.

No model, backward, update, inference, input preparation or repeat tensor QA.
Original20 review reached strict dict equality AFTER passing all288 final FP32
update-bit assertions. Preserve that failure; normalize no scientific metric.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import time


def ref(p):
    p=Path(p).resolve(strict=True); b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def save(p,v):
    with Path(p).open('x') as f: json.dump(v,f,indent=2,allow_nan=False)


def main():
    import numpy as np
    from safetensors.torch import load_file
    from source_step20_math import fixed_step
    from source_risk19 import action_gradient,normalize
    N=Path(__file__).resolve().parent; W=N.parent.parent; start=time.monotonic()
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    reg=json.loads((N/'remaining21_registration.json').read_text()); assert ref(__file__)==reg['code_ref']
    failure=json.loads((N/'failure_review20.json').read_text())
    assert "assert step==result['step'] and step==pre['step']" in failure['traceback']
    original_source=(N/'source_step20_v2.py').read_text()
    assert original_source.index("all(np.array_equal(saved[statekey(k)]") < original_source.index("assert step==result['step'] and step==pre['step']")
    q=json.loads((N/'gpu_completion20.json').read_text()); a=json.loads((N/'gpu_admission20.json').read_text())
    resource=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/evidence_reset_exact_source_risk_single_step_20261021_v20.resource.json'
    resource_value=json.loads(resource.read_text())
    ledger=[json.loads(v) for v in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if v.strip()]
    assert resource_value['status']=='completed' and resource_value['exit_code']==0
    assert [v for v in ledger if v.get('name')==resource_value['name']]==[resource_value]
    assert q['actual_updates']==1 and q['actual_backwards']==78 and q['first_autograd_forwards']==q['first_poststep_forwards']==78
    assert q['base_before']==q['base_after'] and q['all_288_save_reload_exact']
    source_reg=json.loads((N/'registration20.json').read_text()); collection=json.loads(Path(source_reg['collection_ref']['path']).read_text())
    manifest=json.loads(Path(collection['asset_manifest_ref']['path']).read_text())
    for r in [q['gradient_ref'],q['final_weights_ref'],manifest['model_spec']['adapter_weights']]: assert ref(r['path'])==r
    old=load_file(manifest['model_spec']['adapter_weights']['path']); gradient={k:v.numpy() for k,v in load_file(q['gradient_ref']['path']).items()}
    initial={k:old[k.replace('.policy.weight','.weight')].numpy() for k in gradient}
    _,computed=fixed_step(np,initial,gradient)
    pre=json.loads((N/'pre_update20.json').read_text()); assert pre['step']==q['step']
    differences={k:computed[k]-q['step'][k] for k in computed}
    assert all(math.isclose(computed[k],q['step'][k],rel_tol=2e-14,abs_tol=1e-15) for k in computed),differences
    accepted=json.loads((N/'input_acceptance20.json').read_text()); assert ref(accepted['target_ref']['path'])==accepted['target_ref']
    targets=json.loads(Path(accepted['target_ref']['path']).read_text()); rows=[]
    for target,row in zip(targets['sources'],q['source_reports']):
        assert target['sid']==row['sid']; values=[]
        for phase in [0,1]:
            value,stats,_,_=action_gradient(np,[w['lengths'] for w in target['windows']],
                [w['overlap'] for w in target['windows']],[normalize(np,v) for v in row['logits'+str(phase)]],target['gt'])
            assert abs(value-row['J'+str(phase)])<1e-12
            values.append(value)
        rows.append(dict(sid=row['sid'],J0=values[0],J1=values[1],delta=values[1]-values[0],
            KL0to1=row['mean_window_KL0to1'],expected_frames0=row['stats0']['expected_selected_frames'],
            expected_frames1=row['stats1']['expected_selected_frames'],empty_probability1=row['stats1']['probability_source_empty']))
    baseline=ref(W/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    assert baseline['bytes']==384630 and baseline['sha256']=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
    output=dict(status='ONE_STEP_OPTIMIZATION_MECHANISM_COMPLETE_NOT_GENERALIZATION_ADMISSION',
        scientific_status=q['status'],J0=q['J0'],J1=q['J1'],delta=q['delta'],predicted_first_order_gain=q['step']['predicted_first_order_gain'],
        numerical_ambiguity_threshold=q['numerical_ambiguity_threshold'],rows=rows,
        failed_metadata_recheck_absolute_differences=differences,metadata_tolerance='rel2e-14/abs1e-15 for associative float64 sums only; NOT weight tolerance',
        all288_FP32_update_bits_QA='ADOPTED_PRIOR_SUCCESS_BEFORE_ASSERTION_LINE259',
        scalar_fullsource_objective_QA='FIRST_INDEPENDENT_PASS_REMAINING21',
        original_CPU_failure_ref=ref(N/'failure_review20.json'),original_chain_failure_ref=ref(N/'chain_failure20.json'),
        gpu_completion_ref=ref(N/'gpu_completion20.json'),resource_ref=ref(resource),unique_ledger='PASS',
        charged_seconds=resource_value.get('charged_seconds'),sampled_peak_memory_mib=resource_value.get('sampled_peak_memory_mib'),
        actual_new_forwards=156,actual_new_backwards=78,actual_new_updates=1,
        remaining21_new_model_calls=0,remaining21_new_updates=0,seconds=time.monotonic()-start,
        protected_baseline_ref=baseline,more_updates_admitted=False,production_admitted=False,new_ZIP=0,official_submissions=0)
    save(N/'remaining_completion21.json',output)
    print(json.dumps(dict(completion_ref=ref(N/'remaining_completion21.json'),summary=output)))


if __name__=='__main__': main()
