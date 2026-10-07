"""Regression for the real mixed-clock failure and real probe timing shape."""
import copy
import json
from pathlib import Path
import teacher_label as t
import controller as c

obs={'window_id':'clock_regression','window_pts_start_sec':120.0,'window_pts_end_exclusive_sec':150.0,
     'window_duration_sec':30.0,'actual_pts_sec':[120.03658333333334,139.514375,149.98316666666668]}
points=t.window_local_points(obs)
assert abs(points[1]-19.514375)<1e-10
schema=c.read(c.RUN/'next_round_v1/supervision/teacher_response.schema.json')
original=copy.deepcopy(schema); compiled=t.request_schema(schema,obs); constrained=compiled['anyOf'][0]
assert schema==original
start=constrained['properties']['retained_segments']['items']['properties']['start_sec']['enum']
assert points[1] in start and 0.0 in start and 30.0 in start
assert 139.514375 not in start and 150.0 not in start and all(0<=v<=30 for v in start)
assert constrained['properties']['observation_scope']['properties']['sampled_pts_sec']=={'const':obs['actual_pts_sec']}
assert constrained['properties']['observation_scope']['properties']['all_provided_frames_reviewed']==schema['properties']['observation_scope']['properties']['all_provided_frames_reviewed']
assert {(b['properties']['uncertain']['const'],b['properties']['explicit_no_highlight']['const']) for b in compiled['anyOf']}=={(True,False),(False,True),(False,False)}
assert c.measured_window_seconds({'per_window_wall_sec':[10.0,20.0],'window_ids':['a','b']})==20.0
for values in (20.0,[],[float('nan'),1],[-1,1],[1]):
    try:c.measured_window_seconds({'per_window_wall_sec':values,'window_ids':['a','b']})
    except RuntimeError:pass
    else:raise AssertionError('invalid measurement admitted')
report={'status':'PASS_LOCAL_CLOCK_DOMAIN_AND_MEASURED_TIMING_REGRESSION','checks':8,'GPU_started':False,'original_failed_annotation_not_rewritten':True,'uncertainty_and_empty_not_forced':True}
c.write(c.HERE/'clock_cpu_acceptance.json',report,fresh=True)
print(json.dumps(report))
