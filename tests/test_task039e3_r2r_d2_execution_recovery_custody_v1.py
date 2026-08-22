from __future__ import annotations

import contextlib
import copy
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from paperworks.v6 import task039e3_r2r_d2_execution_recovery_custody_v1 as c


class D2RecoveryCustodyV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.root = base / "private"
        self.repo.mkdir()
        self.root.mkdir()
        self.token = c._issue_synthetic_recovery_root_v1(self.root, self.repo)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_approved_root_and_contract_identity(self) -> None:
        self.assertTrue(self.token.outside_git)
        self.assertFalse(self.token.symlink)
        self.assertIn("REDACTED", repr(self.token))
        self.assertEqual(64, len(c.RECOVERY_CUSTODY_MODULE_IDENTITY))

    def test_repository_root_rejected(self) -> None:
        with self.assertRaises(c.D2RecoveryCustodyV1Error):
            c._issue_synthetic_recovery_root_v1(self.repo, self.repo)

    def test_reconstructed_and_deepcopied_root_rejected(self) -> None:
        forged = c.D2RecoveryPrivateRootV1(
            self.token.custody_version, self.token.module_identity, True, False,
            self.token.permission_policy, self.root,
        )
        with self.assertRaises(c.D2RecoveryCustodyV1Error):
            c._validate_root_v1(forged)
        with self.assertRaises(c.D2RecoveryCustodyV1Error):
            copy.deepcopy(self.token)

    def test_atomic_create_rename_reopen_cleanup(self) -> None:
        name = ".sentinel-static"
        payload = b"NON_SCIENTIFIC_SENTINEL"
        self.assertEqual(payload, c._atomic_write_bytes_v1(
            self.token, name, payload, allow_sentinel=True,
        ))
        target = self.root / name
        self.assertEqual(payload, target.read_bytes())
        target.unlink()
        self.assertFalse(target.exists())

    def test_existing_target_and_temp_fail_closed(self) -> None:
        name = ".sentinel-existing"
        (self.root / name).write_bytes(b"x")
        with self.assertRaisesRegex(c.D2RecoveryCustodyV1Error, "TARGET_EXISTS"):
            c._atomic_write_bytes_v1(self.token, name, b"y", allow_sentinel=True)
        (self.root / name).unlink()
        (self.root / f".{name}.tmp").write_bytes(b"x")
        with self.assertRaisesRegex(c.D2RecoveryCustodyV1Error, "TARGET_EXISTS"):
            c._atomic_write_bytes_v1(self.token, name, b"y", allow_sentinel=True)

    def test_unapproved_filename_rejected(self) -> None:
        with self.assertRaises(c.D2RecoveryCustodyV1Error):
            c.write_recovery_private_json_atomic_v1(
                self.token, "alternate.json", {"artifact_hash": "0" * 64}
            )

    def test_path_redacted_permission_error(self) -> None:
        secret_token = "PRIVATE_TOKEN_SHOULD_NEVER_ESCAPE"
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("pathlib.Path.open", side_effect=PermissionError(secret_token)):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(c.D2RecoveryCustodyV1Error) as caught:
                    c._atomic_write_bytes_v1(
                        self.token, ".sentinel-permission", b"x", allow_sentinel=True,
                    )
        channels = (str(caught.exception), repr(caught.exception), stdout.getvalue(), stderr.getvalue())
        self.assertTrue(all(secret_token not in item for item in channels))
        self.assertEqual("D2_RECOVERY_PRIVATE_CUSTODY_WRITE_DENIED", caught.exception.code)

    def test_path_redacted_rename_error(self) -> None:
        secret_token = "PRIVATE_RENAME_TOKEN_SHOULD_NEVER_ESCAPE"
        with mock.patch("os.replace", side_effect=OSError(secret_token)):
            with self.assertRaises(c.D2RecoveryCustodyV1Error) as caught:
                c._atomic_write_bytes_v1(
                    self.token, ".sentinel-rename", b"x", allow_sentinel=True,
                )
        self.assertNotIn(secret_token, str(caught.exception))
        self.assertNotIn(secret_token, repr(caught.exception))
        self.assertEqual("D2_RECOVERY_PRIVATE_CUSTODY_ATOMIC_RENAME_FAILED", caught.exception.code)

    def test_symlink_flag_rejected(self) -> None:
        with mock.patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaisesRegex(c.D2RecoveryCustodyV1Error, "SYMLINK"):
                c._issue_synthetic_recovery_root_v1(self.root, self.repo)

    def test_synthetic_preflight_is_zero_science(self) -> None:
        receipt = c._build_synthetic_preflight_v1(self.token)
        self.assertEqual(receipt.artifact_hash, c.validate_d2_recovery_custody_preflight_v1(receipt))
        self.assertEqual(0, receipt.fusion_computations)
        self.assertEqual(0, receipt.scientific_d0_prediction_parses)
        self.assertEqual(0, receipt.scientific_d1_prediction_parses)
        self.assertEqual(0, receipt.label_parses)
        self.assertEqual(0, receipt.metric_computations)
        self.assertEqual(0, receipt.test2_accesses)


if __name__ == "__main__":
    unittest.main()
