"""Targeted real CPU Torch/PEFT regression; no research model or dataset calls."""
import tempfile
import unittest
from pathlib import Path
import torch
from common import ROOT, runtime_paths, write
from train_arms import order


class TrainingContracts(unittest.TestCase):
    def test_registered_file_and_balanced_draws(self):
        rows = [dict(human_bin=k) for k, count in enumerate([100, 172, 330]) for _ in range(count)]
        natural = order(rows, 'W10', 400, 20261021)
        self.assertEqual(natural, order(rows, 'W11', 400, 20261021))
        self.assertEqual(len(set(natural)), 400)
        balanced = order(rows, 'W01', 400, 20261021)
        self.assertEqual([sum(rows[i]['human_bin'] == k for i in balanced) for k in range(3)], [134, 133, 133])

    def test_fresh_three_arm_peft_lifecycle_and_reload(self):
        from peft import LoraConfig, PeftModel, get_peft_model
        from transformers import LlamaConfig, LlamaForCausalLM
        torch.set_num_threads(2)
        torch.manual_seed(7)
        base = LlamaForCausalLM(LlamaConfig(vocab_size=32, hidden_size=16, intermediate_size=32,
            num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2))
        original = {n: p.detach().clone() for n, p in base.named_parameters()}
        initial = []
        with tempfile.TemporaryDirectory(prefix='s1_cpu_contract_', dir=ROOT) as temporary:
            for arm in ['W10', 'W01', 'W11']:
                torch.manual_seed(20261021)
                model = get_peft_model(base, LoraConfig(r=2, lora_alpha=4, lora_dropout=.05,
                    target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'], task_type='CAUSAL_LM'))
                initial.append({n: p.detach().clone() for n, p in model.named_parameters() if 'lora_' in n})
                optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-3)
                ids = torch.tensor([[1, 2, 3, 4, 5]])
                result = model(input_ids=ids, labels=ids)
                result.loss.backward()
                self.assertTrue(any(p.grad is not None and p.grad.count_nonzero() for p in model.parameters()))
                optimizer.step()
                saved = {n: p.detach().clone() for n, p in model.named_parameters() if 'lora_' in n}
                path = Path(temporary) / arm
                model.save_pretrained(path)
                base = model.unload()
                model = PeftModel.from_pretrained(base, path, is_trainable=False)
                restored = {n: p.detach() for n, p in model.named_parameters() if 'lora_' in n}
                self.assertEqual(set(saved), set(restored))
                self.assertTrue(all(torch.equal(v, restored[n]) for n, v in saved.items()))
                base = model.unload()
                self.assertTrue(all(torch.equal(v, dict(base.named_parameters())[n]) for n, v in original.items()))
                for parameter in base.parameters():
                    parameter.requires_grad_(False)
        self.assertTrue(all(all(torch.equal(v, other[n]) for n, v in initial[0].items()) for other in initial[1:]))

    def test_assistant_tail_is_exact_and_prompt_is_masked(self):
        runtime_paths()
        from sft_contract import assistant_labels
        result = assistant_labels([1, 2, 3, 4, 5], [1] * 5, [1, 2, 3], [1] * 3)
        self.assertEqual(result['labels'], [-100, -100, -100, 4, 5])
        self.assertEqual(result['tail_labels'], [-100, 4, 5])
        self.assertEqual(result['logits_to_keep'], 3)
        with self.assertRaises(Exception):
            assistant_labels([1, 2, 9, 4, 5], [1] * 5, [1, 2, 3], [1] * 3)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TrainingContracts))
    write(ROOT / 'training_cpu_contract_acceptance.json', dict(status='PASS' if result.wasSuccessful() else 'FAIL',
        tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        synthetic_cpu_only=True, research_model_calls=0, research_optimizer_updates=0))
    raise SystemExit(0 if result.wasSuccessful() else 1)
