"""Additional source-adoption and exact-phase membership gates, no reruns."""
import argparse
from pathlib import Path
import sys
parent=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(parent/'code' if (parent/'code').is_dir() else parent))
from common import *


def adoption(scope):
    assert_cpu()
    prior=EXTERNAL if scope=='external' else PRODUCTION
    aggregate=read(prior/'cpu_acceptance.json')
    require(aggregate['status'] in ['PASS_ALL_25_NEW_FEATURE_INPUTS','PASS_ALL_REGISTERED_NEW_FEATURE_INPUTS'],
            'Original accepted cached-image stage status differs')
    for source in aggregate['sources']:
        single=read(prior/'inputs'/source['id']/'acceptance.json')
        require(single==source and single['status']=='PASS_FIRST_NEW_IMAGE_CPU_INPUTS',
                'Original per-source accepted evidence differs from aggregate')
    lock=read(ROOT/('source_lock_'+scope+'.json'))
    current=read(checked(lock['acceptance']))
    require({s['id'] for s in current['sources']}=={s['id'] for s in aggregate['sources']},
            'Inherited source identity set differs')
    write(ROOT/(scope+'_adoption_QA_02.json'),dict(status='PASS_OLD_SINGLE_SOURCE_EQUALS_AGGREGATE_AND_NEW_INPUT_LOCK',
          sources=len(aggregate['sources']),original_aggregate=reference(prior/'cpu_acceptance.json'),
          source_lock=reference(ROOT/('source_lock_'+scope+'.json')),new_decode_encoding_or_forward=0))


def phase(scope,name):
    assert_cpu()
    lock=read(ROOT/('source_lock_'+scope+'.json'))
    accepted=read(checked(lock['acceptance']))
    expected={r['case_id'] for r in accepted['cases']}
    if name=='pilot32':expected=set(accepted['pilot_case_ids'])
    elif name=='remaining_external':expected-=set(accepted['pilot_case_ids'])
    complete=read(ROOT/(name+'_feature_completion.json'));qa=read(ROOT/(name+'_output_QA.json'))
    require(set(qa['cases'])==expected and len(qa['cases'])==len(expected)==complete['actual_new_forwards'],
            'Actual output cases differ from the pre-registered exact phase set')
    entries=[read(checked(r)) for r in complete['entries']]
    require({r['case_id'] for r in entries}==expected and len(entries)==len(expected), 'Receipt set differs from registered actual phase')
    events=[json.loads(x) for x in checked(complete['attempts']).read_text().splitlines() if x.strip()]
    for event_name in ['BEGIN_NEW_WHOLE_WINDOW_PREFILL','ACCEPTED_NEW_WHOLE_WINDOW_PREFILL']:
        rows=[r for r in events if r['event']==event_name]
        require(len(rows)==len(expected) and {r['case_id'] for r in rows}==expected,
                'Exact first forward/accept count differs from registered actual phase')
    write(ROOT/(name+'_phase_membership_QA_02.json'),dict(status='PASS_EXACT_PHASE_SET_AND_FIRST_CALL_DENOMINATOR',
          expected=len(expected),completion=reference(ROOT/(name+'_feature_completion.json')),
          output_QA=reference(ROOT/(name+'_output_QA.json')),source_lock=reference(ROOT/('source_lock_'+scope+'.json')),
          new_decode_encoding_or_forward=0))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['adoption','phase']);p.add_argument('scope',choices=['external','production']);p.add_argument('--phase')
    a=p.parse_args()
    if a.mode=='adoption':adoption(a.scope)
    else:phase(a.scope,a.phase)
