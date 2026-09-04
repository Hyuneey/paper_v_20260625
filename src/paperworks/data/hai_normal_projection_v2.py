"""Positive-allowlist CSV projection; excluded fields are never deserialized.

CSV framing is traversed as bytes. Only selected spans are materialized, decoded,
or type checked. Container integrity and projection identity are separate.
"""
from __future__ import annotations

import csv
from datetime import datetime
from hashlib import sha256
import io
import math
import os
from pathlib import Path
import re
from typing import BinaryIO, Iterator

from paperworks.validation_v2.exp03b_contract_v1 import require, digest


def schema(stream: BinaryIO) -> tuple[list[str], bytes]:
    raw = stream.readline(65537)
    require(len(raw) <= 65536 and raw.endswith(b'\n'), 'HEADER_BOUND')
    text = raw.decode('utf-8-sig').rstrip('\r\n')
    delimiter = b';' if text.count(';') > text.count(',') else b','
    header = next(csv.reader([text], delimiter=delimiter.decode('ascii')))
    require(len(header) == len(set(header)) and all(header), 'HEADER_IDENTITIES')
    return header, delimiter


def selected_rows(stream: BinaryIO, delimiter: bytes, width: int,
                  indices: tuple[int, ...]) -> Iterator[tuple[bytes, ...]]:
    """Scan CSV grammar without creating excluded-field values or strings.

Regex match objects expose spans only; group/slice is used only for allowlisted
    positions. Quoted delimiters/newlines and invalid UTF8 in excluded fields
    remain opaque framing bytes. Invalid CSV framing fails closed, never skips.
    """
    require(delimiter in (b';', b','), 'DELIMITER')
    require(indices and len(set(indices)) == len(indices) and
            all(0 <= i < width for i in indices), 'PROJECTION_INDICES')
    sep = re.escape(delimiter)
    token = re.compile(rb'(?:"(?:[^"]|"")*"|[^"\r\n' + sep + rb']*)(?:' + sep + rb'|\r?\n|$)')
    wanted = frozenset(indices)
    pending = b''
    for physical in stream:
        if not physical.endswith(b'\n'):
            physical += b'\n'  # canonical EOF record terminator; closes trailing empty field
        pending += physical
        require(len(pending) <= 1024 * 1024, 'CSV_RECORD_BOUND')
        pos = 0
        column = 0
        values: dict[int, bytes] = {}
        complete = False
        while pos < len(pending):
            match = token.match(pending, pos)
            if match is None:
                break  # a quoted multiline field may need the next byte line
            end = match.end()
            require(end > pos, 'CSV_PROGRESS')
            tail = pending[end - 1]
            delimiter_end = tail == delimiter[0]
            data_end = end - (1 if delimiter_end or tail == 10 else 0)
            if tail == 10 and data_end > pos and pending[data_end - 1] == 13:
                data_end -= 1
            if column in wanted:
                value = pending[pos:data_end]  # ONLY selected field bytes
                if value.startswith(b'"'):
                    require(value.endswith(b'"'), 'SELECTED_CSV_QUOTE')
                    value = value[1:-1].replace(b'""', b'"')
                values[column] = value
            column += 1
            pos = end
            if not delimiter_end:
                complete = True
                break
        if not complete:
            continue
        require(pos == len(pending) and column == width, 'CSV_ROW_FRAMING')
        require(set(values) == wanted, 'SELECTED_FIELD_MISSING')
        yield tuple(values[i] for i in indices)
        pending = b''
    require(not pending, 'CSV_INCOMPLETE_RECORD')


def project(source: Path, destination: Path, features: tuple[str, ...], *, allowlist_hash: str) -> dict:
    require(features and len(features) == len(set(features)), 'FEATURE_ALLOWLIST')
    require(digest(list(features)) == allowlist_hash, 'FEATURE_AUTHORITY_HASH')
    reserved = ('label', 'attack', 'scenario', 'anomaly', 'class')
    require(not any(any(key in f.lower() for key in reserved) or f.lower() in ('time','timestamp')
                    for f in features), 'RESERVED_FIELD_IN_FEATURE_ALLOWLIST')
    require(not source.is_symlink() and not destination.exists(), 'PROJECTION_DESTINATION')
    temporary = destination.with_suffix(destination.suffix + '.partial')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as incoming:
        header, delimiter = schema(incoming)
        require(header[0] in ('timestamp', 'time'), 'TIMESTAMP_SCHEMA')
        require(all(f in header[1:] for f in features), 'APPROVED_FEATURE_ABSENT')
        selected = (header[0],) + features
        indices = tuple(header.index(f) for f in selected)
        excluded = [f for f in header if f not in selected]
        h = sha256()
        count = 0
        previous = None
        with temporary.open('xb') as outgoing:
            def emit(fields: list[str]) -> None:
                buffer = io.StringIO(newline='')
                csv.writer(buffer, lineterminator='\n').writerow(fields)
                payload = buffer.getvalue().encode('utf-8')
                h.update(payload)
                outgoing.write(payload)
            emit(list(selected))
            for fields in selected_rows(incoming, delimiter, len(header), indices):
                timestamp = fields[0].decode('utf-8')
                current = datetime.fromisoformat(timestamp)
                if previous is not None:
                    require((current - previous).total_seconds() == 1, 'TIMESTAMP_CONTINUITY')
                previous = current
                numbers = [float(value.decode('ascii')) for value in fields[1:]]
                require(all(math.isfinite(value) for value in numbers), 'NONFINITE_APPROVED_FEATURE')
                emit([timestamp] + [repr(value) for value in numbers])
                count += 1
            require(count > 0, 'EMPTY_NORMAL_PROJECTION')
            outgoing.flush()
            os.fsync(outgoing.fileno())
    os.rename(temporary, destination)
    replay_hash = sha256()
    with destination.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            replay_hash.update(chunk)
    require(h.hexdigest() == replay_hash.hexdigest(), 'PROJECTION_DURABLE_HASH')
    label_present = any('attack' in f.lower() or 'label' in f.lower() for f in excluded)
    return {'row_count': count, 'timestamp_identity': selected[0],
            'projected_feature_identities': list(features), 'header_schema_hash': digest(header),
            'feature_allowlist_hash': allowlist_hash,
            'projection_hash': h.hexdigest(), 'excluded_schema_identities': excluded,
            'label_columns_present': label_present, 'label_column_names_observed': label_present,
            'label_values_parsed': False, 'label_values_validated': False, 'label_values_used': False,
            'projection_policy': 'TIMESTAMP_PLUS_APPROVED_FEATURE_ALLOWLIST',
            'scientific_projection_status': 'LABEL_VALUE_BLIND_NORMAL_FEATURE_PROJECTION',
            'raw_container_status': 'NORMAL_CONTAINER_WITH_EXCLUDED_LABEL_FIELDS' if label_present else 'NORMAL_CONTAINER',
            'datatype': 'FINITE_FLOAT64', 'sample_interval_seconds': 1, 'timestamp_continuity': 'PASS'}


def require_projected_fields(receipt: dict, requested: tuple[str, ...]) -> None:
    require(set(requested) <= {receipt['timestamp_identity'], *receipt['projected_feature_identities']},
            'EXCLUDED_FIELD_REQUEST')
