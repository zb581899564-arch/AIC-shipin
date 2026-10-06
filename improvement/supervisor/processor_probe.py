"""CPU-only real-media check of the shared Qwen video timestamp contract."""
import argparse
import json
from pathlib import Path
from transformers import AutoProcessor
from inference_v2.qwen_io import build_temporal_messages, encode_qwen3vl_messages
from inference_v2.temporal import build_temporal_prompt


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True)
    ap.add_argument('--model',required=True)
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    rows=[json.loads(s) for s in Path(args.manifest).read_text().splitlines() if s.strip()][:3]
    processor=AutoProcessor.from_pretrained(args.model,local_files_only=True,min_pixels=131072,max_pixels=131072)
    result=[]
    for row in rows:
        duration=float(row['duration_sec'])
        for window in (None,(25.,55.)) if duration>=55 else (None,):
            messages=build_temporal_messages(row['video_path'],build_temporal_prompt(row['query'],'windowed' if window else 'multi'),
                       clip_start_sec=window[0] if window else None,clip_end_sec=window[1] if window else None)
            encoded=encode_qwen3vl_messages(processor,messages)
            if len(encoded.sampling)!=1:
                raise ValueError('missing video metadata')
            sampling=encoded.sampling[0]
            if not 4 <= sampling['sampled_frames'] <= 64:
                raise ValueError('sample cap violated')
            if encoded.inputs['input_ids'].shape[1]>12288:
                raise ValueError('sequence exceeds training bound')
            if window and not (0 <= sampling['first_timestamp_sec'] < 1 and 25 <= sampling['last_timestamp_sec'] <= 30.1):
                raise ValueError('window timestamp is not local 0..30s: '+json.dumps(sampling))
            if not window and sampling['last_timestamp_sec'] < duration*.9:
                raise ValueError('sample does not span the full media timeline')
            result.append(dict(video_id=row['video_id'],window=window,input_tokens=encoded.inputs['input_ids'].shape[1],
                               sampling=sampling,processor_keys=list(encoded.inputs)))
    Path(args.output).write_text(json.dumps(dict(status='passed',gpu_used=False,rows=result),indent=2)+'\n')
    print(json.dumps(dict(status='passed',gpu_used=False,cases=len(result))))


if __name__=='__main__':
    main()
