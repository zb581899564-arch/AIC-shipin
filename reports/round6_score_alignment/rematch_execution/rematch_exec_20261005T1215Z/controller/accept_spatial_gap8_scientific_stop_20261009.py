"""Close the finite SG8 decision from immutable raw; never rerun media or models."""
import json
from register_b2_package_v1 import remote, REMOTE, RUN


def main():
    code = r'''
import hashlib,json,os,socket,sys
from fractions import Fraction as F
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path(ROOT_VALUE);here=root/'spatial_gap8_pchip_slot4_v2'
out=root/'controller/SG8_scientific_stop_acceptance_20261009.json'
assert not out.exists(),'completed closure must not be repeated'
for lp in root.glob('*/source_lock.json'):
    lock=json.loads(lp.read_bytes())
    for key in ('files','production_files'):
        bound=lock.get(key,{})
        names=bound if isinstance(bound,dict) else [v['path'] for v in bound]
        assert str(out) not in {str((lp.parent/n).resolve()) for n in names},'receipt is frozen'
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1')
sys.path.insert(0,str(here))
import sg8_common as c
from sg8_independent_math import rebuild
lock=c.verify()
plan=c.read(here/'input_01/sample_plan.json');sealed=c.read(here/'input_01/sealed_predictions.json')
complete=c.read(here/'diagnostic_01/inference_completion.json');report=c.read(here/'diagnostic_01/report.json')
stop=c.read(here/'scientific_stop.json');admission=c.read(here/'g0_admission.json')
c.require(complete['observations']==56 and complete['groups']==8 and complete['fresh_calls']==53 and complete['reused_probes']==3,'complete denominator')
c.require(c.read(here/'input_01/seal_receipt.json')['predictions_sha256']==c.sha(here/'input_01/sealed_predictions.json'),'sealed predictions changed')
common,p2j,_=c.old_helpers()
baseline=common.load(c.OLD/'spatial_baseline.py','sg8_stop_original_space')
config=c.read(c.OLD/'config.json');manifest=c.read(config['inputs']['nontest']['manifest'])
meta={r['video_id']:r for r in manifest['records']}
anchors={(r['video_id'],r['source_frame']):r for r in c.rows(c.V14/'nontest_01/anchor_output.jsonl')}
accepted={r['request_sha256']:r for r in complete['accepted']}
cache={r['request_sha256']:r for r in c.read(here/'input_01/cache_recipe_admission.json')['accepted_probe_caches']}
model=c.read(here/'diagnostic_01/model.json')
c.require(model['base_hash']['sha256']==c.BASE_SHA and model['base_hash']['parameters']==8767123696 and model['adapter_enabled'] is False,'actual original model identity')

def parse_box(raw,req):
    center=sys.modules['contracts'].parse_focus_norm(raw,req['source_width'],req['source_height'])
    c.require(center is not None,'original parser rejected immutable raw')
    w,h=baseline.compute_crop_size(req['source_width'],req['source_height'],*req['target_ratio_wh'])
    return baseline.center_to_box(*center,req['source_width'],req['source_height'],w,h)

answers={};proofs={};fresh=reused=0
for obs in plan['requests']:
    if obs['observation_role']!='probe':continue
    req=obs['request'];key=req['anchor_request_sha256'];ref=accepted[key];p=Path(ref['path'])
    c.require(c.sha(p)==ref['sha256'],'accepted response changed')
    done=c.read(p);c.require(done['request']==req and (req['video_id'],req['source_frame']) not in anchors,'probe/support isolation or request mismatch')
    inp_path=here/'input_01/observations'/key/'input.json';inp=c.read(inp_path)
    if done['new_model_calls']==1:
        raw=c.read(p.parent/'raw.json');proof=c.read(p.parent/'cpu_replay.json')
        c.require(done['raw_sha256']==c.sha(p.parent/'raw.json')==proof['raw_sha256'] and
            done['cpu_replay_sha256']==c.sha(p.parent/'cpu_replay.json') and
            done['input_receipt_sha256']==raw['input_receipt_sha256']==proof['input_receipt_sha256']==c.sha(inp_path) and
            done['model_receipt_sha256']==raw['model_receipt_sha256']==proof['model_receipt_sha256']==c.sha(here/'diagnostic_01/model.json'),'complete original CPU/raw/input/model binding')
        c.require(proof['status']=='PASS_REAL_NATIVE_SPACE_PROBE_AND_INDEPENDENT_CPU_REPLAY' and
            proof['new_model_calls']==proof['new_optimizer_updates']==0 and
            raw['actual_input_tensors']==inp['input_tensors']==proof['input_tensors'] and
            raw['input_tokens']==inp['input_tokens']==proof['input_tokens'] and
            raw['request_sha256']==key and raw['adapter_enabled'] is False and raw['do_sample'] is False and
            raw['num_beams']==1 and raw['max_new_tokens']==128,'accepted actual input and original generation contract')
        box=parse_box(raw['raw_output'],req)
        c.require(box==done['box_xyw']==proof['box_xyw'],'raw-to-box reconstruction mismatch')
        proofs[key]=c.sha(p.parent/'cpu_replay.json');fresh+=1
    else:
        old,line_sha=c.cached_output(cache[key])
        c.require(done['status']=='PASS_EXACT_OLD_8B_PROBE_REFERENCE_NO_NEW_CALL' and done['old_cost_preserved'] and
            old==done['output'] and line_sha==done['source_raw_line_sha256'] and inp['request']==req,'old exact reference mismatch')
        box=parse_box(old['raw_output'],req)
        c.require(box==old['box_xyw'] and old['decoded_pixel_sha256']==req['expected_pixel_sha256'],'old native raw mapping')
        reused+=1
    answers[req['video_id'],req['source_frame']]=box
c.require(fresh==len(proofs)==53 and reused==3 and len(answers)==len(accepted)==56,'all successes and independent CPU proofs required')
c.require(len(list((here/'diagnostic_01/new').glob('*/raw.json')))==53 and
    len(list((here/'diagnostic_01/new').glob('*/cpu_replay.json')))==53,'no extra new raw or replay')

def overlap(a,b,ratio):
    # Independent continuous-ratio evaluator: (x, y, x+w, y+h) rectangles.
    tw,th=map(F,ratio)
    def rect(v):
        x,y,w=map(F,v);return (x,y,x+w,y+w*th/tw)
    x1,y1,x2,y2=rect(a);u1,v1,u2,v2=rect(b)
    dx=min(x2,u2)-max(x1,u1);dy=min(y2,v2)-max(y1,v1)
    inter=F(0) if dx<=0 or dy<=0 else dx*dy
    return inter/((x2-x1)*(y2-y1)+(u2-u1)*(v2-v1)-inter)

def exact(v):return F(v['numerator'],v['denominator'])
seal={(r['video_id'],r['source_frame']):r for r in sealed['predictions']}
stored={(r['video_id'],r['source_frame']):r for r in report['matched_rows']}
group_values=[];supports_seen=set()
for group in plan['groups']:
    vid=group['video_id'];q=group['support_ordinals'];ratio=meta[vid]['targetRatioWH'];phase=[]
    support={n:anchors[vid,n]['box_xyw'] for n in q}
    supports_seen.update((vid,n) for n in q)
    c.require(len(q)==4 and q[2]-q[1]==8 and len(group['probe_ordinals'])==7,'registered support and phase structure')
    for f in group['probe_ordinals']:
        linear=p2j.interpolate_box(f,support)[0]
        pchip=[rebuild(q,[support[n][axis] for n in q],f)[1] for axis in (0,1)]+[support[q[1]][2]]
        s=seal[vid,f];r=stored[vid,f]
        c.require(s['linear']==linear and s['pchip']==pchip and s['targetRatioWH']==ratio and
            s['support_output_sha256']==[c.digest(anchors[vid,n]) for n in q],'independent polynomial and original supports differ from prereveal seal')
        value=overlap(pchip,answers[vid,f],ratio)-overlap(linear,answers[vid,f],ratio)
        c.require(r['linear']==linear and r['pchip']==pchip and r['probe']==answers[vid,f] and exact(r['delta'])==value,'independent raw phase reconstruction differs')
        phase.append(value)
    group_values.append(sum(phase,F(0))/7)
c.require(len(supports_seen)==32 and len(group_values)==8 and len({g['source_group'] for g in plan['groups']})==8,'registered group and support denominator')
confirm=group_values[2:];leave=[(sum(confirm)-d)/5 for d in confirm]
checks=dict(confirm_at_least4of6_positive=sum(d>0 for d in confirm)>=4,
    confirm_mean_positive=sum(confirm)>0,all8_mean_positive=sum(group_values)>0,
    all_confirm_leave_one_means_nonnegative=all(d>=0 for d in leave))
c.require(checks==report['checks'] and not any(checks.values()) and
    group_values==[exact(v) for v in report['group_deltas']] and
    sum(confirm)/6==exact(report['confirmation_mean']) and sum(group_values)/8==exact(report['all8_mean']) and
    leave==[exact(v) for v in report['leave_one_confirmation_means']],'fixed exact group gate reconstruction differs')
c.require(report['status']==stop['status']=='NO_426_SG8_FIXED_NUMERIC_GATE' and
    stop['report_sha256']==c.sha(here/'diagnostic_01/report.json') and stop['finite_route_exhausted'] and
    stop['no_final_426_ZIP'] and stop['no_automatic_new_recipe'],'registered finite decision differs')
for name in ('completion.json','final_acceptance.json','execution_failure.json'):
    c.require(not (here/name).exists(),'unexpected terminal artifact '+name)
c.require(not list((here/'nontest_01').glob('*.zip')) and not list((here/'rematch_01').glob('*.zip')),'G2 failure must precede NT or 426 production')
ledger=c.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
n=admission['ledger_prefix_records']
c.require(c.digest(ledger[:n])==admission['ledger_prefix_digest'] and ledger[0]['prior_charged_seconds']==7200,'historical ledger prefix changed')
resources={}
for version,want in [('v1','failed'),('v2','completed')]:
    p=root/'controller'/('aic_SG8_slot4_'+version+'_diagnostic.resource.json');v=c.read(p)
    c.require([r for r in ledger if r.get('name')==v['name']]==[v] and v['status']==want and
        v['exit_code']==(1 if version=='v1' else 0) and v['stop_reason'] is None and v['charged_seconds']>0,'actual unique resource terminal')
    resources[version]=dict(status=v['status'],exit_code=v['exit_code'],stop_reason=v['stop_reason'],
        charged_seconds=v['charged_seconds'],sha256=c.sha(p),unique_ledger_match=True)
owned=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:argv=(p/'cmdline').read_bytes().split(b'\0');argv=[v.decode(errors='replace') for v in argv if v]
    except OSError:continue
    if any(v.startswith(str(here)+'/') and v.endswith('.py') for v in argv[1:]):owned.append(dict(pid=int(p.name),argv=argv))
c.require(not owned,'owned execution not naturally closed')
receipt=dict(status='PASS_INDEPENDENT_SG8_FINITE_NO_426_RAW_GATE_AND_ACCOUNTING',utc=c.utc(),
    source_lock_sha256=c.sha(here/'source_lock.json'),frozen_files=len(lock['files']),all_frozen_bytes_SHA_pass=True,
    observations=56,source_groups=8,engineering_groups=2,confirmation_groups=6,phases_per_group=7,
    new_space_calls=fresh,exact_old_probe_references=reused,accepted_CPU_proofs=len(proofs),
    accepted_CPU_proof_map_digest=c.digest(proofs),original_supports=32,probe_used_as_support=False,
    confirmation_positive_groups=sum(d>0 for d in confirm),required_confirmation_positive_groups=4,
    confirmation_mean=report['confirmation_mean'],all8_mean=report['all8_mean'],checks=checks,
    independent_original_raw_parser_and_polynomial_reconstruction=True,
    report_sha256=c.sha(here/'diagnostic_01/report.json'),scientific_stop_sha256=c.sha(here/'scientific_stop.json'),
    inference_completion_sha256=c.sha(here/'diagnostic_01/inference_completion.json'),resources=resources,
    ledger_records=len(ledger),historical_offset_preserved=7200,original_space_cost_seconds_preserved=18723.876,
    owned_processes=0,new_decoder_processor_calls=0,new_model_calls_in_acceptance=0,new_optimizer_updates=0,
    new_final_426_ZIP=False,new_full_NONTEST_field=False,quality_truth='UNKNOWN',official_new_score=None,
    original_best_B_score=37.63,finite_registered_route_exhausted=True,
    conclusion='KEEP_B_BEST_NO_426_NO_AUTOMATIC_NEW_FORMULA_OR_SAMPLE',
    next_evidence='Independent native target-ratio composition reference with verified usage rights and source isolation before another quality-driven route')
with out.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps(dict(receipt,private_receipt_sha256=c.sha(out)),ensure_ascii=False))
'''.replace('ROOT_VALUE', repr(REMOTE))
    value = json.loads(remote(code, echo=False))
    path = RUN/'controller/SG8_scientific_stop_acceptance_20261009_summary.json'
    assert not path.exists(), 'completed closure aggregate already saved'
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(value, ensure_ascii=False))


if __name__ == '__main__':
    main()
