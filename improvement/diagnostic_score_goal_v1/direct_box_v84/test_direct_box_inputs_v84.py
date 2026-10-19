import copy
from collections import Counter,defaultdict
import gzip
import io
import math
import unittest
from unittest import mock
import torch
import direct_box_inputs_v84 as inputs


def pixels(h,w,offset=0):
    one=torch.arange(h*w*3*16*16,dtype=torch.float32).reshape(h*w,3,16,16)+offset
    return torch.stack((one,one),dim=2).reshape(h*w,1536)


class Tokenizer:
    special={'<vs>':91,'<ve>':92,'<i>':93}
    def __call__(self,text,**kwargs):
        ids=[];i=0
        while i<len(text):
            token=next((s for s in self.special if text.startswith(s,i)),None)
            if token is None:ids.append(1000+ord(text[i]));i+=1
            else:ids.append(self.special[token]);i+=len(token)
        ids=torch.tensor([ids],dtype=torch.int64);return dict(input_ids=ids,attention_mask=torch.ones_like(ids))
    def convert_tokens_to_ids(self,token):return self.special[token]


class ForbiddenProcessor:
    merge_size=2
    def __call__(self,*args,**kwargs):raise AssertionError('No real image processor in pure test')


class Processor:
    vision_start_token,image_token,vision_end_token='<vs>','<i>','<ve>'
    def __init__(self):self.tokenizer=Tokenizer();self.image_processor=ForbiddenProcessor()
    def apply_chat_template(self,messages,add_generation_prompt,**kwargs):
        content=messages[0]['content'];t='<user>'+''.join(c['text'] if c['type']=='text' else '<vs><i><ve>' for c in content)+'</user>'
        return t+('<assistant>' if add_generation_prompt else '')
    def __call__(self,text,images,**kwargs):
        adopted=self.image_processor(images=images);n=int(adopted['image_grid_thw'].prod())//4
        text=text[0].replace('<vs><i><ve>','<vs>'+'<i>'*n+'<ve>')
        return dict(**self.tokenizer(text),**adopted)


def target_fixture():
    sources=[];labels=[];train55=[];screen55=[]
    for i in range(622):
        role='train' if i<602 else 'screen';sid=role+str(i);sha='%064x'%i
        s=dict(source_id=sid,source_sha256=sha,role=role,width=1600,height=900)
        t=dict(source_id=sid,source_sha256=sha,role=role,original_reference_xywh=[100.25,20.5,500.5,400.25],
            reference_modified=False,baseline_index=0,candidate_ious=['MUST_NOT_BE_USED'])
        if role=='screen':s.update(pool=[[0,0,1600]],baseline_box=[0,0,1600],original_BASE_observed=True)
        sources.append(s);labels.append(t)
        old=copy.deepcopy(t)
        if role=='screen':old.update(pool=copy.deepcopy(s['pool']),baseline_box=copy.deepcopy(s['baseline_box']))
        (train55 if role=='train' else screen55).append(old)
    return dict(sources=sources),dict(sources=labels),dict(sources=train55),dict(sources=screen55)


