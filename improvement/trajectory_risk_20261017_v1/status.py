import pathlib,json,os
root=pathlib.Path('/home/inspur/aic_video_work/trajectory_risk_20261017_v1')
def rd(p):return json.loads(p.read_text())
launch=rd(root/'launch.json');p=pathlib.Path('/proc',str(launch['pid']))
live=None
if p.exists():
 st=(p/'stat').read_text();ticks=st[st.rfind(')')+2:].split()[19]
 if ticks==launch['start_ticks']:
  live=dict(argv=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(),start_ticks=ticks,state=st[st.rfind(')')+2:].split()[0],io=(p/'io').read_text(),children=(p/'task'/str(launch['pid'])/'children').read_text())
result=dict(live=live)
for name in ['failure.json','completion.json','baseline_identity.json']:
 if (root/name).exists():result[name]=rd(root/name)
for method in ['NEAREST_PTS_ANCHOR','SHOT_MEDIAN_CENTER']:
 d=root/method
 if (d/'completion.json').exists():result[method]=rd(d/'completion.json')
result['stderr_tail']=(root/'stderr.log').read_text()[-1600:]
print(json.dumps(result))
