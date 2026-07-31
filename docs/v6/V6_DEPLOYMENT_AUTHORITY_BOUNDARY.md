# V6 Deployment Authority Boundary

A v6 delayed-response rule is deployable only when all of these exact
artifacts agree:

1. accepted Rule v1;
2. accepted Verifier v1 result;
3. canonical v6 context collection;
4. `selected_rule` governance binding;
5. synthetic-only runtime authorization receipt;
6. v6 deployment authorization receipt.

`V6DeploymentAuthorizationReceiptV1` binds the governance and runtime receipts
without executing the rule. P1C authorizes only `synthetic_only` scope.

The following never create deployment authority:

- evidence or collection integrity alone;
- a construction candidate receipt;
- verifier acceptance without governance;
- `no_rule`;
- `no_op`;
- runtime `abstain`;
- outer or sealed evidence.

TASK-039P1C does not call `execute_delayed_response_rule`.
