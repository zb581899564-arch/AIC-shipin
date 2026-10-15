"""Small P/O sufficient-condition and real confirmation authority fixtures."""
import ast
from fractions import Fraction as F
from pathlib import Path
from fact_check import upper_bound
from registration import phase_pass, CONDITIONS, validate_complete_covering_grid


def rejects(call):
    try:call()
    except (ValueError,KeyError):return
    raise AssertionError('Expected refusal')


def main():
    # Exactly nine sources/seventeen views can still conceal a missing
    # point-covering view. Reconstruct the complete expected set independently.
    sources=[];clocks={};observed={};registered=[]
    for index in range(9):
        name='s'+str(index);source=dict(video_id=name,source_sha256=str(index+1)*64,clock_sha256=str(index+1)*63+'0')
        sources.append(source);clocks[name]=dict(original_exact_pts=[str(F(i,10)) for i in range(300)],physical_end_exact='30')
        observed[name]=[dict(label='ORDINARY',ordinal=i,exact_pts=str(F(i,10)))
            for i in (range(90,114) if index<8 else range(260,290))]
        pairs=[('0','15'),('15/2','45/2')] if index<8 else [('15','30')]
        for number,(start,stop) in enumerate(pairs):
            registered.append(dict(case_id=name+'.v'+str(number),source_name=name,source_sha256=source['source_sha256'],
                source_clock_sha256=source['clock_sha256'],window_start=start,window_end=stop))
    assert len(registered)==17 and sum(map(len,observed.values()))==222 and len(validate_complete_covering_grid(registered,clocks,observed,sources))==17
    replacement=[dict(view) for view in registered]
    replacement[1].update(window_start='15',window_end='30') # valid grid, same 17 count, but misses an overlapping cover of O
    rejects(lambda:validate_complete_covering_grid(replacement,clocks,observed,sources))
    duplicate=[dict(view) for view in registered];duplicate[1]={**duplicate[0],'case_id':'different-case-same-geometry'}
    rejects(lambda:validate_complete_covering_grid(duplicate,clocks,observed,sources))
    rejects(lambda:validate_complete_covering_grid(registered[:-1],clocks,observed,sources))
    wrong_clock=[dict(view) for view in registered];wrong_clock[0]['source_clock_sha256']='f'*64
    rejects(lambda:validate_complete_covering_grid(wrong_clock,clocks,observed,sources))
    # Exact non-grid-aligned right tail is an additional cover, not a substitute
    # for earlier overlapping windows. For end31/O20 all three cover it.
    tail_sources=[sources[0]];tail_clocks={'s0':dict(original_exact_pts=[str(F(i,10)) for i in range(310)],physical_end_exact='31')}
    tail_observed={'s0':[dict(label='ORDINARY',ordinal=200,exact_pts='20')]}
    tail_views=[dict(case_id='tail'+str(index),source_name='s0',source_sha256=sources[0]['source_sha256'],
        source_clock_sha256=sources[0]['clock_sha256'],window_start=start,window_end=stop)
        for index,(start,stop) in enumerate([('15/2','45/2'),('15','30'),('16','31')])]
    assert len(validate_complete_covering_grid(tail_views,tail_clocks,tail_observed,tail_sources))==3
    rejects(lambda:validate_complete_covering_grid(tail_views[:-1],tail_clocks,tail_observed,tail_sources))
    # The right edge is half-open: O15 excludes [0,15), and a tail coinciding
    # with the regular grid is deduplicated exactly.
    edge_observed={'s0':[dict(label='ORDINARY',ordinal=150,exact_pts='15')]}
    edge_views=[dict(view) for view in registered[:2]];edge_views[0].update(window_start='15',window_end='30')
    assert len(validate_complete_covering_grid(edge_views,{'s0':clocks['s0']},edge_observed,tail_sources))==2
    views=[dict(case_id='a',source_name='s',window_start='0',window_end='15'),
           dict(case_id='b',source_name='s',window_start='15/2',window_end='45/2')]
    ordinary={'s':[dict(ordinal=100,exact_pts='10',label='ORDINARY')]}
    # Half-open end at an O point avoids O; lawful empty remains successful.
    actual=[dict(case_id='a',source_name='s',source_start_exact='0',segments=[[1,10]],native_ranges=[[10,100]],status='MODEL_OK'),
            dict(case_id='b',source_name='s',source_start_exact='15/2',segments=[],native_ranges=[],status='LEGAL_EMPTY')]
    result=upper_bound(views,ordinary,actual,False)
    assert result['status']=='B0_UPPER_BOUND_SUFFICIENT' and result['complete_positive_recipe_executed'] is False
    assert result['original_KEEP_coverage_proved'] is False and result['original_reference_quality_FAILED_preserved'] is True
    # A real candidate that touches O is inconclusive, even if no true B has
    # been computed. Never invent a baseline or declare recipe quality FAIL.
    touching=[{**actual[0],'segments':[[10,11]],'native_ranges':[[100,110]]},actual[1]]
    result=upper_bound(views,ordinary,touching,False)
    assert result['status']=='INCONCLUSIVE_PENDING_REGISTERED_VERIFY' and result['next_level_started'] is False
    assert result['touching_B0_candidates'][0]['ordinary_ordinal']==100
    rejects(lambda:upper_bound(views,ordinary,actual[:-1],False))
    rejects(lambda:upper_bound(views,ordinary,[actual[0],actual[0]],False))
    rejects(lambda:upper_bound(views,ordinary,[{**actual[0],'status':'FAILED'},actual[1]],False))
    rejects(lambda:upper_bound(views,ordinary,[{**actual[0],'segments':[]},actual[1]],False))
    rejects(lambda:upper_bound(views,ordinary,[{**touching[0],'native_ranges':[[90,100]]},actual[1]],False))
    rejects(lambda:upper_bound(views,ordinary,actual))
    protocol_ref={'path':'protocol','sha256':'p'};protocol={'candidate':'OLD_EXPLICIT_KEEP_PLUS_POSITIVE_EVIDENCE_NEW_ADMISSION'}
    result=dict(status='PASS_POSITIVE_FRESH_CONFIRM_PENDING_FIXED40',group='confirm',cases=[{}]*4,
        conditions={key:True for key in CONDITIONS},bindings={'protocol_ref':protocol_ref},candidate=protocol['candidate'],
        production_admitted=False,old_failed_gates_changed=False)
    phase_pass(protocol_ref,protocol,'confirm',result)
    rejects(lambda:phase_pass(protocol_ref,protocol,'confirm',{**result,'status':'STOP_POSITIVE_CONFIRM_REJECTED'}))
    rejects(lambda:phase_pass(protocol_ref,protocol,'confirm',{**result,'conditions':{**result['conditions'],'macro_precision_not_lower':False}}))
    rejects(lambda:phase_pass(protocol_ref,protocol,'confirm',{**result,'status':'PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40'}))
    # No post-GPU processor/input re-encode, and no lower-level launcher exists.
    tree=ast.parse((Path(__file__).parent/'b0_runtime.py').read_text(encoding='utf-8'))
    replay=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='replay')
    assert not [node for node in ast.walk(replay) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and
                node.func.attr in ('encode','retarget','baseline_frames')]
    chain=(Path(__file__).parent/'chain.py').read_text(encoding='utf-8')
    assert chain.index("child(state,'first_input_QA'")<chain.index("stage='B0_GPU_ADMISSION'")
    assert 'facts_verify.py' not in chain and 'positive_runtime.py' not in chain
    print('PASS: exact complete covering-grid set/duplicate/replacement/right-tail QA; P/O half-open sufficient/inconclusive semantics; output/failure/native veto; fresh PASS authority; pre-GPU first QA; no downstream launcher')


if __name__=='__main__':main()
