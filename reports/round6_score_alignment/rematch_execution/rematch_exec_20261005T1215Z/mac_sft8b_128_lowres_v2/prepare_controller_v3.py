"""New engineering run: same scientific recipe, process-tree ownership correction."""
from pathlib import Path
import shutil
import json
SRC=Path(__file__).resolve().parent
DST=SRC.parent/'mac_sft8b_128_lowres_v3'
DST.mkdir(exist_ok=False);(DST/'controller').mkdir()
lock=json.loads((SRC/'source_lock.json').read_text())
for name in lock['files']:
    target=DST/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SRC/name,target)
path=DST/'finish_mac.py';text=path.read_text()
start=text.index('def active_external(');end=text.index('\ndef resources(',start)
text=text[:start]+'''def classify_external(output,owned_roots):
    table={}
    for line in output.splitlines():
        fields=line.strip().split(None,2)
        if len(fields)==3:table[int(fields[0])]=(int(fields[1]),fields[2])
    owned=set(owned_roots)
    while True:
        children={pid for pid,(ppid,_) in table.items() if ppid in owned}
        if children<=owned:break
        owned.update(children)
    found=[]
    for pid,(ppid,command) in table.items():
        if pid in owned or str(HERE) in command:continue
        executable=command.split()[0].lower()
        probable_compute=('python' in executable or 'ollama' in executable or 'llama-server' in executable or
                          'mlx_lm' in command or 'mlx_vlm' in command or 'torchrun' in command)
        if probable_compute and not executable.startswith('/system/'):
            found.append(dict(pid=pid,ppid=ppid,command=command[:1000]))
    return found

def active_external(exclude=()):
    output=subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,command='],text=True)
    return classify_external(output,{os.getpid(),*exclude})
''' +text[end:]
text=text.replace("stopped_owned_child_reason=reason,resources_before=resources_before)",
 "stopped_owned_child_reason=reason,resources_before=resources_before,resources_last=current)")
path.write_text(text)
protocol=DST/'PROTOCOL.md'
protocol.write_text(protocol.read_text()+'''

## 控制器工程修正 v3

v2 首次启动15:15:34，在15.434秒后被自身外部计算守卫停止，exit -15、0 backward/0 update，未到 forward，因此不表示128帧低分辨率再次OOM。旧守卫只按命令行路径排除主训练进程，未排除其Python辅助后代；日志出现 multiprocessing.resource_tracker 清理警告。新v3以正在执行的控制器PID为根，按ps的PPID闭包识别本任务子孙，外部独立Python仍拒绝；控制器失败receipt保留最后资源快照。以合成多层进程树验证辅助后代排除与独立进程拒绝。保持同一科学输入/训练参数，重新冷启动独立probe/full目录，不回写v2源码锁或失败日志。
''')
(DST/'test_process_ownership.py').write_text('''import unittest
from finish_mac import classify_external
class Ownership(unittest.TestCase):
    def test_owned_descendants_and_external_compute(self):
        processes="10 1 python controller\\n11 10 python trainer\\n12 11 python -c resource_tracker\\n13 12 python helper\\n20 1 python external_train\\n21 1 ollama serve\\n30 1 /usr/bin/ssh\\n"
        self.assertEqual({x['pid'] for x in classify_external(processes,{10})},{20,21})
    def test_detached_external_helper_still_blocks(self):
        self.assertEqual(classify_external("12 1 python -c resource_tracker",{10})[0]['pid'],12)
if __name__=='__main__':unittest.main()
''')
print(str(DST))
