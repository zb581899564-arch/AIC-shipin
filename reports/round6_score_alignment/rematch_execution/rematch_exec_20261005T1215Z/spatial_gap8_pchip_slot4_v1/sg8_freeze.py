"""G0 consumer admission, complete independent lock and frozen CPU preflight."""
import ast
from fractions import Fraction
import inspect
from pathlib import Path
import shutil
import socket
import subprocess
import sys

from sg8_common import (HERE,RUN,OLD,V14,read,rows,sha,digest,save,require,utc,state,
    old_helpers,verify)
from sg8_prepare import tensor_binding
from sg8_report import iou
from sg8_math import numeric_gate,box_iou

LEDGER=Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
FINAL=RUN/'controller/V14_final_acceptance_20261008.json'
FINAL_SHA='f8f17dcad75dd96ff0ddcc89caf9f6531ebdcb9e0965fae81a7d4236c2ecc027'


def main():
    require(socket.gethostname()=='inspur-NP5570M5' and not (HERE/'source_lock.json').exists(),'wrong host or already frozen')
    receipts={n:read(HERE/n) for n in ['g0_asset_handoff.json','g0_new_field_contract.json','g0_exposure_review.json',
        'g0_native_processor.json','input_01/seal_receipt.json','input_01/cache_recipe_admission.json']}
    expected={'g0_asset_handoff.json':'PASS_ACTUAL_ORIGINAL_ASSET_AND_PINNED_LINEAR_HANDOFF_NOT_FULL_G0',
        'g0_new_field_contract.json':'PASS_SYNTHETIC_NEW_FIELD_AND_ACTUAL_PINNED_11_STRICT_CONTRACT_NOT_G3',
        'g0_exposure_review.json':'PASS_CURRENT_REPLAN_SAMPLE_EXPOSURE_PROVENANCE',
        'g0_native_processor.json':'PASS_ALL_88_NATIVE_SOURCE_AND_ACTUAL_SPACE_PROCESSOR_NOT_MODEL_CALL',
        'input_01/seal_receipt.json':'SEALED_SUPPORT_ONLY_L_AND_P_BEFORE_PROBE_REVEAL',
        'input_01/cache_recipe_admission.json':'PASS_CACHE_RECIPE_METADATA_NOT_PROBE_REVEAL'}
    require(all(receipts[n]['status']==v for n,v in expected.items()),'required actual G0 component missing')
    require(sha(FINAL)==FINAL_SHA,'original accepted V14 final proof changed')
    final=read(FINAL)
    require(final['status']=='PASS_INDEPENDENT_V14_FINAL_ZIP_TRAINING_SELECTION_AND_ACCOUNTING' and
        final['selected_original_B'] is True and final['selected_epoch']==0 and final['actual_T_optimizer_updates']==15,
        'original time/selected model authority differs')
    ledger=rows(LEDGER);policy=read('/home/inspur/aic_video_work/resource_policy.json')
    require(policy['ledger_initial_charge_seconds']==ledger[0]['prior_charged_seconds']==7200,'historical charge offset changed')
    original_charges={}
    for name in ['rematch_TAUTO_v14_student_train','rematch_TAUTO_v14_nontest_temporal','rematch_TAUTO_v14_rematch_temporal']:
        p=RUN/'controller'/(name+'.resource.json');v=read(p)
        require(v['status']=='completed' and v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0 and
            sum(r==v for r in ledger)==1 and sum(r['name']==name for r in ledger)==1,'original unique completed ledger authority differs')
        original_charges[name]=dict(path=str(p),sha256=sha(p),charged_seconds=v['charged_seconds'])
    common,_,_=old_helpers();baseline=common.load(OLD/'spatial_baseline.py','sg8_control_cpu_original_spatial')
    signature=inspect.signature(baseline.Qwen3VL)
    signature.bind('model',device_map='cuda:0',max_pixels=baseline.DEFAULT_MAX_PIXELS)
    require(baseline.DEFAULT_MAX_PIXELS==131072 and baseline.DEFAULT_CROP_TOKENS==128,'original space request kwargs changed')
    # Actual new tensor consumer, no second native decoder or model invocation.
    import torch
    tensor_files={}
    for path,expected_sha in receipts['g0_native_processor.json']['files'].items():
        require(sha(path)==expected_sha,'actual native CPU receipt changed')
        inp=read(path);folder=Path(path).parent
        require(sha(folder/'processor_inputs.pt')==inp['processor_inputs_sha256'] and
            sha(folder/'native.png')==inp['native_png_sha256'],'actual prepared observation changed')
        values=torch.load(folder/'processor_inputs.pt',map_location='cpu',weights_only=True)
        require({k:tensor_binding(v) for k,v in values.items()}==inp['input_tensors'] and
            int(values['input_ids'].shape[-1])==inp['input_tokens'] and inp['input_tokens']+128<=16384,
            'new inference consumer tensor admission failed')
        tensor_files.update({str(folder/n):sha(folder/n) for n in ['input.json','processor_inputs.pt','native.png']})
    require(len(tensor_files)==264,'complete 88 native inputs required')
    # Exact metric and pre-registered gate differential contracts, no probe answers.
    examples=[([0,0,9],[1,2,9],[9,16]),([2,3,16],[5,1,16],[16,9]),([0,0,3],[9,0,3],[2,3])]
    require(all(iou(a,b,r)==box_iou(a,b,r) for a,b,r in examples),'independent exact metric differs')
    require(iou([0,0,9],[0,0,9],[9,16])==1 and iou([0,0,3],[9,0,3],[2,3])==0,'metric sanity')
    require(numeric_gate([Fraction(1)]*8)['status']=='PASS_NUMERIC_ONLY' and
        numeric_gate([Fraction(0)]*8)['status']=='NO_426' and
        numeric_gate([Fraction(1),Fraction(1)]+[Fraction(1)]*3+[Fraction(0)]*3)['status']=='NO_426','fixed gate contract differs')
    code={str(p):sha(p) for p in HERE.glob('*.py') if p.name!='deploy_cpu_only.py'}
    for p in code:ast.parse(Path(p).read_bytes(),filename=p)
    field_stage=receipts['g0_new_field_contract.json']
    require(len(field_stage['strict']['checks'])==11 and all(field_stage['strict']['checks'].values()) and
        len(field_stage['rejected_mutations'])==6,'new strict semantic contract incomplete')
    contract=dict(status='PASS_NEW_GPU_CONSUMER_EXACT_TENSORS_METRIC_GATE_AND_ORIGINAL_TERMINAL_CPU',utc=utc(),
        native_prepared_observations=88,actual_tensor_files=264,metric_contracts=len(examples)+2,
        fixed_gate_contracts=3,original_constructor_signature=str(signature),files=code,
        new_model_calls=0,new_decoder_calls=0,new_optimizer_updates=0)
    save(HERE/'g0_runtime_consumer_cpu.json',contract)
    frames=sum(v['full_source_frames'] for v in receipts['g0_asset_handoff.json']['scopes'].values())
    fixture=HERE/'g0_synthetic_contract_fixture'
    # Estimate serialized new artifacts from actual synthetic provenance size per frame.
    contract_count=field_stage['strict']['counts']['full_source_frames']
    bytes_per_frame=max((fixture/'predictions.jsonl').stat().st_size//max(1,field_stage['strict']['selected_frames']),
        (V14/'nontest_01/provenance.jsonl').stat().st_size//447,2048)
    planned=frames*bytes_per_frame*4+sum(Path(p).stat().st_size for p in tensor_files)
    state('G0_FULL_ADMISSION_FREEZE_PENDING',new_spatial_calls=0,planned_remaining_output_bytes=planned)
    admission=dict(status='PASS_FULL_G0_NATIVE_ASSET_INPUT_ISOLATION_AND_STRICT_ADMISSION',utc=utc(),
        components={n:sha(HERE/n) for n in receipts},runtime_consumer_sha256=sha(HERE/'g0_runtime_consumer_cpu.json'),
        old_V14_final_proof_sha256=FINAL_SHA,old_gpu_resources=original_charges,old_space_cost_seconds_preserved=18723.876,
        ledger_prefix_records=len(ledger),ledger_prefix_digest=digest(ledger),historical_offset_seconds=7200,
        groups=8,engineering_groups=2,confirmation_groups=6,supports=32,isolated_probes=56,expected_fresh_calls=53,
        exact_old_probe_references=3,planned_remaining_output_bytes=planned,
        capacity_now=dict(disk_free_bytes=shutil.disk_usage(HERE).free,
            gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],text=True).strip()),
        operational_job_timeout_seconds=21600,queue_seconds=259200,
        capacity_policy='ACTUAL_CAPACITY_ONLY_SHARED_EXCLUSIVITY_NO_FIXED_RAM_VRAM_DISK_ADMISSION_QUOTA',
        new_model_calls=0,new_optimizer_updates=0,live_model_tensor_verification_required_inside_shared_GPU_job=True,
        original_G0_component_pending_fields_are_historical_and_resolved_by_other_actual_components=True)
    require(admission['capacity_now']['disk_free_bytes']>=planned,'actual anticipated artifacts exceed disk capacity')
    save(HERE/'g0_admission.json',admission)
    bound={}
    def merge(path,expected_sha):
        path=str(path);require(path not in bound or bound[path]==expected_sha,'authority hash conflict: '+path);bound[path]=expected_sha
    for route in [OLD,V14]+[Path(e['chosen']['folder']).parent for e in receipts['input_01/cache_recipe_admission.json']['accepted_probe_caches']]:
        lock=read(route/'source_lock.json');merge(route/'source_lock.json',sha(route/'source_lock.json'))
        for key in ('files','production_files'):
            for p,h in lock.get(key,{}).items():merge(p,h)
    assets=receipts['g0_asset_handoff.json']
    for p,h in assets['model_files'].items():merge(p,h)
    for v in assets['scopes'].values():
        for p,h in v['files'].items():merge(p,h)
    for e in receipts['input_01/cache_recipe_admission.json']['accepted_probe_caches']:
        f=Path(e['chosen']['folder'])
        for n in ['anchor_requests.jsonl','anchor_output.jsonl','spatial.stage.json']:merge(f/n,sha(f/n))
    for p,h in tensor_files.items():merge(p,h)
    own_files=list(HERE.glob('*.py'))+[HERE/'PROTOCOL.md']+list(HERE.glob('g0_*.json'))+list((HERE/'input_01').glob('*.json'))
    for p in own_files:
        if p.name not in ('deploy_cpu_only.py',) and 'failure' not in p.name:merge(p,sha(p))
    merge(FINAL,FINAL_SHA)
    for v in original_charges.values():merge(v['path'],v['sha256'])
    for p in (RUN/'resource_unlimited_v1_20261007').glob('*.py'):merge(p,sha(p))
    quick={p:h for p,h in bound.items() if (str(HERE) in p or p.endswith('.py')) and not p.endswith('.pt')}
    save(HERE/'source_lock.json',dict(route='spatial_gap8_pchip_slot4_v1',utc=utc(),files=bound,quick_files=quick,
        original_sources_protected=True,sample_and_formula_frozen_before_probe_reveal=True))
    verify()
    save(HERE/'preflight.json',dict(status='PASS_FROZEN_SG8_NATIVE_G0_AND_ALL_BOUND_BYTES',utc=utc(),
        source_lock_sha256=sha(HERE/'source_lock.json'),frozen_files=len(bound),new_model_calls=0,new_optimizer_updates=0))
    state('G0_FROZEN_PREFLIGHT_PASS_SINGLE_LAUNCH_PENDING',new_spatial_calls=0,frozen_files=len(bound),
        source_lock_sha256=sha(HERE/'source_lock.json'))


if __name__=='__main__':main()
