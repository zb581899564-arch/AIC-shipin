"""Persist labels directly chosen by Codex after viewing all 12 original images."""
from spatial_prepare import ROOT,load,save,validate
sid='PJrm840pAUI'
choices=[
('山谷中横穿坡面的公路、溪流和砾石河床。',[226,4,198,352],'选择公路与河谷交汇的中段，保留上下环境；横向山坡两端舍弃。'),
('运动模糊的人群，近处紫衣人物侧头，前景遮挡。',None,'手臂和动作模糊且被遮挡，无法确认竖框能完整保留关键动作。'),
('车窗前戴入耳耳机的侧脸人物。',[87,4,198,352],'保留主要面部轮廓、耳朵耳机和颈肩；车窗与后侧头发环境舍弃。'),
('广场中背包蓝衣人物转身，手在身前握持物体。',[243,4,198,352],'保留蓝衣人物头脸、身前双手和所持物体，舍弃大部分广场和旁人。'),
('石墙前两人互动，黑衣人物抬手，左侧人物侧脸在原图边缘。',[252,4,198,352],'选择黑衣人物面部与抬起的手，左侧人物脸不作为本竖框主体。'),
('彩色房屋和涂鸦墙下的街道人群。',[295,4,198,352],'选择彩色立面与墙下街道，保留垂直建筑层次，舍弃两侧街区。'),
('栏杆外海面和远处船只，大片天空。',[438,4,198,352],'保留右侧较明显船只、海平线与栏杆前景，舍弃左侧海面。'),
('桥墩下白浪拍击支柱，右侧高光海面。',[126,4,198,352],'保留支柱与白浪接触区域，舍弃桥墩横向延伸和右侧高光。'),
('沙地上人物双腿分开，身体倒置，周围有人围观。',None,'双腿及支撑动作横向跨度超过合法竖框，不能同时保留关键支点和两侧腿脚。'),
('橙衣人物面向镜头，手中举着小型摄像机。',[306,4,198,352],'保留脸、举机手和摄像机，舍弃旁人及多数街道背景。'),
('床上人物双手握相机，脸与相机分列左右。',None,'完整头脸和手持相机的横向跨度超过198像素，竖框会新增截断关键物体或头部。'),
('涂鸦墙上下两排合影人群，整体曝光较暗。',None,'群像无明确唯一主角，竖框会丢失多数合影人物，不生成可训练的合格框。')]
m=load(ROOT/'input'/sid/'manifest.json');dest=ROOT/'raw/codex_crop'/sid/'draft_01.json'
if dest.exists():raise SystemExit('Successful raw label already exists; no overwrite')
frames=[]
for f,(caption,box,reason) in zip(m['frames'],choices):
    frames.append(dict(sample_index=f['sample_index'],frame_index=f['frame_index'],pts_seconds=f['pts_seconds'],observed_file=f['file'],visible_content=caption,focus_bounds_xyxy=None,
        crops=[dict(targetRatioWH=[16,9],state='CROP',box_xyw=[0,0,640,360],reason='原图为16:9，完整保留主要可见主体及上下文。'),
               dict(targetRatioWH=[9,16],state='CROP' if box else 'UNKNOWN',box_xyw=box,reason=reason)]))
doc=dict(source_id=sid,annotator_ui='Codex current conversation direct visual annotation',observed_files=[f['file'] for f in m['frames']],
    observation_method='All 12 original 640x360 PNGs displayed via view_image with original detail in this turn',frames=frames,
    quality_reference='MODEL_ANNOTATION_NOT_HUMAN_GOLD',actual_crops_not_yet_reviewed=True)
save(dest,doc);validate(sid,dest);print(str(dest))
