"""First complete150 local-card/goal native prefixes; never run a model here."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import time
import traceback

import torch
from transformers import AutoTokenizer

from coarse_call25 import load_case
from development_data46 import development_sources
from event_table71 import prepare_prefix
from frozen_branch46 import RUN
from summary_context90 import ARMS, context_card, owner_key
from t_io import ROOT, check, identity, read, save
from t_runtime39 import runtime

OUT = ROOT / 'summary_context90'


def await_goals():
    launch = read(ROOT / 'summary_goals89_launch.json'); deadline = time.monotonic() + 360
    while True:
        done, failed = ROOT / 'summary_goals89/completion.json', ROOT / 'summary_goals89/failure.json'
        if failed.exists():
            raise RuntimeError('Actual final-goal phase failed; never repeat it here')
        if done.exists():
            row = read(done)
            if row['state'] != 'FIRST_TWO_FINAL_TRAINED_GOALS_AND_CPU_PASS_NOT_TIME_QUALITY':
                raise ValueError('Actual trained free-goal/first CPU terminal differs')
            return row
        proc = Path('/proc') / str(launch['pid'])
        if not proc.exists():
            raise RuntimeError('Actual89 handle missing without terminal; inspect, never re-launch')
        stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        if stat[19] != launch['start_ticks'] or stat[0] == 'Z' or time.monotonic() > deadline:
            raise RuntimeError('Actual89 handle identity/wait bound differs')
        time.sleep(3)


def goal_text(sid, refs, trained):
    row = torch.load(check(refs['raw']), map_location='cpu', weights_only=True)
    proof = read(check(refs['CPU']))
    expected = ('PASS_FIRST_FINAL_TRAINED_GOAL_FULL_VOCABULARY_CPU' if trained
                else 'PASS_FIRST_BASE_CONTENT_GOAL_TOKEN_AND_VOCABULARY_CPU')
    if (row['source'] != sid or proof['raw'] != refs['raw'] or proof['state'] != expected
            or not isinstance(row['text'], str)):
        raise ValueError('A source goal lacks its actual first role/token CPU binding')
    return row['text']


def main():
    terminal = await_goals(); OUT.mkdir(); torch.set_num_threads(2); rt = runtime()
    interface = read(Path(__file__).with_name('summary_selector_interface90.json'))
    if identity(Path(__file__).with_name('summary_protocol85.json'))['sha256'] != interface['original_protocol_sha256']:
        raise ValueError('Fixed prospective selector interface belongs to another scientific protocol')
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'), values=False, labels=False)
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    trained = read(check(terminal['actual_outputs']))['outputs']
    base = read(ROOT / 'summary_baseline86/GPU_completion.json')['outputs']
    providers = sorted(sources)
    if len(providers) != 2 or set(trained) != set(sources) or set(base) != set(sources):
        raise ValueError('Actual complete two-source goal matrix differs')
    base_text = {sid: goal_text(sid, base[sid], False) for sid in providers}
    trained_text = {sid: goal_text(sid, trained[sid], True) for sid in providers}
    old = read(ROOT / 'event_inputs71/completion.json')
    for ref in old['native_grammar_contract']['code'].values():
        check(ref)
    tasks, provenance, owners = {}, {}, {}
    folder = OUT / 'prefixes'; folder.mkdir()
    for offset, sid in enumerate(providers):
        source = sources[sid]; shifted_sid = providers[(offset + 1) % len(providers)]
        table = read(check(old['source_tables'][sid]))
        texts = [base_text[sid], trained_text[sid], trained_text[shifted_sid]]
        tasks[sid] = {arm: {} for arm in ARMS}; provenance[sid] = {arm: {} for arm in ARMS}
        for index, case in enumerate(source.cases):
            case.values = load_case(case.CPU, rt, tokenizer)[2]
            for arm, text in zip(ARMS, texts):
                proof = prepare_prefix(case, context_card(table, index, case, text), tokenizer, rt,
                                       folder / (arm + '_' + case.name))
                tasks[sid][arm][case.name] = dict(first_event_text_CPU=proof)
                key = owner_key(case, proof)
                owner = owners.setdefault(key, dict(source=sid, case=case.name, arm=arm,
                                                   original_TIME_input=proof))
                provenance[sid][arm][case.name] = dict(owner=owner, physical_key=key,
                    current_card_source=old['source_tables'][sid],
                    actual_goal_source=(shifted_sid if arm == ARMS[2] else sid),
                    original_goal=(base[sid] if arm == ARMS[0] else trained[shifted_sid if arm == ARMS[2] else sid]))
            case.values = {}
            print('SUMMARY90_FIRST_NATIVE_CONTEXT3', sid, case.name, flush=True)
    logical = sum(len(v) for conditions in tasks.values() for v in conditions.values())
    if logical != 150 or torch.cuda.is_initialized():
        raise ValueError('Actual complete150 first native prefixes or CPU role differs')
    save(OUT / 'completion.json', dict(state='FIRST_ALL150_SOURCE_SUMMARY_NATIVE_CONTEXT_INPUTS_PASS',
        inputs=tasks, provenance=provenance, first_logical_inputs=150,
        unique_first_model_calls=len(owners), physical_owners=owners,
        old_native_grammar_CPU_adopted=old['native_grammar_contract'],
        native_interface=identity(Path(__file__).with_name('summary_selector_interface90.json')),
        goals89=identity(ROOT / 'summary_goals89/completion.json'),
        BASE86_adopted=identity(ROOT / 'summary_baseline86/completion.json'),
        all_original_video_and_current_card_adopted=True, no_human_reference_in_inputs=True,
        no_condition_or_provider_identity_in_actual_model_text=True,
        no_old_decode_processor_model_or_independent_QA_repeated=True,
        new8B_calls=0, no_quality_or_production_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        else:
            save(ROOT / 'summary_context90_dependency_failure.json', dict(traceback=traceback.format_exc(), no_upstream_restart=True))
        raise
