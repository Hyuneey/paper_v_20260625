from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from paperworks.validation_v2.io_hash_v1 import sha256_file_v1


class ValidationV2IoHashV1Tests(unittest.TestCase):
    def test_streaming_digest_is_byte_identical_across_chunk_sizes(self) -> None:
        payload = (bytes(range(251)) * 9000) + b"final"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(payload)
            expected = sha256(payload).hexdigest()
            for chunk_bytes in (1, 7, 1024, 1024 * 1024):
                self.assertEqual(sha256_file_v1(path, chunk_bytes=chunk_bytes), expected)

    def test_invalid_inputs_fail_before_read(self) -> None:
        with self.assertRaises(TypeError):
            sha256_file_v1("artifact.bin")  # type: ignore[arg-type]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(b"payload")
            for invalid in (0, -1, True, 1.5):
                with self.assertRaises(ValueError):
                    sha256_file_v1(path, chunk_bytes=invalid)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
