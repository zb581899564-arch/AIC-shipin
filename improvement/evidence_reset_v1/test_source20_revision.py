"""Only the two new pre-first-forward reviewer corrections; old4 PASS adopted."""
import unittest
import numpy as np
from source_step20_v2 import stable_kl


class RevisionChecks(unittest.TestCase):
    def test_extreme_softmax_KL_is_finite_without_log_zero(self):
        self.assertAlmostEqual(stable_kl(np,[0.,-1e6],[1.,-1e6]),0.)
        self.assertAlmostEqual(stable_kl(np,[0.,-1e6],[-1e6,0.]),1e6)
        self.assertGreater(stable_kl(np,[0.,1.],[1.,0.]),0)

    def test_actual_peft_name_mapping_has_no_substring_alias(self):
        named=['base_model.model.model.language_model.layers.0.self_attn.k_proj.lora_A.policy.weight',
               'base_model.model.model.language_model.layers.0.self_attn.k_proj.lora_B.policy.weight']
        state=['base_model.model.model.language_model.layers.0.self_attn.k_proj.lora_A.weight',
               'base_model.model.model.language_model.layers.0.self_attn.k_proj.lora_B.weight']
        self.assertEqual({k.replace('.policy.weight','.weight') for k in named},set(state))


if __name__=='__main__': unittest.main()
