"""First417 logical native-action inputs, old video/ASR adoption only, no labels."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from fractions import Fraction
from pathlib import Path
import shutil
import subprocess
import traceback
from types import SimpleNamespace

import torch
from transformers import AutoTokenizer

from coarse_call25 import load_case
from development_data46 import development_sources
from frozen_branch46 import RUN
from native_input99 import prepare
from native_sets import NativeTimeline
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'native_action_inputs99'


def adopted_audio(case, asr, old_prefix):
    row = read(check(old_prefix))
    if row['case'] != case.name or row['original_CPU'] != case.CPU or row['ASR'] != asr:
        raise ValueError('Old independently accepted AV prefix belongs to another real clip')
    return asr


def fit_inputs(rt, tokenizer, folder, owners):
    inventory = read(ROOT / 'summary_content81/completion.json')
    inputs = read(ROOT / 'summary_inputs84/completion.json')['accepted']
    av = read(ROOT / 'summary_av83/completion.json')['accepted']
    audio = read(ROOT / 'summary_av83/ASR_completion.json')['outputs']
    result = {}; source_meta = {}
    for row in inventory['planned']:
        source = row['source']; sid = source['sid']
        if source['role'] != 'fit':
            raise ValueError('Only original fit sources may enter this first fit input scope')
        timeline = NativeTimeline.from_clock(read(check(source['clock'])))
        result[sid] = {}; source_meta[sid] = source
        for ref in inputs[sid]:
            meta = read(check(read(check(ref))['input']))
            case = SimpleNamespace(name=meta['case_id'], CPU=ref, meta=meta)
            case.values = load_case(ref, rt, tokenizer)[2]
            speech = adopted_audio(case, audio[case.name], av[sid][case.name])
            result[sid][case.name] = prepare(case, timeline, speech, False,
                                             tokenizer, rt, folder / case.name, owners)
            del case.values
            print('NATIVE99_FIRST_FIT_TEXT', case.name, flush=True)
    return result, source_meta


def development_inputs(rt, tokenizer, folder, owners, arms):
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=False)
    av = read(ROOT / 'event_inputs69/completion.json')['accepted']
    audio = read(ROOT / 'event_inputs69/ASR_completion.json')['outputs']
    result, provenance = {}, {}
    for sid, source in sources.items():
        cases = sorted(source.cases, key=lambda c: Fraction(c.meta['window_start']))
        result[sid] = {arm: {} for arm in arms}; provenance[sid] = {}
        for j, case in enumerate(cases):
            case.values = load_case(case.CPU, rt, tokenizer)[2]
            own = adopted_audio(case, audio[case.name], av[sid][case.name])
            other = cases[(j + len(cases) // 2) % len(cases)]
            wrong = adopted_audio(other, audio[other.name], av[sid][other.name])
            correct = prepare(case, source.timeline, own, False, tokenizer, rt,
                              folder / (case.name + '_correct'), owners)
            joint = prepare(case, source.timeline, wrong, True, tokenizer, rt,
                            folder / (case.name + '_joint_shift'), owners)
            visual = prepare(case, source.timeline, own, True, tokenizer, rt,
                             folder / (case.name + '_video_shift'), owners)
            for arm, ref in zip(arms, [correct, correct, joint, visual]):
                result[sid][arm][case.name] = ref
            provenance[sid][case.name] = dict(original_ASR=own, joint_shift_ASR=wrong,
                original_case=case.name, fixed_half_source_audio_provider=other.name,
                all_native_times_and_cell_definitions_unchanged=True,
                visual_shift_is_deliberately_wrong_not_new_native_reference=True)
            case.values = {}
            print('NATIVE99_FIRST_DEV_LOGICAL4', sid, case.name, flush=True)
    return result, provenance


def main():
    OUT.mkdir(); torch.set_num_threads(2); rt = runtime()
    contract = read(ROOT / 'native_action_contract98/completion.json')
    if contract['state'] != 'FIRST_NATIVE_ACTION_CODEC_LOSS_ROLE_CPU_PASS':
        raise ValueError('Actual first role/loss/finite-codec CPU contract required')
    protocol = read(check(contract['protocol']))
    proposed = 417 * (2 * 16384 * 8 + 32768)
    if shutil.disk_usage(ROOT).free < proposed:
        raise RuntimeError('Specific new417 text/first-proof capacity insufficient')
    save(OUT / 'registration.json', dict(protocol=contract['protocol'],
        first_role_loss_codec_CPU=identity(ROOT / 'native_action_contract98/completion.json'),
        logical_fit=217, logical_development=200, new_8B_calls=0,
        no_human_masks_coefficients_or_descriptions_read_by_input_builder=True,
        same_prior_visual_and_ASR_scope=True, estimated_new_bytes=proposed,
        original_inputs=identity(ROOT / 'summary_inputs84/completion.json'),
        original_fit_ASR=identity(ROOT / 'summary_av83/completion.json'),
        original_dev_ASR=identity(ROOT / 'event_inputs69/completion.json'),
        code={n: identity(Path(__file__).with_name(n)) for n in
              ['native_action_inputs99.py', 'native_input99.py', 'native_codec98.py']},
        live_CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:12]))
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'],
                                             local_files_only=True)
    folder = OUT / 'prefixes'; folder.mkdir(); owners = {}
    fit, original_sources = fit_inputs(rt, tokenizer, folder, owners)
    dev, provenance = development_inputs(rt, tokenizer, folder, owners, protocol['development_matrix'])
    fit_count = sum(map(len, fit.values())); dev_count = sum(len(v) for s in dev.values() for v in s.values())
    if fit_count != 217 or dev_count != 200 or len(original_sources) != 9 or torch.cuda.is_initialized():
        raise ValueError('Complete fixed417 logical native action inputs or CPU role differ')
    save(OUT / 'completion.json', dict(state='FIRST_ALL417_LOGICAL_NATIVE_ACTION_INPUTS_CPU_PASS',
        fit=fit, development=dev, original_fit_sources=original_sources,
        development_provenance=provenance, logical_fit=217, logical_development=200,
        unique_physical_input_signatures=len(owners), physical_owners=owners,
        same_correct_input_shared_across_original_and_trained_roles=True,
        all_actual_inputs_within16384_including65action_tokens=True,
        no_human_labels_in_actual_input=True, no_original_confirmation_read=True,
        old_media_RGB_processor_ASR_and_model_successes_repeated=0,
        next='First source-global coefficient/publisher binding and live model/remaining-cost lock before unique5600s native-action job. CPU input success is not quality or production admission.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
