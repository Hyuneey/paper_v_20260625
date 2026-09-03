"""Synthetic metadata contact tests: no network or scientific input."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("exp03_metadata", ROOT / "scripts/exp03_model_access_preflight_v1.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ModelAccessPreflightTests(unittest.TestCase):
    def setup_root(self, temporary):
        root = Path(temporary)
        target = root / MODULE.BASE
        target.mkdir(parents=True)
        (target / "DG03_FIXED_SNAPSHOT_APPROVAL_V1.json").write_bytes(
            (ROOT / MODULE.BASE / "DG03_FIXED_SNAPSHOT_APPROVAL_V1.json").read_bytes())
        return root

    def test_exact_approval_and_alias_rejected(self):
        doc = json.loads((ROOT / MODULE.BASE / "DG03_FIXED_SNAPSHOT_APPROVAL_V1.json").read_bytes())
        MODULE.check_approval(doc)
        for field, value in (("model_snapshot", "gpt-5.4-mini"), ("scientific_concurrency", 2), ("maximum_generation_calls", 820)):
            with self.assertRaises(ValueError):
                MODULE.check_approval({**doc, field: value})

    def test_no_credential_no_contact(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(MODULE.os.environ, {}, clear=True), patch.object(MODULE.http.client, "HTTPSConnection") as connection:
            result = MODULE.run(self.setup_root(directory))
            self.assertEqual(result["status"], "BLOCKED_CREDENTIAL_UNAVAILABLE")
            connection.assert_not_called()

    def test_401_body_not_read_and_no_retry(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(MODULE.os.environ, {"OPENAI_API_KEY": "synthetic"}), patch.object(MODULE.http.client, "HTTPSConnection") as connection:
            root = self.setup_root(directory)
            response = connection.return_value.getresponse.return_value
            response.status = 401
            result = MODULE.run(root)
            self.assertEqual(result["status"], "BLOCKED_PROVIDER_AUTHENTICATION")
            response.read.assert_not_called()
            with self.assertRaises(ValueError):
                MODULE.run(root)
            self.assertEqual(connection.return_value.request.call_count, 1)

    def test_reservation_before_request_and_exact_identity(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(MODULE.os.environ, {"OPENAI_API_KEY": "synthetic"}), patch.object(MODULE.http.client, "HTTPSConnection") as connection:
            root = self.setup_root(directory)
            def check(*args, **kwargs):
                self.assertTrue((root / MODULE.BASE / "MODEL_ACCESS_RESERVATION_V1.json").is_file())
                self.assertEqual(args, ("GET", MODULE.ENDPOINT))
            connection.return_value.request.side_effect = check
            response = connection.return_value.getresponse.return_value
            response.status = 200
            response.read.return_value = json.dumps({"id": MODULE.MODEL, "object": "model"}).encode()
            result = MODULE.run(root)
            self.assertEqual(result["status"], "MODEL_METADATA_ACCESS_PASS")
            self.assertFalse(result["generation_capability_verified"])

    def test_persistence_failure_blocks_transport(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(MODULE, "persist_new", side_effect=OSError), patch.object(MODULE.http.client, "HTTPSConnection") as connection:
            with self.assertRaises(OSError):
                MODULE.run(self.setup_root(directory))
            connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
