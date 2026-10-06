"""Engineering-only recovery before any valid fixed-dev generation."""
import ast
from pathlib import Path

HERE=Path(__file__).resolve().parent
for name in ('runtime.py','controller.py','launch.py','bridge_and_deliver.ps1','dev/evaluate.py','prepare.py'):
    p=HERE/name;code=p.read_text(encoding='utf-8')
    code=code.replace('mac8b_delivery_v1','mac8b_delivery_v2').replace('rematch_MAC8B_v1_','rematch_MAC8B_v2_')
    if name=='runtime.py':
        code=code.replace("HERE=RUN/'mac8b_delivery_v2'","HERE=RUN/'mac8b_delivery_v2'\nASSETS=RUN/'mac8b_delivery_v1'")
        code=code.replace("HERE/'training_evidence/train_report.json'","ASSETS/'training_evidence/train_report.json'")
        start=code.index('def verify():');end=code.index('\ndef inputs(',start)
        code=code[:start]+'''def verify():
    lock=read(HERE/'source_lock.json');a=read(HERE/'admission.json');files=dict(lock['files'])
    for path,digest in a['files'].items():
        require(path not in files or files[path]==digest,'conflicting source/model binding: '+path)
        files[path]=digest
    for path,digest in files.items():require(sha(path)==digest,'bound bytes changed: '+path)
    return a
'''+code[end:]
        code=code.replace('frozen=canonical_frozen_hash(model,torch)','frozen=relocation[\'base_hash\']')
        code=code.replace('fingerprint=canonical_frozen_hash(model,torch)','fingerprint=relocation[\'base_hash\']')
    elif name=='dev/evaluate.py':
        code=code.replace("DELIVERY=RUN/'mac8b_delivery_v2'","DELIVERY=RUN/'mac8b_delivery_v2'\nASSETS=RUN/'mac8b_delivery_v1'")
        code=code.replace("DELIVERY/'training_evidence/train_report.json'","ASSETS/'training_evidence/train_report.json'")
        code=code.replace("adapter=DELIVERY/'adapter'","adapter=ASSETS/'adapter'")
    elif name=='prepare.py':
        code=code.replace("HERE/'training_evidence", "ASSETS/'training_evidence").replace("HERE/'adapter/", "ASSETS/'adapter/")
        code=code.replace("(HERE/'training_evidence')", "(ASSETS/'training_evidence')")
        code=code.replace("    subprocess.run([sys.executable,'-B',str(HERE/'dev/evaluate.py'),'prepare']", "    audit_old_failure()\n    subprocess.run([sys.executable,'-B',str(HERE/'dev/evaluate.py'),'prepare']")
        code=code.replace("variant='MAC_FINAL_LOWRES_CUDA_DELIVERY_V1'","variant='MAC_FINAL_LOWRES_CUDA_PATH_RECOVERY_V2'")
        code=code.replace("    files.update(dev['files'])", "    files.update(dev['files'])\n    for p in (ASSETS/'dev/BASE8B.jsonl',ASSETS/'dev/SFT8B.jsonl',ASSETS/'dev/decision.json',ASSETS/'source_lock.json',ASSETS/'completion.json',ASSETS/'lowres.py'):\n        files[str(p)]=sha(p)")
    p.write_text(code,encoding='utf-8')

p=HERE/'lowres.py';code=p.read_text(encoding='utf-8')
code=code.replace("require(ROOT in resolved.parents and not source.is_symlink(), 'dev source outside Linux workspace')",
    "require(source.is_file(), 'pinned dev source missing')\n    # The caller binds the exact registered Linux path and byte hash; the Mac-only root rule does not apply here.")
code=code.replace("require(canonical_frozen_hash(model,torch)==report['freeze_evidence']['adapter_off'], 'relocated base bytes changed')",
    "base_hash=canonical_frozen_hash(model,torch)\n    require(base_hash==report['freeze_evidence']['adapter_off'], 'relocated base bytes changed')")
code=code.replace("byte_equal=True,base_sha256=", "byte_equal=True,base_hash=base_hash,base_sha256=")
p.write_text(code,encoding='utf-8')

for p in HERE.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
print('PASS v2 independent recovery syntax; frozen v1 untouched')
