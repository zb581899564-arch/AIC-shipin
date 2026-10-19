import json,pathlib
W=pathlib.Path('/home/inspur/aic_video_work')
i=json.loads((W/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json').read_text())
m=json.loads(pathlib.Path(i['source_manifest']['path']).read_text())
print('clock_registry',json.dumps(m['clock_registry'])[:2500])
c=json.loads(pathlib.Path(i['source_clocks']['path']).read_text())
print('source_clocks_type',type(c).__name__)
print('source_clocks_keys',list(c)[:12])
if isinstance(c,dict):
 for k,v in c.items():
  if isinstance(v,list) and v: print(k,'first_keys',list(v[0]) if isinstance(v[0],dict) else type(v[0]).__name__)
print('existing_current_rules', (W/'sprint45_current_official_rules_20261016_v1/official_rule_check_before_package.json').read_text()[:2200])
