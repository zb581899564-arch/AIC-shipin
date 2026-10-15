"""One preregistered native-preparation cohort, with original preordered reserves."""
import json
from pathlib import Path

from deploy_direct_media_05 import REPORT, TEMP, deploy, fresh_host_snapshot
from stage_common_04 import sha, utc


def main():
    if (REPORT/'direct_cohort_registration_06.json').exists():
        raise ValueError('Cohort registered already; inspect its sole chain, do not relaunch')
    fresh_host_snapshot('direct_cohort_host_resources_06.json')
    inventory=json.loads((TEMP/'raw_registered_pool_inventory_06.json').read_text())
    routes=json.loads((TEMP/'raw_registered_pool_routes_06.json').read_text())
    files={}
    route_path=REPORT/'direct_pool_routes_06.json'
    route_path.write_text(json.dumps(routes,indent=2),encoding='utf-8')
    inventory_path=REPORT/'direct_pool_inventory_06.json'
    inventory_path.write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    files[route_path.name]=route_path;files[inventory_path.name]=inventory_path
    for name in ('prepare_direct_cohort_06.py','prepare_media_batch_06.py'):
        files['code/'+name]=Path(__file__).parent/name
    required={name:sha(path) for name,path in files.items()}
    for name in ('stage_common_04.py','native_profile_01.py','native_profile_04.py','download_direct_media_05.py'):
        required['code/'+name]=sha(Path(__file__).parent/name)
    for name in ('direct_source_scope_05.json','effective20_source_registration_05.json','known_source_exclusions_01.json',
                 'FOLLOWUP_PROTOCOL_02.md','NATIVE_MAPPING_CONTRACT_03.md','PROFILE_SCOPE_ADDENDUM_03.md'):
        required[name]=sha(REPORT/name)
    required.update({'metadata_02/source_registration_01.json':sha(REPORT/'metadata_export_01/metadata_02/source_registration_01.json'),
                     'metadata_03/selected_human_references_01.json':sha(REPORT/'metadata_export_01/metadata_03/selected_human_references_01.json'),
                     'metadata_02/val_videoxum.json':'2832f423ff5fd768a979665e30345a56f1723aacc1821986b5ec042bed30f556'})
    reg=dict(status='REGISTERED_INDEPENDENT_EFFECTIVE20_CPU_NATIVE_COHORT_RECOVERY_BEFORE_FIRST_MODEL_RESULT',utc=utc(),
        output_directory='direct_cohort_06',routes_path=route_path.name,required_files=required,
        original_source_registration_unchanged=True,original_05_planned_replacements_preserved=True,
        only_preordered_original_reserves_for_actual_availability_native_origin_endpoint_failure=True,
        known_actual_native_failures={'v_cy-RLevyo_8':{
            'failure_path':'direct_cpu_probe_05/failure.json','diagnostic_path':'direct_actual_clock_diagnostic_05.json',
            'physical_end_exact':'853/6','original_manual_end_exact':'142.33',
            'complete_clock_retained_do_not_decode_again':True}},
        maximum_accessible_candidate_pool_sources=len(routes),maximum_pool_video_payload_bytes=sum(r['bytes'] for r in routes),
        source_download_route='Public publisher CDN directly to Linux, continuing user exception; no Windows media relay or Mac',
        scientific_gates_unchanged=True,screen=12,confirm=8,candidate='L16',reference='D8_USER_REPORTED40.44',
        native_frames=64,maximum_window_seconds=30,min_pixels=131072,max_pixels=131072,max_input_tokens=16384,
        model_params_b='8.78245912',source_selection_uses_predictions_or_quality_scores=False,
        success_stage_retries=False,new_model_calls=0,new_optimizer_updates=0,GPU_launch_admitted=False)
    reg_path=REPORT/'direct_cohort_registration_06.json'
    reg_path.write_text(json.dumps(reg,ensure_ascii=False,indent=2),encoding='utf-8')
    files[reg_path.name]=reg_path
    receipt=deploy(files,'direct_cohort_launch_06','code/prepare_direct_cohort_06.py',reg_path.name)
    print(json.dumps({'control_bytes':receipt['transfer']['bytes'],'maximum_pool_bytes':reg['maximum_pool_video_payload_bytes'],
                      'target_sources':20,'new_model_calls':0,'launch':receipt['launch']}))


if __name__=='__main__':
    main()
