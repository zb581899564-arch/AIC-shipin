"""Local source metadata audit; no competition pixels or test labels are read."""
from pathlib import Path
from collections import Counter
import hashlib,json,csv
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
corpus=load(ROOT/'corpus.json');sources=corpus['sources'];issues=[]
assert len(sources)==50 and sum(len(m['frames']) for m in sources)==600
assert Counter(m['split'] for m in sources)=={'train':40,'validation':10}
ids=[m['source_id'] for m in sources];assert len(set(ids))==50
for m in sources:
    d=ROOT/'input'/m['source_id'];assert sha(d/m['media_file'])==m['media_sha256']
    assert sha(d/'native_pts.npz')==m['native_pts_sha256']
    for f in m['frames']:assert sha(d/f['file'])==f['png_sha256']
    if m.get('human_vector_native_count_equal') is False:
        issues.append(dict(source_id=m['source_id'],native_frames=m['native_frames'],human_vector_length=m['human_vector_length'],disposition='EXCLUDE_HUMAN_VECTOR_ORDINAL_LABELS_UNTIL_ALIGNMENT_PROVEN'))
evidence=[];overlap=[]
inventory=PROJECT/'data_audit/video_inventory.tsv'
rows=list(csv.DictReader(inventory.read_text(encoding='utf-8-sig').splitlines(),delimiter='\t'))
known_ids={r['stem'][:11] for r in rows if len(r['stem'])>=11}
known_hashes={r['sha256'] for r in rows if r.get('sha256')}
evidence.append(dict(path=str(inventory),sha256=sha(inventory),records=len(rows),available_hashes=len(known_hashes),comparison='original 11-char source IDs and available exact hashes'))
rematch=PROJECT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/m0_finalize_01/clean_manifest_426.json'
rr=load(rematch)['records'];rh={r['source_sha256'] for r in rr}
evidence.append(dict(path=str(rematch),sha256=sha(rematch),records=len(rr),available_hashes=len(rh),comparison='exact encoded media hashes only; anonymized source identities unavailable'))
for m in sources:
    if m['source_id'] in known_ids:overlap.append(dict(source_id=m['source_id'],kind='QV_SOURCE_ID_MATCH'))
    if m['media_sha256'] in known_hashes|rh:overlap.append(dict(source_id=m['source_id'],kind='EXACT_MEDIA_HASH_MATCH'))
out=dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_LOCAL_IDENTITIES_AND_FIXED_SPLIT',sources=50,frames=600,
    split=dict(Counter(m['split'] for m in sources)),category_split={c:dict(Counter(m['split'] for m in sources if m['category']==c)) for c in sorted({m['category'] for m in sources})},
    source_overlap_status='NO_MATCH_IN_AVAILABLE_METADATA' if not overlap else 'MATCHES_REQUIRE_ISOLATION',
    overlap=overlap,evidence=evidence,human_frame_alignment_issues=issues,
    semantic_or_reencoded_duplicate_exclusion_proven=False,
    limitations='Local identity metadata comparison does not exclude reencoded/partial duplicates or unknown original identities of rematch media. No contest pixels or test labels were read.')
(ROOT/'corpus_acceptance.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
