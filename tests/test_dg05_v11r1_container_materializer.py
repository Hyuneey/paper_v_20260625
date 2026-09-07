from __future__ import annotations

import gzip
import tempfile
import unittest
from pathlib import Path

from paperworks.validation_v2.dg05_production_chain_v11 import file_hash
from paperworks.validation_v2.dg05_v11r1_container_materializer import (
    DG05V11R1ContainerMaterializerError,
    inspect_container_framing_v11r1,
    materialize_execution_sources_v11r1,
)


class ContainerMaterializerTests(unittest.TestCase):
    def _plan(self, root: Path) -> dict[str, object]:
        rows = []
        for index in range(10):
            payload = f"synthetic-container-{index}\n".encode("ascii")
            source = root / f"source-{index}.csv"
            container = "IDENTITY"
            if index >= 5:
                source = source.with_suffix(".csv.gz")
                source.write_bytes(gzip.compress(payload, mtime=0))
                container = "GZIP"
            else:
                source.write_bytes(payload)
            rows.append({"panel_id": f"SYNTHETIC_{index}", "file_id": f"file-{index}.csv",
                         "path": str(source), "sha256": file_hash(source), "container_type": container})
        return {"physical_custody_hash": "a" * 64, "files": rows}

    def test_framing_and_lossless_synthetic_decode(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); plan = self._plan(root)
            framing = inspect_container_framing_v11r1(plan=plan)
            self.assertEqual(framing["gzip_streams_materialized"], 0)
            decoded, authority = materialize_execution_sources_v11r1(
                plan=plan, output_root=root / "execution", permit_gzip_decode=True
            )
            self.assertEqual(authority["gzip_streams_materialized"], 5)
            self.assertEqual(authority["csv_parser_invocations"], 0)
            for row in decoded["files"]:
                self.assertEqual(file_hash(Path(row["path"])), row["sha256"])

    def test_real_container_decode_is_fail_closed_without_permission(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); plan = self._plan(root)
            with self.assertRaisesRegex(DG05V11R1ContainerMaterializerError, "POSTAPPROVAL_GZIP_DECODE_REQUIRED"):
                materialize_execution_sources_v11r1(plan=plan, output_root=root / "execution", permit_gzip_decode=False)


if __name__ == "__main__":
    unittest.main()
