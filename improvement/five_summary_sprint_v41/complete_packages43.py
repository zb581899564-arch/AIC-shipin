"""One bounded queued CPU completion: actual firstQA -> registered guard -> ZIPs.

No scheduler, model, training, input/output replay, network configuration, retry,
human semantic review, or website submission. Original formal parent is untouched.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request
import zipfile


def require(value, message):
    if not value: raise ValueError(message)


def read(path): return json.loads(Path(path).read_text())


def sha(path):
    import hashlib
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def ref(path):
    path=Path(path).resolve(strict=True)
    return dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path))


def bound(reference):
    p=Path(reference['path']).resolve(strict=True)
    require(p.is_relative_to(Path('/home/inspur/aic_video_work')) and p.is_file() and sha(p)==reference['sha256'],'Bound completion artifact changed')
    if 'bytes' in reference: require(p.stat().st_size==reference['bytes'],'Bound completion size changed')
    return p


def save(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.flush();os.fsync(stream.fileno())


def histories(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if k in ('canonical_sha256','canonical_SHA256','prediction_sha256','canonical_prediction_sha256') and isinstance(v,str):yield v
            else:yield from histories(v)
    elif isinstance(value,list):
        for v in value:yield from histories(v)


def run(path):
    ext=read(path);root=Path(ext['root']);W=root.parent
    require(os.uname().nodename=='inspur-NP5570M5' and ext['schema']=='BOUNDED_FIVE_PACKAGE_COMPLETION43','Exact bounded CPU root/host')
    require(bound(ext['code_ref'])==Path(__file__).resolve(),'Actual completion code identity')
    policy=read(bound(ext['review_policy_ref']));addendum=read(bound(ext['final_set_addendum_ref']))
    require(policy['registered_before_formal_output_count']==0 and not policy['formal_output_contents_read_for_policy'] and
            not addendum['formal_output_contents_read_for_addendum'] and addendum['reviewer_type']=='DETERMINISTIC_REGISTERED_ENGINEERING_COLLAPSE_REVIEW',
            'Exact timing/disclosure of fixed review and final-set addendum')
    save(root/'completion_chain43_claim.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
        argv=Path('/proc/self/cmdline').read_bytes().replace(b'\0',b' ').decode(),registration_ref=ref(path),CPU_only=True))
    end=datetime.fromisoformat(policy['deadline_utc'].replace('Z','+00:00'))
    # Wait only for this already-authorized unique finite parent, never relaunch it.
    missing_count=0;launch=read(bound(ext['formal_launch_ref']))
    while not (root/'formal_chain_completion41.json').exists():
        require(datetime.now(timezone.utc)<end,'Original final deadline reached while waiting for natural formal completion')
        require(not (root/'formal_chain_failure41.json').exists(),'Actual formal chain failure; no automatic recovery')
        proc=Path('/proc')/str(launch['pid'])
        try:
            stat=(proc/'stat').read_text().split(') ',1)[1].split();argv=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode().strip()
            alive=stat[19]==launch['start_ticks'] and str(root) in argv and stat[0]!='Z'
        except OSError:alive=False
        missing_count=0 if alive else missing_count+1
        require(missing_count<3,'Registered actual parent absent without a successful terminal; preserve evidence and stop')
        time.sleep(min(20,max(0.1,(end-datetime.now(timezone.utc)).total_seconds())))
    parent=read(root/'formal_chain_completion41.json')
    require(parent['status']==policy['required_parent_status'],'Actual first formal parent completion status')
    reg=read(bound(ext['generation_registration_ref']));qa=read(bound(parent['output_QA_ref']))
    require(qa['status']==policy['required_first_QA_status'] and qa['invalid_outputs']==0 and qa['total_outputs']==1044,'Actual all1044 first output QA')
    sys.path.insert(0,str(Path(bound(reg['code']['package_five41.py'])).parent))
    from package_five41 import accepted_selection,policy_sets,keymap,lines
    expected={str(i) for i in range(426)}
    inp=read(bound(reg['package_inputs_ref']));domain={(r['video_id'],r['source_frame']) for r in lines(bound(inp['source_field_files']['field_frames.jsonl']))}
    with zipfile.ZipFile(bound(reg['protected_baseline_ref'])) as archive:
        baseline=[json.loads(line) for line in archive.read('predictions.jsonl').splitlines() if line.strip()]
    B=set(keymap(baseline));require(len(B)==policy['baseline_frames']==123506 and B<=domain,'Exact protected baseline and availability domain')
    role_masks={r:accepted_selection(qa['roles'][r]['details'],expected,522)&domain for r in ('TIME','BASE')}
    candidates=policy_sets(B,role_masks['TIME'],role_masks['BASE'])
    conditions=policy['collapse_conditions']
    def guard(selection):
        empty=sorted(expected-{sid for sid,ordinal in selection},key=int)
        reasons=[]
        if not selection:reasons.append('ALL_EMPTY')
        if len(selection)<len(B)*conditions['selected_native_frames_less_than_baseline_fraction']:reasons.append('SEVERE_GLOBAL_UNDERSELECTION')
        if len(empty)>426*conditions['empty_sources_more_than_fraction']:reasons.append('MAJORITY_EMPTY_SOURCES')
        return dict(review_completed=True,catastrophic_collapse=bool(reasons),reasons=reasons,
            selected_native_frames=len(selection),empty_source_ids=empty,baseline_frame_ratio=len(selection)/len(B))
    role_review={r:guard(v) for r,v in role_masks.items()};candidate_review={str(i):guard(v) for i,v in candidates.items()}
    approved=[i for i in range(1,6) if not candidate_review[str(i)]['catastrophic_collapse']]
    actual_review=dict(status='COMPLETE_REGISTERED_ENGINEERING_COLLAPSE_REVIEW43',reviewer_type=addendum['reviewer_type'],
        review_policy_ref=ext['review_policy_ref'],final_set_addendum_ref=ext['final_set_addendum_ref'],formal_output_QA_ref=parent['output_QA_ref'],
        role_collapse_review=role_review,final_policy_review=candidate_review,approved_policies=approved,
        semantic_quality_review=False,external_new_confirmation=False,official_effect='UNKNOWN',
        historical_exposed_external_ref=reg['production_admission_ref'],source_unselected_not_ordinary=True,
        old_proxy_F1_hard_gate_restored=False,new_fit=0,new_model_calls=0,utc=datetime.now(timezone.utc).isoformat())
    save(root/'main_package_collapse_review43.json',actual_review)
    require(not any(v['catastrophic_collapse'] for v in role_review.values()) and approved,
            'Registered model-level collapse guard rejected production, no threshold change/fallback')
    # Refresh only small primary pages at packaging; unchanged PDF links adopt
    # already-read official PDFs rather than re-downloading them.
    previous=read(bound(reg['rule_check_before_package_ref']));folder=root/'rules_at_package43';folder.mkdir()
    pages={}
    def pdfs(text):return sorted(set(re.findall(r'https?://[^\s"<>]+\.pdf',text,re.I)))
    for name,old in previous['pages'].items():
        req=urllib.request.Request(old['url'],headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=18) as response:body=response.read(524289)
        require(1000<len(body)<=524288,'Official primary response invalid')
        target=folder/(name+'.html');target.write_bytes(body);pages[name]=dict(url=old['url'],**ref(target))
        if name in ('track','notice'):
            require(pdfs(body.decode(errors='replace'))==pdfs(Path(old['path']).read_text(errors='replace')),'Official attachment links changed; stop for review')
    rules=dict(previous,pages=pages,status='CURRENT_PRIMARY_REFRESH_AT_ACTUAL_PACKAGE43_LINKS_UNCHANGED',
        earlier_rule_check_ref=reg['rule_check_before_package_ref'],utc=datetime.now(timezone.utc).isoformat())
    save(root/'official_rule_check_at_package43.json',rules)
    admission=dict(status='ADMIT_REVIEWED_FIVE_SUMMARY_PACKAGES_41',production_allowed=True,main_review_completed=True,
        reviewer_type=addendum['reviewer_type'],semantic_quality_review=False,external_new_confirmation=False,official_effect='UNKNOWN',
        official_empty_predictions_allowed=True,catastrophic_collapse_rejected=True,formal_output_QA_ref=parent['output_QA_ref'],
        actual_pipeline_parameters=reg['actual_pipeline_parameters'],fixed_spatial_eligibility_policy_ref=reg['spatial_eligibility_policy_ref'],
        approved_policies=approved,role_collapse_review=role_review,actual_review_ref=ref(root/'main_package_collapse_review43.json'),
        unknown_effect_risk_exploration_not_quality_guarantee=True,utc=datetime.now(timezone.utc).isoformat())
    save(root/'package_admission43.json',admission)
    history=set(reg['historical_prediction_sha256'])
    old=W/'semantic_context_production_20261016_v1/production_registration.json'
    history.update(read(old)['historical_prediction_sha256'])
    oldhistory=W/'meaningful_residual_20261018_v1/production_code_v1/current_delivered_history_01.json'
    history.update(histories(read(oldhistory)))
    save(root/'history_adoption43.json',dict(current_local_ref=reg['history_inventory_ref'],old_production_ref=ref(old),
        old_authoritative_ref=ref(oldhistory),canonical_sha256=sorted(history)))
    package_reg=dict(reg,formal_output_QA_ref=parent['output_QA_ref'],package_admission_ref=ref(root/'package_admission43.json'),
        rule_check_before_package_ref=ref(root/'official_rule_check_at_package43.json'),historical_prediction_sha256=sorted(history),
        extended_history_ref=ref(root/'history_adoption43.json'))
    pkgpath=root/'package_registration43.json';save(pkgpath,package_reg)
    require(datetime.now(timezone.utc)<end and shutil.disk_usage(W).free>ext['package_output_estimate_bytes'],
            'Actual final packaging stage fits remaining declared output capacity and original time boundary')
    with (root/'package43.log').open('xb') as stream:
        result=subprocess.run([reg['python'],'-B',str(bound(reg['code']['package_five41.py'])),'--registration',str(pkgpath)],
            stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    require(result.returncode==0,'Actual CPU package failed; preserve successful packages, no repeat')
    completion=read(root/'packages41/completion.json')
    ready=dict(status='ENGINEERING_PACKAGES_READY_WINDOWS_FINAL_ZIPS_PENDING',accepted_packages=completion['accepted_packages'],
        requested_packages=5,packages=[r for r in completion['results'] if r['status']=='NEW_ENGINEERING_ACCEPTED_OFFICIAL_EFFECT_UNKNOWN'],
        pending=[r for r in completion['results'] if r['status']!='NEW_ENGINEERING_ACCEPTED_OFFICIAL_EFFECT_UNKNOWN'],
        package_completion_ref=ref(root/'packages41/completion.json'),actual_main_review_ref=ref(root/'main_package_collapse_review43.json'),
        GPU_resource_ref=parent['resource_ref'],official_effect='UNKNOWN',website_submitted=False,
        semantic_quality_review=False,external_new_confirmation=False,protected40_47_unchanged=True,
        utc=datetime.now(timezone.utc).isoformat())
    save(root/'delivery_ready43.json',ready)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--registration',required=True);path=Path(p.parse_args().registration)
    try:run(path)
    except BaseException as error:
        root=path.parent
        if not (root/'completion_chain43_failure.json').exists():
            save(root/'completion_chain43_failure.json',dict(error=repr(error),traceback=traceback.format_exc(),
                preserve_all_raw_success_cost=True,automatic_retry=False,new_GPU_calls=0,utc=datetime.now(timezone.utc).isoformat()))
        raise
