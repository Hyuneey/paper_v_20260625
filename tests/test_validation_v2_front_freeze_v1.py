from hashlib import sha256
import importlib.util
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from paperworks.validation_v2.private_vault_v1 import validate_private_path_v1


class FrontFreezeTests(unittest.TestCase):
    def test_any_protected_input_or_freeze_mutation_fails(self):
        spec=importlib.util.spec_from_file_location("front_runner_test",Path(__file__).resolve().parents[1]/"scripts/run_gdn_front_exp04.py")
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/module.FREEZE;path.parent.mkdir(parents=True);path.write_bytes(b"freeze")
            document={"source_hashes":{"code":"a"},"protected_inputs":{"config":"b"}}
            digest=sha256(b"freeze").hexdigest()
            with patch.object(module,"source_hashes",return_value={"code":"a"}),patch.object(module,"protected_inputs",return_value={"config":"b"}):
                module.assert_frozen_inputs(root,document,digest)
                with self.assertRaisesRegex(ValueError,"FROZEN_EXECUTION_INPUT_MUTATION"):
                    module.assert_frozen_inputs(root,{**document,"protected_inputs":{"config":"c"}},digest)
                path.write_bytes(b"mutation")
                with self.assertRaises(ValueError):module.assert_frozen_inputs(root,document,digest)

    def test_lexical_escape_and_reparse_ancestor_fail_before_open(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaisesRegex(ValueError,"OUTSIDE_AUTHORIZED_ROOT"):
                validate_private_path_v1(root/".."/"foreign",allowed_root=root)
            with patch.object(Path,"lstat",return_value=SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=1024)):
                with self.assertRaisesRegex(ValueError,"REPARSE"):
                    validate_private_path_v1(root/"new"/"payload",allowed_root=root)

if __name__=="__main__":unittest.main()
