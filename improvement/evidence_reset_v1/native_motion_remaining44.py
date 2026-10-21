"""Explicit remaining CPU work after motion42's first configuration-QA failure.

Original42 code, first processor output, failure and all accepted native/cut
evidence stay immutable.  Exactly one S24 interval must be read again because
its native RGB was volatile.  That is counted as necessary repeated decoding,
never as a first decode or a repeated successful processor call.  No model or
training is available here; model_case only reads accepted exact tensors.
"""
from __future__ import annotations

import argparse
import ast
from fractions import Fraction
import gzip
import hashlib
import importlib
import inspect
import io
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback
import types


PARTITION = {'fit': ['S24', 'S15', 'S03', 'S20'],
             'process': ['S02', 'S06', 'S08', 'S23']}
SOURCES = tuple(s for ids in PARTITION.values() for s in ids)
INPUT_KEYS = {'pixel_values', 'image_grid_thw', 'input_ids', 'attention_mask'}
MAX_BYTES = 20 * 1024 * 1024
MAX_SECONDS = 300
STATUS = 'PASS_CPU_NATIVE_MOTION_INPUTS_REMAINING44_NOT_GPU_ADMISSION'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def ref(path):
    path = Path(path).resolve(strict=True)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            h.update(chunk)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=h.hexdigest())


def checked(reference, workspace):
    path = Path(reference['path']).resolve(strict=True)
    require(path.is_relative_to(workspace) and path.is_file(), 'Bound file escaped workspace')
    actual = ref(path)
    require(all(actual[k] == reference[k] for k in actual), 'Exact bound file identity changed: ' + str(path))
    return path


def readref(reference, workspace):
    return json.loads(checked(reference, workspace).read_text(encoding='utf-8'))


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def write_new(path, blob):
    with Path(path).open('xb') as stream:
        stream.write(blob)
        stream.flush()
        os.fsync(stream.fileno())


def load_original(reference, workspace):
    """Bound source execution without creating bytecode in immutable old42."""
    path = checked(reference, workspace)
    module = types.ModuleType('bound_native_motion_inputs42_for_remaining44')
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def context(root):
    root = Path(root).resolve(strict=True)
    workspace = root.parent.parent.resolve(strict=True)
    reg = json.loads((root / 'registration44.json').read_text(encoding='utf-8'))
    require(checked(reg['code_ref'], workspace) == Path(__file__).resolve(), 'Exact remaining44 code required')
    old_reg_path = checked(reg['old42_registration_ref'], workspace)
    old_root = old_reg_path.parent
    require(old_root != root and old_root.parent == root.parent and old_reg_path.name == 'registration42.json',
            'New separate remaining root and exact original42 registration required')
    old_reg = readref(reg['old42_registration_ref'], workspace)
    old = load_original(old_reg['code_ref'], workspace)
    _, _, actual_old_reg, manifest = old.context(old_root)
    require(actual_old_reg == old_reg and old.PARTITION == PARTITION, 'Original42 source protocol changed')
    failure_path = checked(reg['old42_failure_ref'], workspace)
    failure = readref(reg['old42_failure_ref'], workspace)
    require(failure_path == old_root / 'failure_prepare42.json'
            and failure['status'] == 'ACTUAL_CPU_PREPARE_FAILURE_RETAIN_ALL_NO_AUTOMATIC_RETRY'
            and failure['new_model_calls'] == failure['new_training'] == 0
            and 'independent_input_QA' in failure['traceback']
            and 'Original explicit128K fast image profile required' in failure['traceback']
            and not (old_root / 'input_acceptance42.json').exists(),
            'Only the actual first42 configuration-QA failure may enter this remaining stage')
    primary_path = checked(reg['old42_primary_ref'], workspace)
    primary = readref(reg['old42_primary_ref'], workspace)
    require(primary_path.parent == old_root / 'cases42'
            and primary['sid'] == 'S24' and primary['anchor_offset'] == 0
            and primary['evaluation_only'] is False and primary['durable_before_first_independent_QA']
            and primary['labels_read'] is False,
            'Adopt exactly the first S24 actual processor output without another processor call')
    nonprimary_cases = [p for p in (old_root / 'cases42').glob('*.json')
                        if not p.name.endswith('.primary.json')]
    require(list((old_root / 'cases42').glob('*.primary.json')) == [primary_path]
            and len(list((old_root / 'cases42').glob('*.pt.gz'))) == 1 and not nonprimary_cases,
            'Original42 must contain only its first primary and packed input')
    return root, workspace, reg, old_root, old_reg, old, manifest, primary


