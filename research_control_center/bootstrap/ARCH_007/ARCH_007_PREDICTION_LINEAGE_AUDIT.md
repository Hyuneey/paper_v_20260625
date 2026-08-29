# ARCH-007 Prediction / Result Lineage Audit

Frozen authority → 54,000 test1 feature rows → 54,000 private SPE values → strict Boolean alarms → 54,000-record public prediction → atomic persistence/replay → label access → 46 alarm episodes → 11/14 event recall and 0.4939336325682589 normal false episodes/hour.

The public prediction has 876 alarm points, contains no score/threshold/label values, and is byte-checked before metrics and after result generation. Independent integrity evidence confirms 54,000-record closure, 876 points, 46 episodes, exact public metric values, zero accepted invalid mutations, and zero post-freeze changes.

