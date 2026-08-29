# Result Integrity Audit

D0 and D2 use durable prediction persistence/replay before labels. D1 validates and shallow-freezes the complete prediction object before labels, but lacks the stronger durable file-before-label gate. Downstream identity and arithmetic audits do not compensate fully for that upstream difference.

Integrity checks establish prediction/label identities, row/order closure, arithmetic consistency, artifact/report binding, and recorded mutation/replay status. They do not establish event independence, sample sufficiency, generalization, superiority, utility, or scientific validity. V2 remains test1-informed development. No frozen authoritative inferential test exists.
