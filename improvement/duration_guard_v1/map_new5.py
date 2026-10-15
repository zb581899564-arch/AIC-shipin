"""Each initial reserved source gets one new complete native clock measurement."""
import json
import os
import socket
from fractions import Fraction as F
from pathlib import Path
from new5_common import BASE, MEDIA, SOURCE_COUNT, read, sha, save, identity, check_download_admission
from native_mapping_v3 import validate_mapping
from native_window_plan import plan_windows
from measured_clock_original import measured_clock

OUT = BASE/'mapping_01'


def main():
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('Unexpected host')
    reg_path = BASE/'new5_source_registration_01.json'
    registration, downloaded, _ = check_download_admission(reg_path)
    bindings = dict(registration_sha256=sha(reg_path), mapping_contract_sha256=sha(BASE/'NATIVE_MAPPING_CONTRACT_V3.md'),
        mapper_sha256=sha(__file__), measured_clock_sha256=sha(Path(__file__).with_name('measured_clock_original.py')),
        mapping_validator_sha256=sha(Path(__file__).with_name('native_mapping_v3.py')),
        window_planner_sha256=sha(Path(__file__).with_name('native_window_plan.py')),
        media_completion_sha256=sha(MEDIA/'completion.json'), source_isolation_sha256=sha(BASE/'source_isolation_acceptance.json'))
    OUT.mkdir(exist_ok=False)
    save(OUT/'launch_claim.json', dict(bindings=bindings, pid=os.getpid(), new_model_calls=0))
    import av
    rows, source = [], None
    try:
        for row in registration['rows']:
            source = row['source_name']
            actual = identity(MEDIA/(source+'.webm'))
            if actual != downloaded[source]['identity']:
                raise ValueError('Actual original media bytes changed')
            with av.open(str(MEDIA/(source+'.webm'))) as container:
                if len(container.streams.video) != 1:
                    raise ValueError('Ambiguous original video stream')
                clock = measured_clock(row, actual, container, container.streams.video[0], av)
            measured_path = OUT/(source+'.observed_clock.json')
            save(measured_path, clock)
            mapped = validate_mapping(row, clock)
            windows = plan_windows(clock)
            path = OUT/(source+'.mapping_bundle.json')
            save(path, dict(status='PASS_ONE_ORIGINAL_NATIVE_MAPPING_AND_WINDOW_PLAN',bindings=bindings,
                clock=clock,mapping=mapped,windows=windows,decode_provenance=dict(kind='NEW_ORIGINAL_COMPLETE_DECODE',
                path=str(measured_path),sha256=sha(measured_path),new_decode=True),new_model_calls=0,new_optimizer_updates=0))
            rows.append(dict(source_name=source,source_group=row['source_group'],bundle_path=str(path),
                bundle_sha256=sha(path),native_frames=clock['n_frames'],windows=len(windows),new_decode=True))
            temporary = OUT/'progress.json.pending'
            temporary.write_text(json.dumps(dict(completed_sources=len(rows),registered_sources=SOURCE_COUNT,last_source=source)),encoding='utf-8')
            temporary.replace(OUT/'progress.json')
            print(json.dumps(rows[-1]),flush=True)
        save(OUT/'completion.json',dict(status='PASS_FIVE_ORIGINAL_NATIVE_MAPPINGS_NOT_PROCESSOR_OR_SOURCE_ADMISSION',
            sources=SOURCE_COUNT,rows=rows,bindings=bindings,new_complete_decodes=SOURCE_COUNT,inherited_complete_clocks=0,
            new_model_calls=0,new_optimizer_updates=0))
    except BaseException as error:
        save(OUT/'failure.json',dict(status='FAILED_NEW5_NATIVE_MAPPING_KEEP_ALL_MEASUREMENTS',source_name=source,
            error=repr(error),successful_bundles_retained=rows,new_model_calls=0))
        raise


if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES']=''
    main()
