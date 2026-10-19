import copy
from pathlib import Path
import unittest
import torch
import direct_box_scope_inputs_v86 as scope
import direct_box_inputs_recovery_v87 as base


def formal_fixture():
    accepted=[];metadata=[];baseline=[];clocks={};refs={}
    for i in range(426):
        vid=str(i);ratio=[16,9] if i==0 else [9,16];sha='%064x'%i
        accepted.append(dict(id=vid,native_frames=80,feature_cells=80 if i==0 else 0,clock_sha256='a'*64,
            chunks=[dict(path='/chunk',sha256='b'*64,samples=list(range(80)),grid=[[1,2,4]]*80,pixel_shape=[640,1536])] if i==0 else []))
        metadata.append(dict(video_id=vid,source_sha256=sha,n_frames=80,targetRatioWH=ratio,width=1920,height=1080))
        baseline.append(dict(video_id=vid,targetRatioWH=ratio,predictions=[dict(frame=n,bboxes=[0,0,1920]) for n in range(80)]))
        clocks[vid]=dict(video_id=vid,source_sha256=sha,normalized_exact_pts=[str(n)+'/10' for n in range(80)])
        refs[vid]=dict(clock=dict(path='/clock',sha256='a'*64),acceptance=dict(path='/accepted',sha256='c'*64))
    return dict(sources=accepted),dict(records=metadata),baseline,clocks,refs


def pixels(h,w,start):
    a=torch.arange(h*w*3*16*16,dtype=torch.float32).reshape(h*w,3,16,16)+start
    return torch.stack((a,a),dim=2).reshape(h*w,1536)


class ScopeTests(unittest.TestCase):
    def test_fixed_even_exact_pts_domain_and32_remaining_distinct_from426(self):
        args=formal_fixture();domain=scope.compile_formal_domain(*args)
        self.assertEqual((domain['all_D_count'],domain['selected_D_count'],domain['official_source_count']),(80,40,426))
        self.assertEqual([s['native_ordinal'] for s in domain['selected_D']],list(range(0,80,2)))
        self.assertEqual(domain['selected_D'][1]['native_pts_exact'],'2/10')
        self.assertEqual((len(domain['pilot_source_ids']),len(domain['remaining_source_ids'])),(32,8))
        self.assertFalse(set(domain['pilot_source_ids'])&set(domain['remaining_source_ids']))
        self.assertEqual(len({s['source_sha256'] for s in domain['selected_D']}),1)
        self.assertTrue(all(s['baseline_box']==[0,0,1920] for s in domain['selected_D']))

    def test_variable_nonfirst_chunk_row_is_exact_source_only_not_first240(self):
        raw=dict(pixel_values=torch.cat([pixels(2,6,0),pixels(4,2,100000)]),image_grid_thw=torch.tensor([[1,2,6],[1,4,2]],dtype=torch.int64))
        source=dict(role='formal',source_layout=dict(row_index=1,row_start=12,row_end_exclusive=20,grid_thw=[1,4,2]))
        packed,_=scope.extract_view(raw,source,base)
        self.assertEqual(packed['pixel_values'].shape,(8,1536));self.assertTrue(torch.equal(packed['pixel_values'],raw['pixel_values'][12:20]))
        bad=copy.deepcopy(source);bad['source_layout']['row_start']=0
        with self.assertRaises(ValueError):scope.extract_view(raw,bad,base)

    def test_confirm_only_adopts_accepted_newvision_signature(self):
        raw=dict(pixel_values=pixels(2,6,0),image_grid_thw=torch.tensor([[1,2,6]],dtype=torch.int64))
        source=dict(role='confirm',source_vision_signature=base.signature(raw));scope.extract_view(raw,source,base)
        source['source_vision_signature']['pixel_values']['sha256']='0'*64
        with self.assertRaises(ValueError):scope.extract_view(raw,source,base)

    def test_profile_same_f4_adopts_not_new_independent_quality(self):
        rows=[dict(source_id=str(i),source_sha256='%064x'%i,width=500,height=300,input_signature={'four':'same'},image_grid_thw=[[1,2,6]],
            actual_input_domain='ACCEPTED_PROCESSOR_RESIZED_FULL_SOURCE_PATCH') for i in range(20)]
        result=scope.same_source_only_inputs(rows,copy.deepcopy(rows));self.assertEqual(result['new_model_calls'],0)
        bad=copy.deepcopy(rows);bad[0]['input_signature']={'four':'different'}
        with self.assertRaises(ValueError):scope.same_source_only_inputs(rows,bad)

    def test_quality_arm_subset_can_shrink_only_after_actual_new_qualifications(self):
        identity=dict(training_completion={'a':1},adapter_weights={'a':2},head_weights={'a':3})
        reg=dict(identity,admitted_arm_names=['DIRECT'],native20_quality_result={'path':'/q','sha256':'a'*64})
        summary=dict(identity,status='PASS_DIRECT_BOX84_NATIVE20_QUALIFIED_ARMS',admitted_arm_names=['DIRECT','ANCHORED_HALF'],result=reg['native20_quality_result'])
        scope.validate_quality(reg,summary,result_key='native20_quality_result')
        bad=copy.deepcopy(summary);bad['status']='STOP_DIRECT_BOX84_NATIVE20_QUALIFIED_ARMS'
        with self.assertRaises(ValueError):scope.validate_quality(reg,bad,result_key='native20_quality_result')


if __name__=='__main__':unittest.main()
