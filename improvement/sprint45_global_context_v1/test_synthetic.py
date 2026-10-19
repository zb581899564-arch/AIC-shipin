"""One small CPU oracle for new grammar, image slices and exact input dedup only."""
import copy
from pathlib import Path
import tempfile
import torch
from global_context_common import (ChunkCache, anchors, compose, effective_input,
    allowed_tokens, parse_output, save_tensor, sha)


def main():
    grammar=dict(zero=10,one=11,space=12,eos=13)
    for k in (1,2,8):
        for bits in ([0]*(2*k),[1]*(2*k),[i%2 for i in range(2*k)]):
            tokens=[]
            for i,bit in enumerate(bits):
                if i:tokens.append(12)
                tokens.append(10+bit)
            tokens.append(13)
            assert len(tokens)==4*k
            assert parse_output(tokens,k,grammar,' '.join(map(str,bits))) == (bits[:k],bits[k:])
            assert all(token in allowed_tokens(i,k,grammar) for i,token in enumerate(tokens))
    for tokens,raw in [([10,12,10,13],'0  0'),([10,12,10],'0 0'),([10,12,10,11],'0 0')]:
        try:parse_output(tokens,1,grammar,raw)
        except ValueError:pass
        else:raise AssertionError('Invalid grammar accepted')
    assert anchors(1)==[0] and anchors(9)==[0,1,2,3,5,6,7,8]
    # Different image grids produce different slice lengths; this oracle selects
    # images 1 and 2 from two old chunks, including the nonzero offset in chunk0.
    parent=Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='synthetic_',dir=parent) as temp:
        directory=Path(temp);chunks=[]
        for i,(samples,grids,pixels) in enumerate([
            ([3,8],[[1,2,2],[1,2,4]],torch.arange(24,dtype=torch.float32).reshape(12,2)),
            ([11],[[1,2,2]],torch.arange(100,108,dtype=torch.float32).reshape(4,2))]):
            path=directory/('%d.pt'%i);save_tensor(path,dict(pixel_values=pixels,image_grid_thw=torch.tensor(grids),sample_ordinals=samples))
            import hashlib
            chunks.append(dict(path=str(path),sha256=sha(path),samples=samples,grid=grids,
                pixel_shape=list(pixels.shape),pixel_sha256=hashlib.sha256(pixels.numpy().tobytes()).hexdigest()))
        refs=[dict(ordinal=8,image_index=1,pixel_slice=[4,12],grid=[1,2,4],old_chunk=chunks[0]),
              dict(ordinal=11,image_index=0,pixel_slice=[0,4],grid=[1,2,2],old_chunk=chunks[1])]
        actual=compose(refs,ChunkCache())
        oracle=torch.tensor([[8.,9.],[10.,11.],[12.,13.],[14.,15.],[16.,17.],[18.,19.],[20.,21.],[22.,23.],
                             [100.,101.],[102.,103.],[104.,105.],[106.,107.]])
        assert torch.equal(actual['pixel_values'],oracle)
        assert actual['image_grid_thw'].tolist()==[[1,2,4],[1,2,2]]
        wrong=copy.deepcopy(refs);wrong[0]['pixel_slice']=[0,8]
        try:compose(wrong,ChunkCache())
        except ValueError:pass
        else:raise AssertionError('Wrong original per-image slice accepted')
        inputs=dict(input_ids=torch.tensor([[1,2,3]]),attention_mask=torch.ones((1,3),dtype=torch.int64),**actual)
        key,_=effective_input(inputs)
        assert effective_input({name:value.clone() for name,value in inputs.items()})[0]==key
        changed={name:value.clone() for name,value in inputs.items()};changed['pixel_values'][0,0]+=1
        assert effective_input(changed)[0]!=key
    print('PASS_SMALL_SYNTHETIC_GRAMMAR_SLICE_AND_EXACT_DEDUP_ORACLE; real tokenizer/model/cache not tested')


if __name__=='__main__':main()
