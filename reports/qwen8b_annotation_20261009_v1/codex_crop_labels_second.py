"""Second source directly annotated after all 12 original PNGs were viewed in this turn."""
from spatial_prepare import ROOT,load,save,validate
sid='JgHubY5Vw3Y'
choices=[
('自行车店内男女两名主持人正面站立。',None,'两名同等重要的主持人横向分开，无法在一个竖框同时保留。'),
('街道路面、前方车辆和骑行视角的白色道路标记。',[222,4,198,352],'保留道路前进方向和路面标记，不以左侧车辆为主角。'),
('店内两名主持人相互看向对方。',None,'对话双方横向分开，竖框会丢失其中一方。'),
('黑底quick release文字与红色禁止标志。',None,'完整字幕与禁止标志横向过宽，竖框会改变文字含义。'),
('手在自行车前轮轴附近操作快拆杆。',[214,4,198,352],'保留操作手的主要可见区域和车轴快拆杆，舍弃外侧轮圈及前臂。'),
('黑底bike camo片头文字。',None,'完整标题横向过宽，不用只保留半个词的竖框。'),
('男子在店内侧脸讲解，背景为彩色轮圈。',[324,4,198,352],'保留男子头脸、耳朵和肩颈，舍弃多数轮圈背景。'),
('黑底locks片头文字。',None,'完整文字横向过宽，竖框会截断字母。'),
('双手在自行车后轮附近操作车锁与钥匙。',None,'双手和锁具关键接触区域横向过宽，不声明完整动作已被竖框保留。'),
('男子在店内侧脸讲话，背景有黄色轮圈。',[324,4,198,352],'保留头脸及肩颈，不以背景轮圈作为主体。'),
('两名主持人相互交流，手势位于两人之间。',None,'双方脸部和交流手势无法同时装入合法竖框。'),
('PURE FIX TV及两行社交账号结尾字幕。',None,'完整品牌和账号信息横向过宽，裁掉部分文字会丢失内容。')]
m=load(ROOT/'input'/sid/'manifest.json');dest=ROOT/'raw/codex_crop'/sid/'draft_01.json';assert not dest.exists()
rows=[]
for f,(caption,box,reason) in zip(m['frames'],choices):
    rows.append(dict(sample_index=f['sample_index'],frame_index=f['frame_index'],pts_seconds=f['pts_seconds'],observed_file=f['file'],visible_content=caption,focus_bounds_xyxy=None,
        crops=[dict(targetRatioWH=[16,9],state='CROP',box_xyw=[0,0,640,360],reason='完整原图保持16:9，不新增裁断。'),
               dict(targetRatioWH=[9,16],state='CROP' if box else 'UNKNOWN',box_xyw=box,reason=reason)]))
save(dest,dict(source_id=sid,annotator_ui='Codex current conversation direct visual annotation',observed_files=[f['file'] for f in m['frames']],frames=rows,
    observation_method='All 12 original 640x360 PNGs displayed via view_image with original detail in this turn',quality_reference='MODEL_ANNOTATION_NOT_HUMAN_GOLD',actual_crops_not_yet_reviewed=True))
validate(sid,dest);print(str(dest))
