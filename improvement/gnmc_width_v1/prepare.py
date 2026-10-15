"""New Linux-only photo cohort. Reuse cached metadata, range-fetch only new JPEGs."""
import datetime as dt
import hashlib
import json
import os
import socket
import struct
import traceback
import urllib.request
import zlib
from pathlib import Path
from common import ROOT, RUN, paths, read, save, sha, encode, prompt_messages, tensor_info

def range_bytes(offset, length):
    protocol = read(ROOT/'protocol.json')
    req = urllib.request.Request(protocol['origin_url'], headers={
        'Range': f'bytes={offset}-{offset+length-1}', 'Accept-Encoding': 'identity'})
    with urllib.request.urlopen(req, timeout=45) as r:
        expected = f'bytes {offset}-{offset+length-1}/{protocol["archive_bytes"]}'
        if r.status != 206 or r.headers.get('Content-Range') != expected:
            raise ValueError('range rejected; full archive response is not read')
        b = r.read(length+1)
    if len(b) != length: raise ValueError('wrong range length')
    return b

def main():
    assert socket.gethostname() == 'inspur-NP5570M5'
    paths()
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from spatial_baseline import Qwen3VL
    protocol = read(ROOT/'protocol.json')
    assert read(ROOT/'purpose_reply.json')['answer'] == '仅学生参赛/科研，不涉及商业产品'
    save(ROOT/'prepare_started.json', {'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'pid':os.getpid(),
        'protocol_sha256':sha(ROOT/'protocol.json'),'model_calls':0,'CUDA_visible':os.environ.get('CUDA_VISIBLE_DEVICES')})
    cfg = read(RUN/'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True,
                                             min_pixels=131072, max_pixels=131072)
    index = read(ROOT/'control/zip_index.json')
    protected = read(ROOT/'control/protected.json')
    denied_names, denied_sha = set(protected['filenames']), set(protected['media_sha256'])
    candidates = {}
    for author_split, role in [('validation','screen'), ('test','confirm')]:
        rows = read(ROOT/f'control/{author_split}.json')
        eligible = [r for r in rows if r['filename'] not in denied_names and '16:9' in r.get('crop_bboxes',{})]
        eligible.sort(key=lambda r: hashlib.sha256((protocol['seed']+'|'+author_split+'|'+r['filename']).encode()).hexdigest())
        candidates[role] = [(author_split,r) for r in eligible[:protocol['candidate_limit_per_role']]]
    plan = []
    for role, rows in candidates.items():
        for split,r in rows:
            name = f'GNMC/{split}/{r["filename"]}'
            if name not in index: raise ValueError('registered original member missing')
            plan.append({'role':role,'item_id':f'gnmc:{split}:{r["filename"]}','member':index[name]})
    payload = sum(r['member']['compressed_bytes']+30 for r in plan)
    if payload > protocol['max_media_range_bytes']: raise ValueError('candidate payload exceeds registered bytes')
    save(ROOT/'media_plan.json', {'rows':plan,'maximum_possible_compressed_payload_bytes':payload,
        'selection_uses_predictions_or_reference_scores':False})
    for child in ('media','rgb','tensors','proofs','reference'): (ROOT/child).mkdir()
    inputs, refs, skipped, fingerprints, hashes = [], [], [], [], set()
    for role, pool in candidates.items():
        accepted = 0
        for split, record in pool:
            if accepted == protocol['items_per_role']: break
            name = record['filename']
            if Path(name).name != name or not name.endswith('.jpeg'): raise ValueError('unsafe source filename')
            item_id = f'gnmc:{split}:{name}'
            member = index[f'GNMC/{split}/{name}']
            key = split+'_'+name
            header = range_bytes(member['header_offset'],30)
            (ROOT/'media'/f'{key}.header').write_bytes(header)
            values = struct.unpack('<4s5H3I2H',header)
            if values[0] != b'PK\x03\x04' or values[3] != member['compression'] or member['compression'] not in (0,8):
                raise ValueError('local header or compression mismatch')
            offset = member['header_offset']+30+values[-2]+values[-1]
            packed = range_bytes(offset,member['compressed_bytes'])
            (ROOT/'media'/f'{key}.packed').write_bytes(packed)
            raw = zlib.decompress(packed,-15) if member['compression'] == 8 else packed
            if len(raw) != member['bytes'] or zlib.crc32(raw)&0xffffffff != member['crc32']:
                raise ValueError('original source member CRC/size mismatch')
            target = ROOT/'media'/key
            target.write_bytes(raw)
            rawsha = sha(target)
            with Image.open(target) as original:
                if original.getexif().get(274,1) != 1: raise ValueError('nontrivial EXIF orientation is not silently applied')
                image = original.convert('RGB')
            W,H = image.size
            array = np.asarray(image)
            rgbsha = hashlib.sha256(array.tobytes()).hexdigest()
            gray = np.asarray(image.convert('L').resize((9,8)))
            fp = sum(int(v)<<i for i,v in enumerate((gray[:,1:]>gray[:,:-1]).reshape(-1)))
            duplicate = rawsha in denied_sha or rawsha in hashes or any((fp^old).bit_count() <= 6 for old in fingerprints)
            if duplicate:
                skipped.append({'item_id':item_id,'reason':'protected/exact/near-duplicate image identity','sha256':rawsha})
                continue
            boxn = record['crop_bboxes']['16:9']
            if len(boxn) != 4 or any(type(v) not in (int,float) or not 0 <= v <= 1 for v in boxn):
                raise ValueError('original normalized annotation invalid; no replacement by quality')
            x1,y1,x2,y2 = map(float,boxn)
            if x2 <= x1 or y2 <= y1: raise ValueError('nonpositive original annotation')
            ref = [x1*W,y1*H,(x2-x1)*W,(y2-y1)*H]
            if abs(ref[2]*9/16-ref[3]) > 2: raise ValueError('declared native16 annotation exceeds original pixel-quantization tolerance')
            np.save(ROOT/'rgb'/f'{key}.npy',array,allow_pickle=False)
            baseline = []
            class Capture:
                max_pixels = 131072
                def _generate(self,messages,limit): baseline.extend(messages); return ''
            Qwen3VL.predict_focus(Capture(),image,[16,9],128)
            proof = {'item_id':item_id,'role':role,'source_sha256':rawsha,'RGB_sha256':rgbsha,
                     'dimensions':[W,H],'reference_used_for_input':False,'stages':{}}
            for stage, messages in [('baseline',baseline),('width',prompt_messages(image))]:
                tensors,text = encode(processor,messages)
                tpath = ROOT/'tensors'/f'{key}.{stage}.pt'
                torch.save(tensors,tpath)
                proof['stages'][stage] = {'path':str(tpath.relative_to(ROOT)), 'file_sha256':sha(tpath),
                    'tensors':tensor_info(tensors),'input_tokens':int(tensors['input_ids'].shape[1]),
                    'template_text':text,'template_sha256':hashlib.sha256(text.encode()).hexdigest()}
            save(ROOT/'proofs'/f'{key}.json',proof)
            inputs.append({'item_id':item_id,'role':role,'key':key,'path':str(target.relative_to(ROOT)),
                'source_sha256':rawsha,'width':W,'height':H,'ratio':[16,9], 'rgb_sha256':rgbsha,
                'proof':f'proofs/{key}.json'})
            refs.append({'item_id':item_id,'role':role,'original_normalized_xyxy':boxn,
                'reference_xywh':ref,'source_sha256':rawsha,'source_group_basis':'publisher_split_filename',
                'original_origin_URL':None,'original_source_independence':'UNKNOWN_BEYOND_FILE_AND_DUPLICATE_CHECKS'})
            hashes.add(rawsha);fingerprints.append(fp);accepted += 1
            print(json.dumps({'role':role,'accepted':accepted,'item_id':item_id}),flush=True)
        if accepted != protocol['items_per_role']: raise ValueError('bounded cohort did not reach registered denominator')
    if torch.cuda.is_initialized(): raise ValueError('CPU acceptance initialized CUDA')
    save(ROOT/'inputs.json',inputs)
    save(ROOT/'reference/labels.json',refs)
    save(ROOT/'input_acceptance.json',{'status':'PASS_FORTY_REAL_STATIC_RGB_EIGHTY_PROCESSOR_INPUTS',
        'items':len(inputs),'stages':len(inputs)*2,'skipped_identity_candidates':skipped,
        'input_sha256':sha(ROOT/'inputs.json'),'labels_sha256':sha(ROOT/'reference/labels.json'),
        'model_calls':0,'source_level_global_isolation':'UNKNOWN','CUDA_initialized':False})

if __name__ == '__main__':
    try: main()
    except Exception as e:
        save(ROOT/'prepare_failure.json',{'status':'STOP_PRESERVE_SUCCESS_NO_AUTOMATIC_RERUN',
            'error':repr(e),'traceback':traceback.format_exc()})
        raise
