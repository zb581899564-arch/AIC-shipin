import unittest
from unittest.mock import Mock

from improvement.final_sprint_v1.temporal_isolation import TemporalFieldEngine


class TemporalIsolationTest(unittest.TestCase):
    def engine(self, name, operator):
        engine = object.__new__(TemporalFieldEngine)
        engine.candidate_id = name
        engine.candidate = {"parent_candidate": "m_time_select", "selection_operator": operator}
        engine.base = {"0": {1: [0, 0, 10], 2: [0, 0, 10]}}
        engine.assets = {"protected_baselines": {"40.48": {"path": "baseline"}},
                         "frozen_spatial_field": {"path": "receipt"}}
        engine.field = {"support": {"0": {0, 1, 2}},
                        "boxes": {"0": {i: [0, 0, 10] for i in range(3)}},
                        "source_checks": {"0": {}},
                        "spec_ref": {}, "cache_ref": {}, "metadata_ref": {}}
        engine.parent_source = Mock(return_value=({"predictions": [{"frame": 0}, {"frame": 2}],
                                                  "evidence": {}}, {}))
        return engine

    def test_frozen_intersection_and_union_are_distinct_structures(self):
        self.assertEqual(self.engine("m_time_prune", "intersection")._selection({"video_id": "0"})[0], {2})
        self.assertEqual(self.engine("m_time_add", "union")._selection({"video_id": "0"})[0], {0, 1, 2})

    def test_unsupported_proposals_are_explicit_unknown(self):
        engine = self.engine("m_time_select", "replacement")
        engine.specialist_selection = Mock(return_value=([0, 4], {}, []))
        engine._finish_source = lambda source, predictions, detail, references, selection: {
            "predictions": predictions, "selection": selection,
            "spatial_provenance": [{"kind": "automatic_spatial"} for _ in predictions]}
        result = engine.produce_source({"video_id": "0"})
        self.assertEqual(result["predictions"], [{"frame": 0, "bboxes": [0, 0, 10]}])
        self.assertEqual(result["selection"]["unsupported_proposals_unknown"], [4])
        self.assertEqual(result["spatial_provenance"][0]["kind"], "native_spatial_field")

    def test_execution_error_cannot_become_empty_selection(self):
        engine = self.engine("m_time_select", "replacement")
        engine.specialist_selection = Mock(side_effect=RuntimeError("actual inference failure"))
        with self.assertRaisesRegex(RuntimeError, "actual inference failure"):
            engine.produce_source({"video_id": "0"})


if __name__ == "__main__":
    unittest.main()
