"""Synthetic mathematical/negative admission tests. No media or model execution."""
from pathlib import Path
from fractions import Fraction as F
import ast, copy, itertools, json, sys, tempfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'science_runtime'))
import quality_contract as q
import science_contract as s
import scientific_gate as gate
import event_metrics as events
from pipeline_controller import accept_terminal, CAPS, TOTAL_CAP


def rejected(call):
    try: call()
    except (ValueError,KeyError): return
    raise AssertionError('invalid fixture admitted')


def protocol():
    return dict(counts=copy.deepcopy(s.COUNTS),epochs=2,seed=20261011,micro_batch=1,gradient_accumulation=4,
        fixed_final_checkpoint_only=True,quality_failure_NO426_no_recipe_retuning=True,
        quality=dict(locked_positive_macro_F1_gain_min='0.05',positive_empty_window_count_nonincrease=True,
        positive_locked_sources_min=3,strictly_improved_locked_sources_min=2,
        locked_complete_silver_min=12,locked_sources_with_at_least_5sec_no_min=2))


def plan_fixture():
    jobs=[]
    for role,n in (('train',16),('process_dev',4),('locked_evaluation',4)):
        for g in range(n):
            group=role+str(g); source=('%064x'%len(jobs))
            for ix in range(4):
                jobs.append(dict(role=role,source_group=group,coverage_class='ordinary' if ix==0 else 'mixed',
                    window=dict(window_id=group+'_'+str(ix),source_sha256=source,
                    source_origin_exact='0',source_duration_exact='120',original_window_index=ix,
                    domain_start_exact=str(30*ix),domain_end_exact=str(30*(ix+1)))))
    return dict(jobs=jobs)


