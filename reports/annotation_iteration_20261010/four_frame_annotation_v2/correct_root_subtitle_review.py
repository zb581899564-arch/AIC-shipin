"""Append-only correction of main-agent contact-sheet false positives.
All four disputed student PNGs were reopened individually before this script.
"""
import runner as r

def main():
    ids={'F11','F30','F49','F50'}
    old=r.read(r.ROOT/'root_student_observed_reference.json')
    new=dict(old);new['utc']=r.utc()
    new['supersedes_sha256']=r.sha(r.ROOT/'root_student_observed_reference.json')
    new['individual_boundary_rechecks']=['F05','F06','F10','F11','F18','F19','F21','F22','F27','F28','F29','F30','F31','F32','F39','F40','F41','F42','F47','F48','F49','F50','F57','F58']
    for row in new['records']:
        if row['frame_id'] in ids:row['subtitle_text']=None
    r.save(r.ROOT/'root_student_observed_reference_v2.json',new)
    review=r.read(r.ROOT/'student_semantic_review.json')
    corrected=dict(review);corrected['utc']=r.utc()
    corrected['supersedes_sha256']=r.sha(r.ROOT/'student_semantic_review.json')
    corrected['corrections']=[x for x in review['corrections'] if not (x['frame_id'] in ids and x['field'] in {'subtitle_text','subtitle_legibility'})]
    corrected['root_observed_reference_sha256']=r.sha(r.ROOT/'root_student_observed_reference_v2.json')
    corrected['root_review_false_positive_frames']=sorted(ids)
    r.save(r.ROOT/'student_semantic_review_v2.json',corrected)
    seal=r.read(r.ROOT/'student_sealed.json')
    final=dict(seal);final['utc']=r.utc();final['supersedes_sha256']=r.sha(r.ROOT/'student_sealed.json')
    final['semantic_review_sha256']=r.sha(r.ROOT/'student_semantic_review_v2.json')
    for row in final['records']:
        if row['frame_id'] in ids:
            assert r.read(row['raw_file'])[[x['frame_id'] for x in r.read(row['raw_file'])].index(row['frame_id'])]['subtitle_text'] is None
            row['subtitle_text']=None;row['subtitle_legibility']='absent'
            row.pop('model_original_fields',None);row.pop('root_corrections',None)
    final['correction_after_native_admission']=True
    final['original_student_phase_seal_unchanged']=True
    r.save(r.ROOT/'student_sealed_v2.json',final)
    r.save(r.ROOT/'ROOT_QA_ERRATUM.json',dict(utc=r.utc(),status='ROOT_FOUR_FALSE_POSITIVE_SUBTITLE_CORRECTIONS_WITHDRAWN',
        frames=sorted(ids),reason='Main agent misattributed neighbouring subtitle content in contact sheets; individual original PNGs show absent subtitles. AGY raw answers were correct.',
        initial_review_and_seal_preserved=True,original_native_admission_binding_preserved=True,
        corrected_student_seal_sha256=r.sha(r.ROOT/'student_sealed_v2.json'),
        protocol_deviation='Corrected semantic seal created after native admission; do not claim corrected student seal preceded native phase.',
        training_admitted=False))
    print('Corrected four primary-review false positives, append-only; zero raw teacher subtitle differences on this window.')

if __name__=='__main__':main()
