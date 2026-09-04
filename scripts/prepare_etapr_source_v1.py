"""Acquire only pinned official code and explicitly hypothetical fixtures."""
from pathlib import Path
from hashlib import sha1, sha256
import json
import urllib.request
from paperworks.validation_v2.exp03b_custody_v1 import seal, publish

ROOT = Path(__file__).resolve().parents[1]
PIN = 'af9e7aed35cfd160cbe0d04c8ec4c102502cb677'
FILES = {
    'LICENSE': 'ac7870740c25e696053bf85e70a0ac2036a2ab0b',
    'eTaPR_pkg/__init__.py': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
    'eTaPR_pkg/etapr.py': '231bcc099cf4ce0c02005e2ba991fb25c17537fa',
    'eTaPR_pkg/tapr.py': '9f47a2ccbf7ed3a60d24bb22eb569f941485a77a',
    'eTaPR_pkg/DataManage/__init__.py': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
    'eTaPR_pkg/DataManage/Range.py': '06fc93be6fde39d65727c57fcbff3e0718fdb91d',
    'eTaPR_pkg/DataManage/File_IO.py': '2aef362391de8d17c098c8d749bbaa1b06a97dfe',
    'eTaPR_pkg/DataManage/Time_Plot.py': '6673faf7a8aa328342da0f1ecd22565d2994b8d2',
    'Sample_Data/Hypothetical_Data/hyp1_anomalies.csv': '39ceb0358889fc69d55d553ecb71088a4100fecd',
    'Sample_Data/Hypothetical_Data/hyp_predictions_alpha_25K.csv': 'e62dd0a0fcd8fd26587acc846159b36bfcffea58',
    'Sample_Data/Hypothetical_Data/hyp_predictions_alpha_50K.csv': '711218c2f48de3da1deb06989c5c069fbdb0fb7b',
    'Sample_Data/Hypothetical_Data/hyp_predictions_alpha_75K.csv': 'd1db1212689e1194bf2190b0facf9b483b14c047',
    'Sample_Data/Hypothetical_Data/hyp_predictions_alpha_100K.csv': '69691be79a00b971b8e4b237438e6d4c2b8cf0be',
}


def main():
    target = ROOT/'artifacts/validation_v2/dg04_xver_prep/metric_source'/PIN
    records = []
    for relative, expected in FILES.items():
        path = target/relative
        if path.exists():
            content = path.read_bytes()
        else:
            with urllib.request.urlopen(f'https://raw.githubusercontent.com/saurf4ng/eTaPR/{PIN}/{relative}', timeout=60) as response:
                content = response.read(16_000_001)
        if len(content) > 16_000_000 or sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest() != expected:
            raise ValueError('PINNED_OFFICIAL_SOURCE_MISMATCH')
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(content)
        records.append({'path': relative, 'git_blob_sha1': expected, 'sha256': sha256(content).hexdigest(), 'bytes':len(content)})
    receipt = seal({'schema':'etapr_selective_source_receipt_v1', 'commit':PIN,
        'upstream':'https://github.com/saurf4ng/eTaPR', 'license':'MIT', 'files':records,
        'source_scope':'CODE_LICENSE_AND_OFFICIAL_HYPOTHETICAL_FIXTURES_ONLY',
        'real_dataset_files_acquired':0, 'provider_calls':0})
    publish(ROOT/'research_control_center/validation_v2/dg04_xver_prep/ETAPR_SOURCE_RECEIPT_V1.json', receipt)
    print(json.dumps({'status':'PINNED_SOURCE_PASS','files':len(records),'hash':receipt['self_hash']}))


if __name__ == '__main__':
    main()
