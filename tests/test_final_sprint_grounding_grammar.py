"""Structural output constraints, not an image/model quality test."""
import unittest

from improvement.final_sprint_v1.grounding_grammar import GroundingGrammar, valid_prefix


class CharacterTokenizer:
    all_special_ids = [9999]

    def get_vocab(self):
        return {chr(value): value for value in range(32, 127)}

    def decode(self, ids, **_kwargs):
        return ''.join(chr(value) for value in ids)


class GroundingGrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grammar = GroundingGrammar(CharacterTokenizer())

    def test_subject_and_semantic_whole_scene_remain_model_choices(self):
        for text in ['{"mode":"subject","boxes":[[0,0,1000,1000]]}',
                     '{ "mode" : "whole_scene", "boxes" : [] }',
                     '{"mode":"subject","boxes":[[0,0,1,1],[2,2,3,3],[4,4,5,5]]}']:
            self.grammar.validate_output([*map(ord, text), 9999], [9999])

    def test_four_boxes_cannot_be_generated_or_adopted(self):
        text = '{"mode":"subject","boxes":[[0,0,1,1],[2,2,3,3],[4,4,5,5]'
        self.assertTrue(valid_prefix(text))
        self.assertFalse(valid_prefix(text + ','))
        with self.assertRaises(ValueError):
            self.grammar.validate_output([*map(ord, text + ',[6,6,7,7]]}'), 9999], [9999])

    def test_integer_extent_and_mode_contracts_are_not_relaxed(self):
        for text in ['{"mode":"subject","boxes":[]}',
                     '{"mode":"whole_scene","boxes":[[0,0,1,1]]}',
                     '{"mode":"subject","boxes":[[900,2,800,4]]}',
                     '{"mode":"subject","boxes":[[0,0,1001,1000]]}',
                     '{"mode":"subject","boxes":[[0,0,1,1],[0,0,1,1]]}']:
            self.assertFalse(valid_prefix(text), text)

    def test_partial_right_edge_can_still_extend_to_a_valid_number(self):
        prefix = '{"mode":"subject","boxes":[[900,0,1'
        self.assertTrue(valid_prefix(prefix))  # 1000 remains possible.
        self.assertFalse(valid_prefix(prefix + ','))
        self.assertTrue(valid_prefix(prefix + '000,1]]}'))
