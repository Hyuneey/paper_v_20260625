from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


_REQUIRED_ENV = (
    "TASK039E3_HISTORICAL_REPOSITORY",
    "TASK039E3_E1_LEDGER",
    "TASK039E3_ORIGINAL_PROPOSAL_LEDGER",
    "TASK039E3_ORIGINAL_PROVIDER_LEDGER",
    "TASK039E3_ORIGINAL_OUTCOME_LEDGER",
    "TASK039E3_CUSTODY_SUPPLEMENT",
)


_INDEPENDENT_RECONSTRUCTION = textwrap.dedent(
    r"""
    import json
    import os
    from collections import Counter
    from pathlib import Path
    import subprocess

    from paperworks.v6.common import stable_hash_v1
    from paperworks.v6.task039e0_rule_construction_prep_v1 import canonical_proposal_hash_v1
    from paperworks.v6.task039e2_execution_configuration_v1 import ProviderProposalCoreV1, RuleProposalEnvelopeV1, WINDOW_NUMERIC_ROLES
    from paperworks.v6.task039e3_execution_prep_v1 import E0_BUDGET_POLICY_HASH, EXECUTION_SCHEDULE_HASH, PROVIDER_MODEL_RECEIPT_HASH, build_main_request_v1
    from paperworks.v6.task039e3_orchestration_v1 import T0_TEMPLATE_HASH, _envelope_to_dict, _project_proposal_document, _provenance
    from paperworks.v6.task039e3_scientific_execution_v1 import PUBLIC_COHORT_FILE, SCHEDULE_FILE, _load_json, _verify_self_hash, load_real_evidence_schedule_v1

    repo = Path(os.environ['TASK039E3_HISTORICAL_REPOSITORY']).resolve(strict=True)
    head = subprocess.run(
        ['git', '-c', f'safe.directory={repo}', 'rev-parse', 'HEAD'],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert head == '5dca2d0431d60ef2f2bdfc907ebfe3fe18521f16'

    cohort = _load_json(repo / PUBLIC_COHORT_FILE)
    _verify_self_hash(cohort, '4eb4da843a61a9c72aba59edcdf90e49766fc571af7eade14d500b3d04d363d4')
    schedule = _load_json(repo / SCHEDULE_FILE)
    _verify_self_hash(schedule, '6db63485387924b28e9ce498aae46412a127ba69055a28e72880e1afffa4c4ca')
    identities = schedule['relation_identities']
    assert len(identities) == len(set(identities)) == 42
    evidence = load_real_evidence_schedule_v1(
        private_ledger_path=Path(os.environ['TASK039E3_E1_LEDGER']),
        public_cohort=cohort,
        relation_identities=identities,
    )
    evidence_by_identity = {item.relation.relation_identity: item for item in evidence}
    assert len(evidence_by_identity) == 42

    proposal_ledger = _load_json(Path(os.environ['TASK039E3_ORIGINAL_PROPOSAL_LEDGER']))
    _verify_self_hash(proposal_ledger, '1d573ae83a147edf4aacb2a806016d7cfaf23b90d17e11e4e7b3c885c30e0e93')
    proposals = proposal_ledger['records']
    assert proposal_ledger['record_count'] == len(proposals) == 251

    expected = {}
    counts = Counter()
    proposal_hashes = validity_hashes = record_hashes = 0
    for record in proposals:
        project = record['project_proposal']
        references = project['preregistered_window_constant_references']
        variables = project['variables']
        assert len(references) == len(WINDOW_NUMERIC_ROLES)
        core = ProviderProposalCoreV1(
            dsl_family=project['dsl_family'],
            relation_identity=project['relation_identity'],
            source=project['source'],
            source_step_direction=project['source_step_direction'],
            target=project['target'],
            target_response_direction=project['target_response_direction'],
            selected_delay_horizon_seconds=project['selected_delay_horizon_seconds'],
            source_threshold_reference=project['source_threshold_reference'],
            source_stability_reference=project['source_stability_reference'],
            target_scale_reference=project['target_scale_reference'],
            window_constant_references=dict(zip(WINDOW_NUMERIC_ROLES, references)),
            variables=tuple(variables),
            runtime_logic_family=project['runtime_logic'],
        )
        arm = record['arm']
        call_number = record['call_number']
        if arm == 'T2':
            assert call_number == 1
        item = evidence_by_identity[record['relation_identity']]
        provenance = _provenance(
            evidence=item,
            arm=arm,
            prompt_version='T0_TEMPLATE_V1' if arm == 'T0' else 'MAIN_INITIAL_PROMPT_V1',
        )
        assert _project_proposal_document(core=core, evidence=item, provenance=provenance) == project
        assert canonical_proposal_hash_v1(project) == record['proposal_hash'] == project['proposal_hash']
        proposal_hashes += 1
        validity = record['validity_result']
        assert validity['proposal_hash'] == record['proposal_hash']
        assert stable_hash_v1({key: value for key, value in validity.items() if key != 'artifact_hash'}) == record['validity_hash'] == validity['artifact_hash']
        validity_hashes += 1
        view = item.render_view()
        prompt_hash = T0_TEMPLATE_HASH if arm == 'T0' else build_main_request_v1(view).model_visible_content_hash
        envelope = RuleProposalEnvelopeV1(
            proposal_core=core,
            construction_arm=arm,
            local_call_number=call_number,
            budget_policy_hash=E0_BUDGET_POLICY_HASH,
            evidence_hash=view.evidence_hash,
            prompt_hash=prompt_hash,
            provider_model_receipt_hash=None if arm == 'T0' else PROVIDER_MODEL_RECEIPT_HASH,
            execution_schedule_hash=EXECUTION_SCHEDULE_HASH,
        )
        preimage = {
            'relation_identity': record['relation_identity'],
            'arm': arm,
            'call_number': call_number,
            'proposal_envelope': _envelope_to_dict(envelope),
            'proposal_hash': record['proposal_hash'],
            'validity_hash': record['validity_hash'],
        }
        assert stable_hash_v1(preimage) == record['record_hash']
        record_hashes += 1
        key = (record['relation_identity'], arm, call_number)
        assert key not in expected
        expected[key] = {**preimage, 'original_record_hash': record['record_hash'], 'recomputed_record_hash': record['record_hash']}
        counts[arm] += 1

    assert counts == {'T0': 42, 'T1': 42, 'T1-B': 125, 'T2': 42}
    assert len(expected) == proposal_hashes == validity_hashes == record_hashes == 251
    independent_digest = stable_hash_v1({'records': [expected[key] for key in sorted(expected)]})

    provider = _load_json(Path(os.environ['TASK039E3_ORIGINAL_PROVIDER_LEDGER']))
    _verify_self_hash(provider)
    failed = [record for record in provider['records'] if record['parse_status'] != 'valid_structured']
    assert len(failed) == 1
    slot = failed[0]['slot']
    assert (slot['arm'], slot['relation_schedule_index'], slot['arm_local_call_number'], failed[0]['parse_status']) == ('T1-B', 19, 2, 'schema_parse_failure')
    missing_key = (identities[19], 'T1-B', 2)
    assert missing_key not in expected
    outcomes = _load_json(Path(os.environ['TASK039E3_ORIGINAL_OUTCOME_LEDGER']))
    _verify_self_hash(outcomes)
    outcome = next(record for record in outcomes['records'] if record['relation_identity'] == identities[19] and record['arm'] == 'T1-B')
    assert outcome['outcome'] == 'accepted_proposal' and outcome['accepted_call_index'] == 1

    # The independent expectation is complete before supplemental custody is opened.
    supplement = _load_json(Path(os.environ['TASK039E3_CUSTODY_SUPPLEMENT']))
    _verify_self_hash(supplement, '54d71edb6357e8c4d4a5479a9f0b130ca0f89f10ed4ff04ad9ba90122f3ff7c2')
    assert supplement['proposal_record_count'] == len(supplement['records']) == 251
    supplement_by_key = {}
    envelope_matches = supplement_only_hash_matches = 0
    for record in supplement['records']:
        key = (record['relation_identity'], record['arm'], record['call_number'])
        assert key not in supplement_by_key and key in expected
        supplement_by_key[key] = record
        independent = expected[key]
        for field in ('proposal_envelope', 'proposal_hash', 'validity_hash', 'original_record_hash', 'recomputed_record_hash'):
            assert record[field] == independent[field]
        envelope_matches += 1
        supplement_preimage = {field: record[field] for field in ('relation_identity', 'arm', 'call_number', 'proposal_envelope', 'proposal_hash', 'validity_hash')}
        assert stable_hash_v1(supplement_preimage) == record['original_record_hash'] == record['recomputed_record_hash']
        supplement_only_hash_matches += 1
    assert set(supplement_by_key) == set(expected)
    assert missing_key not in supplement_by_key
    print(json.dumps({
        'relations': len(evidence_by_identity),
        'proposals': len(expected),
        'proposal_hashes': proposal_hashes,
        'validity_hashes': validity_hashes,
        'record_hashes': record_hashes,
        'mismatches': 0,
        'arm_counts': dict(sorted(counts.items())),
        'envelope_matches': envelope_matches,
        'supplement_only_hash_matches': supplement_only_hash_matches,
        'missing_proposal_absent': missing_key not in supplement_by_key,
        'missing_outcome': outcome['outcome'],
        'independent_digest_length': len(independent_digest),
    }, sort_keys=True))
    """
)


@unittest.skipUnless(
    all(os.environ.get(name) for name in _REQUIRED_ENV),
    "task-local historical custody paths are intentionally external",
)
class IndependentHistoricalReconstructionTests(unittest.TestCase):
    def test_251_historical_envelopes_and_record_hashes(self) -> None:
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(
            Path(environment["TASK039E3_HISTORICAL_REPOSITORY"]) / "src"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", _INDEPENDENT_RECONSTRUCTION],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["relations"], 42)
        self.assertEqual(result["proposals"], 251)
        self.assertEqual(result["proposal_hashes"], 251)
        self.assertEqual(result["validity_hashes"], 251)
        self.assertEqual(result["record_hashes"], 251)
        self.assertEqual(result["mismatches"], 0)
        self.assertEqual(
            result["arm_counts"], {"T0": 42, "T1": 42, "T1-B": 125, "T2": 42}
        )
        self.assertEqual(result["envelope_matches"], 251)
        self.assertEqual(result["supplement_only_hash_matches"], 251)
        self.assertTrue(result["missing_proposal_absent"])
        self.assertEqual(result["missing_outcome"], "accepted_proposal")


if __name__ == "__main__":
    unittest.main()
