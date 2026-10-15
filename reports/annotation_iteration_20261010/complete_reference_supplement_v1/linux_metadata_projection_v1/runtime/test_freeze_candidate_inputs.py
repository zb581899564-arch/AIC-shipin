"""Exercise real byte-freeze inventory on disposable candidate input fixtures."""
import ast,json,tempfile,unittest
from pathlib import Path
from common import HERE,sha
from freeze_inputs import freeze
class FreezeCandidateInputs(unittest.TestCase):
 def fixture(self,root):
  exp=root/'experiment';exp.mkdir();run=root/'historical';run.mkdir()
  def file(p,data=b'fixture'):
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p
  def doc(p,x):return file(p,json.dumps(x).encode())
  def ref(p):return dict(path=str(p.resolve()),sha256=sha(p))
  ordinary=file(exp/'source.mp4');extra=file(run/'source426.mp4');clock=doc(run/'clock.json',dict(ticks=[0,1]))
  manifest=doc(run/'manifest.json',dict(records=[dict(source_path=str(extra),source_sha256=sha(extra))]))
  registry=doc(run/'registry.json',dict(records=[dict(clock_arrays=ref(clock))]))
  plan=doc(run/'plan.json',dict(records=426,windows=521));proof=doc(run/'proof.json',dict(proofs=[]))
  space={k:ref(file(run/(k+'.jsonl'))) for k in ('field_frames','field_shots','anchor_requests','anchor_output','schedule_stage','spatial_stage')}
  strict=run/'baseline_a_pts_v1/vendor/frozen_strict_loader';strictmember=file(strict/'reader.py')
  spec=doc(exp/'candidate.json',dict(schema='FIXED_SILVER_426_FRESH_TEMPORAL_CANDIDATE_V1',
   plan=ref(plan),manifest=ref(manifest),clock_registry=ref(registry),changed_cpu_acceptance=ref(proof),space=space,strict_loader_root=str(strict)))
  for source,assignment in [('common.py','dependency_names'),('candidate_support.py','DEPENDENCIES')]:
   tree=ast.parse((HERE/source).read_text())
   tuples=[ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==assignment for t in n.targets)]
   for name in tuples[0]:file(run/name)
  model=root/'model';model.mkdir();doc(model/'model.safetensors.index.json',dict(weight_map={'weight':'model.safetensors'}))
  for name in ('config.json','generation_config.json','model.safetensors'):file(model/name)
  adapter=root/'adapter';adapter.mkdir();weight=file(adapter/'adapter_model.safetensors');file(adapter/'adapter_config.json')
  science=doc(exp/'science.json',{});processor=doc(exp/'processor.json',dict(rows=[]));references=doc(exp/'registry.json',dict(records={}))
  config=dict(schema='COMPLETE_SILVER_NATIVE_RUNTIME_V1',train_output_dir=str(exp/'train_01'),historical_run_root=str(run),
   candidate_contract=ref(spec),source_files={sha(ordinary):ref(ordinary)},target_sidecars={},model_dir=str(model),processor_dir=str(model),
   initial_adapter_dir=str(adapter),initial_adapter_sha256=sha(weight))
  for key in ('protocol','plan','quality_contract','silver_contract','event_metrics','resource_policy'):config[key]=ref(science)
  config['reference_registry']=ref(references);config['processor_binding']=ref(processor)
  cp=doc(exp/'config.json',config)
  return cp,exp,extra,clock,strictmember,list(space.values()),manifest,spec
 def test_all_actual_candidate_members_frozen(self):
  with tempfile.TemporaryDirectory() as d:
   cp,exp,extra,clock,strict,space,manifest,spec=self.fixture(Path(d))
   receipt=freeze(cp,exp/'lock.json');members=json.loads((exp/'lock.json').read_text())['files']
   for p in (extra,clock,strict,manifest,spec):self.assertEqual(members[str(p.resolve())],sha(p))
   for ref in space:self.assertEqual(members[ref['path']],ref['sha256'])
   self.assertEqual(receipt['new_model_calls'],0)
 def test_changed_candidate_source_rejected_before_lock_written(self):
  with tempfile.TemporaryDirectory() as d:
   cp,exp,extra,*_=self.fixture(Path(d));extra.write_bytes(b'changed source')
   with self.assertRaisesRegex(ValueError,'input binding differs'):freeze(cp,exp/'lock.json')
   self.assertFalse((exp/'lock.json').exists())
if __name__=='__main__':unittest.main()

