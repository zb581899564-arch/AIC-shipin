"""First matched-input development preparation, no labels, training or GPU."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from pathlib import Path
import importlib.util
import json
import time
import torch
from prepare_summary import read, ref, bound, save
from summary_contract import require, signature, build_pixels, independent_pixels, build_text, independent_text
from summary_context_pixels import load_context_frames

W = Path('/home/inspur/aic_video_work')
ROOT = W/'bottleneck_24h_20261019_v1'


def main():
    torch.set_num_threads(2)
    reg = read(ROOT/'summary_dev_CPU_registration_09.json')
    for r in reg['code'].values():
        bound(r)
    original = read(bound(reg['source_registration']))
    old_cpu = read(bound(reg['context_acceptance']))
    contexts = {s['sid']:s for s in old_cpu['context_sources']}
    sources = [s for s in original['sources'] if s['group'] == 'check']
    adopted = read(bound(reg['matched_fullbaseline_source_adoption']))
    clocks = {s['sid']:s['clock_ref'] for s in adopted['sources'] if s['group']=='check'}
    require(set(clocks)=={s['sid'] for s in sources}, 'Exact retained canonical normalized development clocks')
    sources = [dict(s, clock_ref=clocks[s['sid']]) for s in sources]
    require(len(sources) == 8 and set(contexts) == {s['sid'] for s in sources}, 'Exact existing fixed8 development sources')
    dictionary_file = bound(reg['pixel_dictionary'])
    bound(reg['pixel_codec'])
    import sys
    sys.path.insert(0, str(dictionary_file.parent))
    spec = importlib.util.spec_from_file_location('summary07_retained_pixel_dictionary', dictionary_file)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    from transformers import AutoProcessor
    cfg = read(bound(reg['model_config']))
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True)
    out = ROOT/'summary_dev_inputs_09'; out.mkdir(exist_ok=False)
    catalog, requests = [], []; started = time.monotonic()
    for source in sources:
        sid = source['sid']; context = contexts[sid]
        clock = read(bound(source['clock_ref']))
        require(clock['source_sha256'] == source['media']['sha256'], 'Original native source identity')
        record = dict(id=sid, name=source['name'], source_sha256=source['media']['sha256'],
            clock=source['clock_ref'], cells=context['cells'], context_cases=context['cases'],
            source_kind='ADOPTED_SOURCE_CLEAR_CONTEXT_DICTIONARY', dictionary_ref=reg['pixel_dictionary'])
        frames, grid, ordinals = load_context_frames(record, module); catalog.append(record)
        require(all(0 <= o < len(clock['normalized_exact_pts']) for o in ordinals), 'Native ordinals in complete actual clock')
        for window in original['windows']:
            if window['sid'] != sid:
                continue
            uid = window['uid']; meta = window['meta']
            owner = dict(source_id=sid, source_sha256=source['media']['sha256'])
            pixels, plan = build_pixels(frames, grid, ordinals, clock['normalized_exact_pts'],
                                       meta['window_start'], meta['window_end'], owner)
            independent_pixels(frames, grid, pixels, plan, ordinals, clock['normalized_exact_pts'])
            encoded, text = build_text(processor, plan, pixels['video_grid_thw'], clock['physical_end_exact'])
            values = dict(**pixels, **encoded); independent_text(processor, plan, values, text)
            prefix = out/(uid+'.prefix.pt')
            with prefix.open('xb') as f:
                torch.save(encoded, f); f.flush(); os.fsync(f.fileno())
            request = dict(uid=uid, sid=sid, source_sha256=source['media']['sha256'], plan=plan,
                grid_hw=grid, prefix_ref=ref(prefix), input_signature=signature(values), text=text,
                source_clock_ref=source['clock_ref'], source_kind=record['source_kind'],
                first_new_pixel_text_native_QA=True, labels_read=False)
            p = out/(uid+'.json'); save(p, request); requests.append(ref(p))
            save(out/(uid+'.first_acceptance.json'), dict(status='PASS_FIRST_MATCHED_DEV_TWO_VIEW_INPUT',
                uid=uid, request=ref(p), labels_read=False, new_media_processor_or_model=0))
            print(json.dumps(dict(event='MATCHED_DEV_INPUT_ACCEPTED', sid=sid, uid=uid,
                                  input_tokens=text['prefix_tokens'])), flush=True)
        del frames
    require(len(requests) == 43, 'Exact original43 windows, no quality-selected subset')
    save(out/'source_catalog.json', dict(sources=catalog))
    save(out/'prepared.json', dict(inputs=requests, source_catalog=ref(out/'source_catalog.json'),
        exposed_development_not_blind=True, source_group='Fixed historical VideoXum8', labels_read=False))
    save(out/'input_acceptance.json', dict(status='PASS_ALL43_FIRST_MATCHED_DEV8_TWO_VIEW_INPUTS',
        sources=8, windows=43, prepared=ref(out/'prepared.json'), registration=ref(ROOT/'summary_dev_CPU_registration_09.json'),
        original_labels_read=False, new_media_decode=0, new_processor_encoding=0, model_calls=0,
        elapsed_seconds=time.monotonic()-started, inference_admitted=False))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        import traceback
        p = ROOT/'summary_dev_CPU_failure_09.json'
        if not p.exists():
            save(p, dict(error=repr(error), traceback=traceback.format_exc(), successful_items_preserved=True,
                         automatic_retry=False, labels_read=False, GPU_admitted=False))
        raise