class InputTests(unittest.TestCase):
    def test_non_square_actual_prefix_count_and_independent_pixel_boundary(self):
        raw=dict(pixel_values=torch.cat([pixels(2,6),pixels(4,2,100000)]),image_grid_thw=torch.tensor([[1,2,6],[1,4,2]],dtype=torch.int64))
        original=raw['pixel_values'].clone();packed,meta=inputs.extract_source_prefix(raw,[1,2,6])
        self.assertEqual(packed['pixel_values'].shape,(12,1536));self.assertEqual(meta['row_end_exclusive'],12)
        self.assertTrue(inputs.independent_prefix_check(raw,packed,[1,2,6],meta)['status'].startswith('PASS'))
        self.assertTrue(torch.equal(raw['pixel_values'],original));packed['pixel_values']=packed['pixel_values'].clone();packed['pixel_values'][0,0]+=1
        with self.assertRaises(ValueError):inputs.independent_prefix_check(raw,packed,[1,2,6],meta)

    def test_wrong_grid_nonfinite_static_slice_and_total_count_rejected(self):
        for mode in ('grid','nan','static','count'):
            raw=dict(pixel_values=pixels(2,4),image_grid_thw=torch.tensor([[1,2,4]],dtype=torch.int64));expected=[1,2,4]
            if mode=='grid':expected=[1,4,2]
            if mode=='nan':raw['pixel_values'][0,0]=float('nan')
            if mode=='static':raw['pixel_values'][0,256]=-0.
            if mode=='count':raw['pixel_values']=raw['pixel_values'][:-1]
            with self.assertRaises(ValueError):inputs.extract_source_prefix(raw,expected)

    def test_single_image_prompt_first_assistant_last_no_processor_or_digit_classes(self):
        processor=Processor();original=processor.image_processor
        packed=dict(pixel_values=pixels(2,4),image_grid_thw=torch.tensor([[1,2,4]],dtype=torch.int64))
        tokens,meta=inputs.build_text_input(processor,packed['image_grid_thw'])
        self.assertEqual(meta['image_tokens'],2);self.assertTrue(meta['expanded_text'].endswith('<assistant>'))
        self.assertLess(meta['expanded_text'].index(inputs.PROMPT),meta['expanded_text'].index('<vs>'))
        self.assertNotIn('class_token_ids',meta);self.assertEqual(meta['last_hidden_position'],tokens['input_ids'].shape[1]-1)
        inputs.independent_text_check(processor,packed,tokens,meta);self.assertIs(original,processor.image_processor)
        bad=copy.deepcopy(meta);bad['prompt']='hidden label'
        with self.assertRaises(ValueError):inputs.independent_text_check(processor,packed,tokens,bad)

    def test_lossless_gzip_all_four_tensors_roundtrip(self):
        p=Processor();grid=torch.tensor([[1,2,4]],dtype=torch.int64);tokens,_=inputs.build_text_input(p,grid)
        values=dict(**tokens,pixel_values=pixels(2,4),image_grid_thw=grid);stream=io.BytesIO();torch.save(values,stream)
        encoded=gzip.compress(stream.getvalue(),compresslevel=6,mtime=0)
        actual=torch.load(io.BytesIO(gzip.decompress(encoded)),map_location='cpu',weights_only=True)
        self.assertEqual(inputs.signature(actual),inputs.signature(values));self.assertEqual(set(actual),inputs.FOUR)

    def test_original_human_xywh_preserved_without_iou_reconstruction_or_aspect_gate(self):
        fixture=target_fixture();before=copy.deepcopy(fixture);labels,aspect=inputs.compile_targets(*fixture)
        self.assertEqual((len(labels['train']),len(labels['screen'])),(602,20))
        self.assertEqual(labels['train'][0]['original_reference_xywh'],[100.25,20.5,500.5,400.25])
        self.assertEqual(aspect['train']['within_1e_6_of_16_9'],0);self.assertEqual(fixture,before)
        self.assertNotIn('candidate_ious',labels['train'][0]);self.assertEqual(labels['screen'][0]['baseline_box'],[0,0,1600])
        fixture[2]['sources'][0]['source_sha256']='b'*64
        with self.assertRaises(ValueError):inputs.compile_targets(*fixture)

    def test_exact3200_source_equal_metadata_schedule_and_whitelist(self):
        sources=target_fixture()[0]['sources'][:602];refs={inputs.source_id(s):dict(path='/'+s['source_id'],sha256='a'*64) for s in sources}
        rows=inputs.source_schedule(sources,refs);counts=Counter(r['source_id'] for r in rows);mass=defaultdict(float)
        for r in rows:mass[r['source_id']]+=r['draw_weight']/3200
        self.assertEqual((len(rows),len({r['id'] for r in rows})),(3200,3200));self.assertEqual(Counter(counts.values()),{5:412,6:190})
        self.assertTrue(all(math.isclose(v,1/602,rel_tol=1e-14) for v in mass.values()))
        self.assertEqual(rows,inputs.source_schedule(list(reversed(sources)),refs))
        reader=inputs.DirectBoxInputs.__new__(inputs.DirectBoxInputs);reader.allowed={};reader.ref_to_id={}
        with self.assertRaises(ValueError):reader.get_metadata('not_registered')


if __name__=='__main__':unittest.main()
