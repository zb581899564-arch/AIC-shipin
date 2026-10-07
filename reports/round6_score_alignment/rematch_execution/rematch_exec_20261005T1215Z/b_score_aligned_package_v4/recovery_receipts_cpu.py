"""An invalid returned answer must remain intact after the validity gate rejects it."""
from common import *
import tempfile


def main():
    from recovery_receipts import record_and_validate
    tests=0
    with tempfile.TemporaryDirectory(prefix='b2_raw_gate_',dir=RUN/'controller') as directory:
        out=Path(directory)
        failed=dict(output_valid=False,status='PARSE_FAILURE',raw_output='{"segments":[[0.11,0.12]]}',
            parsed_segments=None,parse_errors=['nonempty segment contains no actual source frame'])
        try:
            record_and_validate(out,'97',0,failed)
        except ValueError:
            require(read(out/'recovered_raw/97_0.json')['actual_model_response']==failed,
                    'original rejected response was lost or altered')
            tests+=1
        else:
            raise ValueError('rejected response became accepted')
        success=dict(output_valid=True,status='MODEL_OK',raw_output='{"segments":[[0,1]]}',parsed_segments=[[0,1]])
        path=record_and_validate(out,'97',1,success)
        require(read(path)['actual_model_response']==success,'successful raw response changed');tests+=1
        original=path.read_bytes()
        try:
            record_and_validate(out,'97',1,success)
        except FileExistsError:
            require(path.read_bytes()==original,'prior response overwritten');tests+=1
        else:
            raise ValueError('prior success response overwritten')
    write(HERE/'recovery_receipts_acceptance.json',dict(status='PASS_RECOVERY_RAW_BEFORE_GUARD_CPU',tests=tests,
        rejected_original_response_preserved=True,failed_response_not_accepted=True,prior_success_not_overwritten=True,
        synthetic_only=True,actual_GPU_calls=0,actual_previous_sources_or_outputs_changed=False))
    print('PASS_RECOVERY_RAW_BEFORE_GUARD_CPU')


if __name__=='__main__':
    main()
