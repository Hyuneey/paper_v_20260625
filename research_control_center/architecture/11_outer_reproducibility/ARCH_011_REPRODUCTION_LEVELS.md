# ARCH-011 Reproduction Levels

| Level | Question | Current classification | Qualification |
|---|---|---|---|
| 1 Traceability | Can source/config/artifact/report identities be located? | STRONG / SUPPORTED | Several aggregation/restoration edges remain partial. |
| 2 Same-machine replay | Can frozen integrity evidence be replayed locally? | PARTIAL / MODERATE | Narrow artifact replay exists; full PILOT recomputation is neither authorized nor demonstrated. |
| 3 Fresh-machine synthetic | Can a clean clone install and run non-scientific E2E smoke? | NOT YET DEMONSTRATED | Public tests/fixtures exist, but lock, schema packaging, and one workflow are incomplete. |
| 4 Fresh-machine scientific | Can authorized scientific results be recreated? | NOT DEMONSTRATED / BLOCKED | Requires private assets, environment capsule, authority decision, and explicit authorization. |
| 5 Independent external | Can a third party reproduce without private assets? | PARTIAL CODE-ONLY; FULL SCIENCE NOT AVAILABLE | Synthetic contracts can be released; restricted scientific payloads cannot. |

Never report the project simply as “reproducible: yes/no.”
