"""Single background launch; computation and outputs stay on Linux."""
import json
import os
import socket
import subprocess

import diagnostic as d

d.c.require(socket.gethostname() == 'inspur-NP5570M5', 'unexpected diagnostic launch host')
d.c.require(not (d.HERE / 'start_receipt.json').exists() and not (d.HERE / 'registration.json').exists()
            and not (d.HERE / 'completion.json').exists(), 'prior attempt preserved; do not relaunch')
manifest, _, _ = d.verify()
cpu = d.c.read(d.HERE / 'cpu_acceptance.json')
d.c.require(cpu['status'] == 'PASS_CONTEXT_DIAGNOSTIC_CPU' and cpu['actual_pinned_grammar_examples'] == 10,
            'actual diagnostic grammar CPU gate missing')
for name, digest in cpu['source_sha256'].items():
    d.c.require(d.c.sha(d.HERE / name) == digest, 'tested diagnostic source changed')
command = [str(d.c.PY), '-B', str(d.RUN / 'resource_unlimited_v1_20261007/gpu_run.py'),
           '--name', 'rematch_CONTEXT_DIAG_v1', '--max-seconds', str(manifest['job_wall_max_sec']),
           '--planned-output-bytes', str(manifest['predicted_incremental_output_bytes']),
           '--capacity-reason', 'four actual paired teacher requests plus two sequential source overviews; measured original HTTP bytes',
           '--queue-seconds', str(manifest['queue_max_sec']), '--', str(d.c.PY), '-B', str(d.HERE / 'diagnostic.py')]
receipt = {'status': 'REGISTERED_CONTEXT_DIAGNOSTIC_LAUNCH', 'utc': d.c.utc(), 'command': command,
           'source_lock_sha256': d.c.sha(d.HERE / 'source_lock.json'), 'automatic_return': False,
           'student_training_admitted': False}
d.c.write(d.HERE / 'start_receipt.json', receipt, fresh=True)
with (d.HERE / 'launcher.log').open('x') as log:
    process = subprocess.Popen(command, cwd=d.HERE, stdin=subprocess.DEVNULL, stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1'))
receipt.update(pid=process.pid, status='LAUNCHED_CONTEXT_DIAGNOSTIC_PENDING_REAL_ACCEPTANCE')
d.c.write(d.HERE / 'start_receipt.json', receipt)
print(json.dumps(receipt))
