"""Small pinned code/protocol deployment using the verified direct SSH entry."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPORT = HERE.parents[1] / 'reports/full_view_context_20261021_v1'
REMOTE = '/home/inspur/aic_video_work/full_view_context_20261021_v1'
PROTOCOL = dict(
    mechanism='Same frozen CLIP and same56 exact native points: enlarged center crop versus whole cached resized view',
    sources='Existing7 historically exposed external sources,8 preselected native points each; V05 no exact overlap excluded',
    selection='Adopt metadata10 fixed source-SHA/native-ordinal hash choice; no replacement or nearest-frame matching',
    inventory_sha256='3ed2af618f0fd6cf4ca6a01b02926c5b0ea01a8a5b77c5a9f951172858e68e72',
    inverse7_sha256='7e0e98f99057f2c272f01b2ab8249afbf7ff27895a12a53f6547640b300a6ee3',
    renderer=dict(center='PIL BICUBIC shortside256 floor integer other side, round center crop224',
                  full='PIL BICUBIC longestside224 round other side, center pad224 with roundCLIPmean*255'),
    input_change_includes='Field of view, scale and fill tradeoff at fixed224 budget; NOT pure cropping causality or original full-resolution recovery',
    model='Existing official frozen OpenAI CLIP ViT-B32; new images only; adopt26 successful raw text embeddings',
    weight_sha256='40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af',
    maximum_parameters=8933834762, new_original_media_decode=0, new_original_processor=0,
    new_inverse49=49, adopt_inverse7=7, maximum_image_outputs=112, image_batch=32,
    new_text_forward=0, new_8B_forward=0, training_updates=0, max_gpu_seconds=600,
    planned_output_bytes=96000000,
    reference='Original human ActivityNet broad event captions/timestamps; NOT VideoXum shortened summary or official highlight truth',
    point_labels='For fixed native exact PTS: start<=PTS<end, each point equal mass; single class query AP null',
    minimum_support=dict(sources=5, queries=10),
    metric='Tie-grouped point AP; average scorable queries per source then equal source macro. No comparison to previous dense AP',
    gate=dict(macro_gain=.03, source_fraction=.7, max_source_loss=.05),
    gate_scope='Input mechanism pilot only; even a pass needs separate automatic-query/general-selection evidence; never production admission',
    stop='No renderer, padding, scale, prompt, source or checkpoint sweep after outcome; preserve previous STOPs',
    wrapper_sha256='9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec',
    protected_sha256='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3',
    baseline=40.47, production_allowed=False, no_goal_timer_author_crosschat_or_auto_submission=True)


def main():
    files = {}
    for path in sorted(HERE.glob('*.py')):
        if path.name == 'deploy.py':
            continue
        raw = path.read_bytes()
        ast.parse(raw, filename=path.name)
        files[path.name] = base64.b64encode(raw).decode()
    payload = dict(files=files, protocol=PROTOCOL,
                   sha256={n: hashlib.sha256(base64.b64decode(v)).hexdigest() for n, v in files.items()})
    script = '''
import ast,base64,hashlib,json,os,pathlib,subprocess
r=pathlib.Path(REMOTE);data=json.loads(PAYLOAD)
r.mkdir();(r/'code').mkdir()
for name,value in data['files'].items():
 raw=base64.b64decode(value);assert hashlib.sha256(raw).hexdigest()==data['sha256'][name];ast.parse(raw,filename=name)
 with (r/'code'/name).open('xb') as f:f.write(raw)
with (r/'protocol.json').open('x') as f:json.dump(data['protocol'],f,ensure_ascii=False,indent=2)
receipt={'code_sha256':data['sha256'],'code_bytes':sum(len(base64.b64decode(v)) for v in data['files'].values()),'verified_route':'EasyTiercost1UDP202.196.17.232:6359 viaWLAN','parent_CUDA':'0'}
with (r/'code_acceptance.json').open('x') as f:json.dump(receipt,f,indent=2)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
py='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
with (r/'controller.log').open('x') as log:
 p=subprocess.Popen([py,'-u','-B',str(r/'code/controller.py')],cwd=r,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
out=dict(pid=p.pid,start_ticks=pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],root=str(r),**receipt)
with (r/'launch.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out))
'''.replace('REMOTE', repr(REMOTE)).replace('PAYLOAD', repr(json.dumps(payload)))
    command = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=12',
               'aic-inspur-home', '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -']
    result = subprocess.run(command, input=script.encode(), capture_output=True, timeout=50)
    receipt = dict(returncode=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode())
    REPORT.mkdir()
    for name, value in [('launch.json', receipt), ('protocol.json', PROTOCOL)]:
        with (REPORT / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
    print(json.dumps(receipt, ensure_ascii=False))
    assert result.returncode == 0


if __name__ == '__main__':
    main()
