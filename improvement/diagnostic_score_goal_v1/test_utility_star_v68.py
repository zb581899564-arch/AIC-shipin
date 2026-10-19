import copy
from collections import Counter,defaultdict
import math
from pathlib import Path
import tempfile
import unittest

import crop_geometry_v31 as geometry
from crop_policy_v33 import geometry_features
import utility_star_math_v68 as star
import utility_star_prepare_v68 as preparation


def fixture():
    sources=[];entries=[];requests={};targets=[]
    def reference(name):return dict(path='/immutable/'+name,sha256='a'*64)
    for i in range(602):
        sid='synthetic:'+str(i);sha='%064x'%i;pool=geometry.candidate_pool(1920,1080)
        source=dict(source_id=sid,source_sha256=sha,role='train',width=1920,height=1080,pool=pool,
            source_vision=reference(sid+'/source.pt'),original_BASE_observed=False)
        sources.append(source)
        targets.append(dict(source_id=sid,source_sha256=sha,role='train',candidate_ious=[.7,.8,.6,.5,.9,.4],
            baseline_index=0,reference_modified=False))
        for a,b in ((0,1),(1,0),(2,3),(3,2)):
            cid=star.key(sha,a,b,'CROP31_TRIPLET');r=reference(cid+'.json')
            entries.append(dict(id=cid,source_id=sid,source_sha256=sha,input=r))
            requests[cid]=dict(id=cid,source_id=sid,source_sha256=sha,role='train',candidate_indices=[a,b],
                boxes=[pool[a],pool[b]],vision_inputs=[source['source_vision'],reference(sid+'/%d.pt'%a),reference(sid+'/%d.pt'%b)],
                class_token_ids=[10,11,12],reference_or_target_in_prompt=False)
    plan=star.build_plan(dict(sources=sources),dict(train_inputs=entries,class_token_ids=[10,11,12]),requests)
    refs={c['id']:c['input'] if c['adopted_input'] else reference(c['id']+'.new.json') for c in plan['cases']}
    rows=star.compile_schedule(plan,targets,refs,geometry_features)
    prepared=dict(schema=star.SCHEMA,train_schedule=rows,train_target_RMS=star.TARGET_RMS,class_token_ids=[10,11,12])
    return sources,entries,requests,targets,plan,refs,prepared


class StarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=fixture()

    def test_complete_star_with_actual_adoption_not_hardcoded_856(self):
        *_,plan,refs,prepared=self.data
        self.assertEqual((len(plan['cases']),len(plan['pair_index'])),(6020,3010))
        self.assertEqual((plan['adopted_inputs'],plan['first_new_combinations'],plan['new_crop_count']),(1204,4816,1204))
        self.assertEqual({(p['a'],p['b']) for p in plan['pair_index']},{(0,b) for b in range(1,6)})
        self.assertTrue(all(c['input']==refs[c['id']] for c in plan['cases'] if c['adopted_input']))

    def test_aggregate_mass_all_sources_pairs_equal_and_no_uncovered_candidate(self):
        p=self.data[-1];rows,_,proof=star.validate_schedule(p);mass=defaultdict(float);counts=Counter()
        for r in rows:
            k=(r['source_id'],r['unordered_pair'][1]);mass[k]+=r['draw_weight']/3200;counts[k]+=1
        self.assertEqual(Counter(counts.values()),{1:2820,2:190})
        self.assertTrue(all(math.isclose(v,1/3010,rel_tol=1e-14) for v in mass.values()))
        self.assertEqual(len(mass),3010);self.assertTrue(proof['all_source_stars_connected'])

    def test_true_target_direction_and_both_order_owners(self):
        p=self.data[-1];truth={t['source_id']:t['candidate_ious'] for t in self.data[3]}
        for r in p['train_schedule']:
            self.assertEqual(r['target'],truth[r['source_id']][r['b']]-truth[r['source_id']][r['a']])
            self.assertEqual(r['forward_id'],star.key(r['source_sha256'],r['a'],r['b'],'CROP31_TRIPLET'))
            self.assertEqual(r['reverse_id'],star.key(r['source_sha256'],r['b'],r['a'],'CROP31_TRIPLET'))

    def test_target_values_do_not_select_pairs_draw_order_or_extra_repeats(self):
        targets=copy.deepcopy(self.data[3]);plan=self.data[4];refs=self.data[5]
        for t in targets:t['candidate_ious']=[1-v for v in t['candidate_ious']]
        new=star.compile_schedule(plan,targets,refs,geometry_features)
        self.assertEqual([(r['id'],r['source_id'],r['a'],r['b'],r['draw_weight']) for r in new],
            [(r['id'],r['source_id'],r['a'],r['b'],r['draw_weight']) for r in self.data[-1]['train_schedule']])

    def test_reject_changed_weight_missing_edge_rms_and_labelled_request(self):
        for kind in ('weight','missing','rms'):
            p=copy.deepcopy(self.data[-1])
            if kind=='weight':p['train_schedule'][0]['draw_weight']+=.1
            if kind=='missing':p['train_schedule'].pop()
            if kind=='rms':p['train_target_RMS']*=1.01
            with self.assertRaises(ValueError):star.validate_schedule(p)
        sources,entries,requests,*_=self.data;q=copy.deepcopy(requests);q[next(iter(q))]['target']=.2
        with self.assertRaises(ValueError):star.build_plan(dict(sources=sources),dict(train_inputs=entries,class_token_ids=[10,11,12]),q)

    def test_phase_boundaries_no_original500_updates_and_determinism(self):
        self.assertEqual(list(star.phase_steps('pilot4')),[501,502,503,504])
        remaining=list(star.phase_steps('remaining796'));self.assertEqual((remaining[0],remaining[-1],len(remaining)),(505,1300,796))
        self.assertEqual(star.digest(self.data[-1]),star.digest(copy.deepcopy(self.data[-1])))
        self.assertEqual(star.RECIPE['lora_lr'],5e-5);self.assertEqual(star.RECIPE['head_lr'],.001)

    def test_reader_rejects_unknown_ref_before_materializing_input(self):
        reader=preparation.StarInputs.__new__(preparation.StarInputs);reader.allowed={}
        with self.assertRaises(ValueError):reader.get(dict(path='/unregistered',sha256='b'*64))

    def test_actual_writer_counts_journal_and_preserves_prior_exclusive_file(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);writer=preparation.Writer(out,3)
            writer.data(out/'raw',b'ab');self.assertEqual(writer.bytes,2)
            with self.assertRaises(ValueError):writer.event(out/'journal',event='x')
            with self.assertRaises(FileExistsError):writer.data(out/'raw',b'c')
            self.assertEqual((out/'raw').read_bytes(),b'ab');self.assertEqual(writer.bytes,2)


if __name__=='__main__':unittest.main()
