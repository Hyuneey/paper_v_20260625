# Draft inquiry to the HAI dataset/challenge authors — NOT SENT

Subject: Request for the official HAI 21.03, 22.04, and 23.05 attack-scenario metadata specification

Dear HAI dataset team,

We are preparing a preregistered, result-blind evaluation using the official HAI releases. To reproduce the published attack units without inferring them from observed labels, could you clarify the following separately for HAI 21.03, HAI 22.04, and HAI 23.05?

1. What exactly defines one official attack/scenario occurrence, and how is its stable ID assigned?
2. How is each occurrence bound to a physical test file?
3. What are the authoritative start/end timestamp semantics, including endpoint inclusion, timezone, precision, and cross-midnight behavior?
4. Can one occurrence contain multiple disjoint intervals? If so, how are intervals grouped and ordered? How should repeated or simultaneous interventions be represented?
5. Which official fields identify directly attacked controllers/sensors/actuators, and what are their delimiter, multiplicity, missing-value, and escaping rules?
6. Is affected-process information explicitly supplied, and how should it be distinguished from directly attacked process/point identities?
7. Which artifact is authoritative when label files, summary files, and technical-manual tables differ?
8. What is the canonical scenario and interval ordering, and how should duplicate IDs, duplicate intervals, malformed records, or unknown fields be handled?
9. Is there a machine-readable attack metadata file, schema, generator, or parser that produces the published nominal counts for the evaluated panels (HAI 23.05 `hai-test2`: 38; HAI 22.04 test1–test4: 58; HAI 21.03 test1–test5: 50)? If so, could you provide a versioned link or checksum?

We are not requesting model results or interpretation. A schema, parser, or occurrence-level crosswalk with version provenance would be sufficient.

Sincerely,

[Researcher]
