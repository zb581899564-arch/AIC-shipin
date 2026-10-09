"""Existing pinned grammar accepts an exact Fraction duration; no generation."""
from fractions import Fraction as F
import bw_common as c
def main():
    rt,ex,cc,student,old,frames,production=c.helpers()
    from constrained_json import BoundedSegmentsGrammar
    proofs=[]
    for scope in ('developer','rematch'):
        _,jobs=c.jobs_for(scope)
        for job in jobs:
            for ix,part in enumerate(job['windows']):
                if not c.is_changed(part):continue
                w=part['window'];duration=F(w['exact_raw_end'])-F(w['exact_raw_start'])
                g=BoundedSegmentsGrammar(duration,allow_empty=True)
                c.require(g.duration==duration and g.complete('{"segments":[]}') and
                    g.complete('{"segments":[[0,1]]}') and not g.complete('{"segments":[[0,30]]}'),
                    'existing actual grammar did not preserve new exact duration')
                proofs.append(dict(scope=scope,index=ix,exact_duration=str(duration),float_render=str(w['window_duration_sec']),
                    exact_decimal_lattice_upper_units=g.end_units))
    c.require(len(proofs)==132,'all132 changed grammar consumers')
    c.save(c.HERE/'prefix_cpu_acceptance.json',dict(status='PASS_EXISTING_PINNED_GRAMMAR_EXACT_FRACTION_DURATION',utc=c.utc(),
        cases=132,proofs=proofs,original_grammar_sha256=c.sha(__import__('sys').modules['constrained_json'].__file__),
        no_changed_endpoint_or_epsilon=True,new_model_calls=0,new_decoder_calls=0,new_optimizer_updates=0))
    print('PASS_EXISTING_PINNED_GRAMMAR_EXACT_FRACTION_DURATION',flush=True)
if __name__=='__main__':main()
