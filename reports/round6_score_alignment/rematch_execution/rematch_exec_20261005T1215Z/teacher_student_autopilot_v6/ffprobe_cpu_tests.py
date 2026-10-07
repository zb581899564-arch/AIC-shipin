"""Reproduce missing-PATH ffprobe and validate both real metadata consumers."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import controller as c
import teacher_label as teacher

config = c.read(c.HERE / 'config.json')
os.environ['PATH'] = '/nonexistent'
assert shutil.which('ffprobe') is None
binary = Path(config['ffprobe_path'])
assert c.sha(binary) == config['ffprobe_sha256']
subprocess.run([str(binary), '-version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
planned = c.probe_output_estimate(config)
assert planned > 8_000_000
selection = Path(config['selection_dir'])
train, dev = [c.rows(selection / name) for name in ('selected_train.jsonl', 'selected_dev.jsonl')]
out = c.HERE / 'ffprobe_cpu_selection_01'
out.mkdir(exist_ok=False)
chosen = teacher.choose_probe_windows(train, dev, out, str(binary))
assert len(chosen) == 2 and {w['split'] for w in chosen} == {'train', 'dev'}
command = c.teacher_command(config, {'server_url':'http://127.0.0.1:1'}, 'probe')
assert command[command.index('--ffprobe') + 1] == str(binary)
report = {'status':'PASS_REAL_NONTEST_FFPROBE_WITH_PATH_ABSENT','checks':4,'selected_windows':2,
          'population_windows':len(train)+len(dev),'planned_probe_output_bytes':planned,
          'ffprobe_sha256':c.sha(binary),'GPU_started':False,'labels_generated':False}
c.write(c.HERE / 'ffprobe_cpu_acceptance.json', report, fresh=True)
print(json.dumps(report))
