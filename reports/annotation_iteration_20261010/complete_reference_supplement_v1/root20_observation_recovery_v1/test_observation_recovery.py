"""Pure CPU logic negative checks. No model, processor, PIL or decoder imports."""
import copy
import unittest
import recover_observation as recovery


class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = staticmethod(recovery.original_fact_validator(recovery.CALL.parent / 'common.py'))

    def facts(self):
        return [dict(slot=i, subject='subject', composition='composition', subtitle_visible=False, subtitle_text=None, visible_fact='fact') for i in range(4)]

    def test_closed_original_unchanged(self):
        original = {'group': 0, 'items': self.facts()}
        before = copy.deepcopy(original)
        wrapper, items = recovery.project_fact_container(original, 0, self.validator)
        self.assertEqual(original, before)
        self.assertEqual(wrapper, original)
        self.assertEqual(items, before['items'])

    def test_bare_original_unchanged(self):
        original = self.facts()
        before = copy.deepcopy(original)
        wrapper, items = recovery.project_fact_container(original, 4, self.validator)
        self.assertEqual(original, before)
        self.assertEqual(wrapper, {'group': 4, 'items': before})
        self.assertEqual(items, before)

    def test_list_not_allowed_in_original_closed_groups(self):
        with self.assertRaises(ValueError):
            recovery.project_fact_container(self.facts(), 0, self.validator)

    def test_closed_not_allowed_in_original_bare_groups(self):
        with self.assertRaises(ValueError):
            recovery.project_fact_container({'group': 4, 'items': self.facts()}, 4, self.validator)

    def test_slot_permutation_rejected(self):
        facts = self.facts(); facts[0], facts[1] = facts[1], facts[0]
        with self.assertRaises(AssertionError):
            recovery.project_fact_container(facts, 4, self.validator)

    def test_extra_or_missing_fields_rejected(self):
        for action in ('add', 'delete'):
            facts = self.facts()
            if action == 'add': facts[0]['invented'] = 'extra'
            else: del facts[0]['visible_fact']
            with self.assertRaises(AssertionError):
                recovery.project_fact_container(facts, 4, self.validator)

    def test_subtitle_contract_rejected(self):
        facts = self.facts(); facts[0]['subtitle_text'] = 'not null'
        with self.assertRaises(AssertionError):
            recovery.project_fact_container(facts, 4, self.validator)

    def rows(self):
        path = str(recovery.OWN / 'memory_only.png')
        row = lambda state: {'step_update': {'step_type': 'tool', 'step_index': 1, 'state': state, 'conversation_id': 'fixture', 'tool_name': 'view_file', 'tool_info': {'parameters': {'AbsolutePath': path}}}}
        return [row('ACTIVE'), row('DONE')], {'read_whitelist': [path], 'self_read_whitelist': [], 'write_whitelist': []}

    def test_actual_active_done_identity_positive(self):
        rows, freeze = self.rows()
        tools, _ = recovery.tool_sequence(rows, freeze)
        self.assertEqual(len(tools), 1)

    def test_error_unfinished_and_duplicate_rejected(self):
        for defect in ('error', 'unfinished', 'duplicate'):
            rows, freeze = self.rows()
            if defect == 'error': rows[-1]['step_update']['state'] = 'ERROR'
            elif defect == 'unfinished': rows.pop()
            else: rows.append(copy.deepcopy(rows[-1]))
            with self.assertRaises(ValueError): recovery.tool_sequence(rows, freeze)

    def test_literal_identity_drift_rejected(self):
        rows, freeze = self.rows()
        other = str(recovery.OWN / 'other_memory_only.png')
        freeze['read_whitelist'].append(other)
        rows[-1]['step_update']['tool_info']['parameters']['AbsolutePath'] = other
        with self.assertRaises(ValueError): recovery.tool_sequence(rows, freeze)

    def test_outside_path_rejected(self):
        rows, freeze = self.rows(); freeze['read_whitelist'] = []
        with self.assertRaises(ValueError): recovery.tool_sequence(rows, freeze)

    def test_fact_write_requires_next_response_after_all_four(self):
        response = lambda: {'step_update': {'step_type': 'agent_response', 'state': 'DONE'}}
        rows = [response()] + [{} for _ in range(8)] + [response(), {}, {}]
        batch = [{'step': i, 'active': 1 + 2*i, 'done': 2 + 2*i} for i in range(4)]
        write = {'step': 5, 'active': 10, 'done': 11}
        recovery.four_barrier(rows, batch, write)
        rows[9] = {}
        with self.assertRaises(ValueError): recovery.four_barrier(rows, batch, write)

    def test_not_same_response_rejected(self):
        response = {'step_update': {'step_type': 'agent_response', 'state': 'DONE'}}
        rows = [copy.deepcopy(response)] + [{} for _ in range(8)]
        rows[3] = copy.deepcopy(response)
        batch = [{'step': i, 'active': 1 + 2*i, 'done': 2 + 2*i} for i in range(4)]
        with self.assertRaises(ValueError): recovery.four_barrier(rows, batch)


if __name__ == '__main__':
    unittest.main()
