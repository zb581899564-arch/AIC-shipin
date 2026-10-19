"""First source-overview CPU input QA; frozen pilot and conditional remainder."""
import argparse
from collections import OrderedDict
from pathlib import Path
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pair_common import *
from context_video_input import build_context_pixels,build_context_text,independent_context_pixel_check,independent_context_text_check

GATE='PASS_ALL_NEW_SOURCE_OVERVIEW_CONTEXT_INPUTS'

def registration28(root):
    reg=read(root/'context_CPU_registration_28.json')
    require(reg['schema']=='THREE_VIDEO_SOURCE_OVERVIEW_CPU_INPUTS_V28' and
            bound(reg['preparation_code'])==Path(__file__).resolve(),'Explicit frozen context preparation entry')
    import context_video_input
    require(bound(reg['context_code'])==Path(context_video_input.__file__).resolve(),'Exact new context helper')
    old=read(bound(reg['pair_registration']))
    for name,digest in old['new_code'].items():
        require(sha(root/'pair_code_17'/name)==digest,'Original17 helper must remain frozen')
    for reference in old['old_helpers']:bound(reference)
    require(read(bound(reg['training_completion']))['completed_updates']==200,'Only fixed final200 PAIR role')
    return reg,old

class ContextInputs:
    def __init__(self,root,*,preparing=False):
        self.root=Path(root);self.reg,self.old=registration28(self.root)
        self.catalog=read(bound(self.reg['source_catalog']))
        self.sources={s['id']:s for s in self.catalog['sources']}
        self.cache=OrderedDict()
        old_code=Path(bound(self.reg['old_input_acceptance'])).parent/'code'
        sys.path.insert(0,str(old_code))
        from data import source_pixels
        self.load_pixels=source_pixels
        if preparing:self.prepared=None
        else:
            gate=read(self.root/'context_inputs_28/input_acceptance.json')
            require(gate['status']==GATE and gate['registration']==ref(self.root/'context_CPU_registration_28.json'),
                    'Actual complete first context CPU input QA required')
            self.prepared=read(bound(gate['prepared']))
    def _source(self,sid):
        if sid in self.cache:self.cache.move_to_end(sid);return self.cache[sid]
        source=self.sources[sid]
        frames,grid,ordinals=self.load_pixels(source)
        clock=read(bound(source['clock']))
        require(clock['source_sha256']==source['source_sha256'],'Exact original native source clock')
        result=(frames,grid,ordinals,clock['normalized_exact_pts'])
        self.cache[sid]=result
        while len(self.cache)>2:self.cache.popitem(last=False)
        return result
    def construct(self,source_id,overview_id,ranges,foreign):
        local=self.sources[source_id];overview=self.sources[overview_id]
        a=self._source(source_id);b=self._source(overview_id)
        positional=(a[0],a[1],ranges,a[2],a[3],b[0],b[1],b[2],b[3])
        kwargs=dict(local_owner=dict(source_id=source_id,source_sha256=local['source_sha256']),
            overview_owner=dict(source_id=overview_id,source_sha256=overview['source_sha256']),
            overview_is_foreign=foreign,local_ref=local['old_acceptance'],overview_ref=overview['old_acceptance'],
            pairing_proof_ref=self.old['original_pairing_proof'])
        return build_context_pixels(*positional,**kwargs),positional,kwargs
    def get(self,reference):
        import torch
        request=read(bound(reference))
        require(request['source_sha256']==self.sources[request['source_id']]['source_sha256'] and
                request['overview_source_sha256']==self.sources[request['overview_source_id']]['source_sha256'],
                'Actual local and overview source identity')
        context,_,_=self.construct(request['source_id'],request['overview_source_id'],request['clip_ranges'],request['overview_is_foreign'])
        tokens=torch.load(bound(request['tokens']),map_location='cpu',weights_only=True)
        values=dict(**tokens,pixel_values_videos=context['pixel_values_videos'],video_grid_thw=context['video_grid_thw'])
        require(signature(values)==request['input_signature'] and context['video_metadata']==request['video_metadata'] and
                context['sample_bindings']==request['sample_bindings'],'New three-video first-QA input changed at prediction')
        return values,request

