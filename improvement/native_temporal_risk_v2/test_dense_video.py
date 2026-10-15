"""Target-only CPU recovery checks; never run old successful inputs or models.

Modes: mock (stdlib fixtures), audit (saved proofs + resize predictions only),
target (fresh encode only the failed 23-frame source273/window2 request).
Results print to stdout; the invoking controller owns create-only receipts.
"""
import ast
import copy
import hashlib
import importlib.util
import json
import math
import sys
from collections import UserDict
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
V1 = RUN/'overnight_risk_20261012_v1/dense128_v1'
FAILED_KEY = '772d1cb2df093da55cc45eb109e749893721aebc157cd2caa1964ff31ee18adb'


def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module


def fixture_smart_resize(num_frames,height,width,temporal_factor=2,factor=32,min_pixels=16384,max_pixels=12582912):
    """Observed fixed Transformers4.57.1 primitive, for stdlib wrapper mocks."""
    if num_frames<temporal_factor or min(height,width)<factor or max(height,width)/min(height,width)>200:
        raise ValueError('invalid resize dimensions')
    h_bar=round(height/factor)*factor;w_bar=round(width/factor)*factor;t_bar=round(num_frames/temporal_factor)*temporal_factor
    if t_bar*h_bar*w_bar>max_pixels:
        beta=math.sqrt(num_frames*height*width/max_pixels)
        h_bar=max(factor,math.floor(height/beta/factor)*factor);w_bar=max(factor,math.floor(width/beta/factor)*factor)
    elif t_bar*h_bar*w_bar<min_pixels:
        beta=math.sqrt(min_pixels/(num_frames*height*width))
        h_bar=math.ceil(height*beta/factor)*factor;w_bar=math.ceil(width*beta/factor)*factor
    return h_bar,w_bar


class Grid:
    def __init__(self,value):self.value=value
    def tolist(self):return self.value


