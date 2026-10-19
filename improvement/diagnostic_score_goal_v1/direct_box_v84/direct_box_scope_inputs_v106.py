"""Conditional single-source19/formal input scopes; no actions on import.

CPUreg direct_box_scope_CPU_registration_106_PHASE.json, PHASE confirm19|formal.
schema DIRECT_BOX_EXTERNAL_SOURCE_ONLY_CPU_V106. Refs: preparation_code,
base_input_code87,model_config,source_catalog,CPU_targets(confirm only),domain
(formal only),training_completion,adapter_weights,head_weights,
native20_quality_summary/native20_quality_result,protocol; formal additionally
confirm19_quality_summary/confirm19_quality_result. admitted_arm_names,expected_sources,
deadline_utc,max_seconds,max_new_bytes; formal official_source_count426 and
affected_video_count. Explicit catalogs only; no search or old72 quality gate.
"""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction
import gzip
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import sys
import time
import datetime as dt
import traceback

SCHEMA='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V106'
GATE='PASS_DIRECT_BOX106_SOURCE_ONLY_FIRST_CPU_QA'
CPU_SCHEMA='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_CPU_V106'
SELECTION='OBS_INDEX_EVEN'
EXCLUDED='gnmc:test:006575.jpeg'
BASELINE_SHA='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'


def scope_paths(root,phase):
    require(phase in ('confirm19','formal'),'Only explicit new106 external scopes')
    root=Path(root)
    return dict(registration=root/('direct_box_scope_CPU_registration_106_'+phase+'.json'),
        output=root/'direct_box_scope_inputs_106'/phase,
        remaining=root/'direct_box_scope_remaining_admission_106_formal.json')


def require(value,message):
    if not value:raise ValueError(message)


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


def load_base(reg):
    import hashlib
    r=reg['base_input_code'];p=Path(r['path']).resolve()
    require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],'Exact frozen87 source-only helper')
    return module(p,'_direct106_frozen87')


def validate_quality(reg,summary,*,result_key):
    arms=summary['admitted_arm_names']
    require(summary['status'].startswith('PASS_') and bool(arms) and len(arms)==len(set(arms))
        and set(arms)<=set(('DIRECT','ANCHORED_HALF'))
        and all(summary[k]==reg[k] for k in ('training_completion','adapter_weights','head_weights')),
        'Actual fixed direct-box weights and qualified arm summary required')
    require(set(reg['admitted_arm_names'])<=set(arms) and reg['admitted_arm_names'],'Only previously qualified frozen arms')
    if 'result' in summary:require(summary['result']==reg[result_key],'Actual rich CPU quality ref bound by summary')


def validate_native105_summary(reg,summary):
    require(summary['status']=='PASS_DIRECT_BOX105_NATIVE20_QUALIFIED_ARMS','Only independent105 native20 quality can qualify106')
    validate_quality(reg,summary,result_key='native20_quality_result')


def validate_confirm106_summary(reg,summary):
    require(summary['status']=='PASS_DIRECT_BOX106_CONFIRM19_QUALIFIED_ARMS','Only independent106 fixed19 qualification')
    validate_quality(reg,summary,result_key='confirm19_quality_result')


def same_source_only_inputs(native_requests,profile_requests):
    """Metadata identity only: equal actual F4 must adopt QA, never re-forward."""
    require(len(native_requests)==len(profile_requests)==20,'Complete original20 identity scope')
    for a,b in zip(native_requests,profile_requests):
        require(all(a[k]==b[k] for k in ('source_id','source_sha256','width','height','input_signature','image_grid_thw'))
            and a['actual_input_domain']==b['actual_input_domain']=='ACCEPTED_PROCESSOR_RESIZED_FULL_SOURCE_PATCH'
            and len(a['image_grid_thw'])==1,'Profile is exactly the same source-only observation/domain')
    return dict(status='IDENTICAL_SOURCE_ONLY_F4_ADOPT_PRIOR_OUTPUT_QA',sources=20,
        new_model_calls=0,new_first_QA=0,independent_quality_evidence=False)


