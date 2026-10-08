"""Actual 32B matched context diagnostic, original BF validator and raw-first IO."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import time
import traceback
import bdiag_common as c


def observe(window, out, student):
    import numpy as np
    from PIL import Image
    arr, metadata, plan, evidence = student.decode_window(window)
    frames = []
    (out / 'frames').mkdir()
    for ordinal, point, image in zip(window['planned_source_frame_ordinals'], window['planned_actual_pts_sec'], arr):
        path = out / 'frames' / (str(ordinal).zfill(9)+'.png')
        Image.fromarray(image).save(path, format='PNG')
        pixels = hashlib.sha256(np.ascontiguousarray(image).tobytes()).hexdigest()
        require = c.require
        require(hashlib.sha256(np.ascontiguousarray(np.asarray(Image.open(path).convert('RGB'))).tobytes()).hexdigest()==pixels, 'lossless observation pixels')
        frames.append({'path':str(path),'sha256':c.sha(path),'source_frame_ordinal':ordinal,'pixel_sha256':pixels})
    c.require(evidence['actual_pts_sec']==window['planned_actual_pts_sec'], 'actual decoded native PTS equals registered source table exactly')
    result = dict(window, actual_pts_sec=evidence['actual_pts_sec'],
        source_frame_ordinals=window['planned_source_frame_ordinals'], frame_files=frames,
        frame_pixel_sha256=[f['pixel_sha256'] for f in frames], all_planned_frames_delivered=True,
        teacher_modality='ORDERED_LOSSLESS_INDEPENDENT_IMAGES_WITH_EXPLICIT_NATIVE_PTS',
        actual_native_decoder_evidence=evidence, student_metadata=metadata,
        source_sequential_decode_through_last_sample=True, source_full_decode_performed=False,
        full_source_clock_from_original_registered_C_scan=True, unobserved_sampling_gaps_proven_negative=False)
    c.save(out/'decode_receipt.json',result)
    return result


def check_done(out, seed, variant, student, teacher, boundary):
    import numpy as np
    from PIL import Image
    done = c.read(out/'done.json')
    for p,digest in done['bound_files'].items():
        c.require(c.sha(p)==digest,'diagnostic bound byte changed')
    obs = c.read(out/'decode_receipt.json')
    arr,metadata,plan,evidence=student.decode_window(variant['window'])
    c.require(evidence==obs['actual_native_decoder_evidence'] and metadata==obs['student_metadata'],'independent sequential native source prefix replay')
    for image,file in zip(arr,obs['frame_files']):
        digest=hashlib.sha256(np.ascontiguousarray(image).tobytes()).hexdigest()
        c.require(digest==file['pixel_sha256'] and c.sha(file['path'])==file['sha256'],'independent source/PNG byte equality')
        c.require(hashlib.sha256(np.ascontiguousarray(np.asarray(Image.open(file['path']).convert('RGB'))).tobytes()).hexdigest()==digest,'reopened physical pixel SHA')
    prompt=c.diagnostic_prompt(obs,seed['raw_source_event_seconds'],teacher,boundary)
    c.require((out/'prompt.txt').read_text()==prompt,'exact candidate prompt replay')
    raw=(out/'raw_answer.txt').read_text(); value=json.loads(raw)
    projected=c.matched_projection(value,obs,seed['raw_source_event_seconds'],boundary)
    c.require(projected==done['matched_projection'] and value==done['model_decision'],'raw/original validator/projected candidate equality')
    request=c.read(out/'http/request.json')
    content=[{'type':'text','text':prompt},*teacher.frame_content(obs,namespaced=True)]
    c.require(request['messages']==[{'role':'user','content':content}],'all original HTTP physical content equals replay')
    grammar=boundary.ordered_grammar(obs)
    c.require(request['grammar']==grammar,'registered generation grammar replay')
    result=c.read(out/'server_response.json')
    schema=teacher.request_schema(None,obs)
    # Original runtime validator also checks eager applied grammar and physical
    # relationships. Run in an independent fresh CPU receipt subdirectory.
    check=out/'independent_runtime_replay';check.mkdir()
    teacher.verify_runtime_grammar(result,schema,raw,check,expected_grammar=grammar,observation=obs)
    recipe=c.read(c.HERE/'input_01/teacher_recipe.json')
    c.require(done['measured']['input_sequence_length']<=recipe['max_sequence_length'] and result['usage']['prompt_tokens']==done['measured']['input_sequence_length'],'actual expanded input tokens in pinned teacher contract')
    return {'done_sha256':c.sha(out/'done.json'),'source_native_PNG_RGB_HTTP_prompt_raw_validator_equal':True,
        'input_tokens':done['measured']['input_sequence_length'],'new_model_calls':0}


def attempt(seed, variant, out, admission, student, teacher, boundary):
    c.require(not out.exists(),'diagnostic attempt exists; never repeat or overwrite')
    out.mkdir(parents=True)
    try:
        obs=observe(variant['window'],out,student)
        prompt=c.diagnostic_prompt(obs,seed['raw_source_event_seconds'],teacher,boundary)
        teacher.save_exact_text(out/'prompt.txt',prompt)
        start=time.monotonic()
        answer,measured=teacher.inference(admission['server_url'],prompt,obs,None,admission,out,1800)
        # Frozen inference writes both HTTP bytes and exact answer before any
        # validity check. A parse/validation failure retains those bytes.
        value=json.loads(answer)
        matched=c.matched_projection(value,obs,seed['raw_source_event_seconds'],boundary)
        files=[p for p in out.rglob('*') if p.is_file()]
        done={'status':'PASS_REAL_32B_BOUNDARY_DIAGNOSTIC_NOT_TRUTH_OR_TRAINING','utc':c.utc(),
            'event_key':seed['event_key'],'variant':variant['name'],'window':variant['window'],
            'model_decision':value,'matched_projection':matched,'measured':measured,
            'raw_answer_sha256':c.sha(out/'raw_answer.txt'),'actual_new_32B_call':True,
            'HTTP_wall_seconds':time.monotonic()-start,'teacher_recipe_sha256':c.sha(c.HERE/'input_01/teacher_recipe.json'),
            'bound_files':{str(p):c.sha(p) for p in files},'optimizer_updates':0}
        c.save(out/'done.json',done)
        return done
    except BaseException as error:
        c.save(out/'failure.json',{'utc':c.utc(),'error':type(error).__name__+': '+str(error),
            'traceback':traceback.format_exc(),'original_raw_answer_preserved':(out/'raw_answer.txt').exists(),
            'HTTP_response_preserved':(out/'http/response.bin').exists(),'failure_converted_to_empty':False})
        raise


def main():
    c.verify()
    cad,ex,student,old,teacher,boundary=c.helpers()
    plan=c.read(c.HERE/'input_01/plan.json')
    admission=copy.deepcopy(c.read(c.HERE/'input_01/teacher_recipe.json'))
    admission['job_source_lock_sha256']=c.sha(c.HERE/'source_lock.json')
    teacher.validate_admission(admission,teacher.validator_for(c.HERE))
    session=c.HERE/'run_01/server';session.mkdir(parents=True)
    server=None; fresh=0; proofs=[]
    try:
        server,admission=teacher.start_server(admission,session)
        models=teacher.http_json(admission['server_url']+'/v1/models',None,session/'models_http',timeout=30,method='GET')
        entries=models.get('data',[])
        c.require(len(entries)==1 and 'image' in entries[0].get('architecture',{}).get('input_modalities',[]) and entries[0].get('meta',{}).get('n_ctx')==admission['max_sequence_length'],'actual owned image teacher/model context')
        c.save(session/'model_receipt.json',{'actual_models':models,'admission':admission,
            'source_lock_sha256':c.sha(c.HERE/'source_lock.json'),'not_teacher_finetuning':True})
        for event_index,seed in enumerate(plan['events']):
            for variant in seed['variants']:
                out=c.HERE/'run_01/events'/seed['event_key']/variant['name']
                attempt(seed,variant,out,admission,student,teacher,boundary);fresh+=1
                c.progress('RUNNING_REAL_MATCHED_32B_DIAGNOSTIC',events_completed=event_index,
                    fresh_model_calls=fresh,total_events=16,total_variants=plan['variant_denominator'])
                if event_index==0:
                    proofs.append(check_done(out,seed,variant,student,teacher,boundary))
            if event_index==0:
                c.save(c.HERE/'first_real_acceptance.json',{'status':'PASS_REAL_FIRST_MATCHED_CONTEXTS_AND_INDEPENDENT_CPU_REPLAY',
                    'utc':c.utc(),'event_denominator':1,'context_denominator':len(proofs),'proofs':proofs,
                    'actual_new_32B_calls':fresh,'CPU_replay_new_model_calls':0,'optimizer_updates':0,
                    'semantic_identity_and_boundary_truth':'UNKNOWN'})
        c.save(c.HERE/'inference_completion.json',{'status':'PASS_COMPLETE_REAL_16_EVENT_MATCHED_DIAGNOSTIC',
            'utc':c.utc(),'event_denominator':16,'fresh_model_calls':fresh,'variant_denominator':plan['variant_denominator'],
            'new_8B_calls':0,'optimizer_updates':0,'not_semantic_or_training_acceptance':True})
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:server.wait(timeout=30)
            except __import__('subprocess').TimeoutExpired:server.kill();server.wait(timeout=30)
            c.save(session/'owned_stop.json',{'utc':c.utc(),'owned_server_pid':server.pid,
                'returncode':server.returncode,'external_processes_signalled':False})


if __name__=='__main__':main()
