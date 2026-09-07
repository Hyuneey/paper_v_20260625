from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from paperworks.validation_v2.dg05_production_chain_v11 import canonical_bytes, self_hashed
from paperworks.validation_v2.dg05_v11r2r1_execution_binding import (
    DG05V11R2R1ExecutionBindingError,
    build_execution_binding_v11r2r1,
    replay_execution_binding_v11r2r1,
)


V5 = "ea16f4475de97a224af35627cada524bca1183285cda0ebeede26b54d1b42525"


class V11R2R1ExecutionBindingTests(unittest.TestCase):
    def test_replay_rejects_candidate_or_source_census_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = Path(__file__).resolve().parents[1]
            source = root / "v5.py"
            shutil.copyfile(project / "src/paperworks/validation_v2/dg05_production_route_v5.py", source)
            helper = root / "helper.py"; helper.write_text("x = 1\n", encoding="ascii")
            from paperworks.validation_v2.dg05_production_chain_v11 import file_hash
            rows = [
                {"logical_name": "helper", "relative_path": "helper.py", "byte_hash": file_hash(helper)},
                {"logical_name": "v5_kernel", "relative_path": "v5.py", "byte_hash": file_hash(source)},
            ]
            binding = build_execution_binding_v11r2r1(
                repository_root=root, implementation_source_commit="a" * 40,
                implementation_authorities=rows, authority_hashes={"root": "b" * 64},
                predecessor_release_hash="c" * 64, predecessor_closure_hash="d" * 64,
                predecessor_execution_binding_hash="e" * 64,
            )
            path = root / "binding.json"; path.write_bytes(canonical_bytes(binding) + b"\n")
            candidate = {
                "execution_binding_hash": binding["self_hash"], "designation": "DG05_EXECUTABLE_V11R2R2",
                "implementation_source_commit": "a" * 40, "authority_hashes": {"root": "b" * 64},
                "frozen_v5_kernel_hash": V5, "predecessor_release_hash": "c" * 64,
                "predecessor_closure_hash": "d" * 64, "predecessor_execution_binding_hash": "e" * 64,
                "implementation_authorities": sorted(rows, key=lambda row: row["logical_name"]),
            }
            receipt = replay_execution_binding_v11r2r1(repository_root=root, binding_path=path, candidate_manifest=candidate)
            self.assertEqual(receipt["status"], "PASS")
            candidate["implementation_source_commit"] = "f" * 40
            with self.assertRaises(DG05V11R2R1ExecutionBindingError):
                replay_execution_binding_v11r2r1(repository_root=root, binding_path=path, candidate_manifest=candidate)
