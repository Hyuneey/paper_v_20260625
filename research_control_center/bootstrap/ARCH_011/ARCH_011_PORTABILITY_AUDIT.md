# ARCH-011 Portability Audit

## Boundary

Code/synthetic portability and scientific-result portability are different. A public clone does not contain or authorize raw HAI, sealed labels/test2, private numeric authorities, D0 model parameters, or task-specific custody locators.

## Current classifications

- Source, contracts, public configs, RCC docs, tests, and sanitized reports: public and traceable.
- HAI acquisition metadata and file identities: public-safe metadata; payload externally acquired and not redistributed.
- Candidate/relation/COMMON-42 public artifacts: frozen or regenerable only within their disclosed public/private boundary.
- Numeric authorities, D0 model/threshold payloads, scientific predictions: private/local authority; hashes and aggregate receipts may be public.
- Old preservation bundle: hash-audited historical capsule, but stale relative to current RCC and not a complete scientific restore set.

## Portability blocker

There is no single release manifest that binds source commit, dependency lock, packaged schemas, public artifact checksums, and path-silent private restoration requirements. VALIDATION V2 must create that prospective capsule without rewriting PILOT V1.
