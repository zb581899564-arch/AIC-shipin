"""Synthetic terminal-ledger checks; no GPU runner or model is executed."""
import json
import unittest
from pipeline_controller import accept_terminal

class CostEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.command=['/isolated/python','-B','train.py']
        self.old=(json.dumps(dict(name='historic',charged_seconds=7200))+'\n').encode()
        self.row=dict(name='current_train',command=self.command,runner_source_sha256='runner',
          resource_policy_sha256='policy',status='failed',finished_utc='2026-10-10T20:00:00+00:00',
          exit_code=1,charged_seconds=19.75)
    def accept(self,before=None,after=None,row=None):
        r=self.row if row is None else row
        return accept_terminal(r,self.old if before is None else before,
            self.old+(json.dumps(r)+'\n').encode() if after is None else after,
            name='current_train',command=self.command,runner_sha='runner',policy_sha='policy',
            phase='train',prior_current_cost=0)
    def test_natural_failed_terminal_is_charged(self):
        self.assertEqual(self.accept(),19.75)
    def test_historical_prefix_mutation_rejected(self):
        with self.assertRaisesRegex(ValueError,'prefix changed'):
            self.accept(after=b'{}\n'+(json.dumps(self.row)+'\n').encode())
    def test_duplicate_owned_terminal_rejected(self):
        with self.assertRaisesRegex(ValueError,'unique appended'):
            self.accept(after=self.old+2*(json.dumps(self.row)+'\n').encode())
    def test_foreign_command_rejected(self):
        with self.assertRaisesRegex(ValueError,'command/identity'):
            self.accept(row=dict(self.row,command=['different.py']))
    def test_unrelated_shared_terminal_preserved(self):
        after=self.old+(json.dumps(dict(name='shared_other',charged_seconds=3))+'\n'+json.dumps(self.row)+'\n').encode()
        self.assertEqual(self.accept(after=after),19.75)
    def test_nonpositive_or_nonfinite_charge_rejected(self):
        for value in (0,-1,float('nan'),float('inf'),None):
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'finite and positive'):
                self.accept(row=dict(self.row,charged_seconds=value))

if __name__=='__main__':unittest.main()
