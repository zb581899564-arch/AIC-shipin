"""Contract tests for shared 8B pipeline and sequential decoding rejection."""
from runtime import *
import types

def main():
    import numpy as np
    from constrained_json import BoundedSegmentsGrammar
    results=[]
    def check(name,condition):
        require(condition,name);results.append(dict(name=name,passed=True))
    from lowres import clip_plan,MAX_PIXELS,MAX_SEQUENCE
    check('Mac lowres budget fixed',MAX_PIXELS==32768 and MAX_SEQUENCE==6144)
    plan=clip_plan(dict(fps_num=30,fps_den=1,n_frames=900,clip_start_sec=0,clip_end_sec=30))
    check('64 source ordinals retain endpoints',len(plan['absolute_indices'])==64 and plan['absolute_indices'][0]==0 and plan['absolute_indices'][-1]==899)
    grammar=BoundedSegmentsGrammar(1)
    check('bounded positive sorted interval',grammar.complete('{"segments":[[0,1]]}'))
    check('end beyond source rejected',not grammar.complete('{"segments":[[0,1.0001]]}'))
    check('no empty fallback',not grammar.complete('{"segments":[]}'))
    check('overlap rejected',not grammar.complete('{"segments":[[0,0.8],[0.2,1]]}'))
    check('six segments rejected',not grammar.complete('{"segments":[[0,0.1],[0.1,0.2],[0.2,0.3],[0.3,0.4],[0.4,0.5],[0.5,0.6]]}'))
    frames=[np.full((4,6,3),i,dtype=np.uint8) for i in range(6)]
    class Cap:
        def __init__(self,*_):self.next=0;self.seek_called=False
        def isOpened(self):return True
        def read(self):
            if self.next>=len(frames):return False,None
            frame=frames[self.next];self.next+=1;return True,frame
        def set(self,*_):raise AssertionError('random seek forbidden')
        def release(self):pass
    old=sys.modules.get('cv2');sys.modules['cv2']=types.SimpleNamespace(VideoCapture=Cap)
    try:
        item=dict(n_frames=6,height=4,width=6,source_path='synthetic')
        reader=OrdinalReader(item,dict(branch='CFR_LEGACY'))
        frame,pixel=reader.get(3)
        check('gap consumed from ordinal zero',np.array_equal(frame,frames[3]) and reader.next==4)
        expected=hashlib.sha256(memoryview(frames[5]).cast('B')).hexdigest()
        frame,pixel=reader.get(5,expected)
        check('same-frame expected SHA enforced',pixel==expected)
        backward=False
        try:reader.get(4)
        except RuntimeError:backward=True
        check('backward ordinal rejected',backward)
        mismatch=False
        try:reader.get(5,'0'*64)
        except RuntimeError:mismatch=True
        check('pixel mismatch rejected',mismatch)
        reader.close()
    finally:
        if old is not None:sys.modules['cv2']=old
        else:sys.modules.pop('cv2',None)
    # Verify unchanged strict contracts with their own established CPU suite.
    import subprocess
    report=HERE/'original_contract_cpu_01.json'
    import os
    env=dict(os.environ,PYTHONPATH=str(CODE)+os.pathsep+str(CODE/'vendor'))
    subprocess.run([sys.executable,'-B',str(HERE/'cpu_reference/test_contract_cpu.py'),'--output',str(report)],check=True,env=env)
    check('unchanged PTS/frame/strict serialization regression',read(report).get('status','').startswith('PASS'))
    write(HERE/'cpu_contract_01.json',dict(status='PASS_CPU_CONTRACT',cases=len(results),results=results,
        original_contract_sha256=sha(report),test_sha256=sha(__file__),test_media_read=False,models_loaded=False))
    print(json.dumps(dict(status='PASS_CPU_CONTRACT',cases=len(results))))

if __name__=='__main__':main()
