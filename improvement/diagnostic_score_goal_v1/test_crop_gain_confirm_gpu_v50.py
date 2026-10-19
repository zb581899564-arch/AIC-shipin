import copy
import unittest

from crop_gain_confirm_gpu_v50 import admission


class NewGainAdmission(unittest.TestCase):
    def setUp(self):
        weights = {'path': '/fixed/final500', 'sha256': 'a'*64}
        critic = {'path': '/fixed/critic', 'sha256': 'b'*64}
        self.reg = dict(schema='GAIN_CRITIC_NATIVE19_READONLY_GPU_V50',
            critic_weights=critic, adapter_weights=weights,
            CPU_registration={'path': '/fixed/new49', 'sha256': 'c'*64})
        self.screen = dict(status='PASS_GAIN_CRITIC_SCREEN20_ONLY', confirm_admitted=True,
            production_admitted=False, primary='JOINT14', fixed_final_checkpoint=True,
            critic_weights=critic, adapter_weights=weights)
        self.gate = dict(status='NEW49_REAL_GATE', registration=self.reg['CPU_registration'],
            sources=19, original20_complete=False, first_independent_pixels_text_native_QA=True,
            adapter_weights=weights)
        self.training = dict(completed_updates=500, successful_micro=2000,
            adapter_reload_all288_exact=True, adapter_weights=weights)

    def check(self, screen=None, gate=None, reg=None):
        admission(reg or self.reg, screen or self.screen, gate or self.gate,
                  self.training, 'NEW49_REAL_GATE')

    def test_actual_new_gain_pass(self):
        self.check()

    def test_native_old_ce_pass_is_not_gain_qualification(self):
        screen = copy.deepcopy(self.screen)
        screen['status'] = 'PASS_NATIVE_CROP_SCREEN_ONLY'
        with self.assertRaises(ValueError):
            self.check(screen=screen)

    def test_rejected_gain_cannot_be_run(self):
        screen = copy.deepcopy(self.screen)
        screen.update(status='STOP_GAIN_CRITIC_SCREEN20_REJECTED', confirm_admitted=False)
        with self.assertRaises(ValueError):
            self.check(screen=screen)

    def test_missing_first_native_input_qa(self):
        gate = copy.deepcopy(self.gate)
        gate['first_independent_pixels_text_native_QA'] = False
        with self.assertRaises(ValueError):
            self.check(gate=gate)

    def test_critic_must_remain_the_screen_critic(self):
        reg = copy.deepcopy(self.reg)
        reg['critic_weights']['sha256'] = 'd'*64
        with self.assertRaises(ValueError):
            self.check(reg=reg)


if __name__ == '__main__':
    unittest.main()
