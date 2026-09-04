import io
from pathlib import Path
import tempfile
import unittest

from paperworks.data.hai_normal_projection_v2 import project, selected_rows, require_projected_fields
from paperworks.validation_v2.exp03b_contract_v1 import digest


class ProjectionTests(unittest.TestCase):
    def one(self, excluded=b'0', approved=b'1', extra=b'opaque'):
        root = Path(self.directory.name)
        i = len(list(root.iterdir()))
        src, dst = root/f'{i}.csv', root/f'{i}.projection'
        src.write_bytes(b'timestamp;F;attack;unknown\n2020-01-01 00:00:00;' + approved + b';' + excluded + b';' + extra + b'\n')
        return project(src, dst, ('F',), allowlist_hash=digest(['F'])), dst.read_bytes()

    def setUp(self): self.directory = tempfile.TemporaryDirectory()
    def tearDown(self): self.directory.cleanup()

    def test_excluded_mutation_invariant(self):
        a, raw = self.one()
        for excluded in (b'not-a-number', b'NaN', b'\xff\xfe', b'"a;b"', b'"a\nb"', b'""'):
            b, other = self.one(excluded)
            self.assertEqual(raw, other)
            self.assertEqual(a['projection_hash'], b['projection_hash'])
            self.assertFalse(b['label_values_parsed'])

    def test_downstream_invariant(self):
        import csv
        values = []
        for label in (b'0', b'999', b'\xff'):
            _, raw = self.one(label)
            row = next(csv.DictReader(io.StringIO(raw.decode())))
            self.assertEqual(set(row), {'timestamp', 'F'})
            values.append(float(row['F']) ** 2)
        self.assertEqual(values, [1, 1, 1])

    def test_unknown_not_added(self):
        receipt, raw = self.one(extra=b'\xff')
        self.assertNotIn(b'unknown', raw)
        self.assertEqual(receipt['projected_feature_identities'], ['F'])
        with self.assertRaises(ValueError): require_projected_fields(receipt, ('unknown',))
        with self.assertRaises(ValueError): require_projected_fields(receipt, ('attack',))

    def test_selected_bad_utf8_fails(self):
        with self.assertRaises(UnicodeDecodeError): self.one(approved=b'\xff')

    def test_allowed_numeric_failure(self):
        with self.assertRaises(ValueError): self.one(approved=b'NaN')

    def test_span_selection_and_order(self):
        rows = list(selected_rows(io.BytesIO(b'1,\xff,2\n3,"x,y",4\n'), b',', 3, (2, 0)))
        self.assertEqual(rows, [(b'2', b'1'), (b'4', b'3')])

    def test_no_implicit_extra_column(self):
        with self.assertRaises(ValueError): list(selected_rows(io.BytesIO(b'1,2,3,4\n'), b',', 3, (0,)))

    def test_missing_approved_fails(self):
        root = Path(self.directory.name)
        p = root/'input.csv'; p.write_bytes(b'time;F;attack\n2020-01-01;1;0\n')
        with self.assertRaises(ValueError): project(p, root/'out.csv', ('G',), allowlist_hash=digest(['G']))

    def test_reserved_field_rejected_before_open(self):
        for name in ('attack','label','scenario','anomaly','class','timestamp'):
            with self.assertRaisesRegex(ValueError, 'RESERVED_FIELD'):
                project(Path('not-opened'), Path('not-written'), (name,), allowlist_hash=digest([name]))

    def test_allowlist_authority_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'FEATURE_AUTHORITY_HASH'):
            project(Path('not-opened'), Path('not-written'), ('F',), allowlist_hash=digest(['G']))

    def test_eof_trailing_empty(self):
        self.assertEqual(list(selected_rows(io.BytesIO(b'1,x,'),b',',3,(0,))), [(b'1',)])
        self.assertEqual(list(selected_rows(io.BytesIO(b'1,x,'),b',',3,(2,))), [(b'',)])

    def test_escaped_quotes_and_crlf(self):
        self.assertEqual(list(selected_rows(io.BytesIO(b'1,"a""b\r\nc",2\r\n'),b',',3,(0,2))), [(b'1',b'2')])


if __name__ == '__main__': unittest.main()
