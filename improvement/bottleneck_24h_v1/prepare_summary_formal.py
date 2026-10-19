"""Conditional first production inputs from accepted image patches; CPU only.

No media decode, image encoding, labels, model, mask selection or auto-recovery.
An external capability admission must exist before this entry can run.
"""
import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import torch

from summary_contract import (build_pixels, build_text, independent_pixels,
                              independent_text, require, signature)
from summary_context_pixels import load_context_frames

W = Path('/home/inspur/aic_video_work')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def bound(reference):
    path = Path(reference['path']).resolve(strict=True)
    require(path.is_relative_to(W) and path.is_file(), 'File outside explicit Linux workspace')
    require(sha(path) == reference['sha256'], 'Registered artifact changed: ' + str(path))
    if 'bytes' in reference:
        require(path.stat().st_size == reference['bytes'], 'Registered byte size changed')
    return path


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())


def load_dictionary(registration):
    # Kept explicit even for the currently uncompressed original .pt cases.
    codec = bound(registration['pixel_codec_ref'])
    dictionary = bound(registration['pixel_dictionary_ref'])
    if 'codec' in sys.modules:
        require(Path(sys.modules['codec'].__file__).resolve() == codec, 'Codec module collision')
    else:
        spec = importlib.util.spec_from_file_location('codec', codec)
        module = importlib.util.module_from_spec(spec); sys.modules['codec'] = module
        spec.loader.exec_module(module)
    spec = importlib.util.spec_from_file_location('summary_formal_dictionary', dictionary)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main(registration_path):
    require(os.uname().nodename == 'inspur-NP5570M5' and not torch.cuda.is_initialized(),
            'Only the registered CPU child on the actual training host')
    regpath = Path(registration_path).resolve(strict=True)
    reg = read(regpath)
    require(reg['schema'] == 'SUMMARY_TWO_VIEW_FORMAL_426_V14', 'Explicit production version required')
    root = Path(reg['root']).resolve(strict=True)
    require(root.is_relative_to(W), 'New production root outside workspace')
    for name, reference in reg['code'].items():
        require(bound(reference) == Path(__file__).resolve().parent / name, 'Executed code is not registered')
    admission = read(bound(reg['production_admission_ref']))
    require(admission['status'] == 'ADMIT_FIXED_SUMMARY_FINAL559_426'
            and admission['allow_first_formal_inputs'] is True
            and admission['main_review_completed'] is True,
            'Actual external capability review must precede formal inputs')
    bound(reg['final_adapter_ref']); frozen = read(bound(reg['final_freeze_ref']))
    require(frozen['status'] == 'FINAL559_WEIGHTS_FROZEN_BEFORE_DEV_METRICS'
            and frozen['final_adapter_ref']['sha256'] == reg['final_adapter_ref']['sha256'],
            'Only the fixed final559 adapter may be prepared for production')
    require(0 < reg['actual_resident_parameters'] <= reg['actual_pipeline_parameters'] <= 9_000_000_000,
            'Actual declared complete pipeline must satisfy the parameter limit')
    torch.set_num_threads(reg['cpu_threads'])
    old = read(bound(reg['original_CPU_acceptance_ref']))
    metadata = read(bound(reg['metadata_cache_ref']))
    require(old['status'] == 'PASS_ALL_REGISTERED_NEW_FEATURE_INPUTS'
            and metadata['status'] == 'COMPLETE426_NEW_PURPOSE_METADATA_AVAILABILITY_ONLY_NO_PRODUCTION_ADMISSION',
            'Adopt exact old acceptance and first new-purpose structural metadata')
    sources = {source['id']: source for source in old['sources']}
    rows = {source['sid']: source for source in metadata['source_rows']}
    require(set(sources) == set(rows) == {str(i) for i in range(426)}, 'All426 source denominator')
    require(reg['expected_sources'] == 426 and reg['expected_windows'] ==
            sum(len(source['windows']) for source in rows.values()), 'Fixed declared window count')
    dictionary = load_dictionary(reg)
    from transformers import AutoProcessor
    config = read(bound(reg['model_config_ref']))
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True)
    out = root / 'formal_inputs_14'; out.mkdir(exist_ok=False)
    save(out / 'claim.json', dict(registration_ref=ref(regpath), admission_ref=reg['production_admission_ref'],
        pid=os.getpid(), utc=datetime.now(timezone.utc).isoformat(), automatic_retry=False))
    catalog, requests, source_acceptance = [], [], []
    started = time.monotonic()
    for sid in sorted(sources, key=int):
        oldsource, row = sources[sid], rows[sid]
        clock = read(bound(row['clock_ref']))
        require(clock['source_sha256'] == row['source_sha256'], 'Original accepted media identity')
        require(oldsource['clock_sha256'] == row['clock_ref']['sha256']
                and oldsource['native_sha256'] == row['native_ref']['sha256'], 'Frozen clock/native identity')
        bound(row['native_ref'])
        record = dict(id=sid, name=sid, source_sha256=row['source_sha256'], clock=row['clock_ref'],
            cells=oldsource['feature_cells'], kind='ADOPTED_FORMAL_2HZ_ORIGINAL_IMAGE_PATCHES',
            source_kind='ADOPTED_FORMAL_2HZ_ORIGINAL_IMAGE_PATCHES',
            context_cases=[dict(path=case['path'], sha256=case['sha256'], grids=case['grid'],
                                samples=case['samples']) for case in oldsource['chunks']])
        frames, grid, ordinals = load_context_frames(record, dictionary)
        require(len(frames) == row['source_cells'], 'Every original source observation adopted')
        points = clock['normalized_exact_pts']; end = F(clock['physical_end_exact'])
        # Same equal <=30s partition as the original external inputs; not chosen
        # from official content, predictions, scores or human labels.
        count = (end.numerator + 30 * end.denominator - 1) // (30 * end.denominator)
        actual_windows = [(str(end*i/count), str(end*(i+1)/count)) for i in range(count)]
        require(actual_windows == [(v['start_exact'], v['end_exact']) for v in row['windows']],
                'Declared equal-window source clock partition changed')
        folder = out / sid; folder.mkdir(exist_ok=False)
        accepted = []
        for index, (start, stop) in enumerate(actual_windows):
            uid = 'F%03d_W%03d' % (int(sid), index)
            pixels, plan = build_pixels(frames, grid, ordinals, points, start, stop,
                                       dict(source_id=sid, source_sha256=row['source_sha256']))
            independent_pixels(frames, grid, pixels, plan, ordinals, points)
            encoded, text = build_text(processor, plan, pixels['video_grid_thw'], end)
            values = dict(**pixels, **encoded)
            independent_text(processor, plan, values, text)
            prefix = folder / (uid + '.prefix.pt')
            with prefix.open('xb') as stream:
                torch.save(encoded, stream); stream.flush(); os.fsync(stream.fileno())
            request = dict(uid=uid, sid=sid, source_sha256=row['source_sha256'], plan=plan,
                grid_hw=grid, prefix_ref=ref(prefix), input_signature=signature(values), text=text,
                source_clock_ref=row['clock_ref'], source_kind=record['source_kind'],
                first_new_pixel_text_native_QA=True, labels_read=False)
            request_path = folder / (uid + '.json'); save(request_path, request)
            request_ref = ref(request_path); requests.append(request_ref); accepted.append(request_ref)
            save(folder / (uid + '.first_acceptance.json'), dict(
                status='PASS_FIRST_FORMAL_SUMMARY_TWO_VIEW_INPUT', uid=uid, request_ref=request_ref,
                new_media_decode=0, new_image_encoding=0, model_calls=0, labels_read=False))
            del pixels, encoded, values
        catalog.append(record)
        receipt = folder / 'source_completion.json'
        save(receipt, dict(status='PASS_SOURCE_FIRST_SUMMARY_FORMAL_INPUTS', sid=sid,
            registration_ref=ref(regpath), inputs=accepted, source_record=record,
            successful_items_preserved=True))
        source_acceptance.append(ref(receipt)); del frames
        print(json.dumps(dict(event='FORMAL_SUMMARY_SOURCE_INPUTS_ACCEPTED', sid=sid,
                              windows=len(accepted), total_windows=len(requests))), flush=True)
    require(len(requests) == reg['expected_windows'] and len(catalog) == 426, 'All declared new inputs')
    save(out / 'source_catalog.json', dict(sources=catalog))
    save(out / 'prepared.json', dict(inputs=requests, source_catalog=ref(out / 'source_catalog.json'),
        labels_read=False, original_426_source_denom=True, independent_external_admission=True))
    save(out / 'input_acceptance.json', dict(status='PASS_ALL426_FIRST_SUMMARY_FORMAL_TWO_VIEW_INPUTS',
        sources=426, windows=len(requests), prepared_ref=ref(out / 'prepared.json'),
        source_acceptance_refs=source_acceptance, registration_ref=ref(regpath),
        new_media_decode=0, new_image_processor=0, model_calls=0, labels_read=False,
        elapsed_seconds=time.monotonic()-started, inference_not_started=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--registration', required=True)
    args = parser.parse_args()
    try:
        main(args.registration)
    except BaseException as error:
        failure = Path(args.registration).resolve().parent / 'formal_input_failure_14.json'
        if not failure.exists():
            save(failure, dict(error=repr(error), traceback=traceback.format_exc(),
                preserve_all_successful_items=True, automatic_retry=False, model_started=False,
                utc=datetime.now(timezone.utc).isoformat()))
        raise
