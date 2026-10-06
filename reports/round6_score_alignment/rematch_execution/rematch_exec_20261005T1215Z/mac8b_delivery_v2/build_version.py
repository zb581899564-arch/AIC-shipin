"""Create independent sources; never edit the completed Linux/Mac versions."""
import ast
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUN=HERE.parent
REMOTE="RUN/'mac8b_delivery_v1'"
ADAPTER_SHA='1baa14a96d30d3836478295752c0b932f40f811863c28db99b56102fcfa1d5b5'

def replace_function(text,name,body):
    node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=text.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1])+body.strip()+'\n'+''.join(lines[node.end_lineno:])

runtime=(RUN/'b_sft8b_package_v3/runtime.py').read_text(encoding='utf-8')
runtime=runtime.replace("HERE=RUN/'b_sft8b_package_v3'",f'HERE={REMOTE}')
runtime=runtime.replace("from pathlib import Path",'from pathlib import Path\nfrom lowres import lowres_encode,verify_cuda_adapter')
runtime=replace_function(runtime,'verify','''
def verify():
    lock=read(HERE/'source_lock.json')
    for path,digest in lock['files'].items(): require(sha(path)==digest,'source identity changed: '+path)
    a=read(HERE/'admission.json')
    for path,digest in a['files'].items(): require(sha(path)==digest,'bound model/training identity changed: '+path)
    return a
''')
runtime=replace_function(runtime,'stage_admission','''
def stage_admission(stage,scope,out):
    a=read(HERE/('rematch_MAC8B_v1_'+scope+'_'+stage+'_01.admission.json'))
    require(a.get('authorized') is True and a.get('scope')==scope and a.get('stage')==stage and
        a.get('output')==str(Path(out)) and a.get('source_lock_sha256')==sha(HERE/'source_lock.json'), 'phase authority changed')
    require(read(HERE/'processor_cpu_01.json')['status']=='PASS_ACTUAL_MAC_LOWRES_PROCESSOR','processor gate missing')
    if stage!='long_probe':
        require(read(HERE/'dev/decision.json')['status']=='PASS_FROZEN_WEAK_DEV_GATE','Mac fixed dev gate STOP')
        require(read(HERE/'long_probe_01/probe.stage.json')['status']=='PASS_SYNTHETIC_MAC_LOWRES_8B_INFERENCE','relocation probe missing')
    if scope=='rematch':
        require(read(HERE/'nontest_01/package.stage.json')['status']=='PASS_COMPLETE_8B_PACKAGE_NOT_SCORED_NOT_UPLOADED','Mac NONTEST8 missing')
    if stage=='spatial': require(read(Path(out)/'schedule.stage.json')['status']=='PASS_EXACT_SCHEDULING','scheduling missing')
''')
runtime=runtime.replace("RUN/'temporal_sft8b_full_v1/train_01/train_report.json'","HERE/'training_evidence/train_report.json'")
runtime=runtime.replace("recovery=read(HERE/'partial_recovery_inputs.json') if scope=='rematch' else None",'recovery=None')
runtime=runtime.replace('processor(text=', 'lowres_encode(processor,text=').replace('encoded=p(text=', 'encoded=lowres_encode(p,text=')
runtime=runtime.replace('<=16384','<=6144').replace('separately admitted 16384','registered Mac lowres 6144')
runtime=runtime.replace('inference_max_sequence_length=16384,training_max_sequence_length_unchanged=8192',
    'inference_max_sequence_length=6144,training_max_sequence_length_unchanged=6144,video_pixels_per_frame=32768')
runtime=runtime.replace("require(8192<prefix<=6144,'synthetic case does not exercise corrected inference bound')",
    "require(0<prefix<=6144,'synthetic lowres input exceeds Mac protocol')")
runtime=runtime.replace("PASS_SYNTHETIC_LONG_INPUT_8B_INFERENCE",'PASS_SYNTHETIC_MAC_LOWRES_8B_INFERENCE')
runtime=runtime.replace('inference_limit=16384,training_limit_unchanged=8192','inference_limit=6144,training_limit_unchanged=6144,video_pixels_per_frame=32768')
runtime=runtime.replace("model=PeftModel.from_pretrained(base,a['adapter'],is_trainable=False).eval()",
    "model=PeftModel.from_pretrained(base,a['adapter'],is_trainable=False).eval()\n    relocation=verify_cuda_adapter(model,a)")
runtime=runtime.replace('synthetic_pixels_only=True,contest_media_read=False','relocation=relocation,synthetic_pixels_only=True,contest_media_read=False')
(HERE/'runtime.py').write_text(runtime,encoding='utf-8')
production=(RUN/'b_sft8b_package_v3/production.py').read_text(encoding='utf-8')
(HERE/'production.py').write_text(production.replace('candidate_B_8B','candidate_MAC_8B'),encoding='utf-8')

