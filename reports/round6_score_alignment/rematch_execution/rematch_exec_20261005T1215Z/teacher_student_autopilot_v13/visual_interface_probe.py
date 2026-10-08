"""Bounded real image-interface checks; synthetic inputs never become labels."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import time

import teacher_label as t


def case_plan():
    return [
        {'case_id':'visible_start','red_indices':[0],'source_order':list(range(8))},
        {'case_id':'visible_middle','red_indices':[4],'source_order':list(range(8))},
        {'case_id':'visible_end','red_indices':[7],'source_order':list(range(8))},
        {'case_id':'changed_image_none','red_indices':[],'source_order':list(range(8))},
        {'case_id':'same_start_images_reversed','red_indices':[0],'source_order':list(reversed(range(8)))},
        {'case_id':'changed_one_image_position','red_indices':[2,6],'source_order':list(range(8))},
        {'case_id':'64frame_tail','red_indices':[63],'source_order':list(range(64))},
        {'case_id':'64frame_same_images_reversed','red_indices':[63],'source_order':list(reversed(range(64)))},
    ]


def make_case(plan, out):
    from PIL import Image, ImageDraw
    import numpy as np
    out=Path(out); out.mkdir(parents=True,exist_ok=False)
    directory=out/'frames';directory.mkdir()
    files=[];pixels=[]
    for index,source_index in enumerate(plan['source_order']):
        image=Image.new('RGB',(256,256),(20,150,30))
        draw=ImageDraw.Draw(image)
        if source_index in plan['red_indices']:
            draw.rectangle((64,64,192,192),fill=(240,10,10))
        path=directory/(f'{index:03d}.png');image.save(path)
        pixel=hashlib.sha256(np.asarray(image).tobytes()).hexdigest()
        pixels.append(pixel)
        files.append({'path':str(path),'sha256':t.sha(path),'source_frame_ordinal':index,'pixel_sha256':pixel})
    expected=[index for index,source_index in enumerate(plan['source_order']) if source_index in plan['red_indices']]
    count=len(plan['source_order'])
    observation={'window_id':plan['case_id'],'window_pts_start_sec':0.0,'window_pts_end_exclusive_sec':float(count),
        'window_duration_sec':float(count),'actual_pts_sec':[float(i) for i in range(count)],'source_frame_ordinals':list(range(count)),
        'frame_files':files,'frame_pixel_sha256':pixels,'synthetic_only':True,
        'teacher_modality':'ORDERED_LOSSLESS_INDEPENDENT_IMAGES_SYNTHETIC_INTERFACE_ONLY',
        'synthetic_never_training_labels':True,'label_status':'NOT_A_HIGHLIGHT_ANNOTATION'}
    t.save(out/'synthetic_input.json',{'plan':plan,'expected_red_square_frame_ids':expected,
        'observation':observation,'synthetic_never_training_labels':True},fresh=True)
    return observation,expected


def run_probe(admission, out, *, server_url=None, start_server=True, timeout=3600):
    t.require(socket.gethostname()=='inspur-NP5570M5','real visual interface restricted to registered Linux')
    validator=t.validator_for(t.HERE.parent);t.validate_admission(admission,validator)
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    server=None;results=[];started=time.monotonic()
    try:
        if start_server:
            (out/'server_session').mkdir()
            server,admission=t.start_server(admission,out/'server_session')
            server_url=admission['server_url']
        else:
            t.require(admission['status']=='PASS_REAL_STRONGER_TEACHER_ADMISSION','real external server admission required')
        for plan in case_plan():
            count=len(plan['source_order'])
            schema={'type':'object','additionalProperties':False,'required':['red_square_frame_ids'],
                'properties':{'red_square_frame_ids':{'type':'array','maxItems':count,
                    'items':{'type':'integer','enum':list(range(count))}}}}
            prompt=(f'按给出的图片顺序查看全部{count}张图片。只找绿色背景上明显可见的红色方块。'
                '用图片标注的evidence_frame_id回答，按升序列出所有有红色方块的图片编号。'
                '若所有图片都没有红色方块则输出空列表。只输出JSON，字段恰好red_square_frame_ids。')
            directory=out/'cases'/plan['case_id']
            observation,expected=make_case(plan,directory)
            t.save_exact_text(directory/'prompt.txt',prompt)
            call_started=time.monotonic()
            answer,measured=t.inference(server_url,prompt,observation,schema,admission,directory,timeout)
            parsed=validator.strict_json(answer)
            t.require(isinstance(parsed,dict) and set(parsed)=={'red_square_frame_ids'},'synthetic answer schema differs')
            actual=parsed['red_square_frame_ids']
            match=actual==expected and all(type(i) is int for i in actual)
            item={'case_id':plan['case_id'],'expected_red_square_frame_ids':expected,'actual_red_square_frame_ids':actual,
                'pass':match,'raw_model_answer_sha256':t.text_sha(answer),'actual_input_contract':measured,
                'request_sha256':t.sha(directory/'http/request.json'),'response_sha256':t.sha(directory/'server_response.json'),
                'input_receipt_sha256':t.sha(directory/'synthetic_input.json'),'synthetic_never_training_labels':True}
            item.update(provided_frame_count=count,wall_sec=time.monotonic()-call_started)
            t.save(directory/'case_result.json',item,fresh=True);results.append(item)
        passed=all(item['pass'] for item in results)
        completion={'status':'PASS_REAL_SYNTHETIC_VISUAL_INTERFACE' if passed else 'STOP_REAL_SYNTHETIC_VISUAL_INTERFACE',
            'case_count':len(results),'real_model_calls':len(results),'cases':results,
            'teacher_model_id':t.TEACHER_ID,'teacher_revision':t.TEACHER_REVISION,'runtime_revision':t.RUNTIME_REVISION,
            'weight_files':admission['weight_files'],'job_source_lock_sha256':admission['job_source_lock_sha256'],
            'synthetic_never_training_labels':True,'synthetic_pass_not_highlight_quality':True,
            'runtime_or_weights_changed':False,'no_model_retry':True,'wall_sec':time.monotonic()-started,'utc':t.utc()}
        t.save(out/'completion.json',completion,fresh=True)
        t.require(passed,'simple visible location/order/image-change checks failed; bounded experiment STOP')
        return completion
    except Exception as error:
        if not (out/'completion.json').exists():
            t.save(out/'completion.json',{'status':'STOP_REAL_SYNTHETIC_VISUAL_INTERFACE','reason':str(error),
                'completed_case_count':len(results),'cases':results,'synthetic_never_training_labels':True,'utc':t.utc()},fresh=True)
        raise
    finally:
        if server is not None:
            if server.poll() is None:
                server.terminate()
                try:server.wait(timeout=30)
                except subprocess.TimeoutExpired:server.kill();server.wait(timeout=30)
            t.save(out/'server_stop_receipt.json',{'owned_server_pid':server.pid,'returncode':server.returncode,
                'external_processes_signalled':False,'utc':t.utc()},fresh=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--teacher-admission',type=Path,required=True)
    parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--start-server',action='store_true')
    parser.add_argument('--server-url',default='http://127.0.0.1:8080')
    parser.add_argument('--request-timeout',type=int,default=3600)
    args=parser.parse_args()
    run_probe(t.read(args.teacher_admission),args.out_dir,server_url=args.server_url,
        start_server=args.start_server,timeout=args.request_timeout)
