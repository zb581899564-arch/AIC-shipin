import hashlib
import unittest

from prompt_contract13 import prompt_binding


class Tokenizer:
    def __init__(self, text):
        self.text = text

    def decode(self, ids, **kwargs):
        return self.text


class PromptTests(unittest.TestCase):
    prompt = 'Verify candidate E07 at local [5.25, 9.50]; return KEEP/UNKNOWN/DROP.'

    def detail(self, text):
        return dict(prompt_sha256=hashlib.sha256(text.encode()).hexdigest())

    def test_exact_request_is_present(self):
        record = prompt_binding(Tokenizer('<video>\n' + self.prompt + '\nassistant'), [[1, 2]],
                                self.detail(self.prompt), self.prompt, 'VERIFY', 'Select highlights')
        self.assertTrue(record['complete_task_in_actual_tokens'])

    def test_old_empty_prompt_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            prompt_binding(Tokenizer('Select highlights'), [[1, 2]], self.detail('Select highlights'),
                           self.prompt, 'VERIFY', 'Select highlights')

    def test_declared_hash_alone_cannot_certify_input(self):
        with self.assertRaises(ValueError):
            prompt_binding(Tokenizer('Select highlights'), [[1, 2]], self.detail(self.prompt),
                           self.prompt, 'VERIFY', 'Select highlights')

    def test_other_candidate_or_truncated_text_is_rejected(self):
        for text in [self.prompt.replace('E07', 'E08'), self.prompt[:25]]:
            with self.assertRaises(ValueError):
                prompt_binding(Tokenizer(text), [[1, 2]], self.detail(self.prompt),
                               self.prompt, 'VERIFY', 'Select highlights')


if __name__ == '__main__':
    unittest.main()
