"""Independent B2 v2; preserve the live v1 generation and all frozen evidence."""
from pathlib import Path
import json

RUN = Path(__file__).resolve().parent.parent
OLD = RUN / 'b_score_aligned_package_v1'
NEW = RUN / 'b_score_aligned_package_v2'
NEW.mkdir(exist_ok=False)
excluded = {'source_lock.json', 'cpu_acceptance.json', 'processor_acceptance.json',
            'cache_bindings.json', 'launch.json', 'registration.json', 'progress.json', 'completion.json'}
for path in OLD.iterdir():
    if path.is_file() and path.suffix in ('.py', '.md', '.json') and path.name not in excluded:
        (NEW / path.name).write_bytes(path.read_bytes())

def change(name, old, new):
    path = NEW / name
    source = path.read_text(encoding='utf-8-sig')
    assert source.count(old) == 1, (name, old)
    path.write_text(source.replace(old, new), encoding='utf-8', newline='\n')

change('common.py', '\ndef inputs(scope):', '''
def window_duration(start, end):
    """Same canonical decimal difference in generation and source-frame selection."""
    import math
    from fractions import Fraction
    require(math.isfinite(start) and math.isfinite(end) and start < end,
            'invalid registered window bounds')
    return float(Fraction(str(end)) - Fraction(str(start)))


def inputs(scope):''')
change('engine.py', "float(Fraction(str(end)) - Fraction(str(start)))", 'window_duration(start, end)')
change('production.py', 'validate_segments(segments, end - start)',
       'duration = window_duration(start, end)\n            validate_segments(segments, duration)')
change('production.py', 'native_segment_ranges(segments, points, start, end-start)',
       'native_segment_ranges(segments, points, start, duration)')

change('controller.py', "name = 'rematch_B2_v1_'", "name = 'rematch_B2_v2_'")
change('controller.py', "'STOP_B2_PACKAGE_V1'", "'STOP_B2_PACKAGE_V2'")
change('controller.py', "gpu('engine.py', 'probe', 'synthetic', HERE / 'probe_01', 3600, 30_000_000)",
       "from temporal_reuse import reuse_probe, reuse_temporal, wait_and_handoff\n        reuse_probe(HERE / 'probe_01')")
change('controller.py', "gpu('engine.py', 'temporal', scope, out, maximum, planned)",
       "if scope == 'rematch':\n                checkpoint('WAITING_VALID_B2_V1_TEMPORAL')\n                wait_and_handoff()\n            reuse_temporal(scope, out)")

change('cpu_tests.py', 'real_windows = endpoints = 0', '''real_windows = endpoints = mismatches = original_rejections = 0
    old_engine = load(RUN / 'b_score_aligned_package_v1/engine.py', 'b2_original_engine_cpu')
    from production import select_frames
    replayed_endpoints = []''')
change('cpu_tests.py', "duration = window['window_duration_sec']", '''duration = window['window_duration_sec']
                require(window == old_engine.plan_window(item, clock, start, end, index),
                        'v2 changed the original generated input or duration')
                old_duration = end - start
                mismatches += old_duration != duration
                try:
                    validate_segments([[0, duration]], old_duration)
                except ValueError:
                    original_rejections += 1
                synthetic = dict(video_id=item['video_id'], video_path=item['source_path'],
                    n_frames=item['n_frames'], fps=item['fps_num']/item['fps_den'],
                    targetRatioWH=item['targetRatioWH'], windows=[])
                for other_index, (a, b) in enumerate(window_schedule(item, manifest['kind'], clock)):
                    synthetic['windows'].append(dict(output_valid=True, parse_errors=[], status='LEGAL_EMPTY',
                        clock_record_sha256=clock['clock_record_sha256'], start_sec=a, end_sec=b, parsed_segments=[]))
                synthetic['windows'][index].update(status='MODEL_OK', parsed_segments=[[0, duration]])
                one_manifest = dict(manifest, records=[item])
                selected = select_frames(one_manifest, [synthetic], {item['video_id']: clock})
                expected = native_segment_ranges([[0,duration]], [float(p) for p in clock['pts']], start, duration)
                require([r['source_frame'] for r in selected] == list(range(*expected[0])),
                        'full endpoint was rejected or physical source-frame identity changed')
                from bisect import bisect_left
                require(expected == [(bisect_left(clock['pts'], start), bisect_left(clock['pts'], end))],
                        'canonical full endpoint does not realize exactly the registered natural window')
                replayed_endpoints.append(dict(scope=scope, video_id=item['video_id'], index=index,
                    canonical_duration=duration, selected_frames=len(selected)))''')
change('cpu_tests.py', 'config = settings()', '''require(real_windows == 529 and mismatches == 56 and original_rejections == 29,
            'the original 529-window/29-rejection symptom was not reproduced')
    config = settings()
    from temporal_reuse import verify_algorithm_equivalence, verify_temporal
    equivalence = verify_algorithm_equivalence()
    non_test = verify_temporal('nontest')
    tests += 4''')
change('cpu_tests.py', 'actual_CUDA_started=False,', '''duration_mismatches_reproduced=mismatches,
        original_valid_endpoint_rejections_reproduced=original_rejections,
        repaired_full_endpoint_selection_windows=len(replayed_endpoints),
        generation_algorithm_equivalence=equivalence,
        original_nontest_temporal_replayed=non_test,
        actual_CUDA_started=False,''')

