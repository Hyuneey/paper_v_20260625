import unittest
from paperworks.data.hai_xver_normal_v1 import validate_header,validate_contract
from paperworks.validation_v2.exp03b_custody_v1 import seal


class XverNormalTests(unittest.TestCase):
    def test_schema_versions(self):
        validate_header(['timestamp']+[f'F{i}' for i in range(86)],'22.04')
        validate_header(['time']+[f'F{i}' for i in range(78)],'21.03')

    def test_labels_before_rows(self):
        with self.assertRaises(ValueError):validate_header(['timestamp','attack']+[f'F{i}' for i in range(85)],'22.04')

    def test_wrong_edition(self):
        with self.assertRaises(ValueError):validate_header(['timestamp']+[f'F{i}' for i in range(86)],'21.03')

    def test_empty_allowlist(self):
        d=seal({'pinned_commit':'2a814cebc9a66b06c9e5cd545e2d72e65d383737','attack_access_allowed':False,'provider_calls_allowed':False,'label_columns_allowed':False,'records':[]})
        with self.assertRaises(ValueError):validate_contract(d)

    def test_duplicate_columns(self):
        with self.assertRaises(ValueError):validate_header(['timestamp']+['X']*86,'22.04')

    def test_unknown_version(self):
        with self.assertRaises(ValueError):validate_header(['timestamp'],'23.05')


if __name__=='__main__':unittest.main()
