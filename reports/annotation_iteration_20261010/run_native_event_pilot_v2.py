"""Independent transport retry after zero-token eligibility EOF; no raw overwrite."""
from pathlib import Path
import os

HERE=Path(__file__).resolve().parent
source=(HERE/'run_native_event_pilot.py').read_text(encoding='utf-8')
replacements={
    "folder=Path(d);out=folder/'teacher_proposal.json'":"media=Path(d);folder=media/'attempt02_proxy';folder.mkdir(exist_ok=True);out=folder/'teacher_proposal.json'",
    "m=json.loads((folder/'manifest.json').read_text())":"m=json.loads((media/'manifest.json').read_text())",
    "(folder/'manifest.json').as_posix()":"(media/'manifest.json').as_posix()",
    "HERE/'teacher_completion.json'":"HERE/'teacher_completion_v2.json'",
    "HERE/'teacher_controller_failure.txt'":"HERE/'teacher_controller_failure_v2.txt'",
}
for old,new in replacements.items():
    assert source.count(old)==1,(old,source.count(old))
    source=source.replace(old,new)
# Only this child process and its descendants use the existing local listener.
# No registry, service, node, routing, TLS validation, or global env modification.
os.environ['HTTP_PROXY']='http://127.0.0.1:7892'
os.environ['HTTPS_PROXY']='http://127.0.0.1:7892'
exec(compile(source,str(HERE/'run_native_event_pilot.py'),'exec'),dict(__file__=str(HERE/'run_native_event_pilot.py'),__name__='__main__'))
