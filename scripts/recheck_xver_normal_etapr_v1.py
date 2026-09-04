"""Replay only official hypothetical and synthetic fixtures into new namespace."""
from unittest.mock import patch
import check_etapr_conformance_v1 as original
from paperworks.validation_v2.exp03b_custody_v1 import publish,replay


def capture(_old_path,value):
    replay(value)
    return publish(original.ROOT/'research_control_center/validation_v2/xver_normal/ETAPR_CONFORMANCE_RECEIPT_V1.json',value)


if __name__=='__main__':
    with patch.object(original,'publish',capture):original.main()
