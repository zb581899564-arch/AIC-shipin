"""Record explicit main-agent review decisions; not a blind evaluator."""
import sys
import runner as r

def make(phase):
    paths=list(r.ROOT.glob(f'{phase}_block_*/audit.json'))
    if phase=='student': paths.append(r.ROOT/'pilot/audit.json')
    if (r.ROOT/'recovery_admission.json').exists():
        recovery=r.read(r.ROOT/'recovery_admission.json')
        if recovery['phase']==phase:paths.append(r.ROOT/recovery['recovery_name']/'audit.json')
    records=[]
    for p in paths: records.extend(r.read(p)['records'])
    records.sort(key=lambda x:x['frame_id'])
    assert [x['frame_id'] for x in records]==[f'F{i:02}' for i in range(64)]
    primary=r.read(r.ROOT/f'root_{phase}_observed_reference.json')
    reference={x['frame_id']:x for x in primary['records']}
    decisions=r.read(r.ROOT/f'root_{phase}_subject_decisions.json')
    assert decisions['all_64_teacher_subject_records_reviewed'] is True
    fixes={x['frame_id']:x for x in decisions['corrections']}
    corrections=[]
    for record in records:
        fid=record['frame_id'];actual=reference[fid]
        if record['subtitle_text']!=actual['subtitle_text']:
            corrections.append(dict(frame_id=fid,field='subtitle_text',corrected=actual['subtitle_text'],reason='主控实际逐图转录；教师字幕缺失或不同，保留原答'))
            expected_legibility='absent' if actual['subtitle_text'] is None else 'clear'
            if record['subtitle_legibility']!=expected_legibility:
                corrections.append(dict(frame_id=fid,field='subtitle_legibility',corrected=expected_legibility,reason='与该图实际字幕可见性匹配'))
        if fid in fixes:
            corrections.append(dict(frame_id=fid,field='visible_subject',corrected=fixes[fid]['corrected'],reason=fixes[fid]['reason']))
    r.save(r.ROOT/f'{phase}_semantic_review.json',dict(utc=r.utc(),accepted=True,
        acceptance_scope='PRIMARY_AGENT_REVIEWED_FACTS_WITH_EXPLICIT_CORRECTIONS_NOT_BLIND_GOLD_OR_SFT',
        reviewed_frame_ids=[x['frame_id'] for x in records],
        audit_sha256s={str(p.relative_to(r.ROOT)):r.sha(p) for p in paths},
        actual_root_images_viewed=True,root_observed_reference_sha256=r.sha(r.ROOT/f'root_{phase}_observed_reference.json'),
        subject_decisions_sha256=r.sha(r.ROOT/f'root_{phase}_subject_decisions.json'),
        corrections=corrections,training_admitted=False,manual_user_gold=False))
    print(phase,'review recorded; correction fields:',len(corrections))

if __name__=='__main__':make(sys.argv[1])
