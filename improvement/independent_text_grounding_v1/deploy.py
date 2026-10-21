"""Deploy only necessary small code to the currently observed direct SSH entrance."""
import base64
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
REPORT=HERE.parents[1]/'reports/independent_text_grounding_20261021_v1'
REMOTE='/home/inspur/aic_video_work/independent_text_grounding_20261021_v1'
PROTOCOL=dict(
    mechanism='Frozen independent language-image contrastive representation for event grounding',
    hypothesis='Human event descriptions should locate their real pixels better than fixed query/temporal mismatches',
    distinction='Not a Qwen hidden-state head, threshold/prompt scan, candidate-logprob contrast, or I3D+randomUMT refit',
    sources=8,queries=26,sources_fixed='Existing VideoXum8 V00..V07, all historically exposed',
    reference='Original ActivityNet human text and broad event timestamps in author VideoXum release; not shortened highlight labels',
    inputs='Existing8sample/native64 I3D center-view RGB. CLIP normalization. No new decode, no claim of standard full-frame CLIP preprocessing',
    model='OpenAI CLIP ViT-B/32 frozen, official2021 model, MIT code/weights, English research use',
    weight_bytes=353976522,model_expected_parameters=151277313,
    baseline_parameters=8782557449,expected_total_parameters=8933834762,
    weight_sha256='40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af',
    download='Official Azure weight, pinned OpenAI GitHub source/BPE, ftfy6.3.1 and wcwidth0.2.13 only; every response physical/public route gate, no proxy/relay fallback',
    text='Raw human caption only, no times, no template scan, no truncation, all26 retained',
    pooling='L2 normalize raw frame embeddings; mean8 per native cell then normalize; cosine with normalized text',
    metrics='Native-frame tie-grouped AP; event-average then source-macro over8. No AIC F1/IoU or official-score inference',
    controls=['next caption in same video, circular','next source caption at event-index modulo, circular','half-cell-sequence temporal shift','constant prevalence'],
    controls_scope='Structural correspondence controls; swapped text is not claimed known false at every frame',
    gate=dict(within_gain=.03,cross_gain=.05,shift_gain=.03,constant_gain=.05,sources=6),
    negative_rule='One fixed frozen capability test. If failed, no finetuning, query-word search, full production or exploratory package',
    positive_rule='Only eligible for separate automatic-query pilot; human-caption success cannot authorize official-data human queries or full production',
    gpu_max_seconds=900,planned_output_bytes=100000000,new_training_steps=0,new_8B_calls=0,
    protected_baseline_score=40.47,protected_sha256='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3',
    no_goal_timer_author_crosschat_or_automatic_submission=True,
)


def main():
    names=['common.py','acquire.py','prepare.py','infer.py','review.py','audit.py','controller.py']
    files={n:base64.b64encode((HERE/n).read_bytes()).decode() for n in names}
    payload=json.dumps(dict(files=files,protocol=PROTOCOL))
    script=r'''
import pathlib,json,base64,subprocess,os,hashlib
r=pathlib.Path(REMOTE)
data=json.loads(PAYLOAD)
r.mkdir();(r/'code').mkdir()
for name,value in data['files'].items():
 with (r/'code'/name).open('xb') as f:f.write(base64.b64decode(value))
with (r/'protocol.json').open('x') as f:json.dump(data['protocol'],f,ensure_ascii=False,indent=2)
identity={'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'code').glob('*.py')},'code_bytes':sum(len(base64.b64decode(s)) for s in data['files'].values())}
with (r/'code_acceptance.json').open('x') as f:json.dump(identity,f,indent=2)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
py='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
with (r/'controller.log').open('x') as log:
 p=subprocess.Popen([py,'-u','-B',str(r/'code/controller.py')],env=env,cwd=r,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
out={'pid':p.pid,'start_ticks':pathlib.Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],'root':str(r),'code_bytes':identity['code_bytes'],'automatic_production':False}
with (r/'launch.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out))
'''.replace('REMOTE',repr(REMOTE)).replace('PAYLOAD',repr(payload))
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
             'aic-inspur-home','/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -']
    p=subprocess.run(command,input=script.encode(),capture_output=True,timeout=50)
    receipt=dict(returncode=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode())
    REPORT.mkdir()
    with (REPORT/'launch.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    with (REPORT/'protocol.json').open('x',encoding='utf-8') as f:json.dump(PROTOCOL,f,ensure_ascii=False,indent=2)
    print(json.dumps(receipt,ensure_ascii=False))
    assert p.returncode==0


if __name__=='__main__':
    main()