class Budget:
    def __init__(self, root, old_root, started):
        self.root, self.old_root, self.started = root, old_root, started

    def total(self):
        return sum(p.stat().st_size for folder in [self.root, self.old_root]
                   for p in folder.rglob('*') if p.is_file())

    def check(self):
        require(time.monotonic() - self.started < MAX_SECONDS, 'Remaining44 CPU deadline300seconds reached')

    def write(self, path, blob, *, failure=False):
        if not failure:
            self.check()
        path = Path(path)
        require(path.parent.resolve().is_relative_to(self.root) and not path.exists(),
                'Only fresh remaining44 files may be written')
        reserve = 64 * 1024
        require(self.total() + len(blob) + reserve <= MAX_BYTES,
                'Combined original42+remaining44 actual output exceeds20MiB; retain all')
        require(shutil.disk_usage(self.root).free >= len(blob) + reserve,
                'Actual next remaining buffer and failure receipt cannot fit')
        write_new(path, blob)
        return ref(path)

    def save(self, path, value):
        return self.write(path, json_bytes(value))


def smart_resize_binding(reference, workspace):
    path = checked(reference, workspace)
    module = importlib.import_module('transformers.models.qwen2_vl.image_processing_qwen2_vl')
    function = module.smart_resize
    require(Path(inspect.getfile(function)).resolve() == path,
            'Installed actual smart_resize source differs from registration')
    source = ast.parse(path.read_text(encoding='utf-8'))
    nodes = [n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'smart_resize']
    require(len(nodes) == 1, 'One actual installed smart_resize function required')
    return function, hashlib.sha256(ast.dump(nodes[0], include_attributes=False).encode()).hexdigest()


