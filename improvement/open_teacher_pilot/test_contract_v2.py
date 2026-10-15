import copy
import unittest
from contract_v2 import SCHEMA,parse,validate


class Contract(unittest.TestCase):
    def setUp(self):
        self.item={'state':'UNCERTAIN','start':0,'end':63,'evidence':[0,63],'fact':'no certain highlight decision'}

    def test_generated_and_validated_budget_same(self):
        self.assertEqual(SCHEMA['properties']['spans']['maxItems'],3)
        validate({'spans':[self.item]})
        with self.assertRaises(ValueError):validate({'spans':[self.item]*4})

    def test_overlap_and_off_span_evidence(self):
        first=dict(self.item,start=0,end=12,evidence=[0])
        second=dict(self.item,start=12,end=27,evidence=[19])
        with self.assertRaises(ValueError):validate({'spans':[first,second]})
        second['start']=13;validate({'spans':[first,second]})
        second['evidence']=[12]
        with self.assertRaises(ValueError):validate({'spans':[first,second]})

    def test_no_coercion_or_legacy_conversion(self):
        for field,bad in [('start',True),('end',63.0),('state','NO'),('evidence',[True]),('fact','x'*97)]:
            item=copy.deepcopy(self.item);item[field]=bad
            with self.assertRaises(ValueError):validate({'spans':[item]})
        with self.assertRaises(ValueError):parse('{"spans":[],"spans":[]}')
        with self.assertRaises(ValueError):validate({'keep':[],'ordinary':[],'uncertain':[]})


if __name__=='__main__':unittest.main()
