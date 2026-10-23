"""Fresh transparent media mirror audit; original labels remain authoritative."""
from datetime import datetime, timezone
import json
import traceback
from direct import ROOT, read, save, ref, fetch


def main():
    ROOT.mkdir(exist_ok=False)
    save(ROOT/'registration.json', dict(utc=datetime.now(timezone.utc).isoformat(),
        instruction='Find clear-source direct-access original video plus aligned highlight labels; small pilot before training/production',
        initial_metadata_cap_bytes=12000000, new_media_download_bytes=0,
        no_execute_remote_scripts=True, protected_baseline40_47=True,
        candidate='Newly discovered public YouTubeHighlights mirror; not claiming uploader metadata or converted labels are original gold',
        original_author='aliensunmin/DomainSpecificHighlight; adopt saved primary metadata before any repeated read',
        research_use='Human previously confirmed student research, no commercial product; dataset-specific terms still required',
        code=ref(__file__)))
    repo='jhanglee/youtube-highlights-full'
    meta=read(fetch('https://huggingface.co/api/datasets/'+repo,'hf_repository.json'))
    sha=meta['sha']
    tree=read(fetch('https://huggingface.co/api/datasets/'+repo+'/tree/'+sha+'?recursive=true&expand=false','hf_tree.json'))
    card=fetch('https://huggingface.co/datasets/'+repo+'/resolve/'+sha+'/README.md','hf_README.md')
    save(ROOT/'repository_identity.json',dict(repo=repo,commit=sha,private=meta.get('private'),
        gated=meta.get('gated'),card_data=meta.get('cardData'),tree=ref(ROOT/'metadata/hf_tree.json'),readme=ref(card)))
    print('MIRROR',sha,'CARD',json.dumps(meta.get('cardData'),ensure_ascii=False),flush=True)
    print('FILES',json.dumps(tree,ensure_ascii=False)[:7000],flush=True)
    print('README',card.read_text()[:15000],flush=True)


if __name__=='__main__':
    try:
        main()
    except BaseException:
        if ROOT.exists() and not(ROOT/'metadata_failure.json').exists():
            save(ROOT/'metadata_failure.json',dict(traceback=traceback.format_exc(),automatic_retry=False))
        raise
