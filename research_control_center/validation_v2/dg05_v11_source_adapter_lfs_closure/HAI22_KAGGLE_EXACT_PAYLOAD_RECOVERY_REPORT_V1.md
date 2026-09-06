# HAI22 exact Kaggle payload recovery

Status: `COMPLETE_QA_PASS`

The exact four frozen HAI22 paths were derived from the prior blocker receipt and pinned Git LFS pointers. Each file was downloaded individually from the official public Kaggle dataset `icsdataset/hai-security-dataset`, version 10. Each one-entry download archive contained the exact requested basename.

All four extracted opaque payloads matched both the Git LFS SHA-256 OID and declared byte size exactly:

| File ID | Bytes | SHA-256 / LFS OID | Status |
|---|---:|---|---|
| `test1.csv` | 50,536,532 | `19627f5dac40c3a5039e7468cfd6c6e4ccd37a85055671e8c349b6bce5f50ed1` | `MATERIALIZED_PAYLOAD_VERIFIED` |
| `test2.csv` | 46,616,720 | `b2ba5d6665deee1c86870a3970417b51a3e640a2cc18b9f8de2d6d8a21979923` | `MATERIALIZED_PAYLOAD_VERIFIED` |
| `test3.csv` | 35,066,591 | `f253f1c78a4a4654d843f8f670a24caa7a72ac91e4418b4505009822b3c55940` | `MATERIALIZED_PAYLOAD_VERIFIED` |
| `test4.csv` | 72,931,406 | `2d2e99ed3364d75d27ab84f0a6523496f7295decf363c90b8a1b9b84e1070376` | `MATERIALIZED_PAYLOAD_VERIFIED` |

The verified payloads replaced only their corresponding pointer files in the approved external official checkout. The six previously available payload identities were rehashed without decompression or scientific parsing. Final frozen held-out byte custody is 10/10 verified.

## Access boundary

- Payload bytes were downloaded, extracted, hashed, and copied as opaque binary objects.
- CSV parsers invoked: 0.
- Headers inspected: 0.
- Rows parsed: 0.
- Feature values inspected: 0.
- Label values parsed or inspected: 0.
- Scenario records accessed: 0.
- Predictions executed: 0.
- Metrics computed: 0.
- Credential values exposed: 0.
- Raw payloads committed: 0.
- Private paths published: 0.

No DG-05 execution, scenario-adapter work, or successor-release work was performed.
