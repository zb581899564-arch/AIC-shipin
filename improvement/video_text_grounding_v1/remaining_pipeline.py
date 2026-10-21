"""Bounded common remainder; callers must register and claim their recovery."""
from common import ROOT, ref, write
from controller import stage, WRAPPER
from complete import complete


def run(label, asset_script):
    for name, script in [('assets_remaining' + label, asset_script), ('model_gate', 'model_io.py'),
                         ('torch', 'contracts.py'), ('input', 'prepare.py')]:
        stage(name, script)
    write(ROOT / 'source_input_lock.json', dict(protocol=ref(ROOT / 'protocol.json'),
          recovery=ref(ROOT / f'recovery_registration{label}.json'),
          code={p.name: ref(p) for p in sorted((ROOT / 'code').glob('*.py'))},
          assets=ref(ROOT / 'download_acceptance.json'), model=ref(ROOT / 'model_acceptance.json'),
          torch=ref(ROOT / 'torch_contracts.json'), input=ref(ROOT / 'input_acceptance.json'),
          wrapper=ref(WRAPPER)))
    stage('gpu', 'infer.py', True)
    stage('review', 'review.py')
    stage('audit', 'audit.py')
    complete()
