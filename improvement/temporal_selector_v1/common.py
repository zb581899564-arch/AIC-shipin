"""Explicit new-run bindings. Historical roots are read-only inputs."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

WORK = Path('/home/inspur/aic_video_work')
ROOT = Path(os.environ.get('AIC_TEMPORAL_ROOT', str(WORK/'temporal_selector_20261018_v1')))
RUN = WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PYTHON = WORK/'env/qwen3vl_isolated_20260910/bin/python'
BASELINE_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
BASELINE = WORK/'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip'
EXTERNAL = WORK/'score_residual_execution_20261016_v2'
PRODUCTION = WORK/'semantic_context_production_20261016_v1'
PROMPT = ('Observe the entire silent video sequence. Identify visually distinctive events, actions, '
          'expressive reactions and informative moments, considering preceding and following context. '
          'Ordinary transitions and repetition need not be selected. A sequence can contain all, some, '
          'or no highlights. Do not infer unobserved sound. Assess the visible sequence as a whole.')


def require(value, message):
    if not value:
        raise ValueError(message)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def replace_state(value):
    temporary = ROOT/'state.next.json'
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    temporary.replace(ROOT/'state.json')


def reference(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def checked(ref):
    path = Path(ref['path']).resolve()
    require(path.is_relative_to(WORK.resolve()) and path.is_file(), 'Reference real path escaped work root')
    require(sha(path) == ref['sha256'], 'Reference bytes changed: '+str(path))
    return path


def event(stage, **fields):
    row = dict(utc=utc(), stage=stage, **fields)
    with (ROOT/'journal.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(row, ensure_ascii=False), flush=True)


def tensor_sha(tensor):
    return hashlib.sha256(tensor.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def signature(tensors):
    return {key: dict(shape=list(value.shape), dtype=str(value.dtype), sha256=tensor_sha(value))
            for key, value in tensors.items()}


def assert_cpu():
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only this CPU child must mask its CUDA')


def gpu_terminal(name):
    resource = RUN/'controller'/(name+'.resource.json')
    row = read(resource)
    entries = [json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
               if line.strip() and json.loads(line).get('name') == name]
    require(entries == [row] and row['status'] == 'completed' and row['exit_code'] == 0,
            'Unique shared GPU terminal/ledger mismatch')
    return dict(resource=reference(resource), charged_seconds=row['charged_seconds'],
                peak_memory_mib=row.get('sampled_peak_memory_mib'), name=name)
