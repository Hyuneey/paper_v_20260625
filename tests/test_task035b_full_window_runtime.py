import inspect
import unittest

from experiments.argos_reproduction import multi_rule_full_window_runtime as module


class Task035BFullWindowRuntimeTests(unittest.TestCase):
    def test_replay_contract(self):
        base = {"rule_sha256": "a", "input_sha256": "b", "image_id": "c", "exit_code": 0, "runtime_status": "executable_rule", "output_count": 3, "prediction_sha256": "d", "predicted_positive_count": 1}
        self.assertTrue(module.deterministic_replay_matches(base, dict(base)))
        changed = dict(base, prediction_sha256="e")
        self.assertFalse(module.deterministic_replay_matches(base, changed))

    def test_host_never_loads_generated_source(self):
        source = inspect.getsource(module)
        for token in ("exec(", "eval(", "compile(", "importlib", "runpy"):
            self.assertNotIn(token, source)
        self.assertIn('"labels_mounted": False', source)


if __name__ == "__main__":
    unittest.main()
