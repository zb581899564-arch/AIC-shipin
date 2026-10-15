"""New eight-source identities after frozen development selection; no media/model calls."""
import json
from pathlib import Path

from deploy_media_batch_04 import ssh_script
from stage_common_04 import read, save, sha, utc

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/sparse_context_iteration_20261013_v1'
TEMP = Path('C:/Users/33056/AppData/Local/Temp/aic_third_reference_20261013')


def main():
    output = REPORT/'new_confirm_source_registration_01.json'
    if output.exists():
        raise ValueError('Fresh source identities already frozen; do not select again')
    result = read(REPORT/'screen_01/result.json')
    if result['status'] != 'PASS_SPARSE_SCREEN_PENDING_NEW_UNEXPOSED_CONFIRM8' or result['chosen'] != 'SPARSE50_POST025':
        raise ValueError('Frozen selected development candidate required')
    script = '''import pathlib,json,hashlib,socket,subprocess,os,shutil,datetime
b=pathlib.Path('/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1')
assert socket.gethostname()=='inspur-NP5570M5'
p=b/'metadata_02/val_videoxum.json';raw=p.read_bytes()
assert len(raw)==9575564 and hashlib.sha256(raw).hexdigest()=='2832f423ff5fd768a979665e30345a56f1723aacc1821986b5ec042bed30f556'
data=json.loads(raw);assert len(data)==2001
old=json.loads((b/'metadata_02/source_registration_01.json').read_text())
old_ids={x['video_id'] for x in old['selection']+old['ordered_media_replacements']}
native=json.loads((b/'cohort_input_acceptance_07.json').read_text())
old_ids.update(x['video_id'] for x in native['sources'])
exclusions=json.loads((b/'known_source_exclusions_01.json').read_text())
excluded={x if x.startswith('v_') else 'v_'+x for x in exclusions['youtube_ids']}|old_ids
salt='SPARSE_CONTEXT_NEW_CONFIRM8_20261013_V1'
eligible=[dict(video_id=x['video_id'],youtube_id=x['video_id'][2:],author_duration_raw=str(x['duration']),selection_hash=hashlib.sha256((salt+x['video_id']).encode()).hexdigest()) for x in data if x['video_id'] not in excluded and 30<=x['duration']<=240]
eligible.sort(key=lambda x:(x['selection_hash'],x['video_id']))
owned=[]
for proc in pathlib.Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  argv=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\\0') if x]
  if any(x.startswith(str(b)+'/code/') for x in argv):
   owned.append(dict(pid=int(proc.name),argv=argv,status=(proc/'status').read_text(),io=(proc/'io').read_text()))
 except OSError:pass
resource=pathlib.Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/videoxum20_original_b_native64_20261013_v1.resource.json')
body=json.loads(resource.read_text());assert body['status']=='completed' and body['exit_code']==0
ledger=[json.loads(x) for x in pathlib.Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip() and json.loads(x)['name']==body['name']]
assert ledger==[body]
print(json.dumps(dict(hostname=socket.gethostname(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cpu_count=os.cpu_count(),load=os.getloadavg(),memory=pathlib.Path('/proc/meminfo').read_text(),disk=list(shutil.disk_usage(b)),gpu=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True).stdout,jobs=subprocess.run(['ps','-eo','pid,ppid,pcpu,pmem,args','--sort=-pcpu'],capture_output=True,text=True).stdout[:18000],actual_owned_commands=owned,previous_GPU_terminal=body,previous_GPU_ledger_matches=True,author_file_bytes=len(raw),author_file_sha256=hashlib.sha256(raw).hexdigest(),old_exposed_ids=sorted(old_ids),known_exclusion_count=len(excluded),selection_salt=salt,eligible_count=len(eligible),ordered_candidates=eligible[:64],new_media_downloads=0,new_model_calls=0)))'''
    live = ssh_script(script)
    save(REPORT/'new_confirm_host_and_retained_author_readonly_01.json', live)
    if live['actual_owned_commands']:
        raise ValueError('Existing old cohort commands still active; preserve source IDs and inspect actual processes')
    inventory_path = TEMP/'tornadolabs_metadata.jsonl'
    if sha(inventory_path) != 'b3849e17b6b821044c87789c2b1108009a4c50a0b08d255cd908a97255916042':
        raise ValueError('Pinned public metadata inventory changed')
    inventory = {row['video_id']: row for row in (json.loads(x) for x in inventory_path.read_text().splitlines())}
    absent, available = [], []
    for row in live['ordered_candidates']:
        provider = inventory.get(row['youtube_id'])
        if provider is None:
            absent.append(row['video_id'])
        else:
            available.append(dict(row, group='confirm', provider=provider))
        if len(available) == 24:
            break
    if len(available) < 24:
        raise ValueError('Insufficient frozen public candidates for eight + preordered engineering reserves')
    registration = dict(status='NEW_UNEXPOSED_CONFIRM8_SOURCE_IDS_AND_PREORDERED_RESERVES_FROZEN_BEFORE_MEDIA_MODEL',
        utc=utc(), selection_salt=live['selection_salt'], minimum_author_duration='30', maximum_author_duration='240',
        selection=available[:8], ordered_engineering_reserves=available[8:], missing_in_pinned_public_inventory=absent,
        old_exposed_source_ids=live['old_exposed_ids'], annotation_sha256=live['author_file_sha256'],
        source_annotation_reused_no_download=True, public_inventory_sha256=sha(inventory_path),
        publisher_revision='bc9c567ea67be43daf443cddb832ed983e5ccae5',
        old20_source_roles_and_failures_unchanged=True, original20_are_exposed_development_only=True,
        previous_known_exclusions_sha256=sha(ROOT/'reports/videoxum_reference_iteration_20261013_v1/known_source_exclusions_01.json'),
        frozen_candidate_sha256=sha(REPORT/'screen_01/selection_before_new_confirm.json'),
        selection_uses_reference_or_prediction_quality=False, replacement_policy='Only preregistered public unavailability or actual native origin/manual-end rejection; never network/processor/prediction/quality',
        selected_media_payload_bytes=sum(x['provider']['size_bytes'] for x in available[:8]),
        maximum_selected_and_reserve_pool_bytes=sum(x['provider']['size_bytes'] for x in available),
        confirmation_evaluated=False, new_media_downloads=0, new_CPU_decodes=0, new_model_calls=0, new_optimizer_updates=0)
    save(output, registration)
    print(json.dumps(dict(status=registration['status'],selection=[x['video_id'] for x in available[:8]],
        selected_bytes=registration['selected_media_payload_bytes'],maximum_pool_bytes=registration['maximum_selected_and_reserve_pool_bytes'],
        actual_old_owned_commands=0,previous_GPU_terminal='completed',new_model_calls=0)))


if __name__ == '__main__':
    main()