def compile_formal_domain(accepted,metadata,baseline,clocks,source_refs):
    """Pure fixed even observation intersection; no pixels/labels/nearest map."""
    import hashlib
    def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    a={r['id']:r for r in accepted['sources']};m={r['video_id']:r for r in metadata['records']};b={r['video_id']:r for r in baseline}
    require(len(accepted['sources'])==len(metadata['records'])==len(baseline)==426
        and set(a)==set(m)==set(b)=={str(i) for i in range(426)},'Whole426 original accepted/baseline metadata')
    all_d=[];selected=[]
    for vid in sorted(a,key=int):
        source,meta,base=a[vid],m[vid],b[vid]
        require(base['targetRatioWH']==meta['targetRatioWH'] and source['native_frames']==meta['n_frames'],'Original native/ratio identity')
        if meta['targetRatioWH']!=[16,9]:continue
        clock=clocks[vid];pts=clock['normalized_exact_pts'];pred={r['frame']:r['bboxes'] for r in base['predictions']}
        require(clock['video_id']==vid and clock['source_sha256']==meta['source_sha256'] and len(pts)==source['native_frames']
            and Fraction(pts[0])==0 and source_refs[vid]['clock']['sha256']==source['clock_sha256']
            and all(Fraction(x)<Fraction(y) for x,y in zip(pts,pts[1:])),'Exact native source PTS')
        observation=0;previous=-1
        for chunk in source['chunks']:
            start=0;require(len(chunk['samples'])==len(chunk['grid']),'Actual accepted chunk row metadata')
            for row,(native,grid) in enumerate(zip(chunk['samples'],chunk['grid'])):
                require(type(native)==int and previous<native<len(pts) and len(grid)==3 and grid[0]==1
                    and all(type(v)==int and v>0 for v in grid) and grid[1]%2==grid[2]%2==0,'Unique actual observations/grid')
                previous=native;end=start+math.prod(grid)
                identity=dict(video_id=vid,source_sha256=meta['source_sha256'],native_ordinal=native,native_pts_exact=pts[native],observation_index=observation)
                if native in pred:
                    all_d.append(identity)
                    if observation%2==0:
                        selected.append(dict(**identity,source_id='official:%s:native:%d'%(vid,native),role='formal',width=meta['width'],height=meta['height'],
                            baseline_box=copy.deepcopy(pred[native]),original_BASE_observed=True,targetRatioWH=[16,9],
                            source_vision=dict(path=chunk['path'],sha256=chunk['sha256']),clock=source_refs[vid]['clock'],
                            original_proof=source_refs[vid]['acceptance'],source_layout=dict(row_index=row,row_start=start,row_end_exclusive=end,grid_thw=grid)))
                start=end;observation+=1
            require(start==chunk['pixel_shape'][0],'Cumulative actual patch rows')
        require(observation==source['feature_cells'],'Complete original observation sequence')
    selected.sort(key=lambda s:(s['source_sha256'],s['video_id'],s['native_ordinal']))
    require(len(selected)>=32 and len({s['source_id'] for s in selected})==len(selected),'Fixed positive unique formal owners')
    return dict(selection=SELECTION,all_D=all_d,selected_D=selected,all_D_count=len(all_d),selected_D_count=len(selected),
        all_D_sha256=digest(all_d),selected_D_sha256=digest(selected),pilot_source_ids=[s['source_id'] for s in selected[:32]],
        remaining_source_ids=[s['source_id'] for s in selected[32:]],official_source_count=426,
        affected_video_count=len({s['video_id'] for s in selected}),protected_baseline_sha256=BASELINE_SHA,
        no_nearest_or_interpolation=True)


def extract_view(raw,source,base):
    """Confirmed external full-source or exact registered native chunk row."""
    import torch
    if source['role']!='formal':
        require('source_vision_signature' in source,'Original accepted19 full-source signature required')
        sig=base.signature({k:raw[k] for k in ('pixel_values','image_grid_thw')})
        require(all(sig[k]==source['source_vision_signature'][k] for k in sig),'Adopt exact successful original19 new_vision')
        packed,meta=base.extract_source_prefix(raw,raw['image_grid_thw'][0].tolist())
        base.independent_prefix_check(raw,packed,raw['image_grid_thw'][0].tolist(),meta)
        return packed,meta
    g,p=raw['image_grid_thw'],raw['pixel_values'];layout=source['source_layout'];row=layout['row_index']
    require(g.dtype==torch.int64 and p.dtype==torch.float32 and g.device.type==p.device.type=='cpu'
        and type(row)==int and 0<=row<len(g),'Actual accepted formal chunk dtype/row')
    sizes=g.prod(dim=1);start=int(sizes[:row].sum());end=start+int(sizes[row])
    require(int(sizes.sum())==len(p) and layout['row_start']==start and layout['row_end_exclusive']==end
        and layout['grid_thw']==g[row].tolist(),'Exact per-row grid prefix sums, no fixed240')
    sliced=dict(pixel_values=p[start:end].contiguous(),image_grid_thw=g[row:row+1].contiguous())
    packed,meta=base.extract_source_prefix(sliced,layout['grid_thw']);base.independent_prefix_check(sliced,packed,layout['grid_thw'],meta)
    return packed,meta


