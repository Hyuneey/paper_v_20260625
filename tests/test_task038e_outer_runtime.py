import inspect

from experiments.argos_reproduction import task038e_selected_rule_outer_runtime as runtime


def test_outer_runtime_uses_two_fresh_runs_and_no_label_loader() -> None:
    source = inspect.getsource(runtime.run_outer_physical_units)
    assert 'run_id=f"task038e:{unit_id}:1"' in source
    assert 'run_id=f"task038e:{unit_id}:2"' in source
    assert "outer_labels_path" not in source
    assert "eval(" not in source
    assert "exec(" not in source
