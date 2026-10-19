import copy
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
sys.path.insert(0,str(Path(__file__).parent))
import pair_common
sys.modules['pair_common']=pair_common
from utility_target_compile_v55 import compile_targets
from utility_value_math_v55 import validate_schedule


def fixture():
    sources=[];labels=[];entries=[];requests={};cases=[];planrows=[];oldrows=[];pairs=[];chosen={}
    owners=[]
    for i in range(602):
        sid='s'+str(i);sha=f'{i:064x}';pool=[[0,0,10,6],[1,0,8,5],[2,0,6,4]]
        sources.append(dict(source_id=sid,source_sha256=sha,role='train',width=10,height=6,pool=pool))
        labels.append(dict(source_id=sid,source_sha256=sha,role='train',candidate_ious=[.3,.6,.2],reference_modified=False,baseline_index=0))
        chosen[sid]=[[0,1],[0,2]]
        for a,b in chosen[sid]:
            ids=[]
            for x,y in ((a,b),(b,a)):
                cid=f'{sid}_{x}_{y}';ids.append(cid);r=dict(path='/fake/'+cid,sha256='a'*64)
                e=dict(id=cid,source_id=sid,source_sha256=sha,input=r);entries.append(e)
                requests[cid]=dict(id=cid,source_id=sid,source_sha256=sha,role='train',candidate_indices=[x,y],
                    boxes=[pool[x],pool[y]],reference_or_target_in_prompt=False)
                cases.append(dict(id=cid,source_id=sid,a=x,b=y))
            pairs.append(dict(source_id=sid,a=a,b=b,first_id=ids[0],reverse_id=ids[1]));owners.append(ids)
    schedule=[ids[0] for ids in owners]+[ids[1] for ids in owners[:796]]
    byid={e['id']:e for e in entries}
    for i,cid in enumerate(schedule):
        sid=byid[cid]['source_id'];planrows.append(dict(id=f'T{i}',source_id=sid,case_id=cid))
        oldrows.append(dict(id=f'T{i}',source_id=sid,input=byid[cid]['input'],target=['OLD_CLASS_UNUSED']))
    for i in range(20):
        sid='dev'+str(i);sha=f'{i+602:064x}'
        sources.append(dict(source_id=sid,source_sha256=sha,role='screen',width=10,height=6,pool=pool,baseline_box=pool[0],original_BASE_observed=True))
        labels.append(dict(source_id=sid,source_sha256=sha,role='screen',candidate_ious=[.5,.8,.1],reference_modified=False,baseline_index=0,original_reference_xywh=[0,0,9,5]))
    return (dict(train_schedule=oldrows,screen_inputs=[dict(id=f'D{i}') for i in range(240)],class_token_ids=[15,16,17]),
        dict(GT_used_for_input_or_pair_choice=False,cases=cases,train_schedule=planrows,chosen_train_pairs=chosen),
        dict(sources=sources),dict(sources=labels),dict(train_inputs=entries,pair_index=pairs),requests)


def geom(box,w,h):return np.array([1.]+[box[0]/w,box[1]/h,box[2]/w,box[3]/h]+[0.]*7+[w/h])


class Targets(unittest.TestCase):
    def test_signed_targets_weighting_and_no_screen_leak(self):
        prepared,catalog,dev=compile_targets(*fixture(),geom)
        _,_,proof=validate_schedule(prepared)
        self.assertEqual(proof['unordered_pairs'],1204);self.assertEqual(len(dev),20)
        a=prepared['train_schedule'][0];b=prepared['train_schedule'][1204]
        self.assertEqual(a['target'],-b['target']);self.assertEqual(a['geometry_delta11'],[-v for v in b['geometry_delta11']])
        self.assertEqual(a['draw_weight'],2000/(1204*2))
        self.assertNotIn('candidate_ious',str(catalog));self.assertNotIn('original_reference_xywh',str(prepared))
    def test_changed_source_rejected(self):
        args=list(fixture());args[5][args[4]['train_inputs'][0]['id']]['source_sha256']='f'*64
        with self.assertRaises(ValueError):compile_targets(*args,geom)
    def test_original_pair_order_and_box_rejected(self):
        args=list(fixture());args[1]['train_schedule'][0]['case_id']=args[1]['train_schedule'][1]['case_id']
        with self.assertRaises(ValueError):compile_targets(*args,geom)


if __name__=='__main__':unittest.main()
