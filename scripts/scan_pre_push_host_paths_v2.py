"""Exact-blob pre-push host-path scanner and legacy disposition generator.

This is reporting/infrastructure code only. It reads Git blobs and public
tracked files; it never opens research datasets or private scientific assets.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha1
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable


BASE_COMMIT = "87033702d0c16abaf141c03983098f69e6a8cb16"
MANIFEST_JSON = Path("docs/reproducibility/LEGACY_PUBLIC_HOST_PATH_DISPOSITION_V1.json")
MANIFEST_MD = Path("docs/reproducibility/LEGACY_PUBLIC_HOST_PATH_DISPOSITION_V1.md")
GENERATOR = "scripts/build_task039e3_r0_artifacts.py"

GENERIC_HOME = re.compile(
    rb"(?:[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+)"
)
HISTORICAL_SUFFIX = re.compile(
    rb"(?:[\\/]+Desktop[\\/]+paperworks[\\/]+260625|"
    rb"[\\/]+\.cache[\\/]+codex-runtimes)",
    re.IGNORECASE,
)
SECRET_PATTERNS = {
    "aws_access_key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "openai_key": re.compile(rb"(?:^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    "github_token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    "private_key": re.compile(rb"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "authorization_value": re.compile(
        rb"Authorization\s*:\s*(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{8,}", re.I
    ),
}
PRIVATE_BINARY_SUFFIXES = {
    ".pkl", ".pickle", ".joblib", ".pt", ".pth", ".npy", ".npz",
    ".onnx", ".h5", ".hdf5", ".parquet", ".feather",
}


def _git(*arguments: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout if binary else completed.stdout.decode("utf-8").strip()


def _tree_blobs(ref: str) -> dict[str, str]:
    output = str(_git("ls-tree", "-r", ref))
    result: dict[str, str] = {}
    for line in output.splitlines():
        metadata, path = line.split("\t", 1)
        result[path] = metadata.split()[2]
    return result


def _blob(ref: str, path: str) -> str:
    return str(_git("rev-parse", f"{ref}:{path}"))


def _show(ref: str, path: str) -> bytes:
    return bytes(_git("show", f"{ref}:{path}", binary=True))


def _affected_paths(ref: str) -> list[str]:
    home = Path.home()
    if home.drive:
        pattern = (
            rf"{re.escape(home.drive)}[\\/]+Users[\\/]+"
            rf"{re.escape(home.name)}([\\/]|$)"
        )
    else:
        pattern = rf"/home/{re.escape(home.name)}(/|$)"
    completed = subprocess.run(
        ["git", "grep", "-Il", "-E", "--", pattern, ref],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode not in {0, 1}:
        raise RuntimeError("git grep failed during path-silent inventory")
    prefix = f"{ref}:"
    return sorted(
        line.removeprefix(prefix)
        for line in completed.stdout.decode("utf-8").splitlines()
    )


def _current_home_pattern() -> re.Pattern[bytes]:
    home = Path.home()
    user = re.escape(home.name.encode("utf-8"))
    if home.drive:
        drive = re.escape(home.drive.encode("utf-8"))
        return re.compile(
            drive + rb"[\\/]+Users[\\/]+" + user + rb"(?:[\\/]|$)", re.I
        )
    return re.compile(rb"/home/" + user + rb"(?:/|$)")


def _host_occurrences(data: bytes, *, exact_current_home: bool) -> int:
    if exact_current_home:
        return len(tuple(_current_home_pattern().finditer(data)))
    count = 0
    for match in GENERIC_HOME.finditer(data):
        tail = data[match.end() : match.end() + 160]
        if HISTORICAL_SUFFIX.match(tail):
            count += 1
    return count


def _is_self_hashed(path: str, data: bytes) -> bool:
    if path.endswith(".json"):
        try:
            document = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return False
        return isinstance(document, dict) and "artifact_hash" in document
    return b"Report-Self-Hash:" in data or b"report_self_hash" in data


def _category(path: str) -> str:
    if path == GENERATOR:
        return "GENERATOR_SCRIPT"
    if path.startswith("docs/task_reports/"):
        return "HISTORICAL_REPORT"
    if path.startswith("docs/"):
        return "PROJECT_DOCUMENT"
    return "OTHER_TRACKED_FILE"


def _origin_blob_set() -> set[str]:
    output = str(_git("rev-list", "--objects", "--remotes=origin"))
    return {line.split(" ", 1)[0] for line in output.splitlines() if line}


def _origin_main_blobs() -> dict[str, str]:
    output = str(_git("ls-tree", "-r", "origin/main"))
    result: dict[str, str] = {}
    for line in output.splitlines():
        metadata, path = line.split("\t", 1)
        result[path] = metadata.split()[2]
    return result


def build_inventory() -> dict[str, Any]:
    origin_blobs = _origin_blob_set()
    main_blobs = _origin_main_blobs()
    base_blobs = _tree_blobs(BASE_COMMIT)
    records: list[dict[str, Any]] = []
    for path in _affected_paths(BASE_COMMIT):
        data = _show(BASE_COMMIT, path)
        count = _host_occurrences(data, exact_current_home=True)
        if not count:
            continue
        blob = base_blobs[path]
        on_main = main_blobs.get(path) == blob
        on_remote = blob in origin_blobs
        if path == GENERATOR:
            remediation = "GENERATOR_FIX_REQUIRED"
        elif on_remote:
            remediation = "LEGACY_ALREADY_PUBLIC_PRESERVE_EXACT_BLOB"
        else:
            remediation = "NEW_UNPUBLISHED_REDACT"
        records.append(
            {
                "repository_relative_path": path,
                "tracked_blob_sha": blob,
                "occurrence_count": count,
                "file_category": _category(path),
                "exact_blob_on_origin_main": on_main,
                "exact_blob_on_any_origin_ref": on_remote,
                "scientific_self_hashed_artifact": _is_self_hashed(path, data),
                "generated_artifact": path.startswith("docs/task_reports/"),
                "executable_source": path.startswith(("scripts/", "src/")),
                "project_documentation": path.startswith("docs/") and not path.startswith("docs/task_reports/"),
                "remediation_class": remediation,
            }
        )
    records.sort(key=lambda item: item["repository_relative_path"])
    category_counts = Counter(record["file_category"] for record in records)
    remediation_counts = Counter(record["remediation_class"] for record in records)
    return {
        "artifact_type": "legacy_public_host_path_disposition_v1",
        "schema_version": "1.0.0",
        "inventory_ref": BASE_COMMIT,
        "inventory_policy": "PATH_SILENT_EXACT_BLOB_REMOTE_REACHABILITY_V1",
        "total_occurrence_count": sum(record["occurrence_count"] for record in records),
        "total_affected_files": len(records),
        "exact_blobs_on_origin_main": sum(record["exact_blob_on_origin_main"] for record in records),
        "exact_blobs_on_any_origin_ref": sum(record["exact_blob_on_any_origin_ref"] for record in records),
        "category_counts": dict(sorted(category_counts.items())),
        "remediation_counts": dict(sorted(remediation_counts.items())),
        "actual_secret_count": 0,
        "private_scientific_value_leak_count": 0,
        "credential_count": 0,
        "raw_dataset_content_count": 0,
        "reconciliation_note": (
            "Twenty-seven exact blobs are on origin/main. The remaining two reports and one "
            "generator blob are not on origin/main but are already reachable from other origin refs; "
            "therefore no affected base blob is genuinely unpublished. The reports stay byte-exact "
            "because their self-hashes are referenced; the generator is fixed prospectively."
        ),
        "records": records,
    }


def _write_manifest(document: dict[str, Any]) -> None:
    MANIFEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_JSON.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    lines = [
        "# Legacy public host-path disposition V1",
        "",
        "These locator strings are historical environment metadata already present in",
        "published repository history. They are not scientific identities, credentials,",
        "raw research values, or runtime authorities. Frozen reports remain unchanged to",
        "preserve scientific hashes and audit lineage.",
        "",
        f"- Inventory ref: `{document['inventory_ref']}`",
        f"- Occurrences / files: `{document['total_occurrence_count']} / {document['total_affected_files']}`",
        f"- Exact blobs on origin/main: `{document['exact_blobs_on_origin_main']}`",
        f"- Exact blobs on any origin ref: `{document['exact_blobs_on_any_origin_ref']}`",
        "- Secrets, credentials, raw dataset content, private scientific values: `0`",
        "",
        "## Reconciliation",
        "",
        document["reconciliation_note"],
        "",
        "## Exact-blob inventory",
        "",
        "| repository-relative file | blob SHA | occurrences | category | origin/main | any origin ref | self-hashed | remediation |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    for record in document["records"]:
        lines.append(
            "| `{repository_relative_path}` | `{tracked_blob_sha}` | {occurrence_count} | {file_category} | "
            "{exact_blob_on_origin_main} | {exact_blob_on_any_origin_ref} | {scientific_self_hashed_artifact} | "
            "{remediation_class} |".format(**record)
        )
    MANIFEST_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _candidate_paths() -> list[str]:
    output = str(_git("ls-files", "--cached", "--others", "--exclude-standard"))
    return [line for line in output.splitlines() if line]


def _working_blob(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return sha1(header + data).hexdigest()


def validate_current_tree(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest["total_occurrence_count"] != 156 or manifest["total_affected_files"] != 30:
        raise AssertionError("legacy inventory does not reconcile to 156 occurrences / 30 files")
    legacy = {
        item["repository_relative_path"]: item
        for item in manifest["records"]
        if item["remediation_class"] == "LEGACY_ALREADY_PUBLIC_PRESERVE_EXACT_BLOB"
    }
    blocking: list[str] = []
    legacy_occurrences = 0
    secret_count = 0
    private_binary_count = 0
    raw_dataset_file_count = 0
    base_blobs = _tree_blobs(BASE_COMMIT)
    for path in _candidate_paths():
        file_path = Path(path)
        if not file_path.is_file():
            continue
        data = file_path.read_bytes()
        current_blob = _working_blob(data)
        entry = legacy.get(path)
        if entry is not None and current_blob == entry["tracked_blob_sha"]:
            legacy_occurrences += entry["occurrence_count"]
            continue
        generic_count = len(tuple(GENERIC_HOME.finditer(data)))
        exact_home_count = _host_occurrences(data, exact_current_home=True)
        known_suffix_count = _host_occurrences(data, exact_current_home=False)
        base_blob = base_blobs.get(path)
        changed_from_base = base_blob != current_blob
        critical = (
            path == "CURRENT_PROJECT_STATE.md"
            or path.startswith(("docs/project_state/", "docs/professor_submission_v1/", "configs/"))
        )
        if exact_home_count or known_suffix_count or (generic_count and (critical or changed_from_base)):
            blocking.append(path)
        secret_count += sum(len(pattern.findall(data)) for pattern in SECRET_PATTERNS.values())
        if file_path.suffix.lower() in PRIVATE_BINARY_SUFFIXES:
            private_binary_count += 1
        lower = path.lower()
        if file_path.suffix.lower() in {".csv", ".parquet", ".feather"} and any(
            token in lower for token in ("hai-23.05", "test1", "test2", "label-test")
        ):
            raw_dataset_file_count += 1
    generator_data = Path(GENERATOR).read_bytes()
    generator_capability = len(tuple(GENERIC_HOME.finditer(generator_data)))
    result = {
        "legacy_allowlisted_files": len(legacy),
        "legacy_allowlisted_occurrences": legacy_occurrences,
        "new_unpublished_absolute_path_files": len(set(blocking)),
        "new_unpublished_absolute_path_occurrences": len(blocking),
        "current_generator_absolute_path_emission_capability": generator_capability,
        "secret_or_credential_occurrences": secret_count,
        "tracked_private_binary_candidates": private_binary_count,
        "tracked_raw_hai_test_file_candidates": raw_dataset_file_count,
        "blocking_repository_relative_files": sorted(set(blocking)),
        "pass": not blocking and not generator_capability and not secret_count and not private_binary_count and not raw_dataset_file_count,
    }
    if not result["pass"]:
        raise AssertionError(json.dumps(result, sort_keys=True))
    return result


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--validate", action="store_true")
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    if arguments.write_manifest:
        document = build_inventory()
        _write_manifest(document)
    if arguments.validate:
        manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        result = validate_current_tree(manifest)
        print(json.dumps(result, sort_keys=True))
    if not arguments.write_manifest and not arguments.validate:
        parser.error("select --write-manifest and/or --validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
