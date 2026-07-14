import copy
import json
import re
import unittest
from pathlib import Path

from experiments.argos_reproduction import container_rule_smoke


class Task033ContainerHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = container_rule_smoke.REPO_ROOT
        cls.config = container_rule_smoke.read_json(
            cls.root / "configs/argos_reproduction/task033_e1_runtime_smoke.json"
        )

    def test_all_fixtures_are_synthetic_n_by_one_and_hash_stable(self):
        for entry in self.config["fixtures"]:
            path = self.root / entry["path"]
            before = path.read_bytes()
            first = container_rule_smoke.validate_fixture(path)
            second = container_rule_smoke.validate_fixture(path)
            self.assertEqual(first, second)
            self.assertEqual(first["fixture_id"], entry["fixture_id"])
            self.assertEqual(before, path.read_bytes())
            payload = json.loads(before)
            self.assertEqual(payload["input_kind"], "synthetic_non_kpi")
            self.assertEqual(payload["shape"][1], 1)

    def test_fixture_loader_rejects_paths_outside_task033_root(self):
        with self.assertRaisesRegex(
            container_rule_smoke.Task033HarnessError,
            "TASK033_FIXTURE_PATH_OUTSIDE_APPROVED_ROOT",
        ):
            container_rule_smoke.validate_fixture(
                self.root / "configs/argos_reproduction/task033_e1_runtime_smoke.json"
            )

    def test_exactly_one_wsl_native_runtime_is_selected(self):
        runtime = self.config["runtime"]
        self.assertEqual(runtime["selected"], "wsl_native_rootless_podman")
        self.assertFalse(runtime["docker_desktop_retry"])
        self.assertFalse(runtime["task028_resumed"])
        self.assertFalse(runtime["host_rule_execution_allowed"])

    def test_isolation_arguments_are_fail_closed(self):
        arguments = container_rule_smoke.isolation_arguments(self.config)
        serialized = " ".join(arguments)
        for required in (
            "--network none",
            "--read-only",
            "--cap-drop ALL",
            "--security-opt no-new-privileges",
            "--pids-limit 64",
            "--cpus 1",
            "--memory 256m",
            "/tmp:rw,noexec,nosuid,size=16m",
            "/output:rw,noexec,nosuid,size=1m",
        ):
            self.assertIn(required, serialized)

    def test_host_wrapper_has_no_dynamic_rule_loading_or_provider_client(self):
        source = (self.root / "experiments/argos_reproduction/container_rule_smoke.py").read_text(
            encoding="utf-8"
        )
        for pattern in (
            r"\bexec\(",
            r"\beval\(",
            r"\bcompile\(",
            r"\bimportlib\b",
            r"\brunpy\b",
            r"\bopenai\b",
            r"\banthropic\b",
            r"paperworks\.data",
        ):
            self.assertIsNone(re.search(pattern, source))

    def test_container_image_is_digest_and_dependency_hash_pinned(self):
        containerfile = (self.root / "containers/argos_rule_runtime/Containerfile").read_text(
            encoding="utf-8"
        )
        lock = (self.root / "containers/argos_rule_runtime/requirements.lock").read_text(
            encoding="utf-8"
        )
        self.assertIn("FROM docker.io/library/python@sha256:", containerfile)
        self.assertIn("USER 65532:65532", containerfile)
        self.assertIn("numpy==1.26.4", lock)
        self.assertIn("--hash=sha256:", lock)
        self.assertNotIn("captured_rule", containerfile)

    def test_success_status_requires_nonempty_contract_and_replay(self):
        def run(fixture_id):
            return {
                "process": {"exit_code": 0, "timed_out": False},
                "inference": {
                    "output_shape_valid": True,
                    "output_binary_domain_valid": True,
                    "output_finite": True,
                },
            }

        results = [
            {
                "fixture_id": fixture_id,
                "replay_status": "deterministic",
                "runs": [run(fixture_id), run(fixture_id)],
            }
            for fixture_id in ("constant_series", "monotonic_series", "localized_spike")
        ]
        self.assertEqual(
            container_rule_smoke.evaluate_e1_status({"status": "passed"}, results),
            "passed_runtime_smoke",
        )
        broken = copy.deepcopy(results)
        broken[0]["runs"][1]["inference"]["output_binary_domain_valid"] = False
        self.assertEqual(
            container_rule_smoke.evaluate_e1_status({"status": "passed"}, broken),
            "failed_output_contract",
        )

    def test_replay_status_detects_output_hash_change(self):
        base = {
            "rule_sha256": "a" * 64,
            "fixture_sha256": "b" * 64,
            "container_image_digest": "sha256:" + "c" * 64,
            "input_count": 3,
            "process": {"exit_code": 0, "timed_out": False},
            "inference": {
                "output_returned": True,
                "output_count": 3,
                "output_sha256": "d" * 64,
                "output_binary_domain_valid": True,
            },
        }
        second = copy.deepcopy(base)
        self.assertEqual(container_rule_smoke.fixture_replay_status([base, second]), "deterministic")
        second["inference"]["output_sha256"] = "e" * 64
        self.assertEqual(
            container_rule_smoke.fixture_replay_status([base, second]),
            "runtime_nondeterministic",
        )

    def test_private_mount_tokens_do_not_enter_command_hash_material(self):
        rule = self.root / "artifacts/private_argos_reproduction/task026q/quarantine/private.py"
        fixture = self.root / "fixtures/task033/constant_series.json"
        command = [
            "podman",
            "run",
            f"type=bind,src={container_rule_smoke.windows_to_wsl(rule)},dst=/rule/rule.py,ro",
            f"type=bind,src={container_rule_smoke.windows_to_wsl(fixture)},dst=/fixture/input.json,ro",
        ]
        first = container_rule_smoke.redacted_command_hash(command, rule, fixture)
        other_rule = rule.with_name("other.py")
        other_command = [
            "podman",
            "run",
            f"type=bind,src={container_rule_smoke.windows_to_wsl(other_rule)},dst=/rule/rule.py,ro",
            f"type=bind,src={container_rule_smoke.windows_to_wsl(fixture)},dst=/fixture/input.json,ro",
        ]
        second = container_rule_smoke.redacted_command_hash(other_command, other_rule, fixture)
        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