dev=(RUN/'temporal_sft8b_dev_v1/evaluate.py').read_text(encoding='utf-8')
dev=dev.replace("HERE = RUN/'temporal_sft8b_dev_v1'", "DELIVERY=RUN/'mac8b_delivery_v1'\nHERE=DELIVERY/'dev'\nsys.path.insert(0,str(DELIVERY))\nfrom lowres import lowres_encode,decode_dev_av,verify_cuda_adapter")
dev=dev.replace('8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23',ADAPTER_SHA)
dev=dev.replace("RUN/'temporal_sft8b_full_v1/train_01/train_report.json'","DELIVERY/'training_evidence/train_report.json'")
dev=dev.replace("RUN/'temporal_sft8b_full_v1/train_01/adapter'","DELIVERY/'adapter'")
dev=dev.replace("RUN/'temporal_sft8b_full_v1/dev_protocol.json'","DELIVERY/'DEV_PROTOCOL.md'")
dev=dev.replace('生成一下包中','mac的开发测评和提交包尽早完成')
dev=dev.replace('B_FIXED_104_WEAK_DEV_ONCE','MAC_LOWRES_FIXED_104_WEAK_DEV_ONCE')
dev=dev.replace("comparisons=['BASE8B','SFT8B']","comparisons=['BASE8B','SFT8B'],video_pixels_per_frame=32768,max_input_tokens=6144,decoder='PYAV_SEQUENTIAL_SAME_AS_MAC_TRAINING',execution_device='CUDA_RELOCATED_MAC_FINAL_ADAPTER'")
dev=dev.replace('encoded=processor(text=', 'encoded=lowres_encode(processor,text=')
dev=dev.replace("arr,md,info=decode_cfr_clip(row,tc,np,decord)","arr,md,info=decode_dev_av(row,tc,np,decord)")
dev=dev.replace('<=8192','<=6144')
dev=dev.replace("model=PeftModel.from_pretrained(base,a['adapter'],is_trainable=False).eval()",
    "model=PeftModel.from_pretrained(base,a['adapter'],is_trainable=False).eval()\n    relocation=verify_cuda_adapter(model,a)\n    write(HERE/'cuda_relocation.json',relocation)")
dev=dev.replace('full_protocol_sha256=', 'video_pixels_per_frame=32768,decoder="PYAV_SEQUENTIAL",execution_device="CUDA",full_protocol_sha256=')
(HERE/'dev/evaluate.py').write_text(dev,encoding='utf-8')

processor=(RUN/'b_sft8b_package_v3/processor_cpu.py').read_text(encoding='utf-8')
processor=processor.replace("read(RUN/'temporal_sft8b_dev_v1/admission.json')","read(HERE/'admission.json')")
processor=processor.replace('encoded=processor(text=','encoded=lowres_encode(processor,text=')
processor=processor.replace('PASS_ACTUAL_8B_NATIVE_PROCESSOR','PASS_ACTUAL_MAC_LOWRES_PROCESSOR')
(HERE/'processor_cpu.py').write_text(processor,encoding='utf-8')

test=(RUN/'b_sft8b_package_v3/test_cpu.py').read_text(encoding='utf-8')
start=test.index('    import datetime as dt\n');end=test.index('    grammar=BoundedSegmentsGrammar(1)')
test=test[:start]+'''    from lowres import clip_plan,MAX_PIXELS,MAX_SEQUENCE
    check('Mac lowres budget fixed',MAX_PIXELS==32768 and MAX_SEQUENCE==6144)
    plan=clip_plan(dict(fps_num=30,fps_den=1,n_frames=900,clip_start_sec=0,clip_end_sec=30))
    check('64 source ordinals retain endpoints',len(plan['absolute_indices'])==64 and plan['absolute_indices'][0]==0 and plan['absolute_indices'][-1]==899)
'''+test[end:]
(HERE/'test_cpu.py').write_text(test,encoding='utf-8')
import shutil
shutil.copytree(RUN/'b_sft8b_package_v3/cpu_reference',HERE/'cpu_reference')

verification=(RUN/'b_sft8b_package_v3/verify_delivery.py').read_text(encoding='utf-8')
(HERE/'verify_delivery.py').write_text(verification.replace('candidate_B_8B','candidate_MAC_8B'),encoding='utf-8')
bridge=(RUN/'b_sft8b_bridge_recovery_v2/bridge_recovery.ps1').read_text(encoding='utf-8-sig')
bridge=bridge.replace('b_sft8b_package_v3','mac8b_delivery_v1').replace('candidate_B_8B','candidate_MAC_8B')
bridge=bridge.replace('temporal_sft8b_dev_v1/decision.json','mac8b_delivery_v1/dev/decision.json')
bridge=bridge.replace("(Join-Path $RunRoot 'mac8b_delivery_v1/dev/decision.json')","(Join-Path $packageLocal 'dev/decision.json')")
(HERE/'bridge_and_deliver.ps1').write_text(bridge,encoding='utf-8')
shutil.copyfile(RUN/'b_sft8b_bridge_recovery_v2/bounded_native.ps1',HERE/'bounded_native.ps1')
for p in HERE.rglob('*.py'):
    ast.parse(p.read_text(encoding='utf-8'))
print('PASS independent sources compile; completed versions unchanged')