change('prepare.py', "files={str(path):sha(path) for path in sorted(dependencies)}", '''from temporal_reuse import verify_algorithm_equivalence, verify_temporal, old_entry
    verify_algorithm_equivalence(); verify_temporal('nontest')
    old_b2 = old_entry()
    dependencies.add(old_b2 / 'source_lock.json')
    dependencies.update(Path(path) for path in read(old_b2 / 'source_lock.json')['files'])
    dependencies.update((old_b2 / name for name in (
        'launch.json', 'registration.json', 'probe_01/probe.stage.json',
        'nontest_01/model_identity.json', 'nontest_01/temporal.jsonl', 'nontest_01/temporal.stage.json')))
    dependencies.update(RUN / 'controller' / (name + '.resource.json') for name in (
        'rematch_B2_v1_synthetic_probe_01', 'rematch_B2_v1_nontest_temporal_01'))
    files={str(path):sha(path) for path in sorted(dependencies)}''')
change('prepare.py', "schema='B2_SCORE_ALIGNED_SOURCE_LOCK_V1'", "schema='B2_SCORE_ALIGNED_SOURCE_LOCK_V2'")

config = json.loads((NEW / 'config.json').read_text(encoding='utf-8-sig'))
config['duration_repair'] = dict(original_entry='b_score_aligned_package_v1',
    original_source_lock_sha256='0c63bc55df1ec3a34773dc543f4241241a646ac55249b320c72df02fab598d2c',
    canonical='float(Fraction(str(end)) - Fraction(str(start)))',
    source_pts_changed=False, generated_outputs_changed=False, epsilon_or_endpoint_clipping=False,
    old_live_generation_may_finish=True, unchanged_generation_reuse_requires_SHA_and_original_validator=True)
(NEW / 'config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
(NEW / 'PROTOCOL.md').write_text('''# B2 v2 独立端点合同修复

保持已经训练的B最终8B LoRA、全部生成算法/原生64帧输入/提示词/权重/greedy/16384界。
v1生成使用十进制Fraction差，选帧使用浮点直接减法：529真实元数据窗口56处差异，29个合法全端点被选帧误拒绝。
v2让生成、原validator和物理选帧共享同一个canonical duration，不加epsilon、不截端点、不改输出数值。
CPU须复现全部29拒绝，并在529窗逐一通过全端点真实native帧范围、原输入完全相等与12原目标无损回放。

当前v1 GPU时间生成不受此选帧错误影响，允许其原任务完成；不重生成已经成功的回答。
probe和NONTEST8时间仅在逐SHA、模型/adapter/算法/真实输入/原validator/finite score核验后原字节复用。
完整426/521时间阶段和所属wrapper记账成功后，按完整controller身份与CPU子进程PGID终止v1后续路径，保留外部handoff回执。
v1若已自然STOP，保留原STOP；若尚GPU活跃或有外部进程，等待，绝不按历史PID盲杀。
动态成功时间文件在复用前绑定独立replay/SHA回执，不编辑旧stage/source_lock。

v2单次控制器自动原样复用→重新完整NONTEST8选帧/全源空间/strict→等待原426时间并核验移交→全源CPU镜头/同8B空间→426独立strict ZIP。
科学质量STOP和T更新0保持，新的B2不是新的教师微调，官网分未知。
最终仅一ZIP留Linux；不回传/AIC提交/读100confirm/本地复刻AIC分/手看复赛内容调参。
Mac不参与；共享GPU锁/追加账本/7200偏移和实际容量保持；新大流量仍须许可。
''', encoding='utf-8', newline='\n')
(NEW / 'CONTINUE.md').write_text('''# 当前唯一自主接续：B2 v2

先读PROTOCOL.md、config/source_lock、registration/progress/completion，以及temporal_reuse.py及controller/B2_duration_audit_20261008.json。
原始v1和全部教师失败/拒绝保留；禁止重开v1 launcher、改任何旧冻结源码/回答或把复用当新CUDA生成。
部署小量控制代码→CPU实际529边界/原29拒绝复现→真实NONTEST/processor→冻结→一次launch。
v2先复用实际B LoRA长输入probe与8/8时间回答并重新NONTEST8/strict，随后合法等待正在计算的v1 426/521时间完成和wrapper记账。
temporal_reuse核完整源/算法/模型/帧身份/原validator/输出SHA，再按实时进程身份受控移交；不打断有效GPU生成，不终止外部进程。
原时间成功后全源CPU镜头、同8B空间、独立strict与ZIP大小/SHA/CRC/唯一JSONL/426身份自动接续。
异常立即独立修复；只有PASS_COMPLETE_426_B2_8B_ZIP_ON_LINUX和全部真实验收才能宣称可提交。
每15分钟静默巡检，最终一次报告方案、旧B保留/T0/新分未知、Linux路径/大小/SHA，并删除aic-linux。
最终包留Linux，不自动回传/官网提交；Mac不用，新大流量先许可。GPU空闲的CPU SHA/原生解码/共享队列是合法状态。
''', encoding='utf-8', newline='\n')
print('Created independent B2 v2 control; v1 frozen bytes unchanged.')
