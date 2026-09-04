"""Data-free context selection tests; no optional Torch import."""
import unittest
from audit_xver_gdn_context_v1 import mapped_context


class ContextTests(unittest.TestCase):
    def test_ordered_intersection(self):
        self.assertEqual(mapped_context(('b','a','c'),(('c','b','new'),)),('b','c'))

    def test_missing_is_not_replaced(self):
        self.assertEqual(mapped_context(('P1_PP04D',), (('P1_PP04','P1_PP04SP'),)),())

    def test_no_alias_inference(self):
        self.assertEqual(mapped_context(('P1_X',), (('P1_XD','P1_XZ'),)),())

    def test_file_schema_conflict(self):
        with self.assertRaisesRegex(ValueError,'INCONSISTENT'):
            mapped_context(('a',),(('a',),('b',)))

    def test_duplicate_rejection(self):
        for c,s in [(('a','a'),(('a',),)),(('a',),(('a','a'),))]:
            with self.assertRaises(ValueError): mapped_context(c,s)

    def test_unknowns_not_added(self):
        self.assertEqual(mapped_context(('a',),(('a','Attack','unknown'),)),('a',))

    def test_empty_schema_rejected(self):
        with self.assertRaises(ValueError): mapped_context(('a',),())


if __name__=='__main__': unittest.main()
