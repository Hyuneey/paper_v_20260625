"""Replay existing official/hypothetical conformance into a NEW receipt only."""
import json
from unittest.mock import patch
import check_etapr_conformance_v1 as original
from paperworks.validation_v2.exp03b_custody_v1 import publish,replay,seal


def main():
    prior=json.loads((original.PUB/'ETAPR_CONFORMANCE_RECEIPT_V2.json').read_text());replay(prior)
    def capture(_historical_path,value):
        replay(value)
        output=seal({**{k:v for k,v in value.items() if k!='self_hash'},
                     'resume_replay_of':prior['self_hash'],'real_dataset_accesses':0,
                     'fixture_scope':'OFFICIAL_HYPOTHETICAL_AND_LOCAL_SYNTHETIC_ONLY'})
        return publish(original.PUB/'ETAPR_RESUME_CONFORMANCE_RECEIPT_V3.json',output)
    with patch.object(original,'publish',capture):
        original.main()


if __name__=='__main__':main()
