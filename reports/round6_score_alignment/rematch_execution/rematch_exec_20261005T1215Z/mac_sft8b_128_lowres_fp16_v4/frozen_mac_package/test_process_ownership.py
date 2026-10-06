import unittest
from finish_mac import classify_external
class Ownership(unittest.TestCase):
    def test_owned_descendants_and_external_compute(self):
        processes="10 1 python controller\n11 10 python trainer\n12 11 python -c resource_tracker\n13 12 python helper\n20 1 python external_train\n21 1 ollama serve\n30 1 /usr/bin/ssh\n"
        self.assertEqual({x['pid'] for x in classify_external(processes,{10})},{20,21})
    def test_detached_external_helper_still_blocks(self):
        self.assertEqual(classify_external("12 1 python -c resource_tracker",{10})[0]['pid'],12)
if __name__=='__main__':unittest.main()
