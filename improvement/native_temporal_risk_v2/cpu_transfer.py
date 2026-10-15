"""Bind completed v1 per-window CPU facts without repeating source decoding."""
from pathlib import Path
import dense_runtime as r

PARENT = r.RUN/'overnight_risk_20261012_v1/dense128_v1'
MANIFEST = r.HERE/'CPU_TRANSFER314.json'
EXPECTED_MANIFEST_SHA = '02b5b536255feb679ac1a378bfbc5aba7bd9399e4551f2d6e34ef380f3272dc7'


def validated_transfer(windows):
    registration = r.registration('rematch')[1]
    r.require(r.sha(MANIFEST) == registration['cpu_transfer_manifest_sha256'] == EXPECTED_MANIFEST_SHA,
              'exact partial CPU transfer manifest changed')
    value = r.read(MANIFEST)
    r.require(value['schema'] == 'EXACT_PER_WINDOW_CPU_PROOF_TRANSFER_314_V1' and
              value['old_root'] == str(PARENT) and value['transferred_complete_windows'] == 314 and
              value['remaining_new_cpu_windows'] == 207 and value['production_gpu_calls_before_recovery'] == 0 and
              value['old_scope_status'] == 'NATURAL_CPU_FAILED_NO_GLOBAL_ACCEPTANCE_NO_GPU',
              'partial transfer denominator or historical outcome differs')
    for path, expected in value['source_files'].items():
        r.require(Path(path).parent == PARENT and r.sha(path) == expected, 'original code/proof owner changed')
    for stem in ('old_cpu_failure', 'old_chain_failure'):
        r.require(r.sha(value[stem+'_path']) == value[stem+'_sha256'], 'original natural CPU failure changed')
    r.require(not (PARENT/'rematch_01/prepare_01/acceptance.json').exists() and
              not (PARENT/'rematch_01/gpu_01').exists(), 'cannot reinterpret old failed scope as globally accepted')
    transferred = {}
    for entry in value['entries']:
        identifier = entry['key']
        q, p = Path(entry['request_path']), Path(entry['proof_path'])
        r.require(q.name == 'request.json' and p.name == 'proof.json' and q.parent == p.parent and
                  q.parent.parent == PARENT/'rematch_01/prepare_01' and q.parent.name == identifier,
                  'old per-window proof path owner differs')
        r.require(identifier in windows and identifier not in transferred and
                  r.sha(q) == entry['request_sha256'] and r.sha(p) == entry['proof_sha256'],
                  'old per-window CPU proof is missing, repeated, or changed')
        request, proof = r.read(q), r.read(p)
        window = windows[identifier]
        r.require(request == proof['window'] == window and window['source_id'] == entry['video_id'] and
                  window['index'] == entry['index'] and identifier == r.digest([window['source_id'],window['index']]),
                  'actual current window differs from successful per-window CPU fact')
        evidence = proof['input_evidence']
        r.require(proof['processor_weights_loaded'] is False and proof['CUDA_initialized'] is False and
                  proof['new_model_calls'] == 0 and proof['RGB_cached'] is False,
                  'old proof is not CPU-only native preparation')
        r.require(evidence['window_digest'] == entry['window_digest'] == r.digest(window) and
                  evidence['recipe'] == r.RECIPE and evidence['source_sha256'] == window['source_sha256'] and
                  evidence['source_frame_ordinals'] == window['source_frame_ordinals'] and
                  evidence['sample_exact_pts'] == window['sample_exact_pts'] and
                  evidence['physical_frames'] == len(window['source_frame_ordinals']) and
                  len(evidence['frame_pixel_sha256']) == evidence['physical_frames'],
                  'old pixel/PTS/window fact differs')
        r.require(0 < evidence['input_tokens'] == entry['input_tokens'] <= 16384 and
                  evidence['processor_total_pixels'] == entry['processor_total_pixels'] ==
                  evidence['processor_effective_frames']*evidence['actual_pixels_per_frame'] <= 25165824 and
                  evidence['sampled_frames']*evidence['actual_pixels_per_frame'] <= 25165824 and
                  evidence['explicit_size'] == {'shortest_edge':4096,'longest_edge':25165824} and
                  evidence['max_physical_frames'] == 128 and evidence['truncation'] is False and
                  evidence['implicit_sampling'] is False, 'accepted old input exceeds original unchanged contract')
        transferred[identifier] = {k: entry[k] for k in ('key','video_id','index','request_path','request_sha256','proof_path','proof_sha256')}
    r.require(len(transferred) == 314, 'successful partial CPU transfer denominator differs')
    additional = [MANIFEST] + [Path(p) for p in value['source_files']]
    additional += [Path(value[stem+'_path']) for stem in ('old_cpu_failure','old_chain_failure')]
    return transferred, additional


