# Preservation manifest

| item | status | SHA-256 | notes |
|---|---|---|---|
| all-refs Git bundle | PASS | `232b6c9c0224e1109878e571ed0f45c2703e38e6e2e20426afe55cd5cd591dd1` | complete history verified; local-only |
| source-only HEAD archive | PASS | `8427aacf47697b045224349ccd898d722a9360dfe99660ffb15a4c87ee7b0b3d` | tracked source/tests/config and method/v6 docs only; task results excluded |
| environment manifest | PASS | n/a | sanitized, no local paths |
| canonical branch inventory | PASS | n/a | decision-relevant subset in reproducibility report |
| thesis artifact index | PASS | n/a | public artifacts only |

Excluded by construction: untracked raw HAI, private numeric registries, models/threshold values, private evidence, credentials, and local paths.

Limitation: this is a local preservation package, not an off-site disaster-recovery copy. No remote egress was authorized.
