"""Population, dense sampling, masking and real codec/processor CPU checks."""
import argparse
import copy
import json
import math
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

from mac_contract import epoch_batches,HERE,ASSET_ROOT
from mac_inputs import clip_plan
from row_contract import validate_training_rows
from sft_contract import assistant_labels,sha256

class PureContracts(unittest.TestCase):
    def row(self):return dict(fps_num=30000,fps_den=1001,n_frames=4496,clip_start_sec=10.0,clip_end_sec=40.0)
    def test_dense_plan_has_exact_128_samples(self):
        plan=clip_plan(self.row());self.assertEqual(plan['n_sampled'],128)
        self.assertEqual(len(set(plan['absolute_indices'])),128)
        self.assertEqual(plan['absolute_indices'][0],plan['clip_start_frame_abs'])
        self.assertEqual(plan['absolute_indices'][-1],plan['clip_end_frame_abs'])
    def test_dense_plan_preserves_source_clock_and_increases_sampling(self):
        coarse=clip_plan(self.row(),64);dense=clip_plan(self.row(),128)
        for key in ['clip_start_frame_abs','clip_end_frame_abs','n_frames_in_clip','source_fps']:
            self.assertEqual(coarse[key],dense[key])
        self.assertLessEqual(max(b-a for a,b in zip(dense['absolute_indices'],dense['absolute_indices'][1:])),
                             max(b-a for a,b in zip(coarse['absolute_indices'],coarse['absolute_indices'][1:])))
    def test_short_tail_does_not_invent_frames(self):
        row=self.row();row.update(clip_start_sec=147.883,clip_end_sec=150.017)
        plan=clip_plan(row);self.assertLess(plan['n_sampled'],128)
        self.assertEqual(plan['absolute_indices'][-1],4495)
    def test_full_exact_coverage_and_partial_batch(self):
        batches=epoch_batches(724,5,16,20261006)
        self.assertEqual(len(batches),227);self.assertEqual(len(batches[-1]),4)
        for epoch in range(1,6):
            self.assertEqual(sorted(index for batch in batches for e,index in batch if e==epoch),list(range(724)))
    def test_probe_has_exact_three_updates(self):
        batches=epoch_batches(20,5,16,20261006,48)
        self.assertEqual(len(batches),3);self.assertEqual([len(batch) for batch in batches],[16]*3)
    def test_prompt_and_padding_mask(self):
        identity=assistant_labels([0,10,20,30,40,0],[0,1,1,1,1,0],[10,20],[1,1])
        self.assertEqual(identity['labels'],[-100,-100,-100,30,40,-100])
    def test_real_train_join_and_reject_unknown_dev(self):
        registry=json.loads((HERE/'r7_train_registry.json').read_text())
        original=[json.loads(line) for line in (HERE/'original_train.jsonl').read_text().splitlines() if line.strip()]
        rows=[json.loads(line) for line in (HERE/'full_train.jsonl').read_text().splitlines() if line.strip()]
        self.assertEqual(len(validate_training_rows(registry,rows,original)),704)
        for key,value in [('split','dev'),('segments_clip_local',[])]:
            bad=copy.deepcopy(rows);bad[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_training_rows(registry,bad,original)

class MacCodecProcessor(unittest.TestCase):
    def test_real_lossless_ordinals_pts_and_processor(self):
        import av
        import numpy as np
        import torch
        from transformers import AutoProcessor
        import mac_inputs
        (HERE/'tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=HERE/'tmp',prefix='codec_cpu_') as tmp:
            tmp=Path(tmp);video=tmp/'source.mkv'
            with av.open(str(video),'w') as container:
                stream=container.add_stream('ffv1',rate=30);stream.width=320;stream.height=240;stream.pix_fmt='bgr0'
                for index in range(240):
                    pixels=np.zeros((240,320,3),dtype=np.uint8);pixels[:,:,0]=index
                    frame=av.VideoFrame.from_ndarray(pixels,format='rgb24')
                    for packet in stream.encode(frame):container.mux(packet)
                for packet in stream.encode():container.mux(packet)
            (tmp/'source_map.json').write_text(json.dumps({'SYNTHETIC_NONTEST_CODEC':str(video)}))
            row=dict(window_id='synthetic_codec_cpu_only',parent_sample_id='synthetic',source_path='SYNTHETIC_NONTEST_CODEC',
                source_sha256=sha256(video),fps_num=30,fps_den=1,n_frames=240,width=320,height=240,
                clip_start_sec=.5,clip_end_sec=6.0,segments_clip_local=[[1.0,2.0]])
            tc=mac_inputs.frozen_prompt(HERE/'temporal_common.py')
            processor=AutoProcessor.from_pretrained(str(ASSET_ROOT/'models/Qwen3-VL-8B-Instruct'),local_files_only=True,
                                                    min_pixels=32768,max_pixels=32768)
            high_processor=AutoProcessor.from_pretrained(str(ASSET_ROOT/'models/Qwen3-VL-8B-Instruct'),local_files_only=True,
                                                         min_pixels=131072,max_pixels=131072)
            with patch.object(mac_inputs,'HERE',tmp):
                frames,metadata,identity=mac_inputs.decode_av_clip(row,tc,np,None)
                self.assertEqual(len(frames),128)
                self.assertEqual([int(frame[0,0,0]) for frame in frames],identity['absolute_indices'])
                encoded,keep,evidence=mac_inputs.build_example(processor,row,dict(max_sequence_length=6144,max_pixels=32768),tc,torch,np,None)
                high_encoded,high_keep,high_evidence=mac_inputs.build_example(high_processor,row,dict(max_sequence_length=16384),tc,torch,np,None)
            self.assertEqual(evidence['clip_identity']['n_sampled'],128)
            self.assertEqual(evidence['video_identity']['video_grid_thw'][0][0],64)
            self.assertLessEqual(encoded['input_ids'].shape[1],6144)
            self.assertEqual(evidence['assistant_suffix'],'{"segments":[[1.0,2.0]]}<|im_end|>\n')
            self.assertGreater(evidence['assistant_mask']['supervised_tokens'],0)
            self.assertEqual(evidence['clip_identity']['absolute_indices'],high_evidence['clip_identity']['absolute_indices'])
            self.assertEqual(evidence['assistant_suffix'],high_evidence['assistant_suffix'])
            self.assertLess(encoded['input_ids'].shape[1],high_encoded['input_ids'].shape[1])
            self.assertLess(encoded['pixel_values_videos'].numel(),high_encoded['pixel_values_videos'].numel())
            self.assertLessEqual(evidence['video_identity']['actual_processed_pixels_per_frame'],32768)
            print(json.dumps(dict(status='PASS_REAL_DENSE_LOWRES_INPUT_REDUCTION',
                frames=evidence['clip_identity']['n_sampled'],low_sequence=int(encoded['input_ids'].shape[1]),
                high_sequence=int(high_encoded['input_ids'].shape[1]),
                low_grid=encoded['video_grid_thw'].tolist(),high_grid=high_encoded['video_grid_thw'].tolist(),
                video_processor_size=processor.video_processor.size,
                actual_pixels_per_frame=evidence['video_identity']['actual_processed_pixels_per_frame'],
                source_ordinals_and_targets_unchanged=True)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mac',action='store_true');args=parser.parse_args()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PureContracts)
    if args.mac:suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(MacCodecProcessor))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps(dict(status='PASS_MAC_CPU_CONTRACTS' if result.wasSuccessful() else 'STOP_MAC_CPU_CONTRACTS',
        tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),real_codec_processor_test=args.mac)))
    raise SystemExit(0 if result.wasSuccessful() else 3)
