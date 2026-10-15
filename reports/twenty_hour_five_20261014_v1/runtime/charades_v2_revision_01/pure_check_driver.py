"""Linux synthetic reference/reuse check; does not open any real source/cache."""
import ast
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types

payload = json.loads(base64.b64decode(sys.stdin.buffer.readline()))
code = payload['code']
ast.parse(code)
os.environ['CUDA_VISIBLE_DEVICES'] = ''


def require(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False)


def read(path):
    return json.loads(Path(path).read_text())


with tempfile.TemporaryDirectory(prefix='charades_v2_pure_contract_') as tmp:
    base = Path(tmp)
    root, oldroot = base/'synthetic_new', base/'synthetic_old'
    codepath = base/'synthetic_source_under_check.py'
    codepath.write_text(code, encoding='utf-8')
    common = types.ModuleType('charades_v2_common')
    common.ROOT, common.V1ROOT = root, oldroot
    common.RUN, common.LEGACY = base/'unused_model', base/'unused_runtime'
    common.read, common.save, common.sha, common.require = read, save, sha, require
    common.utc, common.check_deadline = lambda: 'PURE_SYNTHETIC', lambda: None
    common.resource_snapshot = lambda: {'pure_synthetic': True}
    sys.modules['charades_v2_common'] = common
    module = types.ModuleType('synthetic_charades_cpu')
    module.__file__ = str(codepath)
    exec(compile(code, str(codepath), 'exec'), module.__dict__)
    F = module.F
    points = [str(F(i, 25)) for i in range(80)]
    clock = dict(source_id='PURE', source_name='PURE', normalized_exact_pts=points,
        original_exact_pts=points, first_original_pts_exact='0', n_frames=80, native_frames=80,
        last_frame_duration_exact='1/25', physical_end_exact='16/5',
        positive_last_frame_duration_verified=True, original_zero_origin_verified=True)
    reference = dict(actions=[
        dict(class_id='cPURE', start_exact='0.0400', end_exact='0.2000'),
        dict(class_id='cNEG', start_exact='-1', end_exact='1'),
        dict(class_id='cEND', start_exact='1', end_exact='4'),
        dict(class_id='cNOFRAME', start_exact='0.01', end_exact='0.02'),
        dict(class_id='cBAD', start_exact='NaN', end_exact='1'),
        dict(class_id='cZERO', start_exact='1', end_exact='1')], author_length_raw='3.2000')
    report = module._validate_reference(clock, reference)
    require(report['eligible_action_count'] == 1 and report['censored_action_count'] == 5,
            'Partial eligibility denominator mismatch')
    require([row['original_action'] for row in report['actions']] == reference['actions'] and
            report['actions'][0]['start_exact'] == '0.0400' and
            report['actions'][0]['end_exact'] == '0.2000', 'Author original text was rewritten')
    require(report['whole_source_GT_complete'] is False and
            report['whole_source_precision_recall_F1_admitted'] is False and
            report['censored_is_ordinary'] is False, 'Partial label completeness was fabricated')
    zero = module._validate_reference(clock, dict(actions=reference['actions'][1:], author_length_raw='3.2000'))
    empty = module._validate_reference(clock, dict(actions=[], author_length_raw='3.2000'))
    require(zero['zero_in_domain_source_retained'] and zero['eligible_action_count'] == 0 and
            empty['original_empty_actions_retained'], 'Zero eligible/empty source was rejected')
    rejections = 0
    for field, value in [('positive_last_frame_duration_verified', False),
                         ('original_zero_origin_verified', False), ('last_frame_duration_exact', '0')]:
        bad = dict(clock, **{field: value})
        try:
            module._validate_reference(bad, reference)
        except module.NativeEndpointError:
            rejections += 1
        else:
            raise ValueError('Physical clock error was accepted')
    try:
        module._validate_reference(clock, dict(actions='INVALID', author_length_raw='3.2'))
    except ValueError as error:
        require(not isinstance(error, module.NativeEndpointError), 'Metadata error became replacement-eligible')
    else:
        raise ValueError('Invalid reference schema accepted')

    # Synthetic byte fixtures have media/cache-looking filenames but are never
    # passed to a decoder, tensor loader, processor, tokenizer or model.
    source = dict(source_id='PURE', role='dev', rank=1)
    folder = oldroot/'native_01'/'PURE'
    mediapath = oldroot/'media_01'/'PURE'/'PURE.mp4'
    mediapath.parent.mkdir(parents=True)
    mediapath.write_bytes(b'SYNTHETIC_NOT_MEDIA')
    receipt = dict(path=str(mediapath), bytes=mediapath.stat().st_size, sha256=sha(mediapath))
    goodref = dict(actions=reference['actions'][:1], author_length_raw='3.2000')
    clock.update(source_path=str(mediapath), source_bytes=receipt['bytes'], source_sha256=receipt['sha256'])
    oldbindings = dict(source=source, media_receipt=receipt,
        reference_metadata_sha256=module._canonical_sha(goodref), tensor_cache_helper_files=module.HELPER_FILES)
    clockpath = folder/'native_clock.json'
    save(clockpath, dict(status='COMPLETE_ORIGINAL_NATIVE_CLOCK_MEASURED_BEFORE_DOMAIN_ADMISSION',
                        clock=clock, bindings=oldbindings))
    windows = module._windows(clock)
    planpath, domainpath = folder/'windows.json', folder/'reference_validation.json'
    save(planpath, dict(windows=windows, native_clock_sha256=sha(clockpath), reference_labels_used_for_windows=False))
    save(domainpath, dict(status='SYNTHETIC_OLD_DOMAIN'))
    entries, identity = [], {'synthetic_original_runtime_identity': True}
    for window in windows:
        wfolder = folder/('W'+str(window['index']).zfill(3))
        wfolder.mkdir()
        arraypath, tensorpath = wfolder/'frames.npz', wfolder/'encoded_tensors.pt.gz'
        arraypath.write_bytes(b'SYNTHETIC_NOT_NPZ')
        tensorpath.write_bytes(b'SYNTHETIC_NOT_TORCH')
        case = 'CH_PURE_W'+str(window['index']).zfill(3)
        inputpath = wfolder/'input.json'
        meta = dict(case_id=case, source_id='PURE', source_name='PURE', source_role='dev', source_rank=1,
            source_sha256=receipt['sha256'], source_bytes=receipt['bytes'], source_path=str(mediapath),
            source_total_frames=80, all_source_exact_pts=points, original_clock_origin_exact='0',
            window_start=window['start_exact'], window_end=window['end_exact'],
            source_frame_ordinals=window['source_frame_ordinals'], sample_exact_pts=window['sample_exact_pts'],
            native_clock_path=str(clockpath), native_clock_sha256=sha(clockpath),
            reference_available_to_inference=False, reference_labels_used_for_sampling=False, audio_observed=False,
            pixel_sha256=['synthetic_pixel']*64, frame_array_path=str(arraypath), frame_array_sha256=sha(arraypath))
        save(inputpath, meta)
        proofpath = wfolder/'cpu_input.json'
        proof = dict(status='PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT', case_id=case, source_name='PURE',
            input_path=str(inputpath), input_sha256=sha(inputpath), input_tokens=100,
            encoded_tensor_path=str(tensorpath), encoded_tensor_sha256=sha(tensorpath),
            encoded_tensor_format='TORCH_SAVE_GZIP_LOSSLESS_LEVEL1', encoded_tensor_compression_level=1,
            original_b_processor_runtime=identity, input_evidence=dict(physical_frames=64, tensor_signature={'synthetic':True}),
            CPU_only=True, CUDA_initialized=False, actual_new_processor_encodes=1, new_model_calls=0, new_optimizer_updates=0)
        save(proofpath, proof)
        entries.append(dict(case_id=case, source_name='PURE', input_path=str(inputpath), input_sha256=sha(inputpath),
            proof_path=str(proofpath), proof_sha256=sha(proofpath), input_tokens=100,
            encoded_tensor_path=str(tensorpath), encoded_tensor_sha256=sha(tensorpath),
            encoded_tensor_format=proof['encoded_tensor_format'], encoded_tensor_file_bytes=tensorpath.stat().st_size,
            rgb_npz_file_bytes=arraypath.stat().st_size))
    oldcomplete = dict(status=module.OLD_COMPLETION_STATUS, source_id='PURE', role='dev', rank=1, bindings=oldbindings,
        native_clock_path=str(clockpath), native_clock_sha256=sha(clockpath), proofs=entries, accepted_windows=1,
        original_b_processor_runtime=identity, CPU_only=True, CUDA_initialized=False, new_model_calls=0,
        new_optimizer_updates=0, GPU_launch_admitted=False, window_plan_path=str(planpath), window_plan_sha256=sha(planpath),
        reference_validation_path=str(domainpath), reference_validation_sha256=sha(domainpath))
    completepath = folder/'completion.json'
    save(completepath, oldcomplete)
    receipt.update(existing_native_clock_path=str(clockpath), existing_native_clock_sha256=sha(clockpath),
        existing_CPU_completion_path=str(completepath), existing_CPU_completion_sha256=sha(completepath))
    oldhashes = {str(p): sha(p) for p in oldroot.rglob('*') if p.is_file()}
    called = []
    def forbidden(*args, **kwargs):
        called.append('FORBIDDEN')
        raise ValueError('A reused success attempted new decoder/processor/runtime work')
    module._measure_clock = module._decode_rgb_once = module._load_cpu_runtime = forbidden
    out = root/'native_01'/'PURE'
    complete = module.prepare_source(source, receipt, goodref, out, {'pure_registration':True})
    require(complete['proofs'] == entries and complete['actual_new_processor_encodes'] == 0 and
            complete['new_clock_decodes'] == 0 and complete['new_RGB_decodes'] == 0 and not called,
            'Original input reuse performed duplicate work')
    require(complete['native_clock_path'] == str(clockpath) and
            Path(complete['reference_validation_path']).is_relative_to(root) and
            not list(out.glob('W*')), 'Large old cache or clock was copied into new scope')
    require({str(p): sha(p) for p in oldroot.rglob('*') if p.is_file()} == oldhashes, 'Old successful bytes changed')
    require(module.prepare_source(source, receipt, goodref, out, {'pure_registration':True}) == complete and not called,
            'Successful v2 completion did not return immutably')
    # SHA corruption must block reuse, never synthesize a fallback result.
    tensorpath.write_bytes(b'CORRUPTED_SYNTHETIC_TENSOR')
    try:
        module._reuse_cpu_completion(source, receipt, goodref, clock, clockpath, windows)
    except ValueError:
        corruption_rejected = True
    else:
        raise ValueError('Corrupted cache reuse was accepted')
    result = dict(status='PASS_CHARADES_V2_PURE_REFERENCE_AND_REUSE_CONTRACT_ONLY', syntax_files=1,
        eligible_actions=1, censored_actions=5, original_action_text_preserved=True,
        zero_eligible_and_empty_sources_retained=True, physical_clock_rejections=rejections,
        annotation_schema_failure_not_replacement=True, synthetic_inherited_CPU_inputs=1,
        successful_completion_reused_immutably=True, old_cache_paths_and_bytes_preserved=True,
        corruption_rejected=corruption_rejected, new_clock_decodes=0, new_RGB_decodes=0,
        actual_new_processor_encodes=0, real_media_reads=0, real_cache_reads=0, model_calls=0,
        whole_source_GT_complete=False, actual_CPU_or_GPU_admitted=False,
        code_bytes=len(code.encode()), code_sha256=hashlib.sha256(code.encode()).hexdigest())
    print(json.dumps(result, ensure_ascii=False))
