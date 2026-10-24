"""Register deterministic exposed development and a separate unscored test pool."""
import hashlib
import sys
from common import ROOT, WORK, S1, WIDTH, CHECKOUT, paths, read, ref, write, sha, checked


def register():
    protocol = read(ROOT / 'protocol.json')
    cohort = read(S1 / 'cohort.json')
    checked(cohort['license'])
    checked(cohort['purpose'])
    baseline_paths = {
        '40.48': (WORK / 'general_highlight_supervision_20261021_v1/routing_package63/source_remove/candidate_SPORT_ROUTE_REMOVE_8B.zip',
                  384482, '85778a086f3fb0152947ece40b8dc258c7fef717b40519fe3e23fd4f7b0fabbe'),
        '40.47': (WORK / 'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip',
                  384630, 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3')}
    identities = {}
    for key, (p, size, digest) in baseline_paths.items():
        if p.stat().st_size != size or sha(p) != digest:
            raise ValueError('Protected original baseline identity differs')
        identities[key] = ref(p)
    write(ROOT / 'protected_baseline_acceptance.json', identities)
    old_eval = read(WIDTH / 'inputs.json')
    protected = read(WIDTH / 'control/protected.json')
    component = read(ROOT / 'historical_protected.json')
    names = set(protected['filenames']) | {r['item_id'].split(':')[-1] for r in cohort['rows'] + old_eval}
    blocked = set(component['blocked_identity_sha256']) | set(component.get('blocked_component_sha256', []))
    dev = [r for r in cohort['rows'] if r['role'] == 'dev']
    key = lambda s: hashlib.sha256(('SUBJECT_EXTENT_20261024:' + s).encode()).hexdigest()
    dev.sort(key=lambda r: key(r['item_id']))
    baseline = {r['item_id']: r for r in map(__import__('json').loads,
                (S1 / 'center_predictions.jsonl').read_text().splitlines())}
    chosen = [dict(r, baseline=baseline[r['item_id']], historical_exposure='S1_DEVELOPMENT_METRICS_EXPOSED') for r in dev[:20]]
    pool = []
    for r in read(WIDTH / 'control/test.json'):
        n = r['filename']
        variants = [n, n.removesuffix('.jpeg'), 'gnmc:test:' + n, 'GNMC/test/' + n, 'test_' + n]
        if n in names or any(hashlib.sha256(v.encode()).hexdigest() in blocked for v in variants):
            continue
        pool.append(r)
    pool.sort(key=lambda r: key('gnmc:test:' + r['filename']))
    pool = pool[:40]
    index = read(WIDTH / 'control/zip_index.json')
    packed = sum(index['GNMC/test/' + r['filename']]['compressed_bytes'] + 30 for r in pool)
    write(ROOT / 'registration.json', dict(protocol=ref(ROOT / 'protocol.json'), dev=chosen,
        confirm_candidate_names=[r['filename'] for r in pool], confirm_pool_max=40,
        confirm_maximum_compressed_payload_bytes=packed, confirm_count=20,
        selection_independent_of_reference_geometry=True, actual_original_source_independence='UNKNOWN',
        license=cohort['license'], purpose=cohort['purpose'], historical_protection=ref(ROOT / 'historical_protected.json'),
        s1_cohort=ref(S1 / 'cohort.json'), old_eval=ref(WIDTH / 'inputs.json'),
        adopted_control_predictions=ref(S1 / 'center_predictions.jsonl'),
        adopted_control_completion=ref(S1 / 'center_completion.json'),
        runtime_commit='8dcde128be0ffe2df3ccba75d69929b7a9769a6f',
        code={p.name: ref(p) for p in (ROOT / 'code').glob('*.py')},
        spatial_runtime=ref(CHECKOUT / 'improvement/final_sprint_v1/spatial.py')))
    write(ROOT / 'dev_rows.json', chosen)
    print('REGISTERED20_EXPOSED_DEV_AND20_UNSCORED_TEST_FIXED_POOL', packed, flush=True)


def inputs(role):
    paths()
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from improvement.final_sprint_v1.spatial import GROUNDING_PROMPT
    from common import checked, signature
    model_spec = read(ROOT / 'model_spec.json')
    processor = AutoProcessor.from_pretrained(model_spec['model_dir'], local_files_only=True)
    output = ROOT / (role + '_inputs')
    output.mkdir()
    accepted = []
    for row in read(ROOT / (role + '_rows.json')):
        rgb = np.load(checked(row['rgb']), allow_pickle=False)
        if rgb.dtype != np.uint8 or rgb.shape != (row['height'], row['width'], 3):
            raise ValueError('Actual original RGB geometry mismatch')
        if hashlib.sha256(rgb.tobytes()).hexdigest() != row['RGB_sha256']:
            raise ValueError('Actual accepted RGB bytes mismatch')
        messages = [dict(role='user', content=[dict(type='image'), dict(type='text', text=GROUNDING_PROMPT)])]
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        encoded = dict(processor(text=[text], images=[Image.fromarray(rgb)],
            images_kwargs={'size': {'shortest_edge': 65536, 'longest_edge': 131072}},
            text_kwargs={'padding': False, 'truncation': False}, common_kwargs={'return_tensors': 'pt'}).items())
        if not 0 < encoded['input_ids'].shape[1] <= 8192 or not bool((encoded['attention_mask'] == 1).all()):
            raise ValueError('No truncation or padding permitted')
        p = output / (row['item_id'].replace(':', '_') + '.pt')
        with p.open('xb') as f:
            torch.save(encoded, f)
        sig = signature(encoded)
        if signature(torch.load(p, map_location='cpu', weights_only=True)) != sig:
            raise ValueError('First exact CPU input serialization mismatch')
        accepted.append(dict(item_id=row['item_id'], tensor=ref(p), signature=sig, original_rgb=row['rgb']))
    if len(accepted) != 20 or torch.cuda.is_initialized():
        raise ValueError('CPU input count or CUDA isolation mismatch')
    write(ROOT / (role + '_cpu_acceptance.json'), dict(status='PASS_FIRST20_REAL_RGB_PROCESSOR_INPUTS', rows=accepted,
        labels_not_encoder_inputs=True, CUDA_initialized=False))
    print('CPU_INPUT_PASS', role, len(accepted), flush=True)


if __name__ == '__main__':
    register() if sys.argv[1] == 'register' else inputs(sys.argv[1])
