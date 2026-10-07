"""Persist every returned recovery response before accepting or rejecting it."""
from common import *


def record_and_validate(out, video_id, index, result):
    require(isinstance(video_id,str) and video_id.isdecimal() and type(index) is int and index>=0,
            'invalid recovery response identity')
    path=Path(out)/'recovered_raw'/(video_id+'_'+str(index)+'.json')
    write(path,dict(status='RAW_REAL_RECOVERY_OUTPUT_BEFORE_VALIDITY_GUARD',utc=utc(),
        video_id=video_id,index=index,actual_model_response=result,failure_to_empty_conversions=0))
    require(result['output_valid'] is True,'real recovery generation failed; saved raw, never convert to empty')
    return path
