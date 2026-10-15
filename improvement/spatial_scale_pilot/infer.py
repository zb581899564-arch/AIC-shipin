"""One registered static diagnostic. Direct images, original spatial base, no labels."""
import datetime as dt
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path
from geometry import candidates, legal, parse_choice, parse_proposal, place, max_width
from encoding import encode

HERE = Path(__file__).resolve().parent
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
sys.path[:0] = [str(RUN/'b_score_aligned_package_v4'), str(RUN/'baseline_a_pts_v1'),
               str(RUN/'baseline_a_pts_v1/vendor'), str(RUN/'temporal_sft8b_v1')]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def main():
    from PIL import Image
    import torch
    import transformers
    from spatial_baseline import Qwen3VL, parse_focus_norm, compute_crop_size, center_to_box
    from engine import frozen_identity
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    config = json.loads((HERE/'config.json').read_text())
    lock = json.loads((HERE/'source_lock.json').read_text())
    for rel, digest in lock['files'].items():
        if sha(HERE/rel) != digest: raise ValueError('frozen file changed: '+rel)
    for path, digest in lock['external_files'].items():
        if sha(path) != digest: raise ValueError('pinned dependency changed: '+path)
    acceptance = json.loads((HERE/'encoding_acceptance.json').read_text())
    if acceptance['status'] != 'PASS_ALL_FOUR_ORIGINAL_BASELINE_PROCESSOR_TENSORS_EXACT':
        raise ValueError('exact original processor acceptance required')
    baseline_config = json.loads((RUN/'b_score_aligned_package_v4/config.json').read_text())
    if transformers.__version__ != '4.57.1': raise ValueError('unexpected transformer runtime')
    inputs = json.loads((HERE/'inputs.json').read_text())
    if len(inputs) != 4 or len({v['source_sha256'] for v in inputs}) != 4:
        raise ValueError('registered four-image denominator changed')
    for item in inputs:
        if set(item) != {'item_id','path','source_sha256','width','height','ratio'}:
            raise ValueError('input includes unregistered fields or reference labels')
        if sha(HERE/item['path']) != item['source_sha256']: raise ValueError('media SHA changed')
    write(HERE/'started.json', dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                                  source_lock_sha256=sha(HERE/'source_lock.json'),
                                  labels_available_to_inference=False))
    calls = []
    call_context = {'item_id': None, 'stage': 'MODEL_LOADING'}
    call_stream = (HERE/'calls.jsonl').open('x', encoding='utf-8')

    class MeasuredQwen(Qwen3VL):
        def _generate(self, messages, max_new_tokens):
            encoded, text, image_count = encode(self.processor, messages)
            encoded = encoded.to(self.device)
            prefix = encoded.input_ids.shape[1]
            if prefix > 16384: raise ValueError('input too long; no truncation')
            start = time.monotonic()
            with torch.inference_mode():
                out = self.model.generate(**encoded, max_new_tokens=max_new_tokens,
                    do_sample=False, num_beams=1, use_cache=True)
            torch.cuda.synchronize()
            ids = out[:, prefix:]
            raw = self.processor.batch_decode(ids, skip_special_tokens=True,
                clean_up_tokenization_spaces=False)[0]
            record = dict(input_tokens=int(prefix), output_tokens=int(ids.shape[1]),
                seconds=time.monotonic()-start, raw=raw,
                image_count=image_count, prompt_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                **call_context)
            # Persist real answers before any strict parser can reject them.
            call_stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False)+'\n')
            call_stream.flush()
            os.fsync(call_stream.fileno())
            calls.append(record)
            return raw

    model = MeasuredQwen(baseline_config['model_dir'], max_pixels=131072,
                         device_map={'':'cuda:0'}, attn_implementation='sdpa')
    for p in model.model.parameters(): p.requires_grad_(False)
    identity = frozen_identity(model.model, baseline_config)
    write(HERE/'model_identity.json', dict(base=identity, time_adapter_enabled=False,
        pipeline_parameters_if_integrated=8782459120, new_optimizer_updates=0,
        transformers_version=transformers.__version__, torch_version=torch.__version__))
    model.reset_peak_memory()
    with (HERE/'predictions.jsonl').open('x', encoding='utf-8') as stream:
        for item in inputs:
            start = time.monotonic()
            image = Image.open(HERE/item['path']).convert('RGB')
            if image.size != (item['width'], item['height']): raise ValueError('decoded dimensions changed')
            W, H = image.size
            ratio = item['ratio']
            call_context.update(item_id=item['item_id'], stage='BASELINE_CENTER')
            raw = model.predict_focus(image, ratio, max_new_tokens=128)
            center = parse_focus_norm(raw, W, H)
            if center is None: raise ValueError('original strict center failed')
            cw, ch = compute_crop_size(W, H, *ratio)
            baseline_box = center_to_box(*center, W, H, cw, ch)
            if not legal(baseline_box, W, H, ratio): raise ValueError('original illegal crop')
            integer_center = [round(v * 1000) for v in center]
            proposal_prompt = config['proposal_prompt'].format(tw=ratio[0], th=ratio[1])
            call_context['stage'] = 'JOINT_PROPOSAL'
            proposal_raw = model._generate([{'role':'user','content':[
                {'type':'image','image':image,'max_pixels':131072},
                {'type':'text','text':proposal_prompt}]}], 64)
            proposed_center, scale = parse_proposal(proposal_raw)
            pool = candidates(baseline_box, integer_center, proposed_center, scale, W, H, ratio)
            content = [{'type':'text','text':config['rank_prompt'].format(tw=ratio[0], th=ratio[1])},
                       {'type':'text','text':'Original source image:'},
                       {'type':'image','image':image,'max_pixels':131072}]
            for option in pool:
                x,y,w = option['box'];h=w*ratio[1]/ratio[0]
                # Rendering uses the exact evaluator-derived fractional-height crop.
                view = image.transform((320, round(320*ratio[1]/ratio[0])),
                    Image.Transform.EXTENT, (x,y,x+w,y+h), resample=Image.Resampling.BICUBIC)
                content += [{'type':'text','text':f'Candidate ID {option["id"]}:'},
                            {'type':'image','image':view,'max_pixels':131072}]
            call_context['stage'] = 'CANDIDATE_RANK'
            choice_raw = model._generate([{'role':'user','content':content}], 24)
            choice = parse_choice(choice_raw, len(pool))
            center_only = place(proposed_center, max_width(W,H,ratio), W,H,ratio)
            rec = dict(item_id=item['item_id'], source_sha256=item['source_sha256'],
                decoded_rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest(), ratio=ratio,
                status='MODEL_OK', baseline_box=baseline_box, baseline_center=integer_center,
                proposed_center=proposed_center, proposed_scale=scale, center_only_box=center_only,
                candidates=pool, choice=choice, chosen_box=pool[choice]['box'],
                calls=calls[-3:], end_to_end_seconds=time.monotonic()-start,
                reference_labels_read=False, time_selection_changed=False)
            stream.write(json.dumps(rec, ensure_ascii=False, allow_nan=False)+'\n');stream.flush()
            print(json.dumps({'item_id':item['item_id'],'status':'MODEL_OK','calls':len(calls)}),flush=True)
    call_stream.close()
    write(HERE/'inference_completion.json', dict(status='PASS_STATIC_INFERENCE_NOT_QUALITY',
        rows=len(inputs), calls=len(calls), peak_memory_mib=model.peak_memory_mib(),
        peak_scope='INFERENCE_AFTER_MODEL_LOADING_AND_HASH; full job nvidia-smi peak is in wrapper receipt',
        predictions_sha256=sha(HERE/'predictions.jsonl'), source_lock_sha256=sha(HERE/'source_lock.json'),
        new_optimizer_updates=0, official_score=None, labels_read=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        trace = traceback.format_exc()
        write(HERE/'failure.json', dict(status='STOP_NO_RETRY_NO_FALLBACK',
            utc=dt.datetime.now(dt.timezone.utc).isoformat(), error=type(exc).__name__+': '+str(exc),
            traceback=trace, raw_answers_path=str(HERE/'calls.jsonl')))
        raise
