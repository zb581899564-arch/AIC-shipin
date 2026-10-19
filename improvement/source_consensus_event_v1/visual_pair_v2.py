"""Real sparse native-frame pair comparison, bounded external pilot only."""
import os
import sys
from pathlib import Path
import json
import importlib.util
import datetime as dt
from fractions import Fraction as F
import hashlib
import numpy as np

W=Path('/home/inspur/aic_video_work');ROOT=W/'visual_pair_reject_20261018_v1'
RUN=W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PY=W/'env/qwen3vl_isolated_20260910/bin/python'
RAM=Path('/dev/shm/aic_visual_pair_reject_20261018_v1')


def leaf(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module


# Pure IO only. Never import a CPU entry module into this GPU process.
def require(condition,message):
    if not condition:raise ValueError(message)

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def ref(path):
    path=Path(path);h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return dict(path=str(path),bytes=path.stat().st_size,sha256=h.hexdigest())

def bound(value):
    path=Path(value['path']);actual=ref(path)
    require(actual['sha256']==value['sha256'] and ('bytes' not in value or actual['bytes']==value['bytes']),'Changed registered input '+str(path))
    return path

def save(path,value):
    with Path(path).open('x',encoding='utf8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)

class _Metadata:
    @staticmethod
    def utc():return dt.datetime.now(dt.timezone.utc).isoformat()

helper=_Metadata()


def deadline():
    limit=read(ROOT/'registration_01.json')['pilot_cutoff_utc']
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(limit.replace('Z','+00:00')),'Fixed pilot time limit')


def runtime():
    sys.path.insert(0,str(RUN/'baseline_a_pts_v1'))
    return leaf('_visual_pair_exact_runtime',W/'temporal_refinement_pilot_20261011/dev_01/runtime.py')


def sample_sheet(images,indices):
    from PIL import Image,ImageOps
    sheet=Image.new('RGB',(448,448),(127,127,127));tiles=[]
    for i,ordinal in enumerate(indices):
        source=Image.fromarray(images[ordinal]);tile=ImageOps.contain(source,(224,224),Image.Resampling.LANCZOS)
        x=(i%2)*224+(224-tile.width)//2;y=(i//2)*224+(224-tile.height)//2
        sheet.paste(tile,(x,y));tiles.append(dict(ordinal=ordinal,native_rgb_sha256=hashlib.sha256(images[ordinal].tobytes()).hexdigest(),tile_dimensions=[tile.width,tile.height],sheet_offset=[x,y]))
    return sheet,tiles


def prepare():
    os.environ['CUDA_VISIBLE_DEVICES']='';deadline()
    import torch,av
    from PIL import Image
    from transformers import AutoProcessor
    torch.set_num_threads(2)
    reg=read(ROOT/'registration_01.json');config=read(bound(reg['model_config_ref']))
    processor=AutoProcessor.from_pretrained(config['model_dir'],local_files_only=True)
    ip=processor.image_processor
    require(ip.patch_size==16 and ip.temporal_patch_size==2 and ip.merge_size==2 and list(ip.image_mean)==[.5,.5,.5] and list(ip.image_std)==[.5,.5,.5],'Pinned actual standard static image profile')
    out=ROOT/'prepare_01';out.mkdir();RAM.mkdir();records=[]
    for case in reg['cases']:
        deadline();sid=case['sid'];target=out/sid;target.mkdir();clock=read(bound(case['clock_ref']));media=bound(case['media_ref'])
        require(clock['source_sha256']==case['media_ref']['sha256'],'Original media/clock binding')
        wanted=set(case['anchor_ordinals']+case['candidate_ordinals']);images={};observed=[]
        with av.open(str(media)) as container:
            videos=container.streams.video;require(len(videos)==1,'Unique original video stream')
            stream=videos[0];stream.thread_count=2
            for ordinal,frame in enumerate(container.decode(stream)):
                if ordinal in wanted:
                    require(frame.pts is not None and str(F(frame.pts)*frame.time_base)==clock['original_exact_pts'][ordinal],'Actual first new-purpose native frame PTS')
                    image=frame.to_ndarray(format='rgb24');require(image.shape==(clock['height'],clock['width'],3),'Actual native RGB geometry')
                    images[ordinal]=image;observed.append(dict(ordinal=ordinal,pts_exact=clock['original_exact_pts'][ordinal],rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest()))
                if ordinal>=max(wanted):break
        require(set(images)==wanted,'Every requested actual frame decoded once')
        anchor,atile=sample_sheet(images,case['anchor_ordinals']);candidate,ctile=sample_sheet(images,case['candidate_ordinals'])
        anchor.save(target/'anchor.png');candidate.save(target/'candidate.png')
        source_proof=dict(case=case,observed_native_frames=observed,anchor_tiles=atile,candidate_tiles=ctile,source_ref=case['media_ref'],clock_ref=case['clock_ref'],sparse_not_continuous=True,first_new_purpose_decode=True)
        save(target/'source.json',source_proof)
        for order in ['AB','BA']:
            labels=['anchor','candidate'] if order=='AB' else ['candidate','anchor']
            sheets=[Image.open(target/(name+'.png')).convert('RGB') for name in labels]
            text=processor.apply_chat_template([dict(role='user',content=[dict(type='image'),dict(type='image'),dict(type='text',text=reg['prompt'])])],tokenize=False,add_generation_prompt=True,enable_thinking=False)
            require(text.count('<|image_pad|>')==2,'Actual two-image chat markers')
            encoded=processor(text=[text],images=sheets,do_resize=False,return_tensors='pt')
            require(encoded['image_grid_thw'].tolist()==[[1,28,28],[1,28,28]] and list(encoded['pixel_values'].shape)==[1568,1536],'Actual no-resize two448-image grids and patch count')
            path=RAM/(sid+'_'+order+'.pt');torch.save(dict(encoded),path)
            proof=dict(sid=sid,order=order,case_id=sid+'_'+order,sheet_names=labels,sheet_refs=[ref(target/(name+'.png')) for name in labels],source_proof_ref=ref(target/'source.json'),encoded_ref=ref(path),text=text,tensor_signature=runtime().tensor_signature(encoded),model_input_has_labels=False)
            save(target/(order+'.json'),proof);records.append(ref(target/(order+'.json')))
    require(len(records)==reg['expected_calls']==34,'Fixed17two-order inputs')
    save(out/'completion.json',dict(status='PASS34_REAL_SPARSE_IMAGE_INPUTS_PREPARED',inputs=records,registration_ref=ref(ROOT/'registration_01.json'),processor_calls=34,new_purpose_native_decode_sources=17,old_model_processor_successes_repeated=False,utc=helper.utc()))


def input_qa():
    os.environ['CUDA_VISIBLE_DEVICES']='';deadline()
    import torch
    from PIL import Image
    from transformers import AutoTokenizer
    torch.set_num_threads(2)
    cfg=read(bound(read(ROOT/'registration_01.json')['model_config_ref']))
    tokenizer=AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
    pixel_qa=leaf('_visual_pair_pure_pixel_checker',ROOT/'code_v1/crop_observation_v34.py')
    records=[]
    for value in read(ROOT/'prepare_01/completion.json')['inputs']:
        proof=read(bound(value));encoded=torch.load(bound(proof['encoded_ref']),map_location='cpu',weights_only=True)
        require(runtime().tensor_signature(encoded)==proof['tensor_signature'],'Serialized actual CPU tensor inventory')
        require(encoded['image_grid_thw'].tolist()==[[1,28,28],[1,28,28]],'Two actual static image grids')
        for i,sheet_ref in enumerate(proof['sheet_refs']):
            rgb=np.asarray(Image.open(bound(sheet_ref)).convert('RGB'));pixel=encoded['pixel_values'][i*784:(i+1)*784]
            direct,grid=pixel_qa.forward_pack_observation_rgb(rgb)
            require(torch.equal(pixel.contiguous().view(torch.uint8),direct.contiguous().view(torch.uint8)),'Every actual image normalized pixel/patch bit equals independent pure transform')
            recovered,metadata=pixel_qa.recover_observation_rgb(pixel,grid)
            require(np.array_equal(recovered,rgb),'Exact original sheet colors retained, no processor resize')
            pixel_qa.independent_recovery_check(pixel,grid,recovered,metadata)
        expanded=proof['text'].replace('<|image_pad|>','<|image_pad|>'*196)
        require(tokenizer.encode(expanded,add_special_tokens=False)==encoded['input_ids'][0].tolist(),'Independent two-image token expansion and text order')
        require(int((encoded['input_ids']==tokenizer.convert_tokens_to_ids('<|image_pad|>')).sum())==392,'Exactly two196-token image blocks')
        records.append(value)
    require(len(records)==34,'All first input QA complete before GPU')
    save(ROOT/'input_acceptance_01.json',dict(status='PASS34_FIRST_INDEPENDENT_REAL_PIXEL_PATCH_TOKEN_SOURCE_PTS_QA',inputs=records,pure_checker_ref=ref(ROOT/'code_v1/crop_observation_v34.py'),processor_calls=0,registration_ref=ref(ROOT/'registration_01.json'),utc=helper.utc()))


def gpu():
    deadline();require(os.environ.get('CUDA_VISIBLE_DEVICES')=='0','Actual nonempty CUDA0 under shared wrapper')
    import torch,time,math
    torch.set_num_threads(2)
    sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    reg=read(ROOT/'registration_01.json');inputs=read(ROOT/'input_acceptance_01.json');require(inputs['status'].startswith('PASS34'),'First independent inputs mandatory')
    rt=runtime();cfg=read(bound(reg['model_config_ref']));model,processor,identity=rt.b_engine.load_model(cfg)
    from peft.tuners.tuners_utils import BaseTunerLayer
    layers=[v for v in model.modules() if isinstance(v,BaseTunerLayer)];require(len(layers)==144,'Original TIME layer inventory')
    grammar_root=W/'twenty_hour_five_20261014_v1/candidate_verify_v2/code';sys.path.insert(0,str(grammar_root))
    import cv_grammar
    responses=tuple('{"choice":"'+v+'"}' for v in ['A','B','TIE','NEITHER'])
    token_candidates=cv_grammar.candidate_tokens(processor.tokenizer,responses)
    class Preference(cv_grammar.VerifyConstraint):
        def __init__(self,prefix,eos):
            self.tokenizer=processor.tokenizer;self.prompt_length=prefix;self.responses=responses;self.eos=frozenset(eos);self.candidates=tuple(sorted(set(token_candidates)-self.eos));self.cache={};self.stats=dict(calls=0,full_context_decodes=0,dead_ends=0)
    eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
    out=ROOT/'gpu_01';out.mkdir();save(out/'identity.json',identity);outputs=[]
    with model.disable_adapter():
        require(all(v.disable_adapters for v in layers),'Every actual TIME layer disabled for BASE comparisons')
        for value in inputs['inputs']:
            deadline();proof=read(bound(value));target=out/proof['case_id'];target.mkdir()
            encoded=torch.load(bound(proof['encoded_ref']),map_location='cpu',weights_only=True)
            require(rt.tensor_signature(encoded)==proof['tensor_signature'],'Accepted actual CPU input unchanged')
            tensors={k:v.to('cuda:0') for k,v in encoded.items()};require(rt.tensor_signature(tensors)==proof['tensor_signature'],'Actual GPU input equals independently accepted CPU tensors')
            prefix=tensors['input_ids'].shape[1];grammar=Preference(prefix,eos)
            save(target/'request.json',dict(input_ref=value,input_signature=proof['tensor_signature'],role='BASE_ALL144_ADAPTERS_DISABLED',model_call_begin=True,utc=helper.utc()))
            started=time.monotonic()
            with torch.inference_mode():generated=model.generate(**tensors,do_sample=False,max_new_tokens=32,prefix_allowed_tokens_fn=grammar,return_dict_in_generate=True,output_scores=True)
            torch.cuda.synchronize();ids=generated.sequences[0,prefix:];raw=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False);scores=[float(v[0,int(t)]) for v,t in zip(generated.scores,ids)]
            save(target/'raw.json',dict(raw=raw,ids=ids.tolist(),scores=scores,actual_model_call=True,role='BASE_DISABLED',elapsed=time.monotonic()-started,input_tokens=prefix,utc=helper.utc()))
            require(len(ids)==len(scores) and all(math.isfinite(v) for v in scores),'Actual complete finite output token denominator')
            decision=grammar.assert_complete(ids)
            require(decision['choice'] in ['A','B','TIE','NEITHER'],'Actual preference parser')
            save(target/'done.json',dict(status='ACTUAL_MODEL_PREFERENCE_OK',input_ref=value,raw_ref=ref(target/'raw.json'),choice=decision['choice'],sid=proof['sid'],order=proof['order']))
            outputs.append(ref(target/'done.json'));del tensors,encoded,generated
    require(all(not v.disable_adapters for v in layers),'Actual original adapter role restored')
    require(rt.b_engine.frozen_identity(model,cfg)==identity['base'] and rt.b_engine.adapter_identity(model,cfg)==identity['adapter'],'Actual model bytes unchanged')
    require(len(outputs)==34,'Exactly34 first real model calls')
    save(out/'completion.json',dict(status='PASS34_ACTUAL_BASE_PREFERENCES_NO_OPTIMIZER',outputs=outputs,identity_ref=ref(out/'identity.json'),actual_loaded_parameters=identity['logical_parameters'],utc=helper.utc()))


