# ARCH-002 GDN Audit

Verdict: `VERIFIED_WITH_CONSERVATIVE_INTERPRETATION_AND_DOCUMENTED_LIMITATIONS`.

The current passing authority is `UpstreamAlignedGDN`, not the generic smoke backend or earlier blocked history. It trains on normal train1/train2 full P1 context to forecast next values. Node-embedding cosine similarity forms the learned graph; three seed graphs are projected to the frozen 144-pair universe and aggregated.

Graph attention is internal message passing. Its coefficients are not candidate-ranking or final relationship evidence. No post-hoc XAI, SHAP, or attribution is used. An edge is a target-indexed neighbor/input dependency candidate, not temporal cause or confirmed response. The 37×37 Top-5 graph does not remove the diagonal first, so a self identity can consume an internal neighbor slot; the later disjoint-role projection removes exported self pairs, and the functional effect remains untested.

Frozen evidence: three seeds, 39 supported, Top-20. Unique useful GDN contribution remains unvalidated. Scientific executions and test2 accesses: 0.
