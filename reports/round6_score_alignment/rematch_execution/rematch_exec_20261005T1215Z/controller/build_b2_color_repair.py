"""New v3 for the proven log316 conversion error; never edit v1/v2 locks."""
from pathlib import Path
import json

RUN = Path(__file__).resolve().parent.parent
OLD = RUN / 'b_score_aligned_package_v2'
NEW = RUN / 'b_score_aligned_package_v3'
NEW.mkdir(exist_ok=False)
for p in OLD.iterdir():
    if p.is_file() and (p.suffix == '.py' or p.name in ('PROTOCOL.md', 'CONTINUE.md', 'config.json')):
        (NEW / p.name).write_bytes(p.read_bytes())

def change(name, old, new):
    p = NEW / name; source = p.read_text(encoding='utf-8-sig')
    assert source.count(old) == 1, (name, old)
    p.write_text(source.replace(old, new), encoding='utf-8', newline='\n')

change('native_input.py', 'image = frame.to_ndarray(format="rgb24")',
    'from source_color import convert_frame\n            image = convert_frame(frame, w["source_sha256"], "rgb24")')
change('production.py', "        if self.native:\n            from native_frames import VerifiedNativeReader", '''        from source_color import authorized_source, ColorNativeReader
        self.color_special=authorized_source(item['source_sha256'])
        if self.color_special:
            self.reader=ColorNativeReader(item,clock)
        elif self.native:
            from native_frames import VerifiedNativeReader''')
change('production.py', '        if self.native:\n            frame=self.reader.read(index)',
    '        if self.color_special:return self.reader.get(index)\n        if self.native:\n            frame=self.reader.read(index)')
change('production.py', '        if self.native:self.reader=None',
    '        if self.color_special:self.reader.close()\n        elif self.native:self.reader=None')
change('prepare.py', "require(node_identity(HERE/'production.py',('OrdinalReader',)) == node_identity(old/'production.py',('OrdinalReader',)),\n            'cache source decoder algorithm differs')", '''from source_color import verify_default_decoder_ast, authorized_source
    verify_default_decoder_ast(HERE/'production.py',old/'production.py')
    require(read(HERE/'source_color_acceptance.json')['status']=='PASS_B2_DECLARED_COLOR_CONVERSION_CPU',
            'declared conversion CPU acceptance missing')
    for record in inputs('nontest')[1]['records']:
        require(not authorized_source(record['source_sha256']), 'old non-test cache color behavior changed')''')
change('prepare.py', "schema='B2_SCORE_ALIGNED_SOURCE_LOCK_V2'", "schema='B2_SCORE_ALIGNED_SOURCE_LOCK_V3'")
change('controller.py', "name = 'rematch_B2_v2_'", "name = 'rematch_B2_v3_'")
change('controller.py', "'STOP_B2_PACKAGE_V2'", "'STOP_B2_PACKAGE_V3'")
change('controller.py', 'from temporal_reuse import reuse_probe, reuse_temporal, wait_and_handoff',
       'from temporal_reuse import reuse_probe, reuse_temporal, wait_and_handoff, prepare_recovery')
change('controller.py', "            reuse_temporal(scope, out)", '''            if scope == 'rematch':
                plan = prepare_recovery(scope, out)
                if plan['failed_windows']:
                    gpu('recovery.py', 'recover', scope, out, 3600, max(planned, 60_000_000))
                else:
                    reuse_temporal(scope, out)
            else:
                reuse_temporal(scope, out)''')

# Reuse proof: identical default source conversion, generation and model code.
change('temporal_reuse.py', "            require(tree(HERE / name) == tree(old / name), 'generation helper algorithm changed: ' + name)", '''            if name == 'native_input.py':
                from source_color import normalized_native_input
                require(normalized_native_input(HERE / name) == tree(old / name),
                        'native default decode differs beyond the declared unsupported-source conversion')
            else:
                require(tree(HERE / name) == tree(old / name), 'generation helper algorithm changed: ' + name)''')