def evaluate():
    os.environ['CUDA_VISIBLE_DEVICES']='';deadline()
    reg=read(ROOT/'registration_01.json');gpu=read(ROOT/'gpu_01/completion.json');require(gpu['status'].startswith('PASS34'),'Complete actual model outputs')
    outputs={}
    for value in gpu['outputs']:
        done=read(bound(value));raw=read(bound(done['raw_ref']));require(json.loads(raw['raw'])==dict(choice=done['choice']),'Independent untouched raw JSON parse')
        outputs[(done['sid'],done['order'])]=done['choice']
    decisions=[]
    for case in reg['cases']:
        ab=outputs[(case['sid'],'AB')];ba=outputs[(case['sid'],'BA')]
        decisions.append(dict(sid=case['sid'],cohort=case['cohort'],AB=ab,BA=ba,keep=ab=='B' and ba=='A',case=case))
    save(ROOT/'decisions_before_metrics_01.json',dict(status='ALL17_FIXED_ORDER_BALANCED_DECISIONS_BEFORE_CURRENT_METRICS',decisions=decisions,labels_read=False,orders_not_independent=True,utc=helper.utc()))
    # Labels stay outside all model/preparation code, first read below.
    oldm=leaf('_visual_pair_metric_contract',W/'source_consensus_event_20261018_v1/code_v1/source_consensus.py');rows=[]
    for decision in decisions:
        case=decision['case'];sid=case['sid'];data=np.load(bound(case['original_input_ref']),allow_pickle=False);labels=np.load(W/'source_consensus_event_20261018_v1/diagnosis_01'/(sid+'_human_targets.npz'),allow_pickle=False)['labels'];mask=data['baseline'].copy()
        c=case['original_choice'];new=np.zeros(len(mask),bool);new[c['left']:c['right']]=~mask[c['left']:c['right']]
        contrast=float(labels[new].mean()-labels[mask].mean());benefit=contrast>0
        if decision['keep']:mask|=new
        before=oldm.critic.metric(data['baseline'],labels);after=oldm.critic.metric(mask,labels)
        rows.append(dict(sid=sid,keep=decision['keep'],actual_precision_benefit=benefit,actual_precision_contrast=contrast,delta={k:after[k]-before[k] for k in ['precision','recall','f1']},added_frames=int(new.sum()) if decision['keep'] else 0))
    result=dict(status='COMPLETED_ONE_VISUAL_PAIR_REJECT_PILOT_REVIEW_REQUIRED',sources=rows,kept=sum(r['keep'] for r in rows),kept_good=sum(r['keep'] and r['actual_precision_benefit'] for r in rows),kept_bad=sum(r['keep'] and not r['actual_precision_benefit'] for r in rows),rejected_good=sum(not r['keep'] and r['actual_precision_benefit'] for r in rows),rejected_bad=sum(not r['keep'] and not r['actual_precision_benefit'] for r in rows),macro_delta={k:float(np.mean([r['delta'][k] for r in rows])) for k in ['precision','recall','f1']},added_frames=sum(r['added_frames'] for r in rows),all_sources_previously_exposed=True,new_blind_confirmation=False,automatic_production=False,official_joint_score=None,utc=helper.utc())
    save(ROOT/'result_01.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    try:
        {'prepare':prepare,'input_qa':input_qa,'gpu':gpu,'evaluate':evaluate}[sys.argv[1]]()
    except BaseException as error:
        import traceback,uuid
        save(ROOT/('failure_'+uuid.uuid4().hex+'.json'),dict(stage=sys.argv[1],error=repr(error),traceback=traceback.format_exc(),successes_preserved=True,no_automatic_retry=True))
        raise
