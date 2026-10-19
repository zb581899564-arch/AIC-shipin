"""Conditional profile metadata, preserving original native reference geometry.

No pixels/tensors/processor/model reads. Exact original19 completed BASE records
are adopted; missing original006575 is never replaced, retried or made empty.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import read,save,ref,bound,require,utc


def module(reference,name):
    spec=importlib.util.spec_from_file_location(name,bound(reference));m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m


def run(root,scope):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU-only metadata compilation')
    rp=root/'utility_reference_registration_57.json';reg=read(rp)
    require(reg['schema']=='UTILITY_FIXED_PROFILE_REFERENCE_METADATA_V57'
        and bound(reg['code'])==Path(__file__).resolve(),'Exact new metadata purpose')
    quality=read(bound(reg['training_quality_admission']))
    require(quality['status']=='PASS_UTILITY_SCREEN20_ONLY' and quality['evaluation']['quality']['admitted'] is True,
        'Actual fresh utility quality before any new profile preparation')
    out=root/'utility_profile_reference_57'/scope;out.mkdir(parents=True,exist_ok=False)
    save(out/'claim.json',dict(utc=utc(),scope=scope,registration=ref(rp),new_model_calls=0,new_pixel_reads=0))
    try:
        if scope=='screen':
            old=read(bound(reg['original_screen_catalog']));oldtarget=read(bound(reg['original_screen_targets']))
            sources=[s for s in old['sources'] if s['role']=='screen'];ids={s['source_id'] for s in sources}
            targets=[s for s in oldtarget['sources'] if s['source_id'] in ids]
            require(len(sources)==len(targets)==20,'Exact original20 screen scope')
            plan=read(bound(reg['original_screen_case_plan']))
        else:
            require(scope=='confirm','Explicit screen or confirm only')
            helper=module(reg['confirm_pure_code'],'_utility57_original_confirm36')
            geom=module(reg['geometry_code'],'_utility57_original_geometry31')
            old=read(bound(reg['original_confirm_prepared']));refs=old['entries']
            inputgate=read(bound(reg['original_confirm_input_acceptance']))
            qa=read(bound(reg['remaining19_output_acceptance']));done=read(bound(reg['remaining19_completion']))
            require(inputgate['status']=='PASS_FIRST_ALL20_CONFIRM_BASE_AND_NEW_VISION_INPUTS'
                and inputgate['prepared']==reg['original_confirm_prepared'] and inputgate['actual_sources']==20,
                'Adopt actual successful original20 input gate')
            require(qa['status']=='PASS_FIRST_REMAINING19_BASE_AND_ROI_QA_ORIGINAL20_INCOMPLETE'
                and qa['completion']==reg['remaining19_completion'] and qa['actual_sources']==19
                and done['status']=='COMPLETE_REMAINING19_BASE_AND_VISION_ORIGINAL20_INCOMPLETE'
                and done['first_new_BASE_generations']==done['first_new_vision_readouts']==len(done['entries'])==19,
                'Exact remaining19 raw/output QA adopted without rerun')
            rows=[read(bound(r)) for r in refs];records=[]
            for source_ref,result_ref,raw_ref in zip(refs[1:],done['entries'],done['base_calls']):
                result=read(bound(result_ref));base_ref=result['original_BASE'];baseline=read(bound(base_ref))
                require(result['source']==source_ref and result['source_sha256']==baseline['source_sha256']
                    and result['item_id']==baseline['item_id'] and baseline['original_BASE_raw']==raw_ref,
                    'Adopted BASE/source/raw identity')
                records.append(dict(reference=base_ref,value=baseline))
            proofs={row['item_id']:read(bound(row['original_proof'])) for row in rows[1:]}
            sources=helper.build_confirm_catalog(refs,rows,records,proofs,reg['excluded_source'],geom)
            targets=helper.build_cpu_targets(sources,read(bound(reg['original_confirm_labels'])),geom)
            plan=helper.build_confirm_cases(sources)
        require(len(sources)==len({s['source_id'] for s in sources})==len({s['source_sha256'] for s in sources})
            and all(s['source_id']!='gnmc:test:006575.jpeg' and s['original_BASE_observed'] is True
                and s['pool'][0]==s['baseline_box'] for s in sources),'Fixed observed BASE ownership, no missing substitute')
        require(all(t['reference_modified'] is False and t['baseline_index']==0 for t in targets),'Original human coordinates unchanged')
        catalog=dict(sources=sources,scope=scope,GT_included=False,historical_not_blind=True,
            native_RGB_recovery_claimed=False,reference_or_target_in_prompt=False)
        save(out/'source_catalog.json',catalog)
        save(out/'case_plan.json',plan)
        save(out/'CPU_only_targets.json',dict(status='ORIGINAL_NATIVE_REFERENCE_UTILITY_PROFILE_V57',scope=scope,
            sources=targets,historical_not_blind=True,original_confirm20_complete=False if scope=='confirm' else None,
            unmodified_native_geometry=True,GT_included_in_GPU_input=False))
        save(out/'completion.json',dict(status='COMPLETE_UTILITY_PROFILE_REFERENCE_METADATA_V57',scope=scope,
            source_catalog=ref(out/'source_catalog.json'),CPU_targets=ref(out/'CPU_only_targets.json'),sources=len(sources),
            case_plan=ref(out/'case_plan.json'),
            registration=ref(rp),new_decode=0,new_processor=0,new_model_calls=0,new_pixel_reads=0,production_admitted=False))
    except BaseException as e:
        save(out/'failure.json',dict(utc=utc(),error=repr(e),traceback=traceback.format_exc(),preserve_success=True,no_automatic_retry=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--scope',choices=['screen','confirm'],required=True)
    a=p.parse_args();run(a.root,a.scope)
