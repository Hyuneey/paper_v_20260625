"""Lossless container preparation before the frozen CSV projection boundary.

This module never interprets CSV syntax.  For gzip sources it copies the
decompressed byte stream verbatim into a fresh execution namespace after the
caller has passed the real approval gate (or in synthetic qualification).
"""
from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any, Mapping

from .dg05_production_chain_v11 import file_hash, self_hashed


class DG05V11R1ContainerMaterializerError(ValueError):
    pass


def inspect_container_framing_v11r1(*, plan: Mapping[str, Any]) -> dict[str, Any]:
    """Check only raw container magic bytes; no decompression or CSV reads."""
    entries: list[dict[str, Any]] = []
    for row in plan.get("files", ()):
        path = Path(row["path"])
        raw_hash = file_hash(path)
        if raw_hash != row["sha256"]:
            raise DG05V11R1ContainerMaterializerError("RAW_CONTAINER_HASH_REPLAY_FAILED")
        container = row.get("container_type", "IDENTITY")
        if container == "GZIP":
            with path.open("rb") as stream:
                if stream.read(2) != b"\x1f\x8b":
                    raise DG05V11R1ContainerMaterializerError("GZIP_CONTAINER_FRAMING_REQUIRED")
        elif container != "IDENTITY":
            raise DG05V11R1ContainerMaterializerError("UNRECOGNIZED_CONTAINER_TYPE")
        entries.append({"panel_id": row["panel_id"], "file_id": row["file_id"],
                        "raw_container_hash": raw_hash, "container_type": container})
    if len(entries) != 10:
        raise DG05V11R1ContainerMaterializerError("CONTAINER_CENSUS_REQUIRED")
    return self_hashed({"schema": "dg05_v11r1_container_framing_preflight_v1", "status": "PASS",
                        "entries": sorted(entries, key=lambda item: (item["panel_id"], item["file_id"])),
                        "gzip_streams_materialized": 0, "csv_parser_invocations": 0,
                        "feature_rows_parsed": 0, "feature_values_inspected": 0, "label_values_inspected": 0})


def materialize_execution_sources_v11r1(*, plan: Mapping[str, Any], output_root: Path,
                                         permit_gzip_decode: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return projection-ready sources and their raw-to-derived identity binding."""
    if output_root.exists():
        raise DG05V11R1ContainerMaterializerError("EXECUTION_CONTAINER_NAMESPACE_REUSE_REJECTED")
    output_root.mkdir(parents=True)
    entries: list[dict[str, Any]] = []
    derived_rows: list[dict[str, Any]] = []
    for row in plan.get("files", ()):
        raw_source = Path(row["path"])
        raw_hash = file_hash(raw_source)
        if raw_hash != row["sha256"]:
            raise DG05V11R1ContainerMaterializerError("RAW_CONTAINER_HASH_REPLAY_FAILED")
        container = row.get("container_type", "IDENTITY")
        source = raw_source
        decoded_hash = raw_hash
        decoded_size = raw_source.stat().st_size
        if container == "GZIP":
            if not permit_gzip_decode:
                raise DG05V11R1ContainerMaterializerError("POSTAPPROVAL_GZIP_DECODE_REQUIRED")
            with raw_source.open("rb") as stream:
                if stream.read(2) != b"\x1f\x8b":
                    raise DG05V11R1ContainerMaterializerError("GZIP_CONTAINER_FRAMING_REQUIRED")
            source = output_root / str(row["panel_id"]) / str(row["file_id"])
            source.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(raw_source, "rb") as original, source.open("xb") as decoded:
                while chunk := original.read(1024 * 1024):
                    decoded.write(chunk)
            decoded_hash = file_hash(source)
            decoded_size = source.stat().st_size
        elif container != "IDENTITY":
            raise DG05V11R1ContainerMaterializerError("UNRECOGNIZED_CONTAINER_TYPE")
        derived_rows.append({**row, "path": str(source), "sha256": decoded_hash,
                             "raw_container_sha256": raw_hash, "execution_source_sha256": decoded_hash,
                             "execution_source_size": decoded_size})
        entries.append({"panel_id": row["panel_id"], "file_id": row["file_id"],
                        "raw_container_hash": raw_hash, "raw_container_type": container,
                        "decompressed_byte_hash": decoded_hash, "decompressed_byte_count": decoded_size,
                        "scientific_transformation": "NONE_LOSSLESS_CONTAINER_DECODING_ONLY"})
    if len(entries) != 10:
        raise DG05V11R1ContainerMaterializerError("CONTAINER_CENSUS_REQUIRED")
    authority = self_hashed({"schema": "dg05_v11r1_execution_container_authority_v1", "status": "PASS",
                             "physical_custody_hash": plan["physical_custody_hash"], "entries": entries,
                             "gzip_streams_materialized": sum(item["raw_container_type"] == "GZIP" for item in entries),
                             "csv_parser_invocations": 0, "feature_rows_parsed": 0,
                             "feature_values_inspected": 0, "label_values_inspected": 0})
    derived_plan = {**plan, "files": derived_rows,
                    "execution_container_authority_hash": authority["self_hash"]}
    return derived_plan, authority


__all__ = ["DG05V11R1ContainerMaterializerError", "inspect_container_framing_v11r1",
           "materialize_execution_sources_v11r1"]
