"""New execution-phase receipt; old conformance results remain immutable."""
from unittest.mock import patch
import check_etapr_conformance_v1 as original
from xver_execution_common import PUB, document, publish, seal, replay


def capture(_old_path, value):
    replay(value)
    prior=document(PUB/'ETAPR_CONFORMANCE_RECEIPT_V1.json')
    body={k:v for k,v in value.items() if k!='self_hash'}
    body.update(prior_receipt_hash=prior['self_hash'],scope='OFFICIAL_HYPOTHETICAL_AND_SYNTHETIC_ONLY')
    return publish(PUB/'ETAPR_CONFORMANCE_RECEIPT_V2.json',seal(body))


if __name__=='__main__':
    with patch.object(original,'publish',capture):original.main()
