"""Prepare only; new CPU representation source, original AGY dispatch bytes untouched."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
V4=BASE/'engineering_alias_remainder_v4_bootstrap_file'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,d):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def put(p,b):
 with Path(p).open('xb') as f:f.write(b)
def main():
 assert not(HERE/'plan.json').exists() and not(HERE/'root_start_admission.json').exists()
 assert sha(V4/'root_start_admission.json')=='6408d8b81962cd17c8b4e875adb538a566183d8ad78c50c6e74e8f09df8f871d'
 erratum=BASE.parent/'ROOT/bootstrap_line_representation_erratum_v1.json'
 if not erratum.exists():erratum=BASE.parent/'bootstrap_line_representation_erratum_v1.json'
 assert sha(erratum)=='80b6c4145fb639e88b36bbf27730d96ed0f7a508c8edc6109dda7bbec40bbc37'
 common=(V4/'common.py').read_text(encoding='utf-8').replace('ROOT=Path(__file__).resolve().parent',"V5=Path(__file__).resolve().parent\nROOT=V5.parent/'engineering_alias_remainder_v4_bootstrap_file'")
 put(HERE/'common.py',common.encode('utf-8'))
 original=(V4/'audit.py').read_text(encoding='utf-8').split('\ndef completed_scope(')[0]+'\n'
 put(HERE/'original_engine.py',original.encode('utf-8'))
 needle="line_count=len(bootstrap_file.read_bytes().splitlines())";report="bootstrap_required_lines=len(Path(index['bootstrap_instruction_path']).read_bytes().splitlines())"
 assert original.count(needle)==1 and original.count(report)==1
 fixed=original.replace(needle,"line_count=len(bootstrap_file.read_bytes().split(bytes([10])))").replace(report,"bootstrap_required_lines=len(Path(index['bootstrap_instruction_path']).read_bytes().split(bytes([10])))")
 put(HERE/'engine.py',fixed.encode('utf-8'))
 protocol='''# V5 independent line-representation controller — no change to v4 scientific dispatch
Only CPU engineering text line representation changes. Original v4 sources/freeze/request/bootstrap/index/ACK/aliases/native64/clock/clip/8effective/old17actual32facts/schema/science/model/proposals/domain/source/target all stay byte exact. Old33 ERROR/v3 REGISTERED34 prespawn failure/v4 strict REJECTED and all old raw/costs stay preserved. No new frames/decode/GPU/train/semantic gold.
Bind ROOT actual bootstrap-line erratum SHA80b6c4145fb639e88b36bbf27730d96ed0f7a508c8edc6109dda7bbec40bbc37. Exact metadata requires reported lines == len(payload.split(LF)) == countLF+1, bytes exact, tailLF present, noCR. Never +/-1 tolerance. Unique tail six-field ACK remains first view -> second write -> third index; original whitelists/order/actual64 and context/clip/8/student geometry/schema/all ERROR/unfinished/result/reported failures remain strict. Correct text routing ACK is limited engineering evidence, not full attention or semantics.
original_engine is exact extracted original v4 inspect function/imports. engine makes ONLY two textual substitutions: bootstrap checker and its required-lines report use split(LF) instead of splitlines. Wrapper additionally verifies tailLF/noCR. Original v4 actual audit runs once each and is retained. Independent v5 reconstruction is x-written, original reasons must be nonempty subset of exactly BOOTSTRAP_NOT_EXACTLY_ONCE_FIRST_FULL_DONE and BOOTSTRAP_ACK_MISSING_WRONG_OR_ORDER; any other problem STOP. No reclassification of original audit. ROOT independently reviews scope evidence/pixels/facts/semantics.
Controller requires ROOT_APPROVED_START_LINE_REPRESENTATION_V5_FIXED_CLI35_36, original34 real terminal/audit/stopped, independent complete34 actual reconstruction acceptance, zero35/36 requests and currentglobal34. Then only original frozen v4 run_call35 once (19/20), run_call36 once (21/22/23); original7200s/modelhighest/cap36/no37/no retry preserved. request historical prior33 stays a recovery checkpoint, not live predecessor. Real request/process/terminal and ledger define spawned calls. Any35/36 actual failure preserves terminal/cost and stops. Registration34 is never rewound.
One v5 observer watches v5 terminal only, not old v4 stopped. Each completed scope independently retains original v4 immutableprefix and old strict audit; if existing reference it, never rewrite. For future scopes only original v4 scope CPU audit once creates prefix, then newv5 proof once, including middle22 before23. Prefix is actual supplied bytes, not invented. Full terminal cost records actualwall/usage/cashUNKNOWN, not0, pending while active. Original scope v3 status/immutable_prefix/boundfactrows/actualsupply remain available via original audit and representation_audit. Expected fullcore143/183/273 and priorcontext1 remain untouched.
Preparation/test CPU only. Negative synthetic cases are memory-only, never pretend media/raw/output. Mutable active raw/terminal are not frozen prematurely; real immutable terminal/prefix/current sourceSHA must be verified when consumed. Original full24/21denominators and cost histories retained; no root refs/student/runtime changes.
'''
 put(HERE/'PROTOCOL.md',protocol.encode('utf-8'))
 inputs={};calls=[]
 for n in (34,35,36):
  a=V4/f'call{n}';fr=read(a/'freeze.json')
  for p,s in fr['inputs'].items():assert sha(p)==s;inputs[p]=s
  for name in ('freeze.json','index.json','bootstrap_instruction.txt','bootstrap_ack_expected.json','short_prompt.txt','literal_execution_parameters.json','original_v3_frozen_prompt.txt'):inputs[str(a/name)]=sha(a/name)
  assert not(V4/f'call{n}/request.json').exists() if n in (35,36) else (a/'process.json').exists()
  b=(a/'bootstrap_instruction.txt').read_bytes();assert b.endswith(bytes([10])) and bytes([13]) not in b
  calls.append(dict(CLI=n,jobs=fr['fixed_job_indices'],fullcore=fr['expected_core_tool_calls'],context_steps=fr['context_read_count'],freeze_sha256=sha(a/'freeze.json'),bootstrap_sha256=sha(a/'bootstrap_instruction.txt'),bytes=len(b),Python_splitlines=len(b.splitlines()),Go_split_LF=len(b.split(bytes([10])))))
 for p in [V4/'root_start_admission.json',V4/'registered.json',V4/'execution_code_binding.json',V4/'dry_run_acceptance.json',V4/'independent_preparation_acceptance.json',V4/'PROTOCOL.md',erratum,*V4.glob('*.py'),V4/'call34/request.json',V4/'call34/process.json',V4/'call34/bootstrap_ack.json',V4/'actual_readonly_bootstrap_evidence/CLI34_actual_bootstrap_ACK_supply.json',V4/'actual_readonly_bootstrap_evidence/CLI34_bootstrap_ACK_actual_immutable_prefix.jsonl']:inputs[str(p)]=sha(p)
 ledger=BASE/'global_CLI_ledger.jsonl';assert max(json.loads(s)['global_count'] for s in ledger.read_text(encoding='utf-8').splitlines())==34
 put(HERE/'actual_registered34_ledger_prefix.jsonl',ledger.read_bytes());inputs[str(HERE/'actual_registered34_ledger_prefix.jsonl')]=sha(HERE/'actual_registered34_ledger_prefix.jsonl')
 sources={str(p):sha(p) for p in HERE.glob('*.py')};sources[str(HERE/'PROTOCOL.md')]=sha(HERE/'PROTOCOL.md')
 assert len([p for p in HERE.glob('*.py')])==10
 save(HERE/'execution_code_binding.json',dict(utc=datetime.now(timezone.utc).isoformat(),sources=sources,frozen_prior_inputs=inputs,root_actual_erratum=dict(path=str(erratum),sha256=sha(erratum)),original_v4_sources_and_science_unchanged=True,prior_mutable34_raw_and_terminal_not_frozen_early=True,requires_root_gate=True,new_model_calls=0))
 AST=[]
 for p in HERE.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'));AST.append(dict(path=str(p),sha256=sha(p)))
 save(HERE/'plan.json',dict(status='PREPARED_CPU_LINE_REPRESENTATION_V5_PENDING_ROOT',original34_actual_terminal_required=True,new_dispatch_only={'35':[19,20],'36':[21,22,23]},calls=calls,globalcap=36,new_model_calls=0,gate_required='ROOT_APPROVED_START_LINE_REPRESENTATION_V5_FIXED_CLI35_36'))
 save(HERE/'dry_run_acceptance.json',dict(status='PASS_PREPARED_10PY_AST_ALL_V4_BINDINGS_UNCHANGED_NO_MODEL',AST=AST,calls=calls,frozen_prior_input_count=len(inputs),execution_binding_sha256=sha(HERE/'execution_code_binding.json'),root_actual_erratum_sha256=sha(erratum),original_v4_alias_media_context_science_unchanged=True,new_AGY_or_model_calls=0,new_video_decode=0,cash_cost='UNKNOWN_NOT_ZERO'))
 print(json.dumps(dict(root=str(HERE),execution_binding_sha256=sha(HERE/'execution_code_binding.json'),dry_run_sha256=sha(HERE/'dry_run_acceptance.json'),protocol_sha256=sha(HERE/'PROTOCOL.md'),calls=calls,input_count=len(inputs)),ensure_ascii=False))
if __name__=='__main__':main()
