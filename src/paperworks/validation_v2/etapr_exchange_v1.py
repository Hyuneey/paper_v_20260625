"""Pinned official eTaPR adapter; per-file only, no implicit pooling or data I/O."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha1
from math import isfinite
from pathlib import Path
from typing import Sequence

PIN = 'af9e7aed35cfd160cbe0d04c8ec4c102502cb677'
SOURCE_BLOBS = {
    'eTaPR_pkg/__init__.py': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
    'eTaPR_pkg/etapr.py': '231bcc099cf4ce0c02005e2ba991fb25c17537fa',
    'eTaPR_pkg/tapr.py': '9f47a2ccbf7ed3a60d24bb22eb569f941485a77a',
    'eTaPR_pkg/DataManage/__init__.py': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
    'eTaPR_pkg/DataManage/Range.py': '06fc93be6fde39d65727c57fcbff3e0718fdb91d',
    'eTaPR_pkg/DataManage/File_IO.py': '2aef362391de8d17c098c8d749bbaa1b06a97dfe',
    'eTaPR_pkg/DataManage/Time_Plot.py': '6673faf7a8aa328342da0f1ecd22565d2994b8d2',
}


@dataclass(frozen=True)
class EtaprFileExchangeV1:
    file_id: str
    row_count: int
    reference_ranges: tuple[tuple[int, int], ...]
    prediction_ranges: tuple[tuple[int, int], ...]

    def validate(self) -> None:
        if not isinstance(self.file_id, str) or not self.file_id or type(self.row_count) is not int or self.row_count <= 0:
            raise ValueError('INVALID_FILE_IDENTITY')
        for kind, ranges in (('reference',self.reference_ranges), ('prediction',self.prediction_ranges)):
            previous_end = -1
            for interval in ranges:
                if len(interval) != 2 or any(type(v) is not int for v in interval):
                    raise ValueError('INVALID_CLOSED_RANGE')
                start, end = interval
                if not (previous_end < start <= end < self.row_count):
                    raise ValueError('UNORDERED_OVERLAPPING_OR_OUT_OF_FILE_RANGE')
                if kind == 'prediction' and previous_end >= 0 and start == previous_end + 1:
                    raise ValueError('PREDICTION_RANGES_MUST_BE_MAXIMAL')
                previous_end = end


def validate_file_batch_v1(files: Sequence[EtaprFileExchangeV1]) -> None:
    if not files or len({f.file_id for f in files}) != len(files):
        raise ValueError('EMPTY_OR_DUPLICATE_FILE_BATCH')
    for item in files:
        item.validate()


class OfficialEtaprV1:
    """Uses unmodified official implementation; caller supplies pinned import path.

    Never computes an aggregate over files or versions. No attack authorization
    is conferred by this numerical adapter. Empty cases stay explicitly undefined.
    """

    def __init__(self, source_root: Path):
        source_root = source_root.resolve()
        for relative, expected in SOURCE_BLOBS.items():
            raw = (source_root/relative).read_bytes()
            if sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() != expected:
                raise ValueError('OFFICIAL_ETAPR_SOURCE_MISMATCH')
        from eTaPR_pkg import etapr, tapr
        from eTaPR_pkg.DataManage import Range, File_IO, Time_Plot
        for module, relative in ((etapr,'etapr.py'), (tapr,'tapr.py'), (Range,'DataManage/Range.py'),
                                 (File_IO,'DataManage/File_IO.py'), (Time_Plot,'DataManage/Time_Plot.py')):
            if Path(module.__file__).resolve() != source_root/'eTaPR_pkg'/relative:
                raise ValueError('OFFICIAL_ETAPR_IMPORT_IDENTITY_MISMATCH')
        self._engine_class = etapr.eTaPR
        self._range_class = Range.Range

    def score_file(self, exchange: EtaprFileExchangeV1) -> dict:
        exchange.validate()
        identity = {'file_id':exchange.file_id, 'source_commit':PIN,
                    'parameters':{'theta_p':0.5, 'theta_r':0.1, 'delta':0.0},
                    'intervals':'CLOSED_INCLUSIVE', 'point_adjustment':False}
        if not exchange.reference_ranges or not exchange.prediction_ranges:
            return {**identity, 'status':'UNDEFINED_EMPTY_RANGE_INPUT', 'eTaP':None, 'eTaR':None, 'F1':None}
        # Names do not isolate upstream ranges. Therefore instantiate per file.
        engine = self._engine_class(theta_p=0.5, theta_r=0.1, delta=0.0)
        engine.set([self._range_class(a,b,str(i)) for i,(a,b) in enumerate(exchange.reference_ranges)],
                   [self._range_class(a,b,str(i)) for i,(a,b) in enumerate(exchange.prediction_ranges)])
        precision, recall = float(engine.eTaP()), float(engine.eTaR())
        if not all(isfinite(v) and 0 <= v <= 1 for v in (precision, recall)):
            raise ValueError('NONFINITE_OR_OUT_OF_RANGE_ETAPR')
        f1 = 0.0 if precision+recall == 0 else 2*precision*recall/(precision+recall)
        return {**identity, 'status':'PASS', 'eTaP':precision, 'eTaR':recall, 'F1':f1}

    def score_files(self, files: Sequence[EtaprFileExchangeV1]) -> dict:
        validate_file_batch_v1(files)
        return {'files':[self.score_file(f) for f in files],
                'aggregation_status':'UNRESOLVED_NOT_EXECUTED', 'pooled_metric':None}
