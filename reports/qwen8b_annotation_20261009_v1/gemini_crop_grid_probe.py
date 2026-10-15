"""Compact low-reasoning crop probe using source-bound coordinate grids and fixed legal sizes."""
import json,subprocess,time
from spatial_prepare import ROOT,load,save,sha,validate
from gemini_crop_probe import AGY
SID='PJrm840pAUI';MODEL='gemini-3.8-flash-low';job=ROOT/'raw/gemini_crop'/SID/'attempt_grid_low_01'
job.mkdir(parents=True,exist_ok=True)
assert not any(job.iterdir()),'Existing successful or partial run must not be overwritten'
grid=ROOT/'input_coordinate_grid'/SID/'manifest.json'
task=f'''视频构图标注，仅处理{SID}。原生view_file读{grid.as_posix()}，逐张原生view_file实际查看manifest中12张grid_file PNG。每图仍为原始640x360像素，绿色网格间距40像素，顶部标的是x像素，左侧标的是y像素；定位必须按网格数字，不要按工具展示缩放后的坐标猜测。
不看其他教师回答、MP4、人类评分；不运行终端/脚本/代码、联网、其他模型或子代理，不训练。
只标9:16构图。固定合法尺寸w=198,h=352；你只选择整数x（0..442）和整数y（0..8）。本任务不允许其它宽高。先在网格原图找主角头脸与关键手/物体的位置；选出的[ x,x+198 ]范围要覆盖核心部位。无法同时覆盖就UNKNOWN，x/y均null。群像无明确主角可UNKNOWN。不要选与文字所述主角不同的位置。
只用write_to_file写新文件{(job/'compact_labels.json').as_posix()}，JSON顶层source_id、input_mode="SOURCE_BOUND_COORDINATE_GRID"、observed_grid_files、frames12条。每条仅sample_index、visible_content（15字以内）、state CROP/UNKNOWN、x、y、reason（15字以内）。读失败写failure.json停止，不猜。
这些网格只供教师定位，训练使用原始无网格帧。16:9在本源固定为完整原图，由控制程序根据预先声明的策略生成，不冒充额外教师判断。聊天只报告完成计数。'''
(job/'prompt.txt').write_text(task,encoding='utf-8');before=time.perf_counter()
cmd=[str(AGY),'--model',MODEL,'--mode','accept-edits','--sandbox','--output-format','stream-json','--log-file',str(job/'agy.log'),'-p',task]
with (job/'stream.jsonl').open('wb') as out,(job/'stderr.txt').open('wb') as err:
    process=subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=err,check=False)
save(job/'cli_terminal.json',dict(exit_code=process.returncode,wall_seconds=time.perf_counter()-before))
assert process.returncode==0
es=[json.loads(s) for s in (job/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
init=next(e['init'] for e in es if e.get('event')=='init');final=next(e['result'] for e in reversed(es) if e.get('event')=='result')
assert init['model']==MODEL and final['status']=='SUCCESS'
gm=load(grid);seen=set()
for e in es:
    s=e.get('step_update',{})
    if s.get('state')=='DONE' and s.get('tool_name')=='view_file':
        path=s.get('tool_info',{}).get('parameters',{}).get('AbsolutePath','').replace('\\','/')
        for f in gm['frames']:
            if path==f['grid_file'].replace('\\','/'):seen.add(f['sample_index'])
assert seen==set(range(12))
raw=load(job/'compact_labels.json');assert raw['source_id']==SID and len(raw['frames'])==12
m=load(ROOT/'input'/SID/'manifest.json');rows=[];indices=set()
for r in raw['frames']:
    i=r['sample_index'];assert type(i)==int and i not in indices and 0<=i<12;indices.add(i)
    f=m['frames'][i];derived=gm['frames'][i]
    assert sha(ROOT/'input'/SID/f['file'])==f['png_sha256']==derived['original_png_sha256']
    assert sha(__import__('pathlib').Path(derived['grid_file']))==derived['grid_png_sha256']
    assert r['state'] in ('CROP','UNKNOWN')
    if r['state']=='CROP':
        assert type(r['x'])==int and 0<=r['x']<=442 and type(r['y'])==int and 0<=r['y']<=8
        box=[r['x'],r['y'],198,352]
    else:assert r['x'] is None and r['y'] is None;box=None
    rows.append(dict(sample_index=i,frame_index=f['frame_index'],pts_seconds=f['pts_seconds'],observed_file=f['file'],visible_content=r['visible_content'],focus_bounds_xyxy=None,
        crops=[dict(targetRatioWH=[16,9],state='CROP',box_xyw=[0,0,640,360],reason='预先声明的完整原图策略，非新增教师空间判断。'),
               dict(targetRatioWH=[9,16],state=r['state'],box_xyw=box,reason=r['reason'])]))
assert indices==set(range(12))
save(job/'draft_01.json',dict(source_id=SID,annotator_ui=MODEL+'-coordinate-grid-cli',input_mode='SOURCE_BOUND_COORDINATE_GRID',observed_files=[f['file'] for f in m['frames']],frames=sorted(rows,key=lambda r:r['sample_index']),canonicalization='Original identities from verified manifest; fixed legal box sizes declared before call; teacher x/y used exactly, without clamping or shifting'))
validate(SID,job/'draft_01.json')
receipt=dict(status='PASS_12_SOURCE_BOUND_GRID_READS_AND_LEGAL_EXACT_COORDINATES',source_id=SID,model=MODEL,frames=12,duration_seconds=final['duration_seconds'],usage=final['usage'],
    raw_sha256=sha(job/'compact_labels.json'),canonical_sha256=sha(job/'draft_01.json'),grid_manifest_sha256=sha(grid),actual_crops_visually_reviewed=False)
save(job/'acceptance.json',receipt);print(json.dumps(receipt,ensure_ascii=False),flush=True)
