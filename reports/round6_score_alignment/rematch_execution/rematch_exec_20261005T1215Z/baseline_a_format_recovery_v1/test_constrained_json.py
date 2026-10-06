#!/usr/bin/env python3
"""CPU-only fixture tokenizer and exhaustive small-domain prefix regression."""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import unittest

from constrained_json import (BoundedSegmentsGrammar, ConstraintDeadEnd,
    IncompleteConstrainedOutput, ASCII_GRAMMAR_CHARS, ascii_token_candidates,
    make_prefix_constraint)


def canonical(segments):
    return json.dumps({"segments":segments},separators=(",",":"))


class FixtureTokenizer:
    def __init__(self):
        pieces=["<eos>",*sorted(ASCII_GRAMMAR_CHARS),'{"segments":',"[[0,1]]}","13.04",
                "[[1,2],[3,4]]}","[[0,1],[1,2]]}","true","NaN"," ","中","<pad>"]
        self.pieces=dict(enumerate(pieces))
        self.eos_token_id=0
        self.chars={piece:idx for idx,piece in self.pieces.items() if len(piece)==1 and piece in ASCII_GRAMMAR_CHARS}
        self.special_context_token=len(self.pieces)
        self.pieces[self.special_context_token]="0"
        self.decode_arguments=[]
    def get_vocab(self): return {f"piece_{idx}":idx for idx in self.pieces}
    def decode(self,ids,skip_special_tokens=False,clean_up_tokenization_spaces=False):
        self.decode_arguments.append((skip_special_tokens,clean_up_tokenization_spaces))
        parts=[]
        for position,idx in enumerate(ids):
            # Isolated ASCII is advisory: this token changes to an invalid
            # context piece when appended to prior output, and must be rejected.
            parts.append("x" if idx==self.special_context_token and position else self.pieces[idx])
        return "".join(parts)
    def ids(self,text): return [self.chars[char] for char in text]
    def token(self,piece): return next(i for i,p in self.pieces.items() if p==piece)


