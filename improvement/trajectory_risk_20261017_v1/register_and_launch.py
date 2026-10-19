import ast,datetime,hashlib,json,os,pathlib,shutil,socket,subprocess,urllib.request
W=pathlib.Path('/home/inspur/aic_video_work');root=W/'trajectory_risk_20261017_v1'
assert socket.gethostname()=='inspur-NP5570M5'
assert not root.exists(),'Existing root: inspect, do not restart'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def read(p):return json.loads(pathlib.Path(p).read_text())
def save(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2)
root.mkdir();(root/'code').mkdir();(root/'rules').mkdir()
for name,expected in EXPECTED_CODES.items():
 p=W/('incoming_trajectory_20261017_'+name);assert p.stat().st_size==expected['bytes'] and sha(p)==expected['sha256']
 ast.parse(p.read_text());(root/'code'/name).write_bytes(p.read_bytes())
old_rule=read(W/'sprint45_current_official_rules_20261016_v1/official_rule_check_before_package.json')
rule_files=[]
for i,r in enumerate(old_rule['attachments']):
 req=urllib.request.Request(r['url'],headers={'User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(req,timeout=40) as response:data=response.read()
 p=root/'rules'/f'attachment{i}.pdf';p.write_bytes(data)
 assert len(data)==r['bytes'] and sha(p)==r['sha256'],'Current attachment differs: require fresh review'
 rule_files.append(dict(url=r['url'],bytes=len(data),sha256=sha(p),identical_to_prior_full_review=True))
body_urls=['https://www.aicomp.cn/tracks/tracks-6/4267.html','https://www.aicomp.cn/notice/notice-3/5307.html','https://www.aicomp.cn/notice/notice-3/']
pages=[]
for i,url in enumerate(body_urls):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35) as response:data=response.read()
 p=root/'rules'/f'page{i}.html';p.write_bytes(data);pages.append(dict(url=url,bytes=len(data),sha256=sha(p)))
 # All page content is public. The local host reviews current notice directory
 # separately; no model or test material leaves Linux.
save(root/'official_rule_check_before_package.json',dict(status='PASS_CURRENT_RULES_SCOPE',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pages=pages,attachments=rule_files,interpretation='Automatic reproducible same-model spatial trajectory postprocessing; no manual test edits or training; params <=9B; no special organizer permission claimed',offline_quality='UNKNOWN'))
adopt=W/'semantic_context_production_20261016_v1';inputpath=W/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json'
hist=read(adopt/'production_registration.json')['historical_prediction_sha256']
reg=dict(schema='TRAJECTORY_CPU_RISK20261017V1',methods=['NEAREST_PTS_ANCHOR','SHOT_MEDIAN_CENTER'],pts_key='normalized_exact_pts',actual_total_parameters=8782557449,
 user_authorization='User approved two proposed trajectory candidates with 去做; baseline40.47 time/width unchanged, no offline effect gate, no new models',
 baseline=ref(adopt/'package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'),field_inputs=ref(inputpath),rule_check=ref(root/'official_rule_check_before_package.json'),code={n:ref(root/'code'/n) for n in EXPECTED_CODES},
 historical_canonical_sha256=hist,current_candidate_completions=[ref(W/p) for p in ['sprint45_global_context_20261016_v1/packages_01/GLOBAL_CONTEXT/completion.json','sprint45_global_context_20261016_v1/packages_01/EVENT_PAYOFF/completion.json','sprint45_width_packages_20261016_v1/packages_01/NATIVE16_LEARNED_WIDTH/completion.json','sprint45_consensus_veto_last_risk_20261016_v1/completion.json']],
 nearest_rule='minimum absolute exact native PTS distance, earlier ordinal wins exact ties; same shot only; exact original anchor box',
 median_rule='coordinatewise median of original legal same-shot anchor top-left, nearest-even integer rounding; fixed same-shot original width; no cross-shot smoothing',
 offline_effect_validation=False,online_effect='UNKNOWN',new_model_calls=0,new_training_updates=0)
save(root/'registration.json',reg)
py=W/'env/qwen3vl_isolated_20260910/bin/python';cmd=[str(py),'-B','-u',str(root/'code/trajectory.py'),str(root)]
env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
with (root/'stdout.log').open('xb') as out,(root/'stderr.log').open('xb') as err:p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=out,stderr=err,env=env,start_new_session=True)
save(root/'launch.json',dict(pid=p.pid,start_ticks=pathlib.Path('/proc',str(p.pid),'stat').read_text().split()[21],command=cmd,registration=ref(root/'registration.json'),free_bytes=shutil.disk_usage(root).free,CPU_only=True,new_GPU_calls=0))
print(json.dumps(read(root/'launch.json')))
