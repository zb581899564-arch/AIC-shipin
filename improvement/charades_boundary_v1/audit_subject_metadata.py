"""Read existing Linux author metadata id/subject only; no HTTP or media."""
import json
import shlex
import subprocess

PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
SSH = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15',
       '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','aic-inspur-home']
code = r'''import csv,hashlib,io,json,zipfile
from pathlib import Path,PurePosixPath
root=Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/charades_boundary_v1/metadata_01')
source=root/'Charades.zip'
proof=json.loads((root/'annotation_members_01.json').read_text())
def digest(raw):return hashlib.sha256(raw).hexdigest()
with zipfile.ZipFile(source) as z:
 names={PurePosixPath(n).name:n for n in z.namelist()}
 rows={};stats={}
 for split in ('train','test'):
  member=names['Charades_v1_'+split+'.csv'];raw=z.read(member)
  known=next(x for x in proof['members'] if x['name']==member)
  assert digest(raw)==known['sha256'] and len(raw)==known['bytes']
  reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline=''))
  assert 'id' in reader.fieldnames and 'subject' in reader.fieldnames
  table={r['id']:r['subject'] for r in reader}
  assert len(table)>0 and all(table.values())
  rows[split]=table;stats[split]={'member':member,'rows':len(table),'unique_subjects':len(set(table.values())),'member_sha256':known['sha256'],'read_columns':['id','subject'],'subject_missing':sum(not s for s in table.values())}
 readme=names['README.txt'];raw=z.read(readme);known=next(x for x in proof['members'] if x['name']==readme)
 assert digest(raw)==known['sha256']
 lines=raw.decode('utf-8-sig').splitlines();hits=[]
 for ix,line in enumerate(lines):
  if line.strip()=='- subject:':hits.append({'member':readme,'line_1based':ix+1,'definition':lines[ix+1].strip(),'member_sha256':known['sha256']})
 assert len(hits)==1
 roster=json.loads((root/'source_manifest_01.json').read_text())['rows']
 by_role={role:{rows['train'][r['source_id']] for r in roster if r['role']==role} for role in ('dev','confirm','engineering_reserve')}
 cross=by_role['dev']&by_role['confirm']
 union=set(rows['train'].values())|set(rows['test'].values())
 result={'status':'READ_ONLY_AUTHOR_SUBJECT_SCHEMA_AND_COUNTS_AUDIT','source_zip_path':str(source),'source_zip_sha256':digest(source.read_bytes()),'readme_subject_definition':hits[0],'splits':stats,'train_test_subject_intersection_count':len(set(rows['train'].values())&set(rows['test'].values())),'all_author_unique_subjects':len(union),'registered60_unique_subjects':len(set(rows['train'][r['source_id']] for r in roster)),'original_dev_unique_subjects':len(by_role['dev']),'original_confirm_unique_subjects':len(by_role['confirm']),'original_dev_confirm_subject_intersection_count':len(cross),'shared_participant_groups_as_source_id_lists':[[r['source_id'] for r in roster[:20] if rows['train'][r['source_id']]==s] for s in sorted(cross)],'actions_or_quality_used':False,'new_HTTP_requests':0,'new_media_reads':0,'original_metadata_files_modified':False,'no_subject_values_exported':True}
 print(json.dumps(result))
'''

if __name__ == '__main__':
    result = subprocess.run(SSH+[PY+' -B -c '+shlex.quote(code)], capture_output=True, check=True)
    print(result.stdout.decode(), end='')
