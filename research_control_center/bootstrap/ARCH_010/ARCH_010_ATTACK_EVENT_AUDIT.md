# Attack-event Audit

- Policy: maximal file-local contiguous runs of strict label token `1`.
- Interval: half-open `[start,end)`.
- Count: 14 contiguous attack-event units.
- Independence: NOT_ESTABLISHED.
- Hit: any half-open alarm-episode overlap; PA-FREE; no grace/dilation/minimum duration.
- Frozen Recall: D0 11/14; D1 13/14; D2 V1 11/14; D2 V2 11/14.
- Safety: existing sanitized manifests and result artifacts only; no label payload read or metric recomputation.
