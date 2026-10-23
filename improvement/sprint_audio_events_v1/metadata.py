"""Author identity, exact implementation and bounded local asset inventory."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
from common import ROOT, WORK, OLD, read, write, reference, direct_get


def author_metadata():
    repo = 'qiuqiangkong/audioset_tagging_cnn'
    commit = read(direct_get('https://api.github.com/repos/'+repo+'/commits/master', 'commit.json'))['sha']
    tree = read(direct_get('https://api.github.com/repos/'+repo+'/git/trees/'+commit+'?recursive=1', 'tree.json'))
    paths = {row['path']: row for row in tree['tree']}
    files = ['README.md', 'LICENSE', 'pytorch/models.py', 'pytorch/pytorch_utils.py',
             'metadata/class_labels_indices.csv']
    accepted = {}
    for name in files:
        if name not in paths:
            raise ValueError('Required author file missing: '+name)
        path = direct_get('https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+name,
            name.replace('/', '__'))
        import hashlib
        raw = path.read_bytes()
        if hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest() != paths[name]['sha']:
            raise ValueError('Author file Git blob mismatch')
        accepted[name] = reference(path)
    write(ROOT/'author_source_acceptance.json', dict(commit=commit, repo=repo, files=accepted))
    print('AUTHOR_COMMIT', commit, flush=True)
    text = (ROOT/'author/README.md').read_text()
    for line in text.splitlines():
        if any(key in line.lower() for key in ['decisionlevelatt', 'zenodo', 'license']):
            print('AUTHOR_README', line, flush=True)


def inventory():
    base = read(OLD/'first_audio_inputs.json')
    reg = read(OLD/'registration.json')
    rows = []
    for entry in base['receipts']:
        receipt = read(Path(entry['path']))
        rows.append(dict(uid=receipt['uid'], sid=receipt['sid'], keys=list(receipt),
            waveform_ref=receipt['waveform_ref'], waveform_exists=Path(receipt['waveform_ref']['path']).is_file(),
            request_ref=receipt['request_ref'], source_clock_ref=receipt['original_clock_ref']))
    write(ROOT/'existing_audio_inventory.json', dict(first_audio_acceptance_ref=reference(OLD/'first_audio_inputs.json'),
        original_registration_ref=reference(OLD/'registration.json'), rows=rows,
        selected=reg['selected'], dependencies={name: importlib.util.find_spec(name) is not None
            for name in ['torch', 'torchlibrosa', 'librosa', 'soundfile', 'scipy']}))
    print('AUDIO_ROWS', json.dumps(rows[0], ensure_ascii=False), 'N', len(rows), flush=True)


def main():
    ROOT.mkdir(exist_ok=False)
    write(ROOT/'metadata_registration.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        scope='One author timed sound event model compatibility; no GPU, labels, media or production',
        metadata_budget_bytes=12000000, baseline40_47_unchanged=True,
        parent_plan='PROJECT_PRIMARY_PLAN_20261021.md', code=reference(Path(__file__))))
    inventory()
    author_metadata()


if __name__ == '__main__':
    main()
