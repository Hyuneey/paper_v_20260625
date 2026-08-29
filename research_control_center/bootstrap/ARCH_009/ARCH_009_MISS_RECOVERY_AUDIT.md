# Miss-recovery audit

- D0 misses: 3 contiguous event units.
- D1 responses: 3/3.
- V1 admitted: 0/3.
- V2 admitted: 0/3.

V1's frozen sanitized diagnostic identifies two `MULTI_SOURCE_ASYNCHRONOUS`
units and one `SINGLE_SOURCE_ONLY` unit. V2 deliberately retains the two-source
requirement and still recovers none; public evidence does not freeze a complete
per-unit V2 failure trace for the two asynchronous cases.
