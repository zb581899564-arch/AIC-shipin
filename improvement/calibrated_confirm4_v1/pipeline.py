"""Manual stages only; the caller explicitly launches each admitted GPU job."""
import argparse
import json
import os
from pathlib import Path
import traceback
import uuid

from confirm_common import Run, launch_spec, save

CPU = ('b0_prepare', 'b0_input_qa', 'b0_output_qa', 'verify_prepare', 'verify_input_qa',
       'verify_output_qa', 'context_prepare', 'context_input_qa', 'context_output_qa', 'finalize')
GPU = ('b0_gpu', 'verify_gpu', 'context_gpu')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config')
    parser.add_argument('stage', choices=CPU+GPU+('launch_spec',))
    parser.add_argument('--family', choices=('b0', 'verify', 'context'))
    args = parser.parse_args()
    if args.stage in CPU:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''  # This child only; parent visibility stays intact.
    run = Run(args.config)
    try:
        if args.stage == 'launch_spec':
            if args.family is None:
                parser.error('--family is required for launch_spec')
            print(json.dumps(dict(command=launch_spec(run, args.family)), ensure_ascii=False))
            return
        if args.stage in GPU:
            import inference as stage_module
        elif args.stage.endswith('_output_qa') or args.stage == 'finalize':
            import replay as stage_module
        else:
            import prepare as stage_module
        getattr(stage_module, args.stage)(run)
    except BaseException as error:
        save(run.root/'failures'/(args.stage+'_'+uuid.uuid4().hex+'.json'), dict(stage=args.stage,
             error=repr(error), traceback=traceback.format_exc(), preserve_all_success=True,
             repeat_success_forbidden=True, failed_stage_requires_new_explicit_recovery=True))
        raise


if __name__ == '__main__':
    main()
