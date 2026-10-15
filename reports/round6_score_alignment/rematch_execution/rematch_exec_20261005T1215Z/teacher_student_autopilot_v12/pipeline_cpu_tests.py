"""Actual production control flow with CPU doubles; no CUDA or process signalling."""
import ast
from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType,SimpleNamespace as NS
import unittest
from unittest.mock import patch
import autopilot_common as c
import production_t as p
import source_color as color


class ProductionContracts(unittest.TestCase):
    def test_registered_color_implementation_and_recipe_unchanged(self):
        old=c.RUN/'b_score_aligned_package_v4'
        def core(path):
            tree=ast.parse(path.read_text(encoding='utf-8-sig'))
            return [ast.dump(n,include_attributes=False) for n in tree.body
                    if getattr(n,'name',None) in ('convert_frame','ColorNativeReader')]
        self.assertEqual(core(c.HERE/'source_color.py'),core(old/'source_color.py'))
        self.assertEqual(c.read(c.HERE/'config.json')['source_color_repair'],c.read(old/'config.json')['source_color_repair'])
        self.assertEqual(c.read(old/'source_color_acceptance.json')['status'],'PASS_B2_DECLARED_COLOR_CONVERSION_CPU')

    def test_temporal_uses_canonical_physical_duration_and_preserves_failure(self):
        # Exercise the real loop. Model/processor and source wrapper alone are CPU doubles.
        for failed in (False,True):
            with self.subTest(failed=failed), tempfile.TemporaryDirectory(prefix='aic_v8_production_cpu_') as tmp:
                here=Path(tmp);source=here/'source.bin';source.write_bytes(b'CPU_FIXTURE_NO_VIDEO')
                adapter=here/'adapter';adapter.mkdir()
                for name in ('adapter_model.safetensors','adapter_config.json'):(adapter/name).write_bytes(b'CPU_ONLY')
                c.write(here/'student_01/student_completion.json',dict(status='PASS_TRAINED_SELECTED_STUDENT_ADAPTER',
                    selected_adapter_dir=str(adapter), selected_adapter_sha256=c.sha(adapter/'adapter_model.safetensors'),
                    selected_adapter_config_sha256=c.sha(adapter/'adapter_config.json')))
                item=dict(video_id='CPU_ONLY',source_path=str(source),source_sha256=c.sha(source),targetRatioWH=[9,16],n_frames=3,fps_num=10,fps_den=1)
                clocks={'CPU_ONLY':dict(arrays=dict(raw_time_base='1/10',native_pts_ticks=[0,1,2],raw_first_pts_ticks=0),clock_record_sha256='CPU_FIXTURE',branch='native')}
                observed=[]
                def encode(processor,window):
                    observed.append(window['window_duration_sec']);return None,{}
                def generate(*args):
                    if failed:raise ValueError('CPU_REAL_LOOP_FAILURE_FIXTURE')
                    return dict(status='MODEL_OK',output_valid=True,parsed_segments=[[0,observed[-1]]],parse_errors=[],parse_warnings=[])
                student=NS(window_from_pts=lambda *a: {'source_path':str(source),'source_sha256':c.sha(source),'window_duration_sec':float(Fraction('0.3')-Fraction('0.1'))},production_encode=encode,production_generate=generate,INPUT_CONTRACT={'CPU_FIXTURE':True})
                old=NS(verify=lambda:{},inputs=lambda scope:(None,dict(kind='CPU_FIXTURE',records=[item]),clocks))
                frames=NS(window_schedule=lambda *a:[(.1,.3)])
                engine=ModuleType('engine');engine.load_model=lambda *a,**k:(None,NS(tokenizer=None),8782459120)
                gpu=ModuleType('sft_contract');gpu.verify_live_gpu_reservation=lambda:None
                grammar=ModuleType('constrained_json');grammar.ascii_token_candidates=lambda t:[]
                out=here/'result'
                with patch.object(p,'HERE',here),patch.object(p,'verify',return_value={}),patch.object(p,'helpers',return_value=(student,old,frames,None)),patch.dict(sys.modules,engine=engine,sft_contract=gpu,constrained_json=grammar):
                    if failed:
                        with self.assertRaisesRegex(RuntimeError,'never convert failure to empty'):p.temporal('nontest',out)
                    else:p.temporal('nontest',out)
                self.assertEqual(observed,[.3-.1])
                stage=c.read(out/'temporal.stage.json');window=c.rows(out/'temporal.jsonl')[0]['windows'][0]
                self.assertEqual(stage['invalid_windows'],int(failed))
                self.assertEqual(window['output_valid'],not failed)
                if failed:
                    self.assertIsNone(window['parsed_segments'])
                    self.assertIn('CPU_REAL_LOOP_FAILURE_FIXTURE',window['parse_errors'][0])


if __name__=='__main__':unittest.main(verbosity=2)
