"""Numeric metadata only: no image export, model or GPU use."""
import json
from pathlib import Path
import subprocess

RUN=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
if __name__=='__main__':
    manifest=json.loads((RUN/'baseline_a/m0_finalize_01/clean_manifest_426.json').read_text())
    row=next(r for r in manifest['records'] if r['video_id']=='18')
    output=json.loads(subprocess.check_output(['/home/inspur/anaconda3/envs/Andy/bin/ffprobe',
        '-v','error','-select_streams','v:0','-show_entries',
        'stream=start_time,time_base,avg_frame_rate,r_frame_rate,nb_frames,duration',
        '-of','json',row['source_path']],text=True))
    import decord
    reader=decord.VideoReader(row['source_path'],ctx=decord.cpu(0),num_threads=1)
    indices=[0,1,2,len(reader)-1]
    stamps=reader.get_frame_timestamp(indices)
    if hasattr(stamps,'asnumpy'):
        stamps=stamps.asnumpy()
    report={'video_id':'18','source_sha256':row['source_sha256'],'ffprobe':output,
        'decord':{'version':decord.__version__,'count':len(reader),'avg_fps':reader.get_avg_fps(),
                  'indices':indices,'frame_timestamps':stamps.tolist()},
        'images_exported_or_displayed':False,'models_run':False,'gpu_used':False}
    path=RUN/'controller/source18_numeric_time_origin.json'
    with path.open('x') as handle:
        json.dump(report,handle,indent=2)
        handle.write('\n')
    print(json.dumps(report))
