import ast
from pathlib import Path
import unittest


class ThroughputSampling(unittest.TestCase):
    def test_only_fresh_temporal_observations_measure_m_throughput(self):
        # Import this pure decision without Linux fcntl/Torch dependencies.
        path = Path(__file__).parents[1] / 'improvement/final_sprint_v1/runner.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in ('route_family', 'fresh_throughput_sample')]
        namespace = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
        select = namespace['fresh_throughput_sample']
        self.assertFalse(select('m_specialist', False, {'clip_features_7': {}}, '7'))
        self.assertFalse(select('m_generic_control', False, {'clip_features_7': {}}, '7'))
        self.assertTrue(select('m_specialist', False, {'clip_features_6': {}}, '7'))
        self.assertTrue(select('g_subject', False, {'clip_features_7': {}}, '7'))
        self.assertTrue(select('r_phase_event', False, {}, '7'))
        self.assertFalse(select('g_subject', True, {}, '7'))


if __name__ == '__main__':
    unittest.main()