def expected_grid(native_height, native_width, smart_resize):
    height, width = smart_resize(native_height, native_width, factor=32, min_pixels=131072, max_pixels=131072)
    require(height > 0 and width > 0 and height % 32 == width % 32 == 0,
            'Bound smart_resize must yield positive factor32 geometry')
    # Equal effective min/max do not imply exact128K area: integer grid rounding
    # may fall below/above that value.  Verify the actual computed grid instead.
    return [1, height // 16, width // 16]


def QA(processor, values, text, rgb, pixel_sha256, smart_resize, old, torch):
    from torchvision.transforms.v2 import functional as TVF
    from torchvision.transforms import InterpolationMode
    t, h, w = old.model_values(values, torch)
    p = processor.image_processor
    require(p.patch_size == 16 and p.temporal_patch_size == 2 and p.merge_size == 2
            and p.min_pixels == p.max_pixels == 131072
            and p.do_resize and p.do_rescale and p.do_normalize and int(p.resample) == 3
            and p.__class__.__name__.endswith('Fast'), 'Actual effective128K patch16/time2/merge2 fast profile required')
    predicted = expected_grid(rgb.shape[0], rgb.shape[1], smart_resize)
    require([t, h, w] == predicted, 'Actual saved image grid differs from bound effective smart_resize geometry')
    require(hashlib.sha256(rgb.tobytes()).hexdigest() == pixel_sha256,
            'Real full-native RGB must match the first decoded pixel SHA; resized cache is insufficient')
    image = values['pixel_values'].reshape(h // 2, w // 2, 2, 2, 3, 2, 16, 16)
    image = image.permute(4, 5, 0, 2, 6, 1, 3, 7).reshape(3, 2, h * 16, w * 16)
    require(torch.equal(image[:, 0].contiguous().view(torch.uint8), image[:, 1].contiguous().view(torch.uint8)),
            'Single-image temporal duplication differs')
    original = torch.from_numpy(rgb).permute(2, 0, 1).contiguous()
    resized = TVF.resize(original, size=[h * 16, w * 16], interpolation=InterpolationMode.BICUBIC, antialias=True)
    mean = torch.tensor(p.image_mean, dtype=torch.float32) * (1. / p.rescale_factor)
    std = torch.tensor(p.image_std, dtype=torch.float32) * (1. / p.rescale_factor)
    expected = TVF.normalize(resized.to(torch.float32), mean, std)
    require(torch.equal(image[:, 0].contiguous().view(torch.uint8), expected.contiguous().view(torch.uint8)),
            'First independent actual native RGB resize/normalization/channel/patch proof failed')
    marker = processor.vision_start_token + processor.image_token + processor.vision_end_token
    require(text.count(marker) == 1 and text.count(processor.image_token) == 1
            and old.PROMPT in text and processor.video_token not in text,
            'Actual original single-image spatial template differs')
    count = t * h * w // 4
    expanded = text.replace(processor.image_token, processor.image_token * count)
    prefix = processor.tokenizer(expanded, return_tensors='pt', add_special_tokens=False, padding=False, truncation=False)
    require(all(torch.equal(prefix[k], values[k]) for k in ['input_ids', 'attention_mask']),
            'First independent exact image-token expansion must reproduce saved prefix')
    token_id = processor.tokenizer.convert_tokens_to_ids(processor.image_token)
    require(type(token_id) is int and token_id >= 0 and int((values['input_ids'] == token_id).sum()) == count,
            'Actual image tokens must equal actual grid product divided by4')
    return dict(status='PASS_FIRST_REMAINING_NATIVE_RGB_PATCH_PREFIX_FOUR_TENSOR_QA_44',
        raw_processor_size=dict(p.size), effective_min_pixels=p.min_pixels, effective_max_pixels=p.max_pixels,
        effective_size=dict(shortest_edge=131072, longest_edge=131072), expected_grid=predicted,
        actual_grid=[t, h, w], actual_resized_pixels=h * 16 * w * 16,
        image_token_id=token_id, image_tokens=count, prefix_tokens=values['input_ids'].shape[1],
        source_RGB_resize_patch_verified=True, single_image_temporal_duplicate_verified=True,
        exact_prefix_verified=True, original_size_metadata_preserved=True)


def decode_interval(media, clock, start, av, np, budget, state):
    state['frames'], state['native_rows'] = {}, []
    with av.open(str(media), mode='r') as container:
        require(len(container.streams.video) == 1, 'Exactly one original native video stream required')
        for ordinal, frame in enumerate(container.decode(container.streams.video[0])):
            budget.check()
            require(ordinal < clock['n_frames'] and frame.pts is not None and frame.time_base is not None,
                    'Decoded native ordinal/PTS escaped original clock')
            pts = Fraction(frame.pts) * Fraction(frame.time_base)
            require(pts == Fraction(clock['original_exact_pts'][ordinal]), 'Exact original native PTS differs')
            if ordinal < start:
                continue
            rgb = np.ascontiguousarray(frame.to_ndarray(format='rgb24'))
            require(rgb.dtype == np.uint8 and rgb.shape == (clock['height'], clock['width'], 3),
                    'Actual original native RGB24 geometry differs')
            state['frames'][ordinal] = rgb
            state['native_rows'].append(dict(ordinal=ordinal, original_pts_exact=str(pts),
                normalized_pts_exact=clock['normalized_exact_pts'][ordinal], rgb_shape=list(rgb.shape),
                pixel_sha256=hashlib.sha256(rgb.tobytes()).hexdigest()))
            if ordinal == start + 8:
                break
    require(list(state['frames']) == list(range(start, start + 9)),
            'A missing original native frame cannot be padded, skipped or replaced')
    return state['frames'], state['native_rows']


def verify_recovery_rows(actual, retained):
    require(len(actual) == len(retained) == 9 and actual == retained,
            'Necessary S24 reread must reproduce all9 original full-native RGB SHA/PTS/shape rows exactly')


def verify_recovery_gray(frames, native, workspace, cv2, np):
    with np.load(checked(native['gray_ref'], workspace), allow_pickle=False) as z:
        ordinals = native['native_ordinals']
        require(z['native_ordinals'].tolist() == ordinals
                and z['original_exact_pts'].tolist() == [r['original_pts_exact'] for r in native['native_frames']]
                and z['normalized_exact_pts'].tolist() == [str(r['normalized_pts_exact']) for r in native['native_frames']],
                'Original accepted S24 grayscale/native/PTS association changed')
        height, width = z['gray'].shape[1:]
        expected = np.stack([cv2.resize(cv2.cvtColor(frames[o], cv2.COLOR_RGB2GRAY),
                    (width, height), interpolation=cv2.INTER_AREA) for o in ordinals])
        require(expected.dtype == z['gray'].dtype and np.array_equal(expected, z['gray']),
                'Necessary reread must reproduce all9 retained grayscale frames exactly')


def case_primary(uid, sid, role, ordinal, offset, native_ref, frame_row, cache_ref, report,
                 processor_ref, text, signature, prompt):
    return dict(uid=uid, sid=sid, role=role, ordinal=ordinal, anchor_offset=offset,
        source_sha256=frame_row['source_sha256'], native_input_ref=native_ref,
        pixel_sha256=frame_row['pixel_sha256'], exact_pts=frame_row['original_pts_exact'],
        cache_ref=cache_ref, storage_pixel_alias='pixel_values_videos', dictionary_report=report,
        processor_ref=processor_ref, raw_template=text, prompt=prompt, input_signature=signature,
        durable_before_first_independent_QA=True, evaluation_only=offset == 4, labels_read=False)


def _prepare(root, state):
    started = time.monotonic()
    root, workspace, reg, old_root, old_reg, old, manifest, old_primary = context(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only a dedicated CPU-only child may prepare44')
    require(not any((root / n).exists() for n in ['prepare_started44.json', 'failure_prepare44.json',
        'input_acceptance44.json', 'sources44', 'cases44']), 'One explicit remaining44 attempt only; no automatic retry')
    budget = Budget(root, old_root, started)
    state.update(budget=budget, root=root, frames={}, sid=None, pending_uid=None, new_processor_calls=0,
                 first_native_intervals=0, first_native_interval_attempts=0,
                 necessary_S24_interval_rereads=0, necessary_S24_interval_reread_completed=False)
    budget.save(root / 'prepare_started44.json', dict(status='FIRST_EXPLICIT_REMAINING44_STARTED_NO_AUTOMATIC_RETRY',
        old42_registration_ref=reg['old42_registration_ref'], old42_failure_ref=reg['old42_failure_ref'],
        old42_primary_ref=reg['old42_primary_ref'], original42_unchanged=True, maximum_CPU_seconds=MAX_SECONDS,
        combined42_44_output_budget_bytes=MAX_BYTES, maximum_total_processor_calls=24,
        necessary_S24_native_interval_rereads=1, old_successful_processor_calls_to_adopt=1))
    import av
    import cv2
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    codec, dictionary = old.dictionary_helper(old_reg, manifest, workspace)
    smart_resize, smart_ast = smart_resize_binding(reg['smart_resize_code_ref'], workspace)
    cut = old.cut_helper(old_reg['cut_module_ref'], workspace, cv2, np)
    old_native = readref(old_primary['native_input_ref'], workspace)
    old_processor = readref(old_primary['processor_ref'], workspace)
    require(old_native['sid'] == 'S24' and old_native['eligible'] and old_native['cases'] == []
            and old_primary['ordinal'] == old_native['interval_start']
            and old_primary['source_sha256'] == old_native['source_sha256'],
            'Adopt the actual complete original same-shot S24 interval and first anchor only')
    spec = manifest['model_spec']
    processor = AutoProcessor.from_pretrained(spec['model_dir'], revision=spec['revision'],
        local_files_only=True, trust_remote_code=False, min_pixels=131072, max_pixels=131072)
    require(processor.image_processor.to_dict() == old_processor['image_processor_dict'],
            'Remaining work must preserve the exact original actual processor factory and metadata')
    processor_ref = budget.save(root / 'processor_metadata44.json', dict(old_processor,
        original42_processor_ref=old_primary['processor_ref'], original_size_metadata_preserved=True,
        raw_processor_size=dict(processor.image_processor.size), effective_min_pixels=processor.image_processor.min_pixels,
        effective_max_pixels=processor.image_processor.max_pixels,
        effective_size=dict(shortest_edge=131072, longest_edge=131072),
        smart_resize_code_ref=reg['smart_resize_code_ref'], smart_resize_ast_sha256=smart_ast,
        QA_configuration_correction='CHECK_EFFECTIVE_MINMAX_AND_ACTUAL_BOUND_GRID_NOT_RAW_SIZE_DICTIONARY',
        original_failure_retained=True, model_calls=0))
    sources_dir, cases_dir = root / 'sources44', root / 'cases44'
    sources_dir.mkdir()
    cases_dir.mkdir()
    catalog = {s['id']: s for s in manifest['scopes']['train']['sources']}
    require(set(SOURCES) <= set(catalog), 'All original fixed8sources required; no replacements')
    sources, cases, eligible = [], [], []
    for sid in SOURCES:
        budget.check()
        state.update(sid=sid, frames={}, pending_uid=None)
        source = catalog[sid]
        state.update(source_sha256=source['source_sha256'], clock_ref=source['clock_ref'], media_ref=source['media_ref'])
        require(source['group'] == 'train' and source['source_sha256'] == source['media_ref']['sha256'],
                'Actual original training-scope source/media identity differs')
        media = checked(source['media_ref'], workspace)
        clock = readref(source['clock_ref'], workspace)
        old.validate_clock(clock, source, media)
        start = old.interval_start(source['source_sha256'], clock['n_frames'])
        folder = sources_dir / sid
        folder.mkdir()
        if sid == 'S24':
            require(start == old_native['interval_start'] and source['clock_ref'] == old_native['clock_ref']
                    and source['media_ref'] == old_native['media_ref'], 'Necessary S24 reread cannot select another interval')
            state['necessary_S24_interval_rereads'] += 1
            frames, rows = decode_interval(media, clock, start, av, np, budget, state)
            verify_recovery_rows(rows, old_native['native_frames'])
            verify_recovery_gray(frames, old_native, workspace, cv2, np)
            state['necessary_S24_interval_reread_completed'] = True
            row = dict(old_native, original42_native_input_ref=old_primary['native_input_ref'], cases=[],
                original_native_cut_gray_QA_adopted=True, cut_descriptors_recomputed=False,
                necessary_native_interval_reread_count=1, reread_reason='ORIGINAL42_VOLATILE_NATIVE_RGB_LOST_BEFORE_FIRST_QA',
                reread_raw9_pixel_SHA_PTS_shape_match=True, reread_gray9_exact_match=True,
                first_processor_output_adopted_without_processor_call=True)
        else:
            state['first_native_interval_attempts'] += 1
            frames, rows = decode_interval(media, clock, start, av, np, budget, state)
            state['first_native_intervals'] += 1
            grays, comparisons = old.gray_and_cuts(frames, cut, cv2, np)
            buffer = io.BytesIO()
            np.savez_compressed(buffer, gray=grays, native_ordinals=np.array(list(frames), dtype=np.int64),
                original_exact_pts=np.array([r['original_pts_exact'] for r in rows]),
                normalized_exact_pts=np.array([str(r['normalized_pts_exact']) for r in rows]))
            gray_ref = budget.write(folder / 'gray44.npz', buffer.getvalue())
            with np.load(checked(gray_ref, workspace), allow_pickle=False) as saved:
                require(np.array_equal(saved['gray'], grays) and saved['native_ordinals'].tolist() == list(frames)
                        and saved['original_exact_pts'].tolist() == [r['original_pts_exact'] for r in rows]
                        and saved['normalized_exact_pts'].tolist() == [str(r['normalized_pts_exact']) for r in rows],
                        'First new retained native grayscale/PTS/ordinal roundtrip differs')
            same_shot = not any(c['is_cut'] for c in comparisons)
            row = dict(sid=sid, role=next(k for k, ids in PARTITION.items() if sid in ids),
                source_sha256=source['source_sha256'], media_ref=source['media_ref'], clock_ref=source['clock_ref'],
                interval_start=start, native_ordinals=list(frames), native_frames=rows,
                native_width=clock['width'], native_height=clock['height'], crop_geometry=old.crop_geometry(clock['width'], clock['height']),
                gray_ref=gray_ref, gray_shape=list(grays.shape), grayscale_maxedge=192,
                cut_module_ref=old_reg['cut_module_ref'], cut_descriptor_ast_sha256=cut.descriptor_ast_sha256,
                cut_thresholds=dict(hist=cut.HIST_THRESHOLD, gray_mad=cut.GRAY_MAD_THRESHOLD),
                adjacent_cut_comparisons=comparisons, eligible=same_shot,
                eligibility_reason='NINE_EXACT_NATIVE_FRAMES_SAME_PRODUCTION_SHOT' if same_shot else 'CUT_IN_FIXED_INTERVAL_NO_REPLACEMENT',
                anchor_ordinals=[start, start + 4, start + 8], evaluation_only_ordinal=start + 4,
                middle_used_for_flow_ROI_fallback_or_correction=False, labels_read=False, model_calls=0, new_training=0, cases=[],
                decode_profile=dict(PyAV_version=av.__version__, libav_versions=av.library_versions,
                    RGB_format='rgb24', sequential_decode=True, seek=False, OpenCV_version=cv2.__version__),
                necessary_native_interval_reread_count=0)
            del grays
        native_ref = budget.save(folder / 'native_input44.json', row)
        if row['eligible']:
            eligible.append(sid)
            # Non-anchor RGB is no longer needed after native/cut/gray adoption.
            for ordinal in list(frames):
                if ordinal not in row['anchor_ordinals']:
                    del frames[ordinal]
            for offset in [0, 4, 8]:
                budget.check()
                ordinal = start + offset
                uid = sid + '_N' + str(ordinal).zfill(8)
                state['pending_uid'] = uid
                if sid == 'S24' and offset == 0:
                    require(uid == old_primary['uid'], 'Exactly one original successful processor output adopted')
                    primary = dict(old_primary, native_input_ref=native_ref, original42_primary_ref=reg['old42_primary_ref'])
                    values = old.unpack_values(checked(primary['cache_ref'], workspace), dictionary, torch)
                    require(codec.signature(values) == primary['input_signature'], 'Original successful packed input bits changed')
                else:
                    text = processor.apply_chat_template([dict(role='user', content=[dict(type='image'),
                        dict(type='text', text=old.PROMPT)])], tokenize=False, add_generation_prompt=True, enable_thinking=False)
                    encoded = processor(text=[text], images=[Image.fromarray(frames[ordinal])], padding=True, return_tensors='pt')
                    state['new_processor_calls'] += 1
                    require(state['new_processor_calls'] <= 23, 'One adopted plus at most23 first new processor calls')
                    require(set(encoded) == INPUT_KEYS, 'Actual new single-image four-tensor schema differs')
                    values = {k: encoded[k].contiguous() for k in INPUT_KEYS}
                    data, report = old.packed_values(values, dictionary, torch)
                    cache_ref = budget.write(cases_dir / (uid + '.pt.gz'), data)
                    frame_row = dict(rows[offset], source_sha256=source['source_sha256'])
                    primary = case_primary(uid, sid, row['role'], ordinal, offset, native_ref, frame_row,
                        cache_ref, report, processor_ref, text, codec.signature(values), old.PROMPT)
                    primary_ref = budget.save(cases_dir / (uid + '.primary.json'), primary)
                    require(report['pixel_values_videos']['storage'] == 'PIXEL_UINT8_BIT_LUT_V1',
                            'Lossless dictionary required; no original tensor fallback')
                    restored = old.unpack_values(checked(cache_ref, workspace), dictionary, torch)
                    require(codec.exact_equal(values, restored), 'Durable actual four-tensor roundtrip differs')
                    values = restored
                    del encoded, data, restored
                if sid == 'S24' and offset == 0:
                    primary_ref = budget.save(cases_dir / (uid + '.primary.json'), primary)
                budget.check()
                qa = QA(processor, values, primary['raw_template'], frames[ordinal], primary['pixel_sha256'],
                        smart_resize, old, torch)
                qa['smart_resize_code_ref'] = reg['smart_resize_code_ref']
                qa['smart_resize_ast_sha256'] = smart_ast
                case = dict(primary, primary_ref=primary_ref, QA=qa,
                    packed_roundtrip='ALL_FOUR_TENSORS_BIT_EXACT',
                    packed_roundtrip_QA_basis=('ADOPTED_BOUND42_SUCCESS_BEFORE_CONFIGURATION_FAILURE'
                        if sid == 'S24' and offset == 0 else 'FIRST44_ACTUAL_FOUR_TENSOR_ROUNDTRIP'),
                    native_RGB_QA_source=('NECESSARY_ORIGINAL9FRAME_REREAD_ALL_RAW_SHA_AND_GRAY_EXACT'
                        if sid == 'S24' else 'FIRST_NATIVE_INTERVAL_DECODE'),
                    status='PASS_FIRST_NATIVE_SPATIAL_INPUT_REMAINING44')
                case_ref = budget.save(cases_dir / (uid + '.json'), case)
                row['cases'].append(case_ref)
                cases.append(case_ref)
                # Release the actual native RGB only after its first complete QA.
                del frames[ordinal]
                del values
                state['pending_uid'] = None
        sources.append(budget.save(folder / 'source44.json', dict(row, native_input_ref=native_ref)))
        state['frames'] = {}
        del frames
    require(len(sources) == 8 and state['necessary_S24_interval_rereads'] == 1
            and state['first_native_intervals'] == 7 and len(cases) == 3 * len(eligible)
            and state['new_processor_calls'] + 1 == len(cases) <= 24,
            'Fixed8source coverage, one necessary S24 reread and no repeated successful processor calls required')
    result = dict(status=STATUS, source_refs=sources, case_refs=cases, eligible_source_ids=eligible,
        source_partition=PARTITION, sources_covered=8, ineligible_source_ids=[s for s in SOURCES if s not in eligible],
        actual_new_native_intervals_decoded=8, actual_new_native_frames_retained_as_gray=72,
        actual_new_processor_calls=state['new_processor_calls'] + 1,
        count_scope='FIRST_INPUT_TOTALS_ACROSS_BOUND42_AND44_CHAIN',
        first_native_intervals_decoded_in_remaining44=7, necessary_S24_native_interval_rereads=1,
        total_native_interval_decode_executions_in_chain=9, actual_decode_passes_in_remaining44=8,
        old_successful_processor_calls_adopted=1, new_processor_calls_in_remaining44=state['new_processor_calls'],
        successful_processor_calls_repeated=0, original42_native_cut_gray_QA_adopted=True,
        new_model_calls=0, new_training=0, processor_ref=processor_ref, model_spec=spec,
        registration_ref=ref(root / 'registration44.json'), code_ref=reg['code_ref'],
        original42_registration_ref=reg['old42_registration_ref'], original42_failure_ref=reg['old42_failure_ref'],
        original42_primary_ref=reg['old42_primary_ref'], input_code_refs=manifest['input_code'],
        smart_resize_code_ref=reg['smart_resize_code_ref'], smart_resize_ast_sha256=smart_ast,
        same_shot_eligibility_checked_before_processor=True, source_replacement=False,
        middle_frame_only_for_evaluation=True, original_clocks_modified=False, original_baseline_modified=False,
        original42_files_modified=False, original_failure_retained=True, automatic_GPU=False,
        seconds=time.monotonic() - started, maximum_CPU_seconds=MAX_SECONDS,
        output_budget_bytes=MAX_BYTES, combined42_44_output_bytes_before_acceptance=budget.total())
    budget.save(root / 'input_acceptance44.json', result)
    return result


def preserve_failure_RGB(state):
    frames = state.get('frames', {})
    if not frames:
        return dict(status='NO_ACTIVE_NATIVE_RGB_BUFFER')
    try:
        import numpy as np
        ordinals = sorted(frames)
        by_ordinal = {row['ordinal']: row for row in state.get('native_rows', [])}
        buffer = io.BytesIO()
        np.savez_compressed(buffer, rgb=np.stack([frames[o] for o in ordinals]),
            native_ordinals=np.array(ordinals, dtype=np.int64),
            original_exact_pts=np.array([by_ordinal[o]['original_pts_exact'] for o in ordinals]),
            normalized_exact_pts=np.array([str(by_ordinal[o]['normalized_pts_exact']) for o in ordinals]))
        budget = state['budget']
        cache_ref = budget.write(state['root'] / 'failure_active_nativeRGB44.npz', buffer.getvalue(), failure=True)
        return dict(status='ACTIVE_REAL_NATIVE_RGB_RETAINED_FOR_EXPLICIT_RECOVERY_ONLY', cache_ref=cache_ref,
            sid=state['sid'], ordinals=ordinals,
            source_sha256=state['source_sha256'], clock_ref=state['clock_ref'], media_ref=state['media_ref'],
            pixel_SHA256=[hashlib.sha256(frames[o].tobytes()).hexdigest() for o in ordinals])
    except BaseException as error:
        return dict(status='ACTIVE_NATIVE_RGB_NOT_DURABLY_RETAINED',
                    reason=type(error).__name__ + ': ' + str(error), sid=state.get('sid'),
                    ordinals=sorted(frames), no_automatic_retry=True)


def prepare(root):
    state = {}
    try:
        return _prepare(root, state)
    except BaseException:
        trace = traceback.format_exc()
        receipt = Path(root) / 'failure_prepare44.json'
        if not receipt.exists():
            retained = preserve_failure_RGB(state)
            write_new(receipt, json_bytes(dict(status='ACTUAL_REMAINING44_FAILURE_RETAIN_ALL_NO_AUTOMATIC_RETRY',
                traceback=trace, active_native_RGB=retained, sid=state.get('sid'), pending_uid=state.get('pending_uid'),
                new_processor_calls_in_remaining44=state.get('new_processor_calls', 0),
                necessary_S24_native_interval_rereads=state.get('necessary_S24_interval_rereads', 0),
                necessary_S24_native_interval_reread_completed=state.get('necessary_S24_interval_reread_completed', False),
                first_native_interval_attempts_in_remaining44=state.get('first_native_interval_attempts', 0),
                first_native_intervals_decoded_in_remaining44=state.get('first_native_intervals', 0),
                new_model_calls=0, new_training=0, original42_files_modified=False)))
        raise


def model_case(root, case_ref):
    """Read accepted old/new packed input only; never decode/process or rerun QA."""
    root, workspace, reg, _, old_reg, old, manifest, _ = context(root)
    accepted = json.loads((root / 'input_acceptance44.json').read_text(encoding='utf-8'))
    require(accepted['status'] == STATUS and accepted['registration_ref'] == ref(root / 'registration44.json')
            and accepted['code_ref'] == reg['code_ref'] and case_ref in accepted['case_refs'],
            'Only exact accepted remaining44 case references may load')
    case = readref(case_ref, workspace)
    require(Path(case_ref['path']).resolve().is_relative_to(root)
            and case['status'] == 'PASS_FIRST_NATIVE_SPATIAL_INPUT_REMAINING44'
            and case['packed_roundtrip'] == 'ALL_FOUR_TENSORS_BIT_EXACT'
            and case['sid'] in accepted['eligible_source_ids'] and case['prompt'] == old.PROMPT
            and case['labels_read'] is False, 'Accepted case identity or first input-QA status changed')
    native = readref(case['native_input_ref'], workspace)
    offset = case['anchor_offset']
    require(native['eligible'] and offset in [0, 4, 8] and case['evaluation_only'] == (offset == 4)
            and case['ordinal'] == native['interval_start'] + offset
            and case['source_sha256'] == native['source_sha256']
            and case['pixel_sha256'] == native['native_frames'][offset]['pixel_sha256'],
            'Exact saved native ownership/evaluation-only role changed')
    import torch
    codec, dictionary = old.dictionary_helper(old_reg, manifest, workspace)
    values = old.unpack_values(checked(case['cache_ref'], workspace), dictionary, torch)
    require(set(values) == INPUT_KEYS and codec.signature(values) == case['input_signature'],
            'Accepted actual old/new four-tensor signature changed')
    return case, values


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-root', required=True)
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    print(json.dumps(prepare(args.run_root), allow_nan=False))