change('temporal_reuse.py', 'def resource(scope, stage):', 'def resource(scope, stage, allow_declared_failure=False):')
change('temporal_reuse.py', "require(value['status'] == 'completed' and value['exit_code'] == 0,\n            'original wrapper charge/completion is not accepted')", '''require((value['status'] == 'completed' and value['exit_code'] == 0) or
            (allow_declared_failure and scope == 'rematch' and stage == 'temporal' and
             value['status'] == 'failed' and value['exit_code'] == 1 and value.get('stop_reason') is None),
            'original wrapper completion/charged declared decode-failure is not accepted')''')
change('temporal_reuse.py', 'def verify_temporal(scope):', 'def verify_temporal(scope, allow_declared_failure=False):')
change('temporal_reuse.py', "receipt = resource(scope, 'temporal')", "receipt = resource(scope, 'temporal', allow_declared_failure)")
change('temporal_reuse.py', "require(stage['status'] == 'PASS_TEMPORAL_EXECUTION' and stage['invalid_windows'] == 0 and",
       "require((stage['status'] == 'PASS_TEMPORAL_EXECUTION' and stage['invalid_windows'] == 0 or\n        allow_declared_failure and stage['status'] == 'STOP_TEMPORAL_FAILURES' and stage['invalid_windows'] > 0) and")
change('temporal_reuse.py', 'windows = 0', 'windows = 0\n    failed = []')
change('temporal_reuse.py', "duration = plan['window_duration_sec']; details = window['video_identity']", '''duration = plan['window_duration_sec']
            windows += 1
            if window.get('output_valid') is not True:
                from source_color import validate_original_decode_failure
                require(allow_declared_failure, 'failed original window cannot be reused')
                validate_original_decode_failure(item, clock, index, start, end, window)
                failed.append(dict(video_id=item['video_id'], index=index, start_sec=start, end_sec=end,
                    original_window_sha256=hashlib.sha256(json.dumps(window,sort_keys=True).encode()).hexdigest(),
                    reason='REGISTERED_LOG316_CONVERSION_FAILURE_BEFORE_MODEL_INPUT'))
                continue
            from source_color import authorized_source
            require(not authorized_source(item['source_sha256']), 'changed-color successful source cannot be reused')
            details = window['video_identity']''')
change('temporal_reuse.py', '            windows += 1\n    selected = select_frames(manifest, records, clocks)', '''    require(len(failed) == stage['invalid_windows'], 'original failed-window denominator differs')
    selected = select_frames(manifest, records, clocks) if not failed else []''')
change('temporal_reuse.py', 'selected_frames=len(selected), output_sha256=sha(out / \'temporal.jsonl\'),',
       'selected_frames=len(selected) if not failed else None, failed_windows=failed,\n        reusable_valid_windows=windows-len(failed), output_sha256=sha(out / \'temporal.jsonl\'),')
change('temporal_reuse.py', "copied_raw_bytes_exact=True, output_values_changed=0, failures_to_empty=0, model_generation_calls_this_version=0)",
       "copied_raw_bytes_exact=True, output_values_changed=0, failures_to_empty=0, model_generation_calls_this_version=0)")
change('temporal_reuse.py', "require(read(stage_path)['status'] == 'PASS_TEMPORAL_EXECUTION' and\n                read(resource_path)['status'] == 'completed' and read(resource_path)['exit_code'] == 0,\n                'old temporal failure cannot be converted or reused')", '''require(read(stage_path)['status'] in ('PASS_TEMPORAL_EXECUTION','STOP_TEMPORAL_FAILURES'),
                'old temporal failure lacks complete per-window provenance')
            resource('rematch','temporal',allow_declared_failure=True)
            verify_temporal('rematch',allow_declared_failure=True)''')

config=json.loads((NEW/'config.json').read_text())
config['source_color_repair'] = dict(
    schema='PINNED_LOG316_YUV_CONVERSION_V1',
    sources={'8ec893eb5378452de6223f6c8e5878bcea044cb2f9e4feaabf708fa364871722':
        dict(video_id='97',format='yuv420p',color_trc=10,colorspace=2,color_primaries=2,color_range=1,width=720,height=1280)},
    transfer_tag_for_conversion=2, matrix='ITU601', range_changed=False,
    gamma_transform_applied=False, raw_YUV_planes_changed=False, unsupported_other_sources='STOP',
    successful_default_decode_unchanged=True, recovery_only_original_pre_model_decode_failures=True)
(NEW/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Created v3; existing v1 GPU provider and v1/v2 frozen sources unchanged.')