def validated_target(windows):
    """Transfer the one real repaired CPU case, never decode it a second time."""
    registration = r.registration('rematch')[1]
    folder = r.HERE/'target_cpu_01'
    terminal_path = folder/'completion.json'
    r.require(r.sha(terminal_path) == registration['target_cpu_completion_sha256'],
              'one repaired actual CPU proof changed')
    terminal = r.read(terminal_path)
    r.require(terminal['status'] == 'PASS_ONLY_FAILED23_FRAME_ACTUAL_NATIVE_PROCESSOR' and
              terminal['source_id'] == '273' and terminal['index'] == 2 and
              terminal['new_model_calls'] == 0 and terminal['CUDA_initialized'] is False,
              'repaired target identity or CPU-only outcome differs')
    identifier = r.digest(['273',2])
    q, p = folder/'request.json', folder/'proof.json'
    r.require(terminal['request_path'] == str(q) and terminal['proof_path'] == str(p) and
              r.sha(q) == terminal['request_sha256'] and r.sha(p) == terminal['proof_sha256'] and
              r.read(q) == r.read(p)['window'] == windows[identifier],
              'repaired target request/proof differs from actual current window')
    proof = r.read(p)
    r.require(proof['input_evidence'] == terminal['input_evidence'] and
              proof['processor_weights_loaded'] is False and proof['CUDA_initialized'] is False and
              proof['new_model_calls'] == 0 and proof['RGB_cached'] is False,
              'target actual evidence or proof flags differ')
    evidence = proof['input_evidence']
    r.require(evidence['physical_frames'] == 23 and evidence['processor_effective_frames'] == 24 and
              evidence['processor_total_pixels'] <= 25165824 and evidence['input_tokens'] <= 16384 and
              evidence['padding_aware_resize']['adjusted'] is True and
              evidence['padding_aware_resize']['native_frames_removed'] == 0,
              'repaired target did not satisfy unchanged actual input budget')
    original_request = PARENT/'rematch_01/prepare_01'/identifier/'request.json'
    r.require(terminal['original_failed_request_path'] == str(original_request) and
              terminal['original_failed_request_sha256'] == r.sha(original_request) and r.read(original_request) == r.read(q),
              'repaired target differs from original failed request')
    extra = [terminal_path,q,p,original_request]
    for path, expected in terminal['bound_files'].items():
        r.require(r.sha(path) == expected, 'actual target CPU implementation changed')
        extra.append(Path(path))
    r.require(terminal['bound_files'][str(r.HERE/'dense_video.py')] == r.sha(r.HERE/'dense_video.py') and
              terminal['bound_files'][str(PARENT/'dense_runtime.py')] == r.sha(r.HERE/'dense_runtime.py'),
              'production resize is not the targeted actual CPU implementation')
    entry = dict(key=identifier,video_id='273',index=2,request_path=str(q),request_sha256=r.sha(q),
                 proof_path=str(p),proof_sha256=r.sha(p))
    return {identifier:entry},extra
