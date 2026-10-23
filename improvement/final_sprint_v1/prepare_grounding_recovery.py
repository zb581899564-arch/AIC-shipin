"""Prepare one explicit schema-only recovery; no image decode or GPU forward."""
import argparse
from datetime import datetime, timezone
import math
from pathlib import Path

from .contracts import atomic_new, checked, ref, require, stable_key, strict_load
from .grounding_grammar import GroundingGrammar
from .spatial import parse_grounding


def prepare(args):
    old_ref, wrapper_ref = ref(args.old_assets), ref(args.old_wrapper)
    old, wrapper = strict_load(checked(old_ref)), strict_load(checked(wrapper_ref))
    require(wrapper['asset_lock'] == old_ref and wrapper['child_exit_code'] == 1
            and wrapper['work_terminated'] is True and wrapper['no_external_task_signaled'] is True,
            'Exact natural failed wrapper required')
    output = Path(args.output_dir)
    require(not output.exists(), 'Inspect existing recovery outcome; never overwrite it')
    output.mkdir()
    from transformers import AutoProcessor
    processor = AutoProcessor.from_pretrained(old['qwen']['model_dir'], local_files_only=True)
    grammar = GroundingGrammar(processor.tokenizer)
    config = strict_load(Path(old['qwen']['model_dir']) / 'generation_config.json')
    eos = config['eos_token_id']
    eos = [eos] if isinstance(eos, int) else list(eos)
    rows, excluded = [], []
    for item in wrapper['task_terminals']:
        terminal = strict_load(checked(item['terminal_ref']))
        claim_ref = terminal['claim_ref']
        claim = strict_load(checked(claim_ref))
        directory = Path(claim_ref['path']).parent
        success_ref, returned_ref = ref(directory / 'success.json'), ref(directory / 'returned_result.json')
        success, packet = strict_load(checked(success_ref)), strict_load(checked(returned_ref))
        require(success['artifacts']['result'] == returned_ref and
                claim['binding_sha256'] == packet['binding_sha256'] == stable_key(claim['binding']),
                'Old successful function return/claim identities differ')
        result = packet['result']
        try:
            parse_grounding(result['raw_text'], 3)
        except ValueError as error:
            excluded.append(dict(task_id=claim['task_id'], returned=returned_ref,
                                 reason=str(error), original_raw_retained=True))
            continue
        decoded = processor.tokenizer.decode(result['output_token_ids'], skip_special_tokens=True,
                    clean_up_tokenization_spaces=False)
        require(decoded == result['raw_text'] and result['complete_eos'] is True,
                'Actual old tokenizer IDs/raw/EOS differ')
        grammar.validate_output(result['output_token_ids'], eos)
        rows.append(dict(task_id=claim['task_id'], claim=claim_ref, success=success_ref,
            returned=returned_ref, grammar_replay=dict(valid=True, new_model_calls=0,
                output_token_sha256=stable_key(result['output_token_ids']),
                input_sha256=result['input_sha256'], eos_token_ids=eos)))
    require(rows and excluded, 'Expected audited valid outputs plus the original invalid schema answer')
    # Reserve elapsed calendar since the fixed original anchor conservatively;
    # this is a remaining-budget reduction, not an invented GPU charge.
    elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat('2026-10-23T06:10:00+00:00')).total_seconds()
    reserve = math.ceil(max(elapsed, wrapper['wall_seconds_including_load_decode_failures']))
    manifest = dict(schema='AIC_GROUNDING_GRAMMAR_ADOPTION_V1',
        old_assets=old_ref, old_wrapper=wrapper_ref, new_implementation=args.expected_commit,
        new_grammar_source=ref(Path(__file__).with_name('grounding_grammar.py')),
        rows=rows, excluded=excluded, new_inference_calls=0,
        old_actual_wrapper_wall_seconds=wrapper['wall_seconds_including_load_decode_failures'],
        conservative_prior_reserved_wall_seconds=reserve,
        original_failure_and_costs_not_modified=True)
    manifest_ref = atomic_new(output / 'adoption.json', manifest)
    mapping = strict_load(args.base_mapping)
    mapping['run_root'] = str(Path(args.new_run_root).resolve())
    mapping['inherited_grounding'] = manifest_ref
    mapping['resources']['total_execution_seconds'] -= reserve
    require(mapping['resources']['total_execution_seconds'] > 0, 'No total execution budget remains')
    mapping_ref = atomic_new(output / 'mapping.json', mapping)
    return dict(status='TOKEN_REPLAY_ADOPTION_PREPARED_NO_NEW_MODEL_CALLS', adopted=len(rows),
                excluded=len(excluded), manifest=manifest_ref, mapping=mapping_ref)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('old-assets', 'old-wrapper', 'base-mapping', 'new-run-root', 'output-dir', 'expected-commit'):
        parser.add_argument('--' + name, required=True)
    import json
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == '__main__':
    main()
