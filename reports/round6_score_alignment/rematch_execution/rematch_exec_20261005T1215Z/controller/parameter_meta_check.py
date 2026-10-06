"""Count actual module tensor shapes on meta device; no weights/GPU/quality claim."""
import argparse
import json
from pathlib import Path
import sys

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
sys.path.insert(0,str(RUN/'dense_head'))

if __name__=='__main__':
    from accelerate import init_empty_weights
    from transformers import Qwen3VLConfig,Qwen3VLForConditionalGeneration
    from peft import LoraConfig,get_peft_model
    from dense_time import DenseTimeHead,language_targets,parameter_inventory
    config=Qwen3VLConfig.from_pretrained(str(RUN/'models/Qwen3-VL-8B-Instruct'),local_files_only=True)
    with init_empty_weights():
        base=Qwen3VLForConditionalGeneration(config)
        for p in base.parameters():
            p.requires_grad_(False)
        targets=language_targets(base)
        backbone=get_peft_model(base,LoraConfig(r=16,lora_alpha=32,lora_dropout=0.05,
            target_modules=targets,bias='none',modules_to_save=None,task_type='CAUSAL_LM'))
        head=DenseTimeHead(config.text_config.hidden_size)
    report=parameter_inventory(backbone,head)
    report.update(status='PASS_ACTUAL_MODULE_SHAPES_META_ONLY',model_weights_loaded=False,GPU_used=False,
                  inference_chain_parameter_count_pending_real_load=True,language_projections=len(targets))
    path=RUN/'controller/parameter_meta_check.json'
    with path.open('x') as out:
        json.dump(report,out,indent=2)
    print(json.dumps(report))