class DirectBoxScopeInputs:
    def __init__(self,root,*,phase,registration_ref):
        from hashlib import sha256
        root=Path(root);gpu=json.loads(Path(registration_ref['path']).read_text())
        require(sha256(Path(registration_ref['path']).read_bytes()).hexdigest()==registration_ref['sha256'],'Exact107 registration')
        cpu_ref=gpu['CPU_registration'];cpu=json.loads(Path(cpu_ref['path']).read_text())
        self.base=load_base(cpu);self.base.bound(cpu_ref)
        require(self.base.bound(cpu_ref)==scope_paths(root,phase)['registration'].resolve()
            and self.base.bound(gpu['preparation_code'])==Path(__file__).resolve() and cpu['phase']==phase
            and cpu['preparation_code']==gpu['preparation_code'],'Exact106 CPU preparation identity')
        gate=self.base.read(self.base.bound(gpu['input_acceptance']));self.prepared=self.base.read(self.base.bound(gpu['prepared']))
        require(gate['status']==GATE and gate['registration']==cpu_ref and gate['prepared']==gpu['prepared']
            and gate['phase']==phase and self.prepared['phase']==phase and self.prepared['schema']==SCHEMA,'Actual one-scope106 first input gate')
        entries=self.prepared['inference_inputs'];require(len(entries)==len({e['id'] for e in entries})==gate['inputs']==gate['sources']
            and self.prepared['execution_entries']==entries and self.prepared['adopted_success']=={},'Complete one-owner one-input inventory')
        if phase=='formal':require(gate['official_source_count']==self.prepared['official_source_count']==426,'Whole426 protection distinct from observation count')
        self.reader=self.base.DirectBoxInputs.__new__(self.base.DirectBoxInputs)
        self.reader.prepared=self.prepared;self.reader.allowed={e['id']:e for e in entries}
        self.reader.ref_to_id={(e['input']['path'],e['input']['sha256']):e['id'] for e in entries};self.reader.current_id=None;self.reader.cache=None
    def get(self,r):return self.reader.get(r)
    def get_metadata(self,r):return self.reader.get_metadata(r)


def load_inputs(root,*,phase,registration_ref):return DirectBoxScopeInputs(root,phase=phase,registration_ref=registration_ref)


