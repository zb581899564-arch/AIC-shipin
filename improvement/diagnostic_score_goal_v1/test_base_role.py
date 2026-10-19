import unittest
from contextlib import contextmanager
from base_role import frozen_original_base


class Param:
    requires_grad=False
    def requires_grad_(self,value):self.requires_grad=value


class Layer:
    disable_adapters=False
    lora_A={}


class FakeModel:
    def __init__(self):self.p=[Param(),Param()];self.layers=[Layer(),Layer()]
    def parameters(self):return iter(self.p)
    def modules(self):return iter(self.layers)
    @contextmanager
    def disable_adapter(self):
        for m in self.layers:m.disable_adapters=True
        try:yield
        finally:
            for m in self.layers:m.disable_adapters=False
            for p in self.p:p.requires_grad=True  # actual PEFT exit behavior


class BaseRoleTests(unittest.TestCase):
    def test_restore_exact_trainability_and_preserve_answer_inside_scope(self):
        model=FakeModel();saved=[]
        with frozen_original_base(model,expected_layers=2):
            self.assertTrue(all(m.disable_adapters for m in model.layers));saved.append('raw answer persisted')
        self.assertEqual(saved,['raw answer persisted'])
        self.assertFalse(any(p.requires_grad for p in model.p))
        self.assertFalse(any(m.disable_adapters for m in model.layers))

    def test_restore_on_generation_exception_and_preserve_original_error(self):
        model=FakeModel()
        with self.assertRaisesRegex(RuntimeError,'generation failed'):
            with frozen_original_base(model,expected_layers=2):raise RuntimeError('generation failed')
        self.assertFalse(any(p.requires_grad for p in model.p))
        self.assertFalse(any(m.disable_adapters for m in model.layers))

    def test_nonfrozen_input_rejected_before_call(self):
        model=FakeModel();model.p[0].requires_grad=True
        with self.assertRaisesRegex(ValueError,'enabled/frozen'):
            with frozen_original_base(model,expected_layers=2):self.fail('must not call')


if __name__=='__main__':unittest.main()
