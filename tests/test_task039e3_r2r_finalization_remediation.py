from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from paperworks.v6.task039e3_r2r_result_finalizer_v1 import (
    PRIVATE_ARTIFACT_NAMES_R2R_V1,
    PUBLIC_ARTIFACT_NAMES_R2R_V1,
    SUCCESS_STATUS,
    TASK039E3R2RResultFinalizationError,
    finalize_successful_r2r_scientific_result_v1,
)
from paperworks.v6.task039e3_recovery_serialization_v1 import (
    verify_public_artifact_v1,
    write_public_artifact_atomic_v1,
)
from tests.test_task039e3_r2r_finalization_v1 import _arguments


class R2RFinalizationRemediationTests(unittest.TestCase):
    def test_each_private_terminal_artifact_delete_or_corrupt_blocks_pass(self) -> None:
        for target_key, filename in PRIVATE_ARTIFACT_NAMES_R2R_V1.items():
            for mutation in ("delete", "corrupt"):
                with self.subTest(target=target_key, mutation=mutation):
                    with tempfile.TemporaryDirectory() as temporary:
                        base = Path(temporary)
                        private = base / "private"
                        public = base / "public"
                        private.mkdir()
                        target = private / "final_authoritative_r2r_v1" / filename

                        def writer(
                            path: str | Path, document: dict[str, object]
                        ) -> dict[str, object]:
                            destination = Path(path)
                            written = write_public_artifact_atomic_v1(
                                destination, document
                            )
                            if (
                                destination.name
                                == PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]
                            ):
                                if mutation == "delete":
                                    target.unlink()
                                else:
                                    altered = json.loads(
                                        target.read_text(encoding="utf-8")
                                    )
                                    altered["artifact_hash"] = "0" * 64
                                    target.write_text(
                                        json.dumps(
                                            altered,
                                            sort_keys=True,
                                            separators=(",", ":"),
                                        )
                                        + "\n",
                                        encoding="utf-8",
                                    )
                            return written

                        arguments = _arguments(private, public)
                        arguments["artifact_writer"] = writer
                        with self.assertRaises(TASK039E3R2RResultFinalizationError):
                            finalize_successful_r2r_scientific_result_v1(**arguments)

    def test_terminal_receipt_delete_or_corrupt_after_write_blocks_pass(self) -> None:
        for mutation in ("delete", "corrupt"):
            with self.subTest(mutation=mutation):
                with tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary)
                    private = base / "private"
                    public = base / "public"
                    private.mkdir()

                    def writer(
                        path: str | Path, document: dict[str, object]
                    ) -> dict[str, object]:
                        destination = Path(path)
                        written = write_public_artifact_atomic_v1(
                            destination, document
                        )
                        if (
                            destination.name
                            == PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]
                        ):
                            if mutation == "delete":
                                destination.unlink()
                            else:
                                altered = dict(written)
                                altered["artifact_hash"] = "0" * 64
                                destination.write_text(
                                    json.dumps(
                                        altered,
                                        sort_keys=True,
                                        separators=(",", ":"),
                                    )
                                    + "\n",
                                    encoding="utf-8",
                                )
                        return written

                    arguments = _arguments(private, public)
                    arguments["artifact_writer"] = writer
                    with self.assertRaises(TASK039E3R2RResultFinalizationError):
                        finalize_successful_r2r_scientific_result_v1(**arguments)

    def test_returned_hashes_come_from_reread_durable_terminal_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            private = base / "private"
            public = base / "public"
            private.mkdir()

            def misleading_return_writer(
                path: str | Path, document: dict[str, object]
            ) -> dict[str, object]:
                destination = Path(path)
                written = write_public_artifact_atomic_v1(destination, document)
                if (
                    destination.name
                    == PUBLIC_ARTIFACT_NAMES_R2R_V1["execution_receipt"]
                ):
                    return written
                return {"artifact_hash": "0" * 64}

            arguments = _arguments(private, public)
            arguments["artifact_writer"] = misleading_return_writer
            result = finalize_successful_r2r_scientific_result_v1(**arguments)
            self.assertEqual(result.status, SUCCESS_STATUS)
            self.assertEqual(result.public_artifact_order[-1], "execution_receipt")

            for key, filename in PUBLIC_ARTIFACT_NAMES_R2R_V1.items():
                observed = verify_public_artifact_v1(
                    json.loads((public / filename).read_text(encoding="utf-8"))
                )
                self.assertEqual(
                    result.public_artifact_hashes[key], observed["artifact_hash"]
                )
            private_root = private / "final_authoritative_r2r_v1"
            for key, filename in PRIVATE_ARTIFACT_NAMES_R2R_V1.items():
                observed = verify_public_artifact_v1(
                    json.loads((private_root / filename).read_text(encoding="utf-8"))
                )
                self.assertEqual(
                    result.private_artifact_hashes[key], observed["artifact_hash"]
                )
            self.assertEqual(
                result.execution_receipt_hash,
                result.public_artifact_hashes["execution_receipt"],
            )


if __name__ == "__main__":
    unittest.main()