def evidence_fixture(folder):
    """Real PNGs and synthetic NDJSON; never actual teacher/source observation."""
    from PIL import Image
    def value(name,v):
        p=folder/(name+'.json');p.write_text(json.dumps(v),encoding='utf-8');return dict(path=str(p),sha256=s.sha(p))
    source='a'*64; wid='synthetic_test_only'; identity=dict(window_id=wid,source_sha256=source)
    width,height=32,24;frames=[];images=[]
    for i in range(64):
        image=Image.new('RGB',(width,height),(i,2*i,3*i%256));images.append(image)
        p=folder/('%02d.png'%i);image.save(p)
        frames.append(dict(ordinal=i,pts_exact=str(F(i,3)),width=width,height=height,
            pixel_sha256=s.hashlib.sha256(image.tobytes()).hexdigest(),png=dict(path=str(p),sha256=s.sha(p))))
    sheets=[]
    for i in range(8):
        image=Image.new('RGB',(width*2,(height+26)*4),'white')
        for tile in range(8):image.paste(images[i*8+tile],((tile%2)*width,(tile//2)*(height+26)+26))
        p=folder/('sheet%d.png'%i);image.save(p)
        sheets.append(dict(index=i,frame_ordinals=list(range(i*8,i*8+8)),scale_exact='1',image=dict(path=str(p),sha256=s.sha(p))))
    cid='SYNTHETIC_NDJSON_TEST_ONLY';raw=[];observations=[]
    for i in range(8):
        toolpath=sheets[i]['image']['path']
        for state in ('ACTIVE','DONE'):
            raw.append(dict(event='step_update',step_update=dict(conversation_id=cid,step_index=i,state=state,step_type='tool',
                tool_name='view_file',tool_info=dict(name='view_file',parameters=dict(AbsolutePath=toolpath)))))
        observations.append(dict(sheet_index=i,conversation_id=cid,step_index=i,tool_call_id=None,tool_call_id_exposed=False,
            tool_image_path=toolpath,image_sha256=sheets[i]['image']['sha256'],successful=True,raw_image_metadata_visible=False))
    raw.append(dict(event='result',result=dict(status='SUCCESS',error=None)))
    stream=folder/'stream.jsonl';stream.write_text('\n'.join(json.dumps(r) for r in raw)+'\n',encoding='utf-8')
    ev=dict(contact_sheet_manifest=value('manifest',dict(**identity,synthetic_fixture=True,source_rgb_unscaled=True,frames=frames,sheets=sheets)),
        teacher_stream_audit=value('audit',dict(**identity,synthetic_fixture=True,original_stream=dict(path=str(stream),sha256=s.sha(stream)),
        sheet_observations=observations,image_block_claimed=False,
        raw_image_metadata_limitations=['Synthetic fixture mimics real AGY DONE name/parameters only; no raw image block.'],
        tool_issues=[],old_workflow_claimed=False,native_video_delivered=False)),
        blind_initial=value('blind',dict(**identity,blind_attestation=dict(teacher_content_received=False,candidate_prediction_received=False),independent_semantic_review_complete=True)),
        student_processor=value('student',dict(patch_inverse_exact=True,frames=list(range(64)),
        evidence=dict(source_frame_ids=list(range(64)),frame_pixel_sha256=[r['pixel_sha256'] for r in frames]),
        normalized_tensor_sha256='b'*64,video_grid_thw=[[32,20,20]],input_tokens=5000)),
        final_main_review=value('final',dict(**identity,reviewer_role='root',teacher_stream_reviewed=True,
        preteacher_independent_review_crosschecked=True,no_candidate_prediction_exposure_before_reference_freeze=True,complete_partition_reviewed=True)))
    j=dict(role='train',source_group='fixture',coverage_class='mixed',window=dict(**identity,domain_start_exact='0',domain_end_exact='30',
        planned_source_frame_ordinals=list(range(64)),planned_exact_pts=[str(F(i,3)) for i in range(64)],width=width,height=height))
    record=dict(**identity,reference_kind=s.KIND,keep_global_exact=[['8','12']],no_global_exact=[['0','8'],['12','30']],unknown_global_exact=[],
        events=[dict(event_id='e',local=['8','12'],visible_reason='synthetic oracle')],training_admitted=True,
        consequential_unknowns=[],explicit_no_highlight=False,student_observable_complete_target=True,all_target_boundaries_adjudicated=True,
        main_review_assertions={k:True for k in ('direct_visible_facts_checked','all_NO_ranges_explicitly_reviewed','no_audio_content_invented',
        'necessary_preparation_and_result_considered','no_artificial_event_merging','no_candidate_prediction_exposure_before_reference_freeze','student_visibility_checked')},
        boundary_decisions=[dict(event_id='e',side=side,boundary_global_exact=v,uncertainty_start_exact=v,uncertainty_end_exact=v,
        inside_evidence='synthetic',outside_evidence_or_domain_boundary='synthetic') for side,v in (('start','8'),('end','12'))],evidence=ev)
    return j,record


def main():
    for p in HERE.parent.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'))
    # Exhaustive independent unit-cell truth completions are a metric oracle.
    cases=0
    for length in range(3,7):
        cells=[(F(i),F(i+1)) for i in range(length)]; keep=cells[:1];no=cells[1:2];unknown=cells[2:]
        for bits in itertools.product((0,1),repeat=length):
            pred=[c for c,b in zip(cells,bits) if b];m=q.metrics([(0,length)],keep,no,unknown,pred);scores=[]
            for labels in itertools.product((0,1),repeat=len(unknown)):
                truth=keep+[c for c,b in zip(unknown,labels) if b]
                # Sum discrete cell truth directly, independent of interval helper.
                truth_cells={int(a) for a,b in truth};pred_cells={i for i,b in enumerate(bits) if b}
                scores.append(F(2*len(truth_cells & pred_cells),len(truth_cells)+len(pred_cells)))
            assert min(scores)==m['f1_lower'] and max(scores)==m['f1_upper'];cases+=1
    groups=[i//4 for i in range(64)];sch=q.schedule(groups);loss=[F(i+1,17) for i in range(64)]
    assert sch['updates']==32 and sum(len(b['indices']) for b in sch['batches'])==128
    for epoch in (0,1):
        batches=[b for b in sch['batches'] if b['epoch']==epoch]
        assert sorted(i for b in batches for i in b['indices'])==list(range(64))
        assert sum(q.batch_loss_mean_ce(sch,b['indices'],loss) for b in batches)/len(batches)==sum(loss)/64
    rejected(lambda:q.schedule(groups,seed=20261010));rejected(lambda:q.schedule(groups[:60]))
    p=protocol();plan=plan_fixture();s.validate_plan(plan,p)
    short=copy.deepcopy(plan)
    for j in short['jobs']:
        ix=j['window']['original_window_index']
        j['window'].update(source_duration_exact='40',domain_start_exact=str(ix*10),domain_end_exact=str((ix+1)*10))
    s.validate_plan(short,p)
    broken=copy.deepcopy(plan);broken['jobs'][64]['window']['source_sha256']=broken['jobs'][0]['window']['source_sha256'];rejected(lambda:s.validate_plan(broken,p))
    broken=copy.deepcopy(plan);broken['jobs'].pop();rejected(lambda:s.validate_plan(broken,p))
    broken=copy.deepcopy(plan);broken['jobs'][0]['coverage_class']='PENDING_SEMANTIC';rejected(lambda:s.validate_plan(broken,p))
    broken=copy.deepcopy(plan);broken['jobs'][0]['window']['domain_start_exact']='1';rejected(lambda:s.validate_plan(broken,p))
    broken=copy.deepcopy(p);broken['counts']['optimizer_updates']=31;rejected(lambda:s.validate_protocol(broken))
    with tempfile.TemporaryDirectory(prefix='cpu_fixture_',dir=HERE) as tmp:
        folder=Path(tmp).resolve();assert folder.is_relative_to(HERE)
        j,r=evidence_fixture(folder);s.verify_window(r,j)
        pure=copy.deepcopy(r);pure.update(keep_global_exact=[],no_global_exact=[['0','30']],events=[],boundary_decisions=[],explicit_no_highlight=True)
        purejob=copy.deepcopy(j);purejob['coverage_class']='ordinary';s.verify_window(pure,purejob)
        unk=copy.deepcopy(pure);unk.update(no_global_exact=[],unknown_global_exact=[['0','30']],explicit_no_highlight=False,training_admitted=False)
        uj=copy.deepcopy(j);uj.update(role='locked_evaluation',coverage_class='unknown');s.verify_window(unk,uj)
        falseempty=copy.deepcopy(unk);falseempty['explicit_no_highlight']=True;rejected(lambda:s.verify_window(falseempty,uj))
        for change in ('wide_boundary','missing_boundary','train_unknown','uncovered','bad_role','old_kind','ordinary_mixed','too_many_events','fake_png','changed_sheet_tile','text_id_only','done_wrong_path','done_missing','done_structured_failure','stream_ERROR','fake_tool_call_id','fake_image_block','bad_stream'):
            x=copy.deepcopy(r);jj=copy.deepcopy(j)
            if change=='wide_boundary':x['boundary_decisions'][0]['uncertainty_end_exact']='9'
            if change=='missing_boundary':x['boundary_decisions'].pop()
            if change=='train_unknown':x['no_global_exact']=[['0','7'],['12','30']];x['unknown_global_exact']=[['7','8']]
            if change=='uncovered':x['no_global_exact']=[['0','7'],['12','30']]
            if change=='bad_role':jj['role']='locked_evaluation'
            if change=='old_kind':x['reference_kind']='FINITE_OBSERVATION_SILVER_EDITING_ADVICE_NOT_GOLD'
            if change=='ordinary_mixed':jj['coverage_class']='ordinary'
            if change=='too_many_events':x['events']*=6
            if change in ('fake_png','changed_sheet_tile'):
                m=s.read_bound(x['evidence']['contact_sheet_manifest'])
                if change=='fake_png':
                    bad=folder/'fake.png';bad.write_bytes(b'not PNG')
                    m['frames'][0]['png']=dict(path=str(bad),sha256=s.sha(bad))
                else:
                    from PIL import Image
                    bad=folder/'bad_sheet.png'
                    with Image.open(m['sheets'][0]['image']['path']) as image:
                        image.putpixel((0,26),(255,0,255));image.save(bad)
                    m['sheets'][0]['image']=dict(path=str(bad),sha256=s.sha(bad))
                mp=folder/(change+'.json');mp.write_text(json.dumps(m));x['evidence']['contact_sheet_manifest']=dict(path=str(mp),sha256=s.sha(mp))
            if change in ('text_id_only','done_wrong_path','done_missing','done_structured_failure','stream_ERROR','fake_tool_call_id','fake_image_block','bad_stream'):
                audit=s.read_bound(x['evidence']['teacher_stream_audit']);sp=Path(audit['original_stream']['path'])
                rows=[json.loads(v) for v in sp.read_text().splitlines()]
                if change=='text_id_only':rows=[dict(event='text',message='SYNTHETIC_NDJSON_TEST_ONLY all ids 0 1 2 3 4 5 6 7')]
                if change=='done_wrong_path':rows[1]['step_update']['tool_info']['parameters']['AbsolutePath']=str(folder/'other.png')
                if change=='done_missing':rows.pop(1)
                if change=='done_structured_failure':rows[1]['step_update']['tool_info']['output']={'isError':True,'error':'Synthetic real tool failure'}
                if change=='stream_ERROR':rows[-1]['result'].update(status='ERROR',error='actual synthetic failure')
                if change=='fake_tool_call_id':audit['sheet_observations'][0].update(tool_call_id='invented_id',tool_call_id_exposed=True)
                if change=='fake_image_block':audit['image_block_claimed']=True
                if change=='bad_stream':rows=[dict(event='text',message='view_file ids are not step_update')]
                altered=folder/(change+'.jsonl');altered.write_text('\n'.join(json.dumps(v) for v in rows)+'\n')
                audit['original_stream']=dict(path=str(altered),sha256=s.sha(altered))
                ap=folder/(change+'_audit.json');ap.write_text(json.dumps(audit));x['evidence']['teacher_stream_audit']=dict(path=str(ap),sha256=s.sha(ap))
            rejected(lambda:s.verify_window(x,jj))
    # Known independent worlds exercise gate pass, equal-score failure, new-spill failure.
    jobs={};refs={};base={};new={}
    for role in ('process_dev','locked_evaluation'):
        for group in range(4):
            for ix in range(4):
                key='%s_%d_%d'%(role,group,ix);a=ix*10
                jobs[key]=dict(role=role,source_group=role+str(group),coverage_class='mixed',window=dict(domain_start_exact=str(a),domain_end_exact=str(a+10)))
                refs[key]=dict(keep_global_exact=[[str(a),str(a+8)]],no_global_exact=[[str(a+8),str(a+10)]],unknown_global_exact=[],
                    events=[dict(local=['0','8'])])
                base[key]=dict(status='MODEL_OK',parsed_segments=[['0','4']]);new[key]=dict(status='MODEL_OK',parsed_segments=[['0','8']])
    def sums(pred,role):return gate.summarize(jobs,refs,{k:v for k,v in pred.items() if jobs[k]['role']==role},q,events,role)
    db,lb=sums(base,'process_dev'),sums(base,'locked_evaluation');dn,ln=sums(new,'process_dev'),sums(new,'locked_evaluation')
    assert gate.gate(db,dn,lb,ln,q,p)['status']=='PASS_FIXED_SILVER_QUALITY_GATE'
    assert gate.gate(db,db,lb,lb,q,p)['status'].startswith('STOP')
    unknown_jobs=copy.deepcopy(jobs);unknown_refs=copy.deepcopy(refs)
    for key,j in unknown_jobs.items():
        if j['role']=='locked_evaluation':
            j['coverage_class']='unknown';a=F(j['window']['domain_start_exact'])
            unknown_refs[key].update(keep_global_exact=[[str(a),str(a+4)]],no_global_exact=[[str(a+4),str(a+8)]],
                                    unknown_global_exact=[[str(a+8),str(a+10)]],events=[dict(local=['0','4'])])
    coverage=gate.reference_coverage(unknown_jobs,unknown_refs,q,p)
    assert coverage['checks']['locked_complete_silver_min'] is False and coverage['checks']['positive_locked_sources_min'] is False
    spill=copy.deepcopy(new);spill['locked_evaluation_0_0']['parsed_segments']=[['0','9']]
    assert gate.gate(db,dn,lb,sums(spill,'locked_evaluation'),q,p)['checks']['no_new_unrelated_spill'] is False
    assert CAPS==dict(train=7200,evaluate=7200,nontest=1800,candidate=14400) and TOTAL_CAP==sum(CAPS.values())==30600
    terminal=dict(name='synthetic_failed_job',command=['python','-B','fixture'],charged_seconds=F(1,2),runner_source_sha256='runner',resource_policy_sha256='policy',
        status='failed',finished_utc='fixture',exit_code=1)
    terminal['charged_seconds']=.5;before=b'{"name":"historical"}\n';after=before+(json.dumps(terminal)+'\n').encode()
    args=dict(name=terminal['name'],command=terminal['command'],runner_sha='runner',policy_sha='policy',phase='train',prior_current_cost=0)
    assert accept_terminal(terminal,before,after,**args)==.5
    rejected(lambda:accept_terminal(terminal,before,after+json.dumps(terminal).encode(),**args))
    assert not any(name in sys.modules for name in ('torch','transformers','av','peft'))
    print(json.dumps(dict(status='PASS_SYNTHETIC_CPU_ORACLES_AND_NEGATIVE_ADMISSION_ONLY',unknown_oracle_cases=cases,
        updates_tested=32,backward_examples_tested=128,model_calls=0,native_video_decoder_calls=0,processor_calls=0,real_png_fixture_pixels_verified=True,synthetic_teacher_ndjson_only=True,
        actual_reference_admitted=False,actual_training_verified=False,actual_426_zip_verified=False)))


if __name__=='__main__':main()
