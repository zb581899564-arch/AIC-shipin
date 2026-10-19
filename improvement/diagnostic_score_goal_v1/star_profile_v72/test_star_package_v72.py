import copy
import unittest
import numpy as np
import crop_geometry_v31 as geometry
import crop_policy_v33 as policy
from star_package_v72 import patch_protected,canonical,replay_choices


def fixture():
    rows=[]
    for i in range(426):
        ratio=[16,9] if i%2==0 else [9,16];w=1920 if i%2==0 else 1080
        rows.append(dict(video_id=str(i),targetRatioWH=ratio,model_params_b=8.782557449,
            predictions=[dict(frame=f,bboxes=[0,0,w]) for f in range(290 if i<392 else 289)]))
    source=dict(source_id='official:0:native:0',video_id='0',native_ordinal=0,native_pts_exact='0',observation_index=0,
        source_sha256='a'*64,targetRatioWH=[16,9],width=1920,height=1080,
        baseline_box=[0,0,1920],pool=[[0,0,1920],[240,135,1440]])
    choice=dict(source_id=source['source_id'],source_sha256=source['source_sha256'],predicted_gains=dict(UTILITY=[0.,.1]),
        choices=dict(UTILITY=1),selected_native_box=source['pool'][1],raw_pair_owners={'1':['f','r']})
    return rows,source,choice


class Package(unittest.TestCase):
    def test_independent_primary_scalar_replay(self):
        _,s,_=fixture();sid=s['source_id'];sha=s['source_sha256']
        pairs=[dict(source_id=sid,candidate_index=0,first_id='self',reverse_id='self',same_crop=True),
            dict(source_id=sid,candidate_index=1,first_id='f',reverse_id='r',same_crop=False)]
        values={k:dict(source_id=sid,source_sha256=sha,CPU_value=v) for k,v in [('self',9.),('f',.3),('r',-.1)]}
        out=replay_choices([s],pairs,values,np.zeros(11),policy.geometry_features)
        self.assertEqual(out[0]['choices']['UTILITY'],1);self.assertAlmostEqual(out[0]['predicted_gains']['UTILITY'][1],.2)
        values.pop('r')
        with self.assertRaises(KeyError):replay_choices([s],pairs,values,np.zeros(11),policy.geometry_features)
    def test_exact_one_frame_overlay_all_time_and_other_boxes_preserved(self):
        rows,s,c=fixture();before=canonical(rows)
        new,changed=patch_protected(rows,[s],[c],geometry.legal)
        self.assertEqual(len(changed),1);self.assertEqual(new[0]['predictions'][0]['bboxes'],s['pool'][1])
        self.assertEqual(new[0]['predictions'][1:],rows[0]['predictions'][1:]);self.assertEqual(new[1]['predictions'],rows[1]['predictions'])
        self.assertNotEqual(canonical(new),before);self.assertEqual(canonical(rows),before)
    def test_parameter_change_alone_not_new_candidate(self):
        rows,s,c=fixture();c.update(predicted_gains=dict(UTILITY=[0.,-.1]),choices=dict(UTILITY=0),selected_native_box=s['pool'][0])
        new,changed=patch_protected(rows,[s],[c],geometry.legal)
        self.assertEqual(changed,[]);self.assertEqual(canonical(new),canonical(rows))
    def test_wrong_frame_or_off_budget_observation_rejected(self):
        for field,value in [('observation_index',1),('baseline_box',[1,0,1920]),('native_ordinal',999)]:
            rows,s,c=fixture();s[field]=value
            with self.assertRaises(ValueError):patch_protected(rows,[s],[c],geometry.legal)


if __name__=='__main__':unittest.main()