class MockProcessor:
    video_processor=SimpleNamespace(patch_size=16,temporal_patch_size=2,merge_size=2,do_resize=True)
    def __init__(self):self.calls=[]
    def __call__(self,**kwargs):
        self.calls.append(copy.deepcopy({k:v for k,v in kwargs.items() if k!='videos'}))
        video=kwargs['videos'][0];t,h,w=video.shape[0],video.shape[-2],video.shape[-1]
        size=kwargs['videos_kwargs']['size'];h,w=fixture_smart_resize(t,h,w,min_pixels=size['shortest_edge'],max_pixels=size['longest_edge'])
        return UserDict(video_grid_thw=[Grid([(t+1)//2,h//16,w//16])],input_ids=SimpleNamespace(shape=(1,12345)))


def mock():
    new=load(HERE/'dense_video.py','mock_dense_video_v2')
    old_path=HERE.parent/'native_temporal_risk_v1/dense_video.py'
    if not old_path.exists():old_path=V1/'dense_video.py'
    old=load(old_path,'mock_dense_video_v1')
    ast.parse((HERE/'dense_video.py').read_text());ast.parse(Path(__file__).read_text())
    new._smart_resize_function=lambda:fixture_smart_resize
    vp=MockProcessor();checked=0
    for t in range(2,129):
        for h,w in ((1080,1920),(1280,720),(720,1280),(1080,1080),(192,3840)):
            plan=new.padding_resize_plan(vp,(t,3,h,w),fixture_smart_resize)
            original_h,original_w=fixture_smart_resize(t,h,w,min_pixels=4096,max_pixels=25165824)
            original_total=((t+1)//2)*2*original_h*original_w
            assert plan['adjusted']==(original_total>25165824)
            assert plan['predicted_total_pixels']<=25165824
            if not plan['adjusted']:assert plan['actual_resize_cap']==25165824
            checked+=1
    unaffected=0
    for t,h,w in ((128,1080,1920),(128,1280,720),(128,720,1280),(64,1080,1920),(23,720,1280),(2,1080,1920)):
        a,b=MockProcessor(),MockProcessor();args=dict(text=['fixed'],videos=[SimpleNamespace(shape=(t,3,h,w))],video_metadata=[{'frames_indices':list(range(t))}])
        old_encoded=old.encode(a,**args);new_encoded=new.encode(b,**args)
        assert a.calls==b.calls and old.identity(a,old_encoded,t)==new.identity(b,new_encoded,t)
        assert old_encoded.keys()==new_encoded.keys()
        unaffected+=1
    proc=MockProcessor();encoded=new.encode(proc,text=['fixed'],videos=[SimpleNamespace(shape=(23,3,1080,1920))],video_metadata=[{}])
    identity=new.identity(proc,encoded,23)
    assert identity['video_grid_thw']==[12,48,84] and identity['processor_total_pixels']==24772608
    assert identity['padding_aware_resize']['actual_resize_cap']==24117248
    assert new._EVIDENCE_ATTRIBUTE not in encoded and set(encoded)=={'video_grid_thw','input_ids'}
    assert identity['explicit_size']==old.LEGACY_VIDEO_SIZE
    print(json.dumps(dict(status='PASS_PADDING_AWARE_MOCKS',predictions=checked,unchanged_call_and_identity_fixtures=unaffected,
        target_grid=identity['video_grid_thw'],target_total_pixels=identity['processor_total_pixels'],actual_resize_cap=24117248,
        model_data_keys_unchanged=True,new_model_calls=0)))


def runtime():
    # The isolated test process may import frozen helpers but never edits them.
    sys.path.insert(0,str(V1))
    return load(V1/'dense_runtime.py','target_only_dense_runtime_v1')


def audit():
    r=runtime();new=load(HERE/'dense_video.py','audit_dense_video_v2');old=load(V1/'dense_video.py','audit_dense_video_v1')
    processor=r.processor_cpu();checked=0;source273_failed=False
    proofs=sorted((V1/'rematch_01/prepare_01').glob('*/proof.json'))
    if len(proofs)!=314:raise ValueError('expected exactly314 completed v1 CPU proofs')
    for path in proofs:
        proof=r.read(path);w=proof['window'];e=proof['input_evidence']
        t=e['sampled_frames'];plan=new.padding_resize_plan(processor,(t,3,w['height'],w['width']))
        if plan['adjusted'] or plan['predicted_grid']!=e['video_grid_thw']:raise ValueError('successful frozen proof would change: '+str(path))
        fake={'video_grid_thw':[Grid(e['video_grid_thw'])],'input_ids':SimpleNamespace(shape=(1,e['input_tokens']))}
        if new.identity(processor,fake,t)!=old.identity(processor,fake,t):raise ValueError('successful identity would change')
        checked+=1
    pilots=0
    for path in sorted((V1/'pilot_01/prepare_01').glob('*/proof.json')):
        proof=r.read(path);w=proof['window'];e=proof['input_evidence'];t=e['sampled_frames']
        plan=new.padding_resize_plan(processor,(t,3,w['height'],w['width']))
        if t!=128 or plan['adjusted'] or plan['predicted_grid']!=e['video_grid_thw']:raise ValueError('frozen128 pilot would change')
        fake={'video_grid_thw':[Grid(e['video_grid_thw'])],'input_ids':SimpleNamespace(shape=(1,e['input_tokens']))}
        if new.identity(processor,fake,t)!=old.identity(processor,fake,t):raise ValueError('pilot identity would change')
        pilots+=1
    if pilots!=6:raise ValueError('six frozen128 pilot proof denominator differs')
    w=r.read(V1/'rematch_01/prepare_01'/FAILED_KEY/'request.json')
    plan=new.padding_resize_plan(processor,(23,3,w['height'],w['width']))
    if not plan['adjusted'] or plan['original_predicted_total_pixels']<=25165824:raise ValueError('failed target does not reproduce padding overflow')
    print(json.dumps(dict(status='PASS_314_PLUS_SIX_UNAFFECTED_PREDICTION_AND_IDENTITY',proofs=checked,pilots=pilots,
        successful_native_decodes_repeated=0,successful_processor_encodes_repeated=0,old_tensor_signature_bytes_rewritten=0,
        failed_target_resize_plan=plan,CPU_only=True,new_model_calls=0)))


def target():
    import torch
    r=runtime();new=load(HERE/'dense_video.py','dense_video')
    request_path=V1/'rematch_01/prepare_01'/FAILED_KEY/'request.json';w=r.read(request_path)
    if w['source_id']!='273' or w['index']!=2 or len(w['source_frame_ordinals'])!=23 or (w['height'],w['width'])!=(1080,1920):
        raise ValueError('only original failed source273/window2/23-frame target is permitted')
    out=HERE/'target_cpu_01';out.mkdir(exist_ok=False)
    try:
        r.save(out/'request.json',w)
        processor=r.processor_cpu()
        encoded,evidence=r.encode_window(processor,w)
        expected=new.padding_resize_plan(processor,(23,3,1080,1920))
        if evidence['padding_aware_resize']!=expected or evidence['video_grid_thw']!=[12,48,84]:raise ValueError('actual targeted grid/cap differs')
        if evidence['physical_frames']!=23 or evidence['processor_effective_frames']!=24 or torch.cuda.is_initialized():
            raise ValueError('target native frame denominator or CPU-only contract differs')
        if new._EVIDENCE_ATTRIBUTE in encoded:raise ValueError('resize evidence leaked into model tensor data')
        r.save(out/'proof.json',dict(window=w,input_evidence=evidence,processor_weights_loaded=False,
            CUDA_initialized=False,new_model_calls=0,RGB_cached=False))
        result=dict(status='PASS_ONLY_FAILED23_FRAME_ACTUAL_NATIVE_PROCESSOR',utc=r.utc(),
            original_failed_request_path=str(request_path),original_failed_request_sha256=r.sha(request_path),
            request_path=str(out/'request.json'),request_sha256=r.sha(out/'request.json'),
            proof_path=str(out/'proof.json'),proof_sha256=r.sha(out/'proof.json'),
            bound_files={str(HERE/'dense_video.py'):r.sha(HERE/'dense_video.py'),
                str(Path(__file__).resolve()):r.sha(Path(__file__).resolve()),
                str(V1/'dense_runtime.py'):r.sha(V1/'dense_runtime.py')},
            source_id=w['source_id'],index=w['index'],input_evidence=evidence,
            encoded_model_data_keys=sorted(encoded.keys()),CPU_only=True,CUDA_initialized=False,new_model_calls=0,
            successful314_encodes_repeated=0,source_pts_and_sampling_unchanged=True,
            prepared_once_for_explicit_v2_handoff=True)
        r.save(out/'completion.json',result)
        print(json.dumps(result,ensure_ascii=False))
    except Exception as exc:
        r.failure(out,exc);raise


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('mock','audit','target'):raise ValueError('usage: test_dense_video.py mock|audit|target')
    {'mock':mock,'audit':audit,'target':target}[sys.argv[1]]()
