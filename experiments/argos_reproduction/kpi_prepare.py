"""Prepare one KPI series for ARGOS rule-only reproduction smoke tests.

Downloaded packages, extracted files, and converted CSVs are written only under
ignored ``artifacts/`` paths.  Tracked outputs contain hashes and aggregate
provenance only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class KpiStats:
    kpi_id: str
    row_count: int = 0
    label_counts: Counter[str] = field(default_factory=Counter)
    malformed_timestamp_count: int = 0
    malformed_value_count: int = 0
    malformed_label_count: int = 0

    def eligible(self, min_row_count: int) -> bool:
        return (
            self.row_count >= min_row_count
            and self.malformed_timestamp_count == 0
            and self.malformed_value_count == 0
            and self.malformed_label_count == 0
            and self.label_counts.get("0", 0) > 0
            and self.label_counts.get("1", 0) > 0
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kpi_id": self.kpi_id,
            "row_count": self.row_count,
            "label_counts": dict(sorted(self.label_counts.items())),
            "malformed_timestamp_count": self.malformed_timestamp_count,
            "malformed_value_count": self.malformed_value_count,
            "malformed_label_count": self.malformed_label_count,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_json(data: Any) -> str:
    return sha256_text(stable_json(data))


def write_json(path: Path, data: dict[str, Any]) -> None:
    resolved = path.resolve()
    if not resolved.is_relative_to(REPO_ROOT):
        raise ValueError(f"Refusing to write outside repository: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def package_info(path: Path, git_blob_sha: str, source_url: str) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved.is_relative_to(REPO_ROOT):
        recorded_path = resolved.relative_to(REPO_ROOT).as_posix()
    else:
        recorded_path = path.as_posix()
    return {
        "path": recorded_path,
        "source_url": source_url,
        "git_blob_sha": git_blob_sha,
        "local_sha256": sha256_file(resolved),
        "byte_size": resolved.stat().st_size,
    }


def safe_extract_zip(zip_path: Path, output_dir: Path) -> list[dict[str, Any]]:
    output_root = output_dir.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    extracted: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir() or info.filename.startswith("__MACOSX/"):
                continue
            target = (output_root / info.filename).resolve()
            if not target.is_relative_to(output_root):
                raise ValueError(f"Refusing path traversal in zip entry: {info.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as src, target.open("wb") as dst:
                dst.write(src.read())
            extracted.append(
                {
                    "filename": info.filename,
                    "file_size": info.file_size,
                    "compressed_size": info.compress_size,
                    "extracted_path": target.relative_to(REPO_ROOT).as_posix(),
                    "local_sha256": sha256_file(target),
                }
            )
    return extracted


def valid_timestamp(value: str) -> bool:
    if value is None or value == "":
        return False
    text = str(value).strip()
    if not text:
        return False
    try:
        numeric = float(text)
        return math.isfinite(numeric)
    except ValueError:
        pass
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def normalize_label(value: str) -> str | None:
    text = str(value).strip()
    if text in {"0", "0.0"}:
        return "0"
    if text in {"1", "1.0"}:
        return "1"
    return None


def inspect_train_csv(csv_path: Path) -> dict[str, KpiStats]:
    stats: dict[str, KpiStats] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"timestamp", "value", "label", "KPI ID"}
        if set(reader.fieldnames or []) != required:
            raise ValueError(f"Unexpected train CSV columns: {reader.fieldnames}")
        for row in reader:
            kpi_id = row["KPI ID"].strip()
            item = stats.setdefault(kpi_id, KpiStats(kpi_id=kpi_id))
            item.row_count += 1
            if not valid_timestamp(row["timestamp"]):
                item.malformed_timestamp_count += 1
            try:
                value = float(row["value"])
                if not math.isfinite(value):
                    item.malformed_value_count += 1
            except ValueError:
                item.malformed_value_count += 1
            label = normalize_label(row["label"])
            if label is None:
                item.malformed_label_count += 1
            else:
                item.label_counts[label] += 1
    return stats


def select_kpi_id(stats: dict[str, KpiStats], min_row_count: int) -> str:
    eligible = sorted(k for k, item in stats.items() if item.eligible(min_row_count))
    if not eligible:
        raise ValueError("No eligible KPI ID found under the predeclared selection policy")
    return eligible[0]


def safe_kpi_filename(kpi_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", kpi_id)


def convert_selected_series(train_csv: Path, selected_kpi_id: str, output_csv: Path) -> dict[str, Any]:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    label_counts: Counter[str] = Counter()
    row_count = 0
    with train_csv.open("r", encoding="utf-8", newline="") as src, output_csv.open(
        "w", encoding="utf-8", newline=""
    ) as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=["value", "label", "index"])
        writer.writeheader()
        for row in reader:
            if row["KPI ID"].strip() != selected_kpi_id:
                continue
            label = normalize_label(row["label"])
            if label is None:
                raise ValueError(f"Malformed label in selected KPI {selected_kpi_id}")
            writer.writerow({"value": row["value"], "label": label, "index": row_count})
            label_counts[label] += 1
            row_count += 1
    return {
        "converted_path": output_csv.relative_to(REPO_ROOT).as_posix(),
        "converted_sha256": sha256_file(output_csv),
        "row_count": row_count,
        "label_counts": dict(sorted(label_counts.items())),
        "columns": ["value", "label", "index"],
        "timestamp_index_policy": "source timestamp validated; ARGOS index is zero-based source row order within selected KPI ID",
        "preprocessing_version": "task024_minimal_kpi_to_argos_v1",
    }


def prepare(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    private_root = (REPO_ROOT / config["private_artifact_root"]).resolve()
    train_zip = REPO_ROOT / config["packages"]["train"]["local_path"]
    gt_zip = REPO_ROOT / config["packages"]["ground_truth"]["local_path"]
    extracted_root = private_root / "extracted"
    converted_root = private_root / "converted"

    extracted = {
        "train": safe_extract_zip(train_zip, extracted_root),
        "ground_truth": safe_extract_zip(gt_zip, extracted_root),
    }
    train_csv = extracted_root / "phase2_train.csv"
    stats = inspect_train_csv(train_csv)
    selected_kpi_id = select_kpi_id(stats, config["selection_policy"]["minimum_row_count"])
    selected_stats = stats[selected_kpi_id]
    output_csv = converted_root / f"{safe_kpi_filename(selected_kpi_id)}_argos.csv"
    converted = convert_selected_series(train_csv, selected_kpi_id, output_csv)

    available_kpi_ids = sorted(stats)
    eligible_kpi_ids = sorted(
        k for k, item in stats.items() if item.eligible(config["selection_policy"]["minimum_row_count"])
    )
    manifest = {
        "schema_version": "1.0",
        "artifact_type": "task024_kpi_dataset_manifest",
        "task_id": "TASK-024",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_repository": config["source_repository"],
        "source_repository_commit": config["source_repository_commit"],
        "source_repository_commit_date": config.get("source_repository_commit_date"),
        "packages": {
            "train": package_info(
                train_zip,
                config["packages"]["train"]["git_blob_sha"],
                config["packages"]["train"]["source_url"],
            ),
            "ground_truth": package_info(
                gt_zip,
                config["packages"]["ground_truth"]["git_blob_sha"],
                config["packages"]["ground_truth"]["source_url"],
            ),
        },
        "extraction": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "extracted_files": extracted,
        },
        "upstream_preprocessing": {
            "pinned_readme_references_generate_csv": True,
            "historical_generate_csv_found": False,
            "decision": "minimal_reproduction_adapter_under_experiments_argos_reproduction",
        },
        "selection_policy": config["selection_policy"],
        "selection_audit": {
            "available_kpi_id_count": len(available_kpi_ids),
            "available_kpi_ids": available_kpi_ids,
            "eligible_kpi_id_count": len(eligible_kpi_ids),
            "eligible_kpi_ids": eligible_kpi_ids,
            "selected_kpi_id": selected_kpi_id,
            "selected_stats": selected_stats.to_dict(),
            "selection_basis": "lexicographically smallest eligible KPI ID",
            "not_selected_by_argos_performance": True,
        },
        "converted_argos_csv": converted,
        "ground_truth_use": {
            "package_downloaded_and_extracted": True,
            "hdf_parsing_performed": False,
            "label_source_for_initial_rule_only_smoke": "phase2_train.csv label column",
            "reason": "TASK-024 first rule-only smoke uses train package labels and does not run final evaluation",
        },
        "boundaries": config["boundaries"],
    }
    manifest["manifest_hash"] = sha256_json(manifest)
    write_json(REPO_ROOT / config["output_manifest_path"], manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare TASK-024 KPI ARGOS fixture")
    parser.add_argument(
        "--config",
        default="configs/argos_reproduction/task024_kpi_sandbox_smoke.json",
        help="TASK-024 config path.",
    )
    args = parser.parse_args()
    manifest = prepare((REPO_ROOT / args.config).resolve())
    print(json.dumps({"selected_kpi_id": manifest["selection_audit"]["selected_kpi_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
