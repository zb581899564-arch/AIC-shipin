"""Primary-agent observations after actually displaying all 64 student images.
Not a blind gold reference, not sent to AGY, not editorial importance labels.
"""
import runner as r

subs={i:None for i in range(64)}
for lo,hi,text in [(0,5,'y personas siempre intentando...'),(6,11,'Abrazarte.'),
    (19,21,'¿Qué hago al respecto?'),(28,30,'simple,'),
    (32,37,'siempre puedes ignorar a esas personas'),(38,39,'y esconderte,'),
    (42,50,'lo más que puedas'),(58,63,'y cuando la puerta esté abierta sal un rato')]:
    for i in range(lo,hi+1):subs[i]=text

def observed_subject(i):
    if i<=5:return '室内挂钟前深色T恤人物的上半身，手部姿态不同'
    if i<=13:return '室内绿色台面上坐着小型犬，旁有木制家具和白色帘布'
    if i<=17:return '室内小型犬头部及胸前近景'
    if i<=30:return '草地背景前的小型犬头部及上半身近景'
    if i<=37:return '室内挂钟前人物的上半身，视线偏向画面左侧'
    if i<=45:return '小型犬位于两片白色遮挡物之间，部分身体被遮挡'
    if i<=50:return '室内小型犬面部近景'
    if i<=55:return '室内挂钟前人物，上半身或侧脸可见'
    if i==56:return '室内墙面挂钟与画面右缘人物身体局部'
    if i==57:return '室内墙面挂钟，人物未在画面内明确可见'
    if i==58:return '低角度门口台阶，远处遮挡细节无法确认具体主体'
    if i==59:return '门口台阶后方可见小型犬头部'
    if i==60:return '门口台阶上小型犬的身体及四肢可见'
    if i==61:return '画面右侧台阶上小型犬身体局部，头部被画面边缘截断'
    return '草地上小型犬的背面及身体，朝画面远处方向'

if __name__=='__main__':
    doc,ss=r.index('student')
    r.save(r.ROOT/'root_student_observed_reference.json',dict(utc=r.utc(),
        evidence='Primary agent actually displayed F36-F39 originals and remaining 60 pixels in full-resolution labelled four-image contact sheets',
        student_index_sha256=ss,role='exposed_source_manual_diagnostic_not_blind_gold',
        reviewed_frame_ids=[x['frame_id'] for x in doc['frames']],
        records=[dict(frame_id=f'F{i:02}',subtitle_text=subs[i],visible_subject=observed_subject(i)) for i in range(64)],
        uncertainty_notes={'F58':'Do not assert a clearly visible dog or its absence from obscured distant details.'},
        shared_with_teacher=False, training_admitted=False))
    print('Recorded 64 actual student-image observations; not SFT.')
