import concurrent.futures
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest

import pro_budget as budget


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="ai-yiguodun-tests-")
        self.base = Path(self.scratch.name)
        self.root = self.base / "pro-budget"

    def tearDown(self):
        self.scratch.cleanup()

    def packet(self, index):
        path = self.base / f"context-r{index:02d}.md"
        path.write_text(f"# Complete synthetic context\nTask: test\nRound: {index}\n", encoding="utf-8")
        return path

    def test_fourth_request_rejected_and_resume_does_not_reset(self):
        budget.initialize(self.root, "test", 0)
        for number in range(3):
            self.assertEqual(budget.reserve(self.root, [self.packet(number)])["slot"], number + 1)
        self.assertEqual(budget.status(self.root)["remaining"], 0)
        with self.assertRaisesRegex(ValueError, "PRO_LIMIT_REACHED"):
            budget.reserve(self.root, [self.packet(3)])
        with self.assertRaises(ValueError):
            budget.initialize(self.root, "renamed-task", 0)

    def test_confirmed_historical_calls_count(self):
        budget.initialize(self.root, "test", 2)
        self.assertEqual(budget.reserve(self.root, [self.packet(0)])["slot"], 3)
        self.assertEqual(budget.status(self.root)["remaining"], 0)

    def test_unknown_invalid_initial_count_rejected(self):
        for count in (-1, 4, None, True):
            with self.assertRaises(ValueError):
                budget.initialize(self.root, "test", count)

    def test_empty_packet_does_not_consume_budget(self):
        budget.initialize(self.root, "test", 0)
        packet = self.base / "empty.md"
        packet.write_text(" \n", encoding="utf-8")
        with self.assertRaises(ValueError):
            budget.reserve(self.root, [packet])
        self.assertEqual(budget.status(self.root)["remaining"], 3)

    def test_non_markdown_rejected(self):
        budget.initialize(self.root, "test", 0)
        packet = self.base / "file.txt"
        packet.write_text("Context", encoding="utf-8")
        with self.assertRaises(ValueError):
            budget.reserve(self.root, [packet])

    def test_duplicate_packet_cannot_trigger_blind_retry(self):
        budget.initialize(self.root, "test", 0)
        packet = self.packet(0)
        budget.reserve(self.root, [packet])
        with self.assertRaisesRegex(ValueError, "already reserved"):
            budget.reserve(self.root, [packet])
        self.assertEqual(budget.status(self.root)["used_or_reserved"], 1)

    def test_uncertain_and_not_sent_do_not_refund(self):
        budget.initialize(self.root, "test", 0)
        budget.reserve(self.root, [self.packet(0)])
        budget.outcome(self.root, 1, "uncertain", "Delivery cannot be determined")
        budget.outcome(self.root, 1, "not-sent", "Later observation: no visible message")
        self.assertEqual(budget.status(self.root)["remaining"], 2)
        self.assertEqual(len(budget.status(self.root)["outcomes"]), 2)

    def test_exact_sha_and_chrome_requirement_recorded(self):
        budget.initialize(self.root, "test", 0)
        packet = self.packet(0)
        value = budget.reserve(self.root, [packet])
        self.assertEqual(value["packets"][0]["sha256"], hashlib.sha256(packet.read_bytes()).hexdigest())
        self.assertEqual(value["packets"][0]["bytes"], packet.stat().st_size)
        self.assertEqual(value["required_browser"], "Google Chrome")
        self.assertFalse(budget.status(self.root)["ui_execution_verified_by_this_script"])

    def test_split_markdown_packet_supported(self):
        budget.initialize(self.root, "test", 0)
        value = budget.reserve(self.root, [self.packet(0), self.packet(1)])
        self.assertEqual(len(value["packets"]), 2)
        self.assertEqual(budget.status(self.root)["used_or_reserved"], 1)

    def test_corrupt_ledger_fails_closed(self):
        budget.initialize(self.root, "test", 0)
        (self.root / "run.json").write_text(json.dumps({"limit": 99}), encoding="utf-8")
        with self.assertRaises(ValueError):
            budget.reserve(self.root, [self.packet(0)])

    def test_concurrent_requests_never_exceed_three_slots(self):
        budget.initialize(self.root, "test", 0)
        packets = [self.packet(index) for index in range(6)]

        def attempt(packet):
            for _ in range(100):
                try:
                    return budget.reserve(self.root, [packet])["slot"]
                except ValueError as error:
                    if "BUDGET_LOCKED" not in str(error):
                        return None
                    time.sleep(0.005)
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            slots = [slot for slot in pool.map(attempt, packets) if slot is not None]
        self.assertEqual(set(slots), {1, 2, 3})
        self.assertEqual(len(slots), 3)
        self.assertEqual(budget.status(self.root)["remaining"], 0)

    def test_concurrent_same_packet_reserves_only_once(self):
        budget.initialize(self.root, "test", 0)
        packet = self.packet(0)

        def attempt(_):
            for _ in range(100):
                try:
                    return budget.reserve(self.root, [packet])["slot"]
                except ValueError as error:
                    if "BUDGET_LOCKED" not in str(error):
                        return None
                    time.sleep(0.005)
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            slots = [slot for slot in pool.map(attempt, range(6)) if slot is not None]
        self.assertEqual(slots, [1])
        self.assertEqual(budget.status(self.root)["used_or_reserved"], 1)

    def test_interrupted_lock_is_preserved_and_blocks(self):
        budget.initialize(self.root, "test", 0)
        lock = self.root / "reservation.lock"
        lock.write_text('{"token":"old-operation"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "BUDGET_LOCKED"):
            budget.reserve(self.root, [self.packet(0)])
        self.assertTrue(lock.exists())
        self.assertEqual(budget.status(self.root)["used_or_reserved"], 0)


if __name__ == "__main__":
    unittest.main()
