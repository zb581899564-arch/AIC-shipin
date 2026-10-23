"""Regression for cached-only R accidentally forecasting old GPU work again."""
import ast
from pathlib import Path
import unittest


class DerivedForecastTest(unittest.TestCase):
    def test_parent_inference_is_charged_only_to_fresh_inference_estimates(self):
        path = Path(__file__).parents[1] / 'improvement/final_sprint_v1/runner.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'historical_forecast_delta']
        scope = {'DERIVED_CANDIDATES': {'r_time_apex', 'm_time_prune'}}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
        delta = scope['historical_forecast_delta']
        self.assertEqual(delta('r_time_apex', 0, 200), 0)
        self.assertEqual(delta('m_time_prune', 0, 200), 0)
        self.assertEqual(delta('r_time_event', 20, 200), 180)


if __name__ == '__main__':
    unittest.main()
