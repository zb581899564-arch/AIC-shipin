from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
def assert_root_resume_admission():
    p=ROOT.parents[1]/'03_w11_lawful_observation_completion.json'
    doc=json.loads(p.read_text(encoding='utf-8-sig'))
    assert doc['status']=='PASS_ACTUAL_COMPLETE_LAWFUL_MEDIA_AND_PROPOSAL_WITH_EARLY_TRANSPORT_ERROR_PRESERVED'
    assert not doc['tool_issues'] and not doc['proposal_geometry_identity_issues'] and doc['CLI_after']==26
    assert doc['original_pngs_delivered']==64 and doc['effective_pngs_delivered']==8 and doc['native_video_delivered'] is True
    for val in doc.values():
        if isinstance(val,dict) and set(val)=={'path','sha256'}:
            assert hashlib.sha256(Path(val['path']).read_bytes()).hexdigest()==val['sha256']
    return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),training_admitted=False)
