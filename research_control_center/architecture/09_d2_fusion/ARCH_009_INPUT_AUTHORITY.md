# D2 input authority

| Input | V1 authority | V2 authority | Use |
|---|---|---|---|
| D0 | frozen `ScientificDetectorPredictionArtifactV1` bytes and hash | same frozen D0 authority | Boolean point alarm only |
| D1 | frozen `ScientificRulePredictionArtifactV1` bytes and hash | same frozen D1 authority | alarming record index plus relation binding |
| Source identity | frozen 42-entry relation-to-source map | same canonical source mapping | collapse duplicate rules from one source |
| Temporal authority | exact decision index | frozen 42-relation native-horizon map | V1 same-index grouping; V2 active-token interval |
| Configuration | committed V1 design/authorization hashes | separate V2 design/authorization hashes | fail-closed policy identity |

Fusion does not read raw HAI features, labels, D0 scores, or execute D0/D1.
It validates committed upstream bytes, schemas, hashes, row closure, label-blind
flags and relation/source identities. Labels become available only after the
combined prediction has been durably persisted.