class GrammarTests(unittest.TestCase):
    def test_complete_ordinary_precision_and_every_prefix(self):
        grammar=BoundedSegmentsGrammar(13)
        for segments in ([[0,13]],[[.0001,.0002]],[[.0123,1.2345],[1.2345,3.1415]],
                         [[0,1],[1,2],[2,3],[3,4],[4,5]]):
            text=canonical(segments)
            self.assertTrue(grammar.complete(text),text)
            for length in range(len(text)+1):
                self.assertTrue(grammar.valid_prefix(text[:length]),text[:length])
            self.assertFalse(grammar.complete(text[:-1]))

    def test_reproduces_13_second_1304_rejection(self):
        grammar=BoundedSegmentsGrammar(13)
        self.assertFalse(grammar.valid_prefix('{"segments":[[0,13.04'))
        self.assertFalse(grammar.complete(canonical([[0,13.04]])))
        self.assertTrue(grammar.complete(canonical([[0,13]])))

    def test_reproduces_6_8_9_segment_rejection(self):
        grammar=BoundedSegmentsGrammar(30)
        for count in (6,8,9):
            text=canonical([[i,i+1] for i in range(count)])
            self.assertFalse(grammar.valid_prefix(text),count)
            self.assertFalse(grammar.complete(text),count)
        self.assertTrue(grammar.complete(canonical([[i,i+1] for i in range(5)])))

    def test_numbers_can_gain_integer_digits_or_decimal_digits(self):
        grammar=BoundedSegmentsGrammar(13)
        prefix='{"segments":[[12,'
        self.assertTrue(grammar.valid_prefix(prefix+'1')) # can become 13
        self.assertFalse(grammar.valid_prefix(prefix+'1]'))
        self.assertTrue(grammar.valid_prefix(prefix+'12.'))
        self.assertTrue(grammar.valid_prefix(prefix+'12.0001'))
        self.assertFalse(grammar.valid_prefix(prefix+'12.0000'))
        self.assertFalse(grammar.valid_prefix(prefix+'14'))
        prefix='{"segments":[[0,13'
        self.assertTrue(grammar.valid_prefix(prefix))
        self.assertTrue(grammar.valid_prefix(prefix+'.0000'))
        self.assertFalse(grammar.valid_prefix(prefix+'.0001'))

    def test_no_number_prefix_dead_end_at_start_or_next_segment(self):
        grammar=BoundedSegmentsGrammar(2)
        self.assertFalse(grammar.valid_prefix('{"segments":[[2'))
        self.assertFalse(grammar.valid_prefix('{"segments":[[0,2],'))
        self.assertTrue(grammar.valid_prefix('{"segments":[[0,1.9999],[1.9999,2'))
        self.assertFalse(grammar.valid_prefix('{"segments":[[0,1.9999],[1.9998'))

    def test_fractional_duration_and_exact_last_decimal_bound(self):
        for duration in (Fraction(739,60),Fraction(739,2997),Fraction(1,2997),Fraction(1234567,2997)):
            grammar=BoundedSegmentsGrammar(duration)
            end=grammar.end_units/10000
            self.assertLessEqual(Fraction(str(end)),duration)
            self.assertTrue(grammar.complete(canonical([[0,end]])))
            self.assertFalse(grammar.complete(canonical([[0,(grammar.end_units+1)/10000]])))
        self.assertFalse(BoundedSegmentsGrammar(Fraction(739,60)).complete('{"segments":[[0,12.3167]]}'))
        self.assertTrue(BoundedSegmentsGrammar(Fraction(739,60)).complete('{"segments":[[0,12.3166]]}'))

    def test_empty_bool_nonfinite_negative_exponent_leading_zero_precision(self):
        grammar=BoundedSegmentsGrammar(30)
        invalid=['{"segments":[]}','{"segments":[[true,1]]}','{"segments":[[0,NaN]]}',
                 '{"segments":[[0,Infinity]]}','{"segments":[[-1,2]]}',
                 '{"segments":[[+0,2]]}','{"segments":[[00,2]]}','{"segments":[[0,01]]}',
                 '{"segments":[[0,1e1]]}','{"segments":[[.1,2]]}',
                 '{"segments":[[0.,2]]}','{"segments":[[0,1.00001]]}',
                 '{"segments":[[0,1]],"other":2}',' {"segments":[[0,1]]}',
                 '{"segments": [[0,1]]}','{"segments":[[0,1]]}\n',
                 '{"Segments":[[0,1]]}','{"segments":[[0,1]]}{}']
        for text in invalid:
            self.assertFalse(grammar.valid_prefix(text),text)

    def test_backward_equal_overlap_and_unsorted(self):
        grammar=BoundedSegmentsGrammar(30)
        for segments in ([[1,1]],[[2,1]],[[0,2],[1,3]],[[3,4],[0,1]]):
            self.assertFalse(grammar.complete(canonical(segments)),segments)
        self.assertTrue(grammar.complete(canonical([[0,2],[2,3]])))

    def test_valid_precision_lexical_variants(self):
        grammar=BoundedSegmentsGrammar(3)
        for number in ("2","2.0","2.00","2.000","2.0000","0.0001"):
            self.assertTrue(grammar.complete('{"segments":[[0,'+number+']]}'),number)

    def test_duration_and_count_fail_closed(self):
        for duration in (0,-1,True,"NaN","Infinity",Fraction(1,100001)):
            with self.assertRaises(ValueError): BoundedSegmentsGrammar(duration)
        for count in (0,6,True,1.0):
            with self.assertRaises(ValueError): BoundedSegmentsGrammar(1,count)

    def test_prefix_numeric_feasibility_matches_exhaustive_small_domain(self):
        grammar=BoundedSegmentsGrammar(1)
        representations=[]
        for units in range(151):
            for precision in range(5):
                factor=10**(4-precision)
                if units%factor: continue
                text=str(units//10000) if precision==0 else f"{units//10000}.{units%10000:04d}"[:2+precision]
                representations.append((units,text))
        prefixes={text[:length] for _,text in representations for length in range(len(text)+1)}
        prefixes.update(("00","0.00000","-",".","1","10","99","0.02"))
        for lower,upper in ((0,0),(1,1),(1,3),(19,71),(149,150),(0,150)):
            for prefix in prefixes:
                expected=any(lower<=value<=upper and text.startswith(prefix) for value,text in representations)
                self.assertEqual(grammar._number_can_finish(prefix,lower,upper),expected,(prefix,lower,upper))


class TokenAdapterTests(unittest.TestCase):
    def setUp(self): self.tokenizer=FixtureTokenizer()
    def make(self,duration=13,prompt_length=2,**kwargs):
        return make_prefix_constraint(self.tokenizer,prompt_length,duration,**kwargs)
    def tokens(self,text): return [999,998]+self.tokenizer.ids(text)

    def test_actual_full_context_decode_eos_and_cache(self):
        constraint=self.make()
        allowed=constraint(0,self.tokens(""))
        self.assertIn(self.tokenizer.token('{"segments":'),allowed)
        self.assertNotIn(self.tokenizer.eos_token_id,allowed)
        self.assertEqual(constraint(0,self.tokens("")),allowed)
        self.assertEqual(constraint.stats["cache_hits"],1)
        text=canonical([[0,13]])
        self.assertEqual(constraint(0,self.tokens(text)),[self.tokenizer.eos_token_id])
        self.assertEqual(constraint.assert_complete(self.tokenizer.ids(text)+[0]),{"segments":[[0,13]]})
        self.assertTrue(all(args==(False,False) for args in self.tokenizer.decode_arguments))

    def test_multichar_token_crosses_grammar_boundaries(self):
        constraint=self.make()
        allowed=constraint(0,self.tokens('{"segments":'))
        self.assertIn(self.tokenizer.token("[[0,1]]}"),allowed)
        self.assertIn(self.tokenizer.token("[[1,2],[3,4]]}"),allowed)
        self.assertIn(self.tokenizer.token("[[0,1],[1,2]]}"),allowed)

    def test_multichar_numeric_token_is_bound_by_duration(self):
        piece=self.tokenizer.token("13.04")
        prefix='{"segments":[[0,'
        self.assertNotIn(piece,self.make(13)(0,self.tokens(prefix)))
        self.assertIn(piece,self.make(Fraction(326,25))(0,self.tokens(prefix)))

    def test_context_changes_cannot_bypass_single_piece_prefilter(self):
        candidates=ascii_token_candidates(self.tokenizer)
        self.assertIn(self.tokenizer.special_context_token,candidates)
        constraint=self.make(candidate_token_ids=candidates)
        self.assertNotIn(self.tokenizer.special_context_token,constraint(0,self.tokens('{"segments":[[')))

    def test_invalid_prefix_no_allowed_and_truncation_stop(self):
        constraint=self.make()
        for text in ('{"segments":[[0,13.04',canonical([[0,1]]*6)):
            with self.assertRaises(ConstraintDeadEnd): constraint(0,self.tokens(text))
        with self.assertRaises(IncompleteConstrainedOutput):
            constraint.assert_complete(self.tokenizer.ids('{"segments":[[0,1]'))
        with self.assertRaises(IncompleteConstrainedOutput):
            constraint.assert_complete(self.tokenizer.ids('{"segments":')+[0]+self.tokenizer.ids('[[0,1]]}'))
        self.assertEqual(constraint.stats["dead_ends"],2)

    def test_missing_tokenization_path_is_explicit_stop(self):
        constraint=self.make(candidate_token_ids=[self.tokenizer.token("13.04")])
        with self.assertRaises(ConstraintDeadEnd): constraint(0,self.tokens(""))

    def test_multiple_eos_ids_only_after_completion(self):
        constraint=self.make(eos_token_ids=[0,500])
        self.assertNotIn(500,constraint(0,self.tokens("")))
        self.assertEqual(constraint(0,self.tokens(canonical([[0,1]]))),[0,500])

    def test_prompt_identity_and_eos_configuration_stop(self):
        constraint=self.make()
        with self.assertRaises(ConstraintDeadEnd): constraint(0,[999])
        with self.assertRaises(ValueError): self.make(prompt_length=-1)
        with self.assertRaises(ValueError): self.make(eos_token_ids=[])


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise FileExistsError("preserve constrained grammar evidence")
    stream=io.StringIO()
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                             for cls in (GrammarTests,TokenAdapterTests)])
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    here=Path(__file__).resolve().parent
    receipt={"schema":"aic_bounded_segments_prefix_cpu_test_v1",
             "status":"PASS_PURE_CPU_PREFIX_GRAMMAR_FIXTURE_TOKENIZER" if result.wasSuccessful() else "BLOCK_PREFIX_GRAMMAR",
             "tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
             "output":stream.getvalue(),"source_sha256":hashlib.sha256((here/"constrained_json.py").read_bytes()).hexdigest(),
             "test_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             "real_qwen_tokenizer_verified":False,"model_run":False,"GPU_used":False,
             "contest_media_read":False,"semantic_labels_read":False,"quality_claim":False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as target:
        json.dump(receipt,target,ensure_ascii=False,indent=2)
        target.write("\n")
    print(stream.getvalue())
    return 0 if result.wasSuccessful() else 1


if __name__=="__main__": raise SystemExit(main())
