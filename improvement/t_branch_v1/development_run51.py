"""Explicit execution-path adapter; scientific48 functions and gates unchanged."""
import importlib
from pathlib import Path
import sys

from t_io import ROOT

STAGES = dict(prepare='development_prepare48', coarse='development_coarse48',
    verify_prepare='development_verify_prepare48', verify='development_verify48', review='development_review48')
TRAINING = ROOT / 'joint_continue50/completion.json'


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in STAGES:
        raise ValueError('One explicit registered development stage is required')
    module = importlib.import_module(STAGES[sys.argv[1]])
    module.OUT = ROOT / 'development51'
    if sys.argv[1] == 'coarse':
        from frozen_branch46 import final_actor

        def bound_final_actor(model, old_requested_path):
            if Path(old_requested_path) != ROOT / 'joint_remaining47/completion.json':
                raise ValueError('Unexpected legacy training dependency; never look for latest')
            return final_actor(model, TRAINING)

        module.final_actor = bound_final_actor
    module.main()


if __name__ == '__main__':
    main()
