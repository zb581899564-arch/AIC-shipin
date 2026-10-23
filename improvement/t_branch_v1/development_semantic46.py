"""First exact half-second BASE-semantic inputs on the two fixed dev recordings."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from fractions import Fraction

import av
import numpy as np
from PIL import Image
import torch
from transformers import AutoProcessor

from frozen_branch46 import RUN, semantic_modules
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'development_semantic46'


def prepare_source(source, processor, production, frozen):
    sid = source['sid']; folder = OUT / sid
    folder.mkdir()
    clock = read(check(source['clock']))
    points, groups, samples = frozen.frame_plan(clock)
    path = folder / 'native.npz'
    with path.open('xb') as stream:
        np.savez_compressed(stream, groups=groups, sample_ordinals=np.asarray(samples))
    from source_color import convert_frame
    desired, images, ordinals, accepted, observed = set(samples), [], [], [], 0
    with av.open(str(check(source['media']))) as container:
        stream = container.streams.video[0]
        stream.codec_context.thread_count = 1
        origin = Fraction(clock['first_PTS_exact'])
        for index, frame in enumerate(container.decode(stream)):
            if index >= len(points) or Fraction(frame.pts) * frame.time_base - origin != points[index]:
                raise ValueError('First semantic decode differs from registered original PTS')
            observed += 1
            if index in desired:
                images.append(Image.fromarray(convert_frame(frame, source['media']['sha256'], 'rgb24')))
                ordinals.append(index)
                if len(images) == 8:
                    accepted.append(frozen.save_chunk(processor, production, points, images, ordinals, folder, len(accepted)))
                    images, ordinals = [], []
        if images:
            accepted.append(frozen.save_chunk(processor, production, points, images, ordinals, folder, len(accepted)))
    if observed != len(points) or [i for row in accepted for i in row['samples']] != samples:
        raise ValueError('First complete semantic source/sample count differs')
    words = {word: processor.tokenizer.encode(word, add_special_tokens=False) for word in ('Yes', 'No')}
    if any(len(ids) != 1 for ids in words.values()):
        raise ValueError('Frozen semantic Yes/No must be single token')
    save(folder / 'semantic_CPU_completion.json', dict(state='PASS_FIRST_DEV_EXACT_SEMANTIC_INPUTS',
        source=source, chunks=accepted, native=identity(path), cells=len(samples), words={k: v[0] for k, v in words.items()},
        first_original_source_decode=1, input_read_labels=False, all_four_policies_share_identical_BASE_features=True))
    print('DEV46_SEMANTIC_CPU_PASS', sid, len(samples), len(accepted), flush=True)
    return identity(folder / 'semantic_CPU_completion.json')


def main():
    OUT.mkdir()
    runtime()
    import baseline_semantic57_prepare as frozen
    production, _, _ = semantic_modules()
    processor = AutoProcessor.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    processor.tokenizer.padding_side = 'left'
    wanted = set(read(ROOT / 'code/joint_policy_protocol44.json')['development_sources'])
    plan = read(ROOT / 'pilot_profile21/registration.json')['planned']
    sources = [row['source'] for row in plan if row['source']['sid'] in wanted]
    accepted = [prepare_source(source, processor, production, frozen) for source in sources]
    if {row['sid'] for row in sources} != wanted or torch.cuda.is_initialized():
        raise ValueError('Actual fixed source set/CPU-only constraint differs')
    save(OUT / 'completion.json', dict(state='PASS_ALL_FIRST_DEV_FROZEN_SEMANTIC_INPUTS', sources=accepted))


if __name__ == '__main__':
    main()
