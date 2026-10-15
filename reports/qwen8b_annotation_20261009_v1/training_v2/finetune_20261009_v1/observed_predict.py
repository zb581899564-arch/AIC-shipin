"""Same fixed generation inputs; matched base comparison disables only the adapter."""
import argparse
import runpy
import sys
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--base-comparison',action='store_true')
a,remaining=p.parse_known_args()
if a.base_comparison:
    import peft
    original=peft.PeftModel.from_pretrained
    def load(*args,**kwargs):
        model=original(*args,**kwargs)
        generate=model.generate
        def disabled_generate(*values,**options):
            with model.disable_adapter():
                return generate(*values,**options)
        model.generate=disabled_generate
        return model
    peft.PeftModel.from_pretrained=load
root=Path(remaining[remaining.index('--dataset-root')+1])
sys.path.insert(0,str(root/'training_v2'))
sys.argv=[str(root/'training_v2/predict_rows.py')]+remaining
runpy.run_path(sys.argv[0],run_name='__main__')
