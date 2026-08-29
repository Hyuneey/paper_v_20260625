#!/usr/bin/env python3
"""Build public-safe ARCH-011 audit artifacts from static frozen evidence.

This builder writes RCC documentation only. It does not import scientific
modules, resolve private locators, access test2, or execute a reproduction.
"""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path


AUTHORITY = "2dc7e6c23d5e9503bd4953a70e6bc20e39994b6e"
RCC_HEAD = "63bfd013bfc1c897d69144129cf7192d36075587"


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    rcc = Path(__file__).resolve().parents[1]
    arch = rcc / "architecture" / "11_outer_reproducibility"
    boot = rcc / "bootstrap" / "ARCH_011"
    gen = rcc / "generated"
    arch.mkdir(parents=True, exist_ok=True)
    boot.mkdir(parents=True, exist_ok=True)

    report = """# 이 연구를 다른 환경에서도 다시 돌릴 수 있는가

## 1. 현재 OUTER에는 왜 결과가 없는가

기존 OUTER는 HAI 23.05 test2에서 D0, D1, D2 V1을 한 번만 확인하려던 confirmatory study였다.
한 번의 과학 시도가 시작된 뒤 첫 test2 feature custody 조건이 거절되었고, feature file을 열거나
읽기 전에 정지했다. 따라서 scientific result는 `UNAVAILABLE`, generalization은 `UNCONFIRMED`다.

## 2. test2를 실제로 읽었는가

Custody-level feature-file check는 1회 있었다. 그러나 feature byte read, hash, semantic parse,
label access, prediction, metric, outcome exposure는 모두 0이었다. 그러므로 “완전히 접촉하지 않았다”와
“과학적으로 읽었다”는 표현이 모두 부정확하다.

## 3. 기존 OUTER를 다시 실행하면 되는가

아니다. 단 한 번의 authorized attempt가 소비되었고 retry budget은 0이다. 구 protocol은
`NOT_RETRYABLE_BY_PROTOCOL`이다. 새 실행에는 새 study identity, authority, preregistration이 필요하다.

## 4. 새로운 held-out 검증은 무엇이 달라야 하는가

Data identity, feature/event-unit contract, development/validation/final 역할, final Rule/runtime authority,
stronger detector, fusion policy, metrics, durable prediction-before-label custody, reporting plan을 결과 전에
고정해야 한다. 같은 물리적 test2를 쓸 수 있는지는 content seal이 보존되었다는 사실만으로 결정되지
않으며 `STUDY_DESIGN_REQUIRED`다.

## 5. 현재 무엇까지 재현 가능한가

Traceability는 강하다. 같은 환경의 frozen artifact integrity replay도 부분적으로 가능하다. 반면 fresh
machine synthetic end-to-end와 scientific recomputation은 실행으로 입증되지 않았다. External full
reproduction은 private assets와 redistribution boundary 때문에 현재 불가능하다.

## 6. 같은 PC에서의 재현과 새 PC 재현은 무엇이 다른가

같은 PC에는 local custody와 과거 environment가 남아 있을 수 있다. 새 PC는 Python/package lock,
schema resources, Git authority, private asset restoration, numeric backend identity를 모두 다시 구성해야
한다. 동일 SHA만으로 동일 scientific environment가 만들어지는 것은 아니다.

## 7. 어떤 private asset이 필요한가

Raw HAI payload, private label/test2 custody, D0 preprocessing/model/threshold authority, relation/runtime
numeric authority, task-specific registries와 locators가 필요하다. 공개 release에는 payload나 path가 아니라
logical ID, hash, schema, restoration contract만 포함해야 한다.

## 8. 현재 환경 의존성

Core metadata는 Python >=3.11과 jsonschema 4.26.0을 선언한다. 하지만 scientific NumPy 2.3.5와 test
tooling은 project metadata에 완전히 선언되지 않았고 root lock이 없다. GDN의 exact environment는
CPython 3.12.13, windows-amd64, CPU, exact wheels와 external roots에 결속된다.

## 9. 절대경로·운영체제 의존성

Current core는 대체로 relative path와 explicit encoding을 사용한다. 그러나 schema loader는 source-tree
layout을 가정하고, scientific custody는 local environment bindings를 요구하며, exact GDN은 Windows
platform contract다. Historical absolute host paths는 frozen provenance이며 current recipe가 아니다.

## 10. PILOT V1은 어떻게 보존할 것인가

PILOT V1 artifacts와 현재 qualification을 그대로 보존한다. 새 lock, bridge, durable gate 또는 protocol을
과거 artifact에 소급 적용하지 않는다.

## 11. VALIDATION V2는 어떻게 분리할 것인가

새 method/config/authority/environment/experiment IDs와 prediction schema version을 사용한다. V1 hashes와
결과는 immutable predecessor로 참조하고, V2 결과만 remediated method의 evidence가 된다.

## 12. Final execution authority 선택지

RuleV1-only는 conceptual clarity가 높지만 V4 cohort/semantics를 바꿀 위험과 큰 이관 부담이 있다. Formal
V4는 가장 작은 구현 범위지만 canonical verifier claim을 좁혀야 한다. Verified canonical-to-V4 bridge는
V4 runtime 보존과 canonical admissibility를 함께 노릴 수 있으나 lossless mapping과 conformance test가
필수다. 현재 권고는 bridge를 우선 검증하고, lossless equivalence가 증명되지 않으면 formal V4로 범위를
좁히는 것이다. 이 선택은 아직 DEC-020으로 최종 승인되어야 한다.

## 13. Fresh-machine rehearsal 계획

Clone, public dependency install, import/static verification, RCC tests, synthetic contract, synthetic
candidate-to-metric smoke, public artifact restoration 순서로 진행하고 과학 데이터 전에 멈춘다. Authority와
dependency remediation 후, held-out access 전에 실행하는 것이 가장 안전하다.

## 14. 논문 제출 시 공개 가능한 범위

Source, schemas, tests, synthetic fixture, public configs, RCC docs, sanitized example artifacts, dependency
lock과 reproduction guide는 공개 가능하다. Raw/private data, credentials, private locators, restricted numeric
payload, sealed labels/test2, private provider payload는 제외한다.

## 15. 다음 remediation에서 꼭 고쳐야 할 것

첫 순서는 final authority decision과 versioned bridge contract/conformance freeze다. 이어서 D1 durable
pre-label persistence를 구현하고, environment lock/schema packaging/entrypoint를 scientific held-out 전에
fresh-machine rehearsal로 검증한다. ARCH-011은 어떤 remediation도 구현하지 않았다.
"""

    outer = """# ARCH-011 OUTER Custody Audit

## Intended role

The old study was a one-shot confirmatory HAI 23.05 P1 test2 evaluation of frozen D0, COMMON-42 D1, and D2 V1. It prohibited fitting, recalibration, rule selection, policy change, D2 V2, retry, and post-result redesign.

## Exact stop point

The state reached `OUTER_SCIENTIFIC_ATTEMPT_STARTED`. The first test2 feature custody predicate then emitted `OUTER_TEST2_FEATURE_CUSTODY_REJECTED` before file open/read and before `TEST2_FEATURE_HASH_VALIDATED`.

| Counter | Frozen historical value |
|---|---:|
| scientific attempts | 1 |
| retries | 0 |
| feature custody checks | 1 |
| feature byte reads | 0 |
| feature hashes | 0 |
| feature semantic parses | 0 |
| label accesses / parses | 0 |
| D0/D1/D2 executions | 0 |
| frozen predictions | 0 |
| metrics / outcomes | 0 |

The public blocker does not distinguish symlink from another non-regular-file condition. No more specific local cause is inferred.

## Interpretation

- Result: `UNAVAILABLE`.
- Generalization: `UNCONFIRMED`.
- Negative held-out performance: not observed.
- Old protocol: `NOT_RETRYABLE_BY_PROTOCOL`.
- Same physical test2 reuse: `STUDY_DESIGN_REQUIRED`; content sealing alone neither authorizes nor forbids a genuinely new study.
"""

    environment = """# ARCH-011 Environment Audit

The public source is inspectable without private data, but a complete fresh scientific environment is not reconstructible from project metadata alone.

Key findings:

1. `pyproject.toml` declares Python >=3.11 and `jsonschema[format-nongpl]==4.26.0`; frozen scientific NumPy 2.3.5 and pytest are not declared, and no root resolved lock exists.
2. Frozen D0 pins CPython 3.12.13 and NumPy 2.3.5 but not the NumPy wheel, BLAS/LAPACK vendor, CPU instruction set, or thread identity.
3. Exact GDN is a narrow CPython 3.12.13/windows-amd64/CPU/exact-wheel/external-root contract; generic `.[gdn]` is not equivalent.
4. Canonical and v6 schema loaders assume a repository source-tree layout; schemas are not evidenced as installed package data.
5. Git checkout/ancestry is part of several governance gates. A wheel or source archive without `.git` cannot replay every historical authorization path.
6. Private HAI, numeric, model, registry, and locator assets are intentionally external. This is a custody boundary, not a reason to publish them.
7. RCC Python is stdlib/path-relative; its Windows batch launcher is convenience debt, not a scientific blocker.

Classification: `PASS_WITH_PORTABILITY_BLOCKERS`. Fresh-machine remains P1 engineering hardening before held-out execution, not a blocker to read-only design work.
"""

    portability = """# ARCH-011 Portability Audit

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
"""

    levels = """# ARCH-011 Reproduction Levels

| Level | Question | Current classification | Qualification |
|---|---|---|---|
| 1 Traceability | Can source/config/artifact/report identities be located? | STRONG / SUPPORTED | Several aggregation/restoration edges remain partial. |
| 2 Same-machine replay | Can frozen integrity evidence be replayed locally? | PARTIAL / MODERATE | Narrow artifact replay exists; full PILOT recomputation is neither authorized nor demonstrated. |
| 3 Fresh-machine synthetic | Can a clean clone install and run non-scientific E2E smoke? | NOT YET DEMONSTRATED | Public tests/fixtures exist, but lock, schema packaging, and one workflow are incomplete. |
| 4 Fresh-machine scientific | Can authorized scientific results be recreated? | NOT DEMONSTRATED / BLOCKED | Requires private assets, environment capsule, authority decision, and explicit authorization. |
| 5 Independent external | Can a third party reproduce without private assets? | PARTIAL CODE-ONLY; FULL SCIENCE NOT AVAILABLE | Synthetic contracts can be released; restricted scientific payloads cannot. |

Never report the project simply as “reproducible: yes/no.”
"""

    new_heldout = """# ARCH-011 New Held-Out Requirements

Before any new held-out outcome is exposed, freeze:

1. a new study identity and preregistration;
2. data/file/split identity and custody policy;
3. feature and event-unit contracts;
4. development, policy-selection, validation, and final-test roles;
5. VALIDATION V2 method, canonical-to-V4 bridge or alternative final authority;
6. D0/stronger detector, COMMON portfolio, numeric authority, and fusion policy;
7. shared Recall/FAR metric contracts and reporting plan;
8. durable predictions for every arm before label access;
9. a one-shot budget and no-post-test-tuning rule;
10. environment/release manifest and fresh-machine rehearsal receipt.

The old protocol grants no retry. Reusing the same physical test2 is not automatically authorized or prohibited: zero content was exposed, but a new study must decide whether custody-only contact preserves its intended independence. If that cannot be defended prospectively, select a new data identity or split.
"""

    pilot = """# ARCH-011 PILOT V1 Reproduction Status

| Question | Status |
|---|---|
| Traceable? | YES, with explicit source, artifact, config, and public-report lineage. |
| Integrity replayed? | YES for audited frozen result/artifact checks in the original environment. |
| Same-machine scientific recomputation? | NOT AUTHORIZED and NOT DEMONSTRATED by ARCH-011. |
| Fresh-machine scientific recomputation? | NOT DEMONSTRATED. |
| External full scientific reproduction? | NOT AVAILABLE without authorized private assets. |

PILOT V1 stays immutable. Its interpretation remains qualified by V4 authority, D1's weaker in-memory pre-label gate, test1 development scope, and absent held-out result. No artifact is retroactively rewritten or invalidated.
"""

    versioning = """# ARCH-011 VALIDATION V2 Versioning

VALIDATION V2 must use prospective identities rather than silently replacing PILOT V1:

- new method and experiment IDs;
- new config/environment and data-manifest IDs;
- a final authority/bridge version and conformance receipt;
- versioned prediction/trace/result schemas when custody or fields change;
- a new preregistration and one-shot held-out authorization;
- immutable references to all PILOT V1 artifacts and qualifications.

Only V2 outputs may support remediated-method claims. V1 remains historical pilot evidence. Graph-Guided and Agentic remain conditional on EXP-01 and EXP-03.
"""

    fresh = """# ARCH-011 Fresh-Machine Rehearsal Protocol

This protocol is a design only; ARCH-011 did not execute it.

| Stage | Inputs | Expected output | Failure criterion | Private assets? | Scientific execution? |
|---|---|---|---|---|---|
| 1 Clone | exact reviewed release commit | clean checkout and recorded Git/OS/CPU | wrong SHA, dirty tree | No | No |
| 2 Install | public locked core/test profile | resolved package receipt | undeclared/unresolved dependency | No | No |
| 3 Import/static | package, schemas, configs | imports and packaged resource closure | source-tree-only resource failure | No | No |
| 4 RCC tests | RCC public files | validator and RCC unit PASS | stale registry/privacy violation | No | No |
| 5 Synthetic contract | synthetic fixture only | schema/split/authority negative tests PASS | private locator/network required | No | No |
| 6 Synthetic E2E | synthetic candidate/evidence/rule data | candidate -> relation -> rule -> verifier -> runtime -> metric smoke | uncontrolled code/provider/label leakage | No | No |
| 7 Artifact restore | public/sanitized manifest | checksum/identity replay | missing or stale public artifact | No | No |
| 8 Optional science | separately authorized private assets | new VALIDATION V2 receipt | any missing gate or pre-label custody failure | Yes | Yes |

The first rehearsal stops after Stage 7. Run it after final-authority, dependency, schema-resource, and entrypoint remediation, and before any held-out access.

One-command commands such as `python -m paperworks status`, `smoke`, and `verify-artifacts` are `USEFUL`, not required for the thesis if the same staged commands are documented and tested.
"""

    release = """# ARCH-011 Release Scope

## Public thesis release

- source and schemas/contracts;
- public configs, tests, and synthetic fixtures;
- RCC architecture/claim/governance documents;
- sanitized example artifacts and public checksums;
- dependency lock, environment manifest, installation and staged smoke instructions;
- data acquisition/provenance instructions and license/terms notices;
- explicit statement that result integrity is not scientific validation.

## Exclude

- raw HAI or other restricted payloads;
- sealed labels/test2 and private paths;
- credentials, `.env` custody bindings, tokens, or provider secrets;
- private numeric/model/threshold payloads and restricted predictions;
- raw provider responses when custody prohibits release.

## Checkpoint strategy

ARCH-011 does not push. After user decisions and one reviewed privacy/cleanliness/stale-branch check, a single RCC branch checkpoint push is reasonable. It must not include private assets or imply scientific-authority mutation.
"""

    mismatches = """# ARCH-011 Mismatches

| ID | Incorrect or risky wording/state | Audited boundary | Severity |
|---|---|---|---|
| M-011-01 | old OUTER can simply retry | one authorized attempt consumed; zero retries | HIGH |
| M-011-02 | full scientific environment is dependency-locked | NumPy/test tooling/root lock incomplete | HIGH |
| M-011-03 | installed wheel is equivalent to source checkout | schema loaders and Git gates assume repository layout | HIGH |
| M-011-04 | fresh-machine scientific replay is available | private assets and environment capsule are missing | HIGH |
| M-011-05 | generic GDN optional install reproduces frozen GDN | exact Windows/wheel/root contract differs | HIGH |
| M-011-06 | test2 was untouched or scientifically read | one custody check, zero content reads | MEDIUM |
| M-011-07 | same physical test2 is automatically reusable | new-study design/authorization decision required | MEDIUM |
| M-011-08 | same-machine integrity replay equals scientific recomputation | scope and authorization differ | MEDIUM |
| M-011-09 | historical preservation bundle is current restore capsule | it predates current RCC/scientific state | MEDIUM |
| M-011-10 | private scientific assets are public-regenerable | payloads remain external/restricted | MEDIUM |
| M-011-11 | PILOT V1 and VALIDATION V2 may share unversioned identity | prospective method/version separation required | MEDIUM |
| M-011-12 | bridge is already the locked authority | it is preferred but DEC-020 remains open | MEDIUM |
| M-011-13 | Windows dashboard launcher blocks science | underlying RCC scripts are portable stdlib | LOW |
| M-011-14 | a one-command CLI is mandatory | useful hardening, not thesis-critical | LOW |

Totals: 14 — CRITICAL 0, HIGH 5, MEDIUM 7, LOW 2.
"""

    gap_update = """# ARCH-011 GAP-000 Impact Update

- Changed priorities: none.
- New root blockers: none. Dependency and schema-layout findings refine GAP-011/GAP-012.
- Removed blockers: none.
- Fresh-machine rehearsal remains engineering hardening with urgency P1 before held-out execution, not before read-only design work.
- GAP-001 authority choice remains global pre-validation work; bridge portability cost is real but does not reverse the preferred target.
- PILOT V1 remains interpretable with qualifications; invalidated artifacts remain 0.
"""

    multi = """# ARCH-011 Multi-Agent Review

Four independent read-only specialists audited environment, OUTER custody, artifact portability, and reproduction/release. The coordinator cross-checked their outputs against the pinned source and GAP-000. Independent QA was run only after synthesis.

Resolved synthesis points:

- Custody contact is not content access.
- Same-machine artifact replay is not fresh-machine scientific reproduction.
- Private assets are expected custody dependencies, but missing public lock/schema/entrypoint closure is portability debt.
- The bridge is recommended prospectively, not recorded as already approved.
- No specialist executed science, accessed test2 content, installed packages, or modified scientific source.
"""

    user_summary = """# OUTER와 재현성을 쉽게 이해하기

## 1. OUTER가 정확히 무엇인가?

개발에 쓰지 않은 held-out test2에서 frozen D0/D1/D2 V1을 한 번 확인하려던 confirmatory study다.

## 2. 왜 결과가 없는가?

유일한 시도가 시작된 뒤 첫 feature custody 검사에서 파일을 열기 전에 중단되었다. Prediction과 metric이 없으므로 성능 결과도 없다.

## 3. test2 내용은 본 적이 있는가?

Custody check는 1회였지만 feature bytes/hash/parse와 labels는 모두 0이다. 즉 과학 내용은 보지 않았다.

## 4. 그냥 다시 실행하면 왜 안 되는가?

One-shot attempt가 소비되었고 retry 권한이 0이기 때문이다. 새 study와 preregistration이 필요하다.

## 5. 새 held-out은 어떻게 해야 하는가?

Data, method, authority, event unit, metrics, fusion policy, environment, prediction-before-label 순서를 결과 전에 고정해야 한다. 같은 test2 reuse 여부도 새 연구가 명시적으로 결정해야 한다.

## 6. traceability와 reproducibility는 뭐가 다른가?

Traceability는 어떤 source/artifact가 결과를 만들었는지 찾는 능력이다. Reproducibility는 실제 다른 환경에서 같은 절차와 출력을 다시 만드는 능력이다.

## 7. same-machine과 fresh-machine은 뭐가 다른가?

같은 PC에는 local asset과 environment가 남아 있다. Fresh machine은 dependency, schema, Git authority, private restoration을 처음부터 재구성해야 한다.

## 8. 현재 프로젝트는 어디까지 재현 가능한가?

Traceability는 강하고 same-machine integrity replay는 부분 지원된다. Fresh-machine synthetic/scientific reproduction은 아직 실행으로 입증되지 않았다.

## 9. PILOT V1과 VALIDATION V2를 왜 나누는가?

과거 결과를 새 code와 protocol로 소급 변경하지 않기 위해서다. V1은 그대로 보존하고 remediation 결과는 V2로만 평가한다.

## 10. 어떤 authority option이 가장 현실적인가?

Verified canonical RuleV1/VerifierV1-to-V4 bridge를 먼저 검증하는 안이 가장 균형적이다. V4 runtime을 보존하면서 canonical validity를 연결할 수 있다. 단 lossless equivalence가 증명되어야 하며 최종 승인은 아직 필요하다.

## 11. fresh-machine rehearsal은 언제 해야 하는가?

Authority/dependency/entrypoint remediation 뒤, held-out 접근 전이다. 첫 rehearsal은 synthetic/public 단계에서 멈춘다.

## 12. 논문 공개본에는 무엇을 포함해야 하는가?

Source, tests, schemas, synthetic fixture, public configs, RCC docs, lock과 guide를 포함한다. Raw/private data, test2, credentials, private numeric/model payload는 제외한다.

기억할 한 문장: **현재 연구는 잘 추적되지만, 새 컴퓨터에서 과학 결과를 다시 만드는 상태는 아직 아니다.**
"""

    docs = {
        "ARCH_011_REPORT.md": report,
        "ARCH_011_OLD_OUTER_TIMELINE.md": outer,
        "ARCH_011_NEW_HELDOUT_REQUIREMENTS.md": new_heldout,
        "ARCH_011_PILOT_V1_REPRODUCTION.md": pilot,
        "ARCH_011_REPRODUCTION_LEVELS.md": levels,
        "ARCH_011_VALIDATION_V2_VERSIONING.md": versioning,
        "ARCH_011_FRESH_MACHINE_PROTOCOL.md": fresh,
        "ARCH_011_RELEASE_SCOPE.md": release,
        "ARCH_011_MISMATCHES.md": mismatches,
        "ARCH_011_GAP_UPDATE.md": gap_update,
    }
    for name, payload in docs.items():
        write_text(arch / name, payload)

    env_rows = [
        {"dependency":"Python core","version_pin":">=3.11","required_for":"package/RCC","declared_where":"pyproject.toml","installable_from_public_source":"YES","private":"false","platform_sensitive":"LOW","determinism_sensitive":"YES","missing":"project-wide exact interpreter lock","risk":"MEDIUM"},
        {"dependency":"CPython","version_pin":"3.12.13 frozen D0/GDN","required_for":"exact PILOT replay","declared_where":"scientific contracts/receipts","installable_from_public_source":"YES_IN_PRINCIPLE","private":"false","platform_sensitive":"YES","determinism_sensitive":"YES","missing":"not project-wide lock","risk":"HIGH"},
        {"dependency":"jsonschema[format-nongpl]","version_pin":"4.26.0","required_for":"schema validation","declared_where":"pyproject.toml","installable_from_public_source":"YES","private":"false","platform_sensitive":"LOW","determinism_sensitive":"YES","missing":"transitive lock","risk":"MEDIUM"},
        {"dependency":"NumPy","version_pin":"2.3.5 frozen D0","required_for":"STAT/D0","declared_where":"source and receipts only","installable_from_public_source":"YES","private":"false","platform_sensitive":"YES","determinism_sensitive":"YES","missing":"pyproject declaration; wheel/BLAS/thread lock","risk":"HIGH"},
        {"dependency":"torch","version_pin":"2.12.1 optional","required_for":"GDN","declared_where":"pyproject optional gdn","installable_from_public_source":"YES_IN_PRINCIPLE","private":"false","platform_sensitive":"YES","determinism_sensitive":"YES","missing":"exact wheelhouse equivalence","risk":"MEDIUM"},
        {"dependency":"torch-geometric","version_pin":"2.8.0 optional","required_for":"GDN","declared_where":"pyproject optional gdn","installable_from_public_source":"YES_IN_PRINCIPLE","private":"false","platform_sensitive":"YES","determinism_sensitive":"YES","missing":"exact validated environment","risk":"MEDIUM"},
        {"dependency":"pytest","version_pin":"UNKNOWN","required_for":"repository tests","declared_where":"test imports only","installable_from_public_source":"YES","private":"false","platform_sensitive":"LOW","determinism_sensitive":"NO","missing":"dev/test dependency group","risk":"MEDIUM"},
        {"dependency":"Git CLI","version_pin":"UNKNOWN current contract","required_for":"authority/ancestry gates","declared_where":"governance subprocess calls","installable_from_public_source":"YES","private":"false","platform_sensitive":"MEDIUM","determinism_sensitive":"YES","missing":"portable minimum/manifest mode","risk":"MEDIUM"},
        {"dependency":"Exact GDN wheelhouse/roots","version_pin":"hash-bound windows-amd64","required_for":"exact GDN scientific environment","declared_where":"gdn remediation environment","installable_from_public_source":"PARTIAL","private":"true","platform_sensitive":"HIGH","determinism_sensitive":"YES","missing":"portable restoration capsule","risk":"HIGH"},
        {"dependency":"HAI/private authorities","version_pin":"logical IDs/hashes","required_for":"scientific replay","declared_where":"custody manifests","installable_from_public_source":"NO_FROM_CLONE","private":"true","platform_sensitive":"PATH","determinism_sensitive":"YES","missing":"payload intentionally excluded","risk":"EXPECTED"},
        {"dependency":"Provider SDK","version_pin":"NOT_APPLICABLE","required_for":"historical/future construction only","declared_where":"stdlib urllib transport","installable_from_public_source":"STDLIB","private":"false","platform_sensitive":"NETWORK","determinism_sensitive":"YES","missing":"external model service","risk":"EXP03_ONLY"},
        {"dependency":"RCC dashboard","version_pin":"stdlib","required_for":"RCC views/tests","declared_where":"RCC scripts","installable_from_public_source":"YES","private":"false","platform_sensitive":"LOW; .bat convenience only","determinism_sensitive":"NO","missing":"portable launcher docs","risk":"LOW"},
    ]
    write_csv(arch / "ARCH_011_ENVIRONMENT_MATRIX.csv", ["dependency","version_pin","required_for","declared_where","installable_from_public_source","private","platform_sensitive","determinism_sensitive","missing","risk"], env_rows)

    path_rows = [
        {"issue_id":"PATH-01","surface":"schema resources","assumption":"repository-root schemas via module parents","classification":"SOURCE_TREE_DEPENDENCY","severity":"HIGH","sanitized_action":"package resources or explicitly test repository-checkout release mode"},
        {"issue_id":"PATH-02","surface":"scientific custody","assumption":"external environment bindings","classification":"EXPECTED_PRIVATE_BOUNDARY","severity":"MEDIUM","sanitized_action":"path-silent restoration manifest"},
        {"issue_id":"PATH-03","surface":"GDN","assumption":"windows-amd64 and external roots","classification":"FROZEN_PLATFORM_CONTRACT","severity":"MEDIUM","sanitized_action":"restore exact environment or version new validated one"},
        {"issue_id":"PATH-04","surface":"Git governance","assumption":"checkout ancestry and source closure","classification":"GIT_RUNTIME_DEPENDENCY","severity":"MEDIUM","sanitized_action":"choose Git checkout or signed release-manifest run mode"},
        {"issue_id":"PATH-05","surface":"historical reports","assumption":"legacy host paths/commands","classification":"FROZEN_PROVENANCE_NOT_CURRENT_RECIPE","severity":"MEDIUM","sanitized_action":"do not copy locators into release guide"},
        {"issue_id":"PATH-06","surface":"RCC launcher","assumption":"Windows batch convenience","classification":"CONVENIENCE_ONLY","severity":"LOW","sanitized_action":"document portable Python command"},
    ]
    write_csv(arch / "ARCH_011_PATH_MACHINE_ASSUMPTIONS.csv", ["issue_id","surface","assumption","classification","severity","sanitized_action"], path_rows)

    artifact_rows = [
        {"artifact":"source/contracts/tests","classification":"PUBLIC_REGENERABLE","needed_for_code":"YES","needed_for_synthetic":"YES","needed_for_pilot_replay":"YES","needed_for_validation_v2":"YES","release":"INCLUDE","notes":"exact reviewed commit"},
        {"artifact":"HAI provenance/manifests","classification":"PUBLIC_FROZEN","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"YES","needed_for_validation_v2":"YES","release":"INCLUDE_METADATA_ONLY","notes":"payload external/restricted"},
        {"artifact":"raw HAI/test labels/test2","classification":"LOCAL_ONLY","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"YES","needed_for_validation_v2":"YES","release":"EXCLUDE","notes":"authorized custody only"},
        {"artifact":"GDN ranking/environment evidence","classification":"PUBLIC_RANKING_PLUS_PRIVATE_SEED_LEDGERS","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"CONDITIONAL","needed_for_validation_v2":"EXP01","release":"SANITIZED_RECEIPTS_ONLY","notes":"no persisted GDN model checkpoint; exact external roots/wheels required"},
        {"artifact":"candidate artifacts","classification":"PUBLIC_FROZEN","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"YES","needed_for_validation_v2":"VERSION_NEW","release":"SANITIZED_INCLUDE","notes":"aggregate/provenance safe"},
        {"artifact":"relation artifacts","classification":"PUBLIC_FROZEN_WITH_PRIVATE_EVIDENCE","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"YES","needed_for_validation_v2":"VERSION_NEW","release":"SANITIZED_INCLUDE","notes":"no raw values"},
        {"artifact":"numeric authority","classification":"PRIVATE_FROZEN","needed_for_code":"NO","needed_for_synthetic":"SYNTHETIC_ONLY","needed_for_pilot_replay":"YES","needed_for_validation_v2":"YES","release":"SCHEMA_HASH_ONLY","notes":"private payload excluded"},
        {"artifact":"COMMON-42","classification":"PUBLIC_FROZEN","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"YES","needed_for_validation_v2":"BRIDGE_OR_NEW_VERSION","release":"SANITIZED_INCLUDE","notes":"V4 pilot authority"},
        {"artifact":"D0 preprocessing/model/threshold","classification":"PRIVATE_FROZEN","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"YES","needed_for_validation_v2":"YES","release":"HASH_RECEIPT_ONLY","notes":"numeric payload private"},
        {"artifact":"D0/D1/D2 public-safe prediction artifacts","classification":"PUBLIC_FROZEN","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"INTEGRITY_ONLY","needed_for_validation_v2":"NEW_OUTPUT","release":"INCLUDE_PUBLIC_SAFE","notes":"tracked sanitized frozen artifacts; not raw private inputs"},
        {"artifact":"private prediction restoration inputs","classification":"LOCAL_ONLY","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"CONDITIONAL","needed_for_validation_v2":"AUTHORIZED_ONLY","release":"EXCLUDE","notes":"private inputs and custody material are not redistributed"},
        {"artifact":"metric/result reports","classification":"PUBLIC_FROZEN","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"YES","needed_for_validation_v2":"NEW_OUTPUT","release":"INCLUDE_SANITIZED","notes":"integrity is not validation"},
        {"artifact":"old preservation bundle","classification":"LOCAL_ONLY_STALE","needed_for_code":"NO","needed_for_synthetic":"NO","needed_for_pilot_replay":"PARTIAL","needed_for_validation_v2":"NO","release":"NOT_CURRENT_CAPSULE","notes":"historical checkpoint only"},
    ]
    write_csv(arch / "ARCH_011_ARTIFACT_PORTABILITY.csv", ["artifact","classification","needed_for_code","needed_for_synthetic","needed_for_pilot_replay","needed_for_validation_v2","release","notes"], artifact_rows)

    authority_rows = [
        {"option":"A_RULEV1_END_TO_END","implementation_scope":"LARGE","scientific_clarity":"HIGH","pilot_v1_preservation":"RISK_OF_SEMANTIC_OR_COHORT_CHANGE","v4_runtime_compatibility":"REQUIRES_PORT_OR_REWRITE","verifier_claim_coherence":"HIGH_IF_COMPLETE","reproduction_complexity":"HIGH","testing_burden":"HIGH","portability":"GOOD_AFTER_COMPLETION","bug_risk":"HIGH","assessment":"NOT_RECOMMENDED_FOR_ELEGANCE_ONLY"},
        {"option":"B_FORMAL_V4","implementation_scope":"SMALL_TO_MEDIUM","scientific_clarity":"HIGH_IF_METHOD_NARROWED","pilot_v1_preservation":"STRONG","v4_runtime_compatibility":"DIRECT","verifier_claim_coherence":"CANONICAL_CLAIM_MUST_BE_NARROWED","reproduction_complexity":"LOWEST","testing_burden":"MEDIUM","portability":"BEST_IMMEDIATE","bug_risk":"LOWEST","assessment":"FALLBACK_MINIMUM_SCOPE"},
        {"option":"C_VERIFIED_CANONICAL_TO_V4_BRIDGE","implementation_scope":"MEDIUM","scientific_clarity":"HIGH_IF_LOSSLESS","pilot_v1_preservation":"STRONG","v4_runtime_compatibility":"DIRECT_AFTER_BRIDGE","verifier_claim_coherence":"HIGH_WITH_CONFORMANCE_RECEIPT","reproduction_complexity":"MEDIUM","testing_burden":"HIGH_TARGETED","portability":"GOOD_WITH_VERSIONED_BRIDGE","bug_risk":"MEDIUM","assessment":"RECOMMENDED_PROSPECTIVE_TARGET_PENDING_DEC020"},
    ]
    write_csv(arch / "ARCH_011_AUTHORITY_OPTIONS.csv", ["option","implementation_scope","scientific_clarity","pilot_v1_preservation","v4_runtime_compatibility","verifier_claim_coherence","reproduction_complexity","testing_burden","portability","bug_risk","assessment"], authority_rows)

    evidence = {
        "task_id": "ARCH-011", "status": "READ_ONLY_AUDIT_COMPLETE", "verdict": "PASS_WITH_PROSPECTIVE_PORTABILITY_GATES",
        "rcc_head": RCC_HEAD, "scientific_authority": AUTHORITY,
        "old_outer": {"result":"UNAVAILABLE", "retryability":"NOT_RETRYABLE_BY_PROTOCOL", "feature_custody_checks":1, "feature_byte_reads":0, "semantic_parses":0, "label_accesses":0, "predictions":0, "metrics":0, "outcomes":0, "same_test2_reuse":"STUDY_DESIGN_REQUIRED"},
        "reproduction_levels": {"traceability":"STRONG", "same_machine":"PARTIAL_MODERATE", "fresh_machine_synthetic":"NOT_DEMONSTRATED", "fresh_machine_scientific":"NOT_DEMONSTRATED_BLOCKED", "external":"PARTIAL_CODE_ONLY"},
        "authority_recommendation": "C_VERIFIED_CANONICAL_TO_V4_BRIDGE_PENDING_USER_APPROVAL; FALLBACK_B_IF_LOSSLESS_EQUIVALENCE_CANNOT_BE_PROVEN",
        "gap_update": {"changed_priorities":0, "new_root_blockers":0, "removed_blockers":0, "pilot_invalidated_artifacts":0},
        "mismatches": {"total":14, "critical":0, "high":5, "medium":7, "low":2},
        "safety": {"scientific_executions":0, "test2_content_accesses":0, "scientific_source_changes":0, "remediation_implementations":0, "fresh_machine_runs":0, "dependency_installs":0, "remote_pushes":0},
    }
    write_text(boot / "ARCH_011_EVIDENCE.json", json.dumps(evidence, indent=2, ensure_ascii=False))

    boot_map = {
        "ARCH_011_REPORT.md": report,
        "ARCH_011_OUTER_CUSTODY_AUDIT.md": outer,
        "ARCH_011_ENVIRONMENT_AUDIT.md": environment,
        "ARCH_011_PORTABILITY_AUDIT.md": portability,
        "ARCH_011_REPRODUCTION_LEVELS.md": levels,
        "ARCH_011_FRESH_MACHINE_PROTOCOL.md": fresh,
        "ARCH_011_VALIDATION_V2_VERSIONING.md": versioning,
        "ARCH_011_RELEASE_SCOPE.md": release,
        "ARCH_011_MISMATCHES.md": mismatches,
        "ARCH_011_MULTI_AGENT_REVIEW.md": multi,
    }
    for name, payload in boot_map.items():
        write_text(boot / name, payload)
    shutil.copyfile(arch / "ARCH_011_AUTHORITY_OPTIONS.csv", boot / "ARCH_011_AUTHORITY_OPTIONS.csv")
    write_text(gen / "ARCH_011_USER_SUMMARY.md", user_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
