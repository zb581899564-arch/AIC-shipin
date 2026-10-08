"""Close the finite STOP from original raw bytes, without decoder/model replay."""
import json
from register_b2_package_v1 import remote, REMOTE, RUN


def main():
    code = r'''
import hashlib,json,socket,statistics,sys,textwrap,zipfile
from pathlib import Path
assert socket.gethostname()=='inspur-NP5570M5'
root=Path(ROOT_VALUE);here=root/'native_round_alignment_v1'
out=root/'controller/NRA_scientific_stop_acceptance_20261009.json'
assert not out.exists(),'completed STOP acceptance must not be repeated'
for lp in root.glob('*/source_lock.json'):
    lock=json.loads(lp.read_bytes());bound=lock.get('files',lock.get('production_files',{}))
    names=list(bound) if isinstance(bound,dict) else [v['path'] for v in bound]
    assert str(out) not in {str((lp.parent/n).resolve()) for n in names},'receipt is frozen'
sys.path.insert(0,str(here))
import nr_common as c
# Reuse only the frozen final consumer's raw/validator and aggregate reconstruction.
# The accepted decoder/processor proofs are checked by their original done SHA.
source=(here/'final_acceptance.py').read_text()
start=source.index('    c.verify();')
end=source.index("    c.require(len(groups)==96 and gate",start)
exec(textwrap.dedent(source[start:end]),globals())
c.require(len(groups)==96 and fresh==102 and len(proofs)==102,'complete STOP denominator')
c.require(not gate(all_metric['mean'],expanded_metric['mean'],changed,down/96),'STOP must reject original gate')
c.require(registered['status']=='STOP_NATIVE_ROUND_ALIGNMENT_INVESTMENT','wrong registered outcome')
stop=c.read(here/'scientific_stop.json');c.require(stop['report']==registered and stop['no_final_426_ZIP'] is True,'STOP differs')
c.require(stop['next']=='FINITE_REGISTERED_INPUT_MECHANISMS_EXHAUSTED_KEEP_B_NO_FURTHER_PROMPT_PIXEL_DENSITY_SCAN','unexpected next route')
for name in ('completion.json','final_acceptance.json','execution_failure.json'):
    c.require(not (here/name).exists(),'unexpected complete or failed execution: '+name)
c.require(not list((here/'rematch_01').glob('*.zip')),'unexpected 426 candidate')
ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl');resources={}
for name in ('nontest','developer'):
    p=root/'controller'/('aic_NRA_v1_'+name+'.resource.json');v=c.read(p)
    c.require([r for r in ledger if r.get('name')==v['name']]==[v] and v['status']=='completed' and
        v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'unique GPU terminal')
    resources[name]={'sha256':c.sha(p),'charged_seconds':v['charged_seconds'],'unique_ledger_match':True}
nt=here/'nontest_01';validation=c.read(nt/'independent_validation.json');checks=validation['checks']
c.require(validation['status']=='PASS_INDEPENDENT_STRICT_VALIDATION' and len(checks)==11 and
    all(v is True for v in checks.values()) and validation['video_records']==8,'NONTEST strict denominator')
archive=nt/'candidate_NATIVE_ROUND_ALIGNMENT_8B.zip'
c.require(c.sha(archive)==validation['zip_sha256'],'actual NONTEST archive SHA')
with zipfile.ZipFile(archive) as z:
    c.require(z.namelist()==['predictions.jsonl'] and z.testzip() is None and
        z.read('predictions.jsonl')==(nt/'predictions.jsonl').read_bytes(),'NONTEST ZIP CRC and original bytes')
space=c.read(nt/'spatial.stage.json');c.require(space['reused_cache'] is True and space['model_calls_this_T_candidate']==0,'exact space reuse')
lock=c.read(here/'source_lock.json');bound=lock.get('files',lock.get('production_files',{}))
receipt={'status':'PASS_INDEPENDENT_FINITE_SCIENTIFIC_STOP_RAW_AGGREGATE_AND_ACCOUNTING',
    'utc':c.utc(),'source_lock_sha256':c.sha(here/'source_lock.json'),'frozen_files':len(bound),
    'raw_reconstructed_records':len(rows),'source_groups':len(groups),'windows':112,
    'new_developer_calls':fresh,'exact_original_calls_reused':112-fresh,
    'accepted_CPU_done_SHA_count':len(proofs),'developer_CPU_receipt_sha256':c.sha(here/'developer_01/replay_acceptance.json'),
    'all104_Q_minus_B0':all_metric,'expanded72_Q_minus_B0':expanded_metric,
    'changed_native_sets':changed,'groups_down':down,'original_fixed_gate_pass':False,
    'report_sha256':c.sha(here/'developer_01/report.json'),'scientific_stop_sha256':c.sha(here/'scientific_stop.json'),
    'resources':resources,'ledger_lines':len(ledger),'historical_offset_preserved':7200,
    'nontest':{'video_records':8,'prediction_frames':validation['prediction_frames'],'checks':checks,
        'zip_bytes':archive.stat().st_size,'zip_sha256':c.sha(archive),'only_non_test_package':True},
    'new_decoder_processor_calls':0,'new_model_calls':0,'new_optimizer_updates':0,
    'new_final_426_ZIP':False,'best_existing_B_score':37.63,'official_new_score':None,
    'quality_truth':'UNKNOWN','finite_registered_input_mechanisms_exhausted':True}
c.save(out,receipt)
print(json.dumps(dict(receipt,private_receipt_sha256=c.sha(out)),ensure_ascii=False))
'''.replace('ROOT_VALUE', repr(REMOTE))
    value=json.loads(remote(code, echo=False))
    path=RUN/'controller/NRA_scientific_stop_acceptance_20261009_summary.json'
    assert not path.exists(), 'private STOP aggregate already recorded'
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(value,ensure_ascii=False))


if __name__=='__main__':
    main()