def run(root,phase,stage='all'):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Only CPU106 child')
    import torch
    from transformers import AutoProcessor
    root=Path(root);paths=scope_paths(root,phase);rp=paths['registration'];reg=json.loads(rp.read_text())
    base=load_base(reg);require(reg['schema']==CPU_SCHEMA and reg['phase']==phase and base.bound(reg['preparation_code'])==Path(__file__).resolve(),'Explicit new conditional106 CPU registration')
    def summary(name):
        value=reg[name];return base.read(base.bound(value)) if set(value)=={'path','sha256'} else value
    native=summary('native20_quality_summary');validate_native105_summary(reg,native);base.bound(reg['native20_quality_result'])
    if phase=='formal':
        confirm=summary('confirm19_quality_summary');validate_confirm106_summary(reg,confirm);base.bound(reg['confirm19_quality_result'])
        require(set(reg['admitted_arm_names'])==set(native['admitted_arm_names'])&set(confirm['admitted_arm_names']),'Exact previously qualified arm intersection')
    sources=base.read(base.bound(reg['source_catalog']))['sources'];require(len(sources)==reg['expected_sources'] and len({s['source_id'] for s in sources})==len(sources),'Exact explicit source scope')
    if phase=='confirm19':
        require(stage=='all' and len(sources)==19 and all(s['source_id']!=EXCLUDED and s['role']=='confirm' for s in sources)
            and set(reg['admitted_arm_names'])==set(native['admitted_arm_names']),'Only fixed successful original19/all native-qualified arms')
        original=base.read(base.bound(reg['original_confirm_prepared']))['entries']
        require(len(original)==20 and [s['original_entry'] for s in sources]==original[1:],'Exact original20 entries[1:] metadata/cache, never substitute missing source')
        require(base.read(base.bound(original[0]))['item_id']==EXCLUDED,'Exact lost source permanently excluded')
        for s,r in zip(sources,original[1:]):
            row=base.read(base.bound(r))
            require(row['item_id']==s['source_id'] and row['source_sha256']==s['source_sha256'] and row['new_vision']==s['source_vision']
                and row['new_vision_signature']==s['source_vision_signature'],'Original successful19 full-source vision mapping')
    else:
        require(phase=='formal' and stage in ('pilot32','remaining'),'Formal requires first32 then explicit remaining')
        domain=base.read(base.bound(reg['domain']));require(domain['selection']==SELECTION and domain['selected_D']==sources
            and domain['selected_D_sha256']==base.digest(sources) and domain['all_D_sha256']==base.digest(domain['all_D'])
            and domain['protected_baseline_sha256']==reg['protected_baseline']['sha256']==BASELINE_SHA
            and domain['official_source_count']==reg['official_source_count']==426,'Fixed even exactnative40.47 domain')
        base.bound(reg['protected_baseline'])
        require(all(s['source_id']=='official:%s:native:%d'%(s['video_id'],s['native_ordinal']) and s['observation_index']%2==0
            and s['targetRatioWH']==[16,9] for s in sources),'Every selected owner is the exact even-index native16 observation')
    out=paths['output'];out.parent.mkdir(exist_ok=True)
    if stage!='remaining':out.mkdir(exist_ok=False)
    else:require(out.is_dir(),'Adopt prior successful formal32 scope')
    started=time.monotonic();receipts=[];entries=[];budget_reg=reg
    if stage=='remaining':
        cp=paths['remaining'];continuation=base.read(cp);pilot=base.read(base.bound(continuation['pilot_acceptance']))
        require(pilot['status']=='PASS_DIRECT_BOX106_FORMAL_CPU_PILOT32_ONLY' and pilot['registration']==base.ref(rp)
            and continuation['schema']=='DIRECT_BOX106_FORMAL_REMAINING_CPU_ADMISSION' and continuation['original_registration']==base.ref(rp)
            and continuation['domain']==reg['domain'] and continuation['source_catalog']==reg['source_catalog']
            and continuation['remaining_source_ids']==[s['source_id'] for s in sources[32:]],'Only explicit same-domain remaining, no pilot repeat')
        entries=pilot['entries'];receipts=pilot['first_QA'];selected=sources[32:]
        require(len(entries)==len(receipts)==32 and [e['source_id'] for e in entries]==[s['source_id'] for s in sources[:32]],'Adopt exact original32 without repeat')
        for proof in receipts:base.bound(proof)
        budget_reg=continuation
    else:selected=sources[:32] if stage=='pilot32' else sources
    writer=base.Writer(out,budget_reg['max_new_bytes'])
    def budget():require(time.monotonic()-started<budget_reg['max_seconds'] and dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(budget_reg['deadline_utc'].replace('Z','+00:00')),'Explicit CPU106 budget/deadline')
    writer.json(out/(stage+'_claim.json'),dict(registration=base.ref(rp),phase=phase,stage=stage,model_calls=0))
    try:
        cfg=base.read(base.bound(reg['model_config']));processor=AutoProcessor.from_pretrained(cfg['model_dir'],local_files_only=True,min_pixels=65536,max_pixels=65536)
        for s in selected:
            budget();identifier=base.digest(['DIRECT106_SOURCE',s['source_id'],s['source_sha256']])[:24]
            raw=torch.load(base.bound(s['source_vision']),map_location='cpu',weights_only=True);packed,layout=extract_view(raw,s,base)
            tokens,text=base.build_text_input(processor,packed['image_grid_thw']);qa=base.independent_text_check(processor,packed,tokens,text)
            values=dict(**tokens,**packed);stream=io.BytesIO();torch.save(values,stream);payload=stream.getvalue();compressed=gzip.compress(payload,compresslevel=6,mtime=0)
            encoded=writer.data(out/(identifier+'.pt.gz'),compressed)
            actual=torch.load(io.BytesIO(gzip.decompress(base.bound(encoded).read_bytes())),map_location='cpu',weights_only=True)
            require(base.signature(actual)==base.signature(values),'First new106 lossless F4 roundtrip')
            q=dict(id=identifier,source_id=s['source_id'],source_sha256=s['source_sha256'],role=s['role'],width=s['width'],height=s['height'],
                input_signature=base.signature(values),image_grid_thw=packed['image_grid_thw'].tolist(),text_evidence=text,prompt=base.PROMPT,
                encoded_input=encoded,codec=dict(codec=base.CODEC,uncompressed_bytes=len(payload),compressed_bytes=len(compressed)),
                reference_or_target_in_prompt=False,native_RGB_recovered=False,actual_input_domain='ACCEPTED_PROCESSOR_RESIZED_FULL_SOURCE_PATCH',
                source_layout=copy.deepcopy(s['source_layout']) if phase=='formal' else layout,prefix_extraction=layout,
                original_source_tensor=s['source_vision'],original_proof=s['original_proof'],phase=phase,
                training_completion=reg['training_completion'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'])
            for k in ('video_id','native_ordinal','native_pts_exact','observation_index','clock','targetRatioWH'):
                if k in s:q[k]=s[k]
            qr=writer.json(out/(identifier+'.json'),q);proof=writer.json(out/(identifier+'.first_QA.json'),dict(request=qr,text_QA=qa,source_layout=layout,compressed_four_tensor_roundtrip=True,old_source_processor_repeated=False,new_original_decode=0))
            entries.append(dict(id=identifier,source_id=s['source_id'],source_sha256=s['source_sha256'],role=s['role'],input=qr));receipts.append(proof)
        if stage=='pilot32':
            writer.json(out/'pilot_acceptance.json',dict(status='PASS_DIRECT_BOX106_FORMAL_CPU_PILOT32_ONLY',registration=base.ref(rp),domain=reg['domain'],entries=entries,first_QA=receipts,
                sources=32,new_bytes_before_acceptance=writer.bytes,elapsed_seconds=time.monotonic()-started,model_calls=0,production_admitted=False));return
        require([e['source_id'] for e in entries]==[s['source_id'] for s in sources],'All exact original scope owners; no fallback source')
        prepared=dict(schema=SCHEMA,phase=phase,inference_inputs=entries,execution_entries=entries,adopted_success={},sources=len(sources),
            source_catalog=reg['source_catalog'],CPU_targets=reg['CPU_targets'] if phase=='confirm19' else None,domain=reg.get('domain'),
            training_completion=reg['training_completion'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],admitted_arm_names=reg['admitted_arm_names'],
            observation_profile='ACCEPTED_PROCESSOR_RESIZED_FULL_SOURCE_PATCH',native_RGB_recovered=False,production_admitted=False)
        if phase=='formal':prepared.update(official_source_count=426,affected_video_count=reg['affected_video_count'],selection=SELECTION,protected_baseline=reg['protected_baseline'])
        pr=writer.json(out/'prepared.json',prepared)
        gate=dict(status=GATE,phase=phase,registration=base.ref(rp),prepared=pr,inputs=len(entries),sources=len(sources),first_QA=receipts,new_bytes_before_acceptance=writer.bytes,
            elapsed_seconds=time.monotonic()-started,new_original_decode=0,old_source_processor_repeated=0,model_calls=0)
        if phase=='formal':gate.update(official_source_count=426,affected_video_count=reg['affected_video_count'])
        writer.json(out/'input_acceptance.json',gate)
    except BaseException as error:
        with (out/(stage+'_failure.json')).open('x',encoding='utf-8') as stream:json.dump(dict(error=repr(error),traceback=traceback.format_exc(),completed=receipts,preserve_all_success=True,automatic_retry=False),stream,indent=2)
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['confirm19','formal'],required=True)
    p.add_argument('--stage',choices=['all','pilot32','remaining'],default='all');a=p.parse_args();run(a.root,a.phase,a.stage)