def prepare(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU preparation masks only itself')
    import torch
    from transformers import AutoProcessor
    torch.set_num_threads(2)
    reg,old=registration28(root)
    import datetime as dt
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')),
            'Inside overall authorized work window')
    loader=ContextInputs(root,preparing=True)
    inventory=read(bound(reg['case_inventory']))
    old_prepared=read(bound(reg['old_prepared']))
    originals={e['id']:e for e in old_prepared['dev_inputs']}
    require(len(originals)==295 and inventory['selected_by_GT_or_scores'] is False,'Frozen original295 input inventory')
    out=root/'context_inputs_28';out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(utc=utc(),pid=os.getpid(),registration=ref(root/'context_CPU_registration_28.json'),
         original_decode=0,original_processor_calls=0))
    cfg=read(bound(old['model_config']))
    processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,max_pixels=65536,min_pixels=65536)
    done=[];new_entries={};class_ids=None;matches=[]
    try:
        for specification in inventory['inputs']:
            oid=specification['original_case_id'];original=originals[oid];request=read(bound(original['input']))
            sid=request['source_id'];foreign=specification['overview_is_foreign'];overview_id=specification['overview_source_id']
            require(sid==specification['source_id'] and request['source_sha256']==loader.sources[sid]['source_sha256'],
                    'Adopt original actual A/B local source and ranges')
            context,args,kwargs=loader.construct(sid,overview_id,request['clip_ranges'],foreign)
            encoded,text=build_context_text(processor,context)
            independent_context_pixel_check(*args,context=context,**kwargs)
            independent_context_text_check(processor,context,encoded,text)
            if class_ids is None:class_ids=text['class_token_ids']
            require(class_ids==text['class_token_ids']==request['class_token_ids'],'One actual0/1/2 class identity')
            cid=specification['id'];directory=out/sid;directory.mkdir(exist_ok=True)
            tokens=directory/(cid+'.tokens.pt')
            with tokens.open('xb') as stream:torch.save(encoded,stream)
            require(signature(encoded)==signature(torch.load(tokens,map_location='cpu',weights_only=True)),'New prefix actual save/reload')
            values=dict(**encoded,pixel_values_videos=context['pixel_values_videos'],video_grid_thw=context['video_grid_thw'])
            path=directory/(cid+'.json')
            data=dict(id=cid,original_case_id=oid,old_input=original['input'],source_id=sid,source_sha256=request['source_sha256'],
                overview_source_id=overview_id,overview_source_sha256=loader.sources[overview_id]['source_sha256'],
                overview_is_foreign=foreign,clip_ranges=request['clip_ranges'],tokens=ref(tokens),input_signature=signature(values),
                class_token_ids=class_ids,video_grid_thw=context['video_grid_thw'].tolist(),video_metadata=context['video_metadata'],
                sample_bindings=context['sample_bindings'],source_refs=context['source_refs'],text_evidence=text,
                observation_appearances=context['observation_appearances'],distinct_owner_native_observations=context['distinct_owner_native_observations'],
                no_GT_or_label_in_prompt=True,old_two_video_QA_substituted=False)
            save(path,data)
            entry=dict(id=cid,source_id=sid,inputref=ref(path))
            done.append(entry);new_entries[cid]=entry
            matches.append(dict(id=cid,foreign=foreign,grid=data['video_grid_thw'],sequence_tokens=text['sequence_tokens'],
                visual_tokens=text['video_token_count'],observation_appearances=context['observation_appearances']))
            del values,encoded,context
        roles={name:[new_entries[cid] for cid in ids] for name,ids in inventory['pilot_role_ids'].items()}
        require(roles['BASE_TRUE']==roles['PAIR_TRUE'] and
                {k:len(v) for k,v in roles.items()}=={'BASE_TRUE':45,'PAIR_TRUE':45,'PAIR_FOREIGN':40},'Fixed130 pilot role count')
        prepared=out/'prepared.json'
        save(prepared,dict(source_catalog=reg['source_catalog'],inputs=done,pilot_roles=roles,case_inventory=reg['case_inventory'],
            all_TRUE_ids=inventory['all_TRUE_ids'],FOREIGN_ids=inventory['FOREIGN_ids'],class_token_ids=class_ids,
            profiles=matches,reference_labels_read_by_GPU=False,new_real_vision_processor_calls=0,original_decode=0,
            frozen_primary_role='PAIR_TRUE',remaining_or_production_admitted=False))
        save(out/'input_acceptance.json',dict(status=GATE,prepared=ref(prepared),registration=ref(root/'context_CPU_registration_28.json'),
            TRUE_inputs=295,FOREIGN_inputs=40,inputs=len(done),first_independent_pixels_text_native_owner_QA=True,
            actual3video_grids=True,old_two_video_QA_substituted=False,new_real_vision_processor_calls=0,original_decode=0))
        require(len(done)==335 and not torch.cuda.is_initialized(),'All335 first new inputs accepted on CPU')
        print('ALL335_CONTEXT_INPUTS_ACCEPTED',flush=True)
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),completed=done,preserve_all_success=True,
             no_automatic_retry=True))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);prepare(p.parse_args().root)
