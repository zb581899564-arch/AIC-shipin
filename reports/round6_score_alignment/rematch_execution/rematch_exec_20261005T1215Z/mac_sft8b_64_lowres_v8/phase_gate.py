"""Pure acceptance gate: only complete, byte-frozen, finite updates may continue."""
import math
from sft_contract import require,BASE_PARAMS,LORA_PARAMS,TOTAL_PARAMS

def validate_finished_phase(report,phase):
    require(phase in ('probe','full'),'unknown acceptance phase')
    expected='PASS_MAC_8B_64_PROBE' if phase=='probe' else 'PASS_MAC_FULL_INTERVAL_SFT_TRAINING_ENGINEERING'
    require(report['status']==expected and report['base_frozen'] and report['vision_frozen'] and
            report['adapter_reload_succeeded'] and report['loss_finite'],'Mac phase evidence did not pass')
    require(report['effective_batches']==(48 if phase=='probe' else 3620) and
            report['optimizer_steps']==(3 if phase=='probe' else 227),'Mac exposure count incomplete')
    require(report['parameter_inventory']==dict(base=BASE_PARAMS,lora=LORA_PARAMS,total=TOTAL_PARAMS),
            'actual parameter inventory changed')
    frozen=report['freeze_evidence'];before=frozen['before_training']
    require(before['parameters']==BASE_PARAMS and all(frozen[name]==before for name in
        ('after_training','after_reload','adapter_off')),'complete frozen parameter bytes differ')
    require(len(report['updates'])==report['optimizer_steps'],'update receipt missing')
    for index,update in enumerate(report['updates'],1):
        require(update['optimizer_step']==index and math.isfinite(update['mean_loss']) and
                math.isfinite(update['gradient_norm']) and update['gradient_norm']>0 and
                update['changed_lora_tensors']>0,'missing/nonfinite/unchanged optimizer update')
        for family,item in update['lora_gradient_evidence'].items():
            require(family in ('lora_A','lora_B') and item['tensors']==item['connected']==item['finite']==144,
                    'actual language LoRA gradient connection incomplete')
    require(math.isfinite(report['wall_seconds']) and report['wall_seconds']>0,'invalid measured run cost')
    if phase=='probe':
        require(math.isfinite(report['peak_memory_allocated_mib']) and report['peak_memory_allocated_mib']>0 and
                report['peak_memory_allocated_mib']*2**20<=report['mps_recommended_max_memory_bytes'],
                'measured probe working set is outside the live recommended MPS capacity')
    return report
