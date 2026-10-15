"""Prospective bounded engineering recovery under the human continue request."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
old=R/'teacher_dispatch_capacity_v4_authorization.json';classification=R/'teacher_expansion/engineering_alias_remainder_v6_fresh_scope_prefix_v2/actual_CLI35_terminal_classification_v1.json';capacity=R/'root_actual_teacher_capacity_v1.json'
assert json.loads(classification.read_text())['actual_native_reads']==0
assert not list((R/'teacher_expansion').glob('*/call36/request.json'))
assert not list((R/'teacher_expansion').glob('*/call37/request.json'))
v=dict(status='ROOT_PROSPECTIVE_BOUNDED_ENGINEERING_RECOVERY_PREPARATION_ONLY_START_GATE_PENDING',utc=datetime.now(timezone.utc).isoformat(),human_scope_quote='那你继续去做下一步,然后一直做,直到能打包一个比较合理的包为止。',human_authorized_continued_annotation_and_necessary_engineering_repairs=True,human_explicit_numeric37_approval_not_claimed=True,budget_numbers_are_ROOT_prospective_engineering_decision=True,prior_budget=bind(old),prior_cap36_and_frozen_routes_are_historical_unchanged=True,actual_CLI35_REJECT=bind(classification),actual_capacity_evidence=bind(capacity),new_fresh_routes={'36':[19,20],'37':[21,22,23]},new_global_CLI_max=37,new_calls_max=2,timeout_seconds_per_call=7200,core_tools_per_call={'36':202,'37':302},old_unused36_plans_not_relaunched=True,new_independent_directory_and_ROOT_actual_source_input_negative_acceptance_gate_required=True,automatic_retry=False,calls_beyond37_allowed=False,any_precompletion_tool_or_media_or_whitelist_failure_STOP_before37=True,first36_complete_real_evidence_and_natural_terminal_required_before37=True,scientific_fixed_window_count=24,supplement_denominator=21,all_original_64native_16facts_clip8preview_roles_sources_domain_PTS_pixel_geometry_model_KEEP_NO_UNKNOWN_quality_and_SFT_recipe_unchanged=True,no_repeat_of_successful_scientific_media=True,teacher_proposals_are_not_truth_or_training_admission=True,old_raw_failed_costs_STOP_UNKNOWNs_preserved=True,source_upload_permission='STILL_PENDING_SEPARATELY_NO_TRANSFER',GPU_training_or_426_not_authorized_by_this_registration=True,no_new_rental_or_topup=True,cash_cost='UNKNOWN_NOT_ZERO',new_model_calls_by_registration=0,new_optimizer_updates=0,root_registration_source=bind(__file__))
p=R/'teacher_dispatch_capacity_v5_split_recovery_authorization.json'
with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(bind(p),ensure_ascii=False))

