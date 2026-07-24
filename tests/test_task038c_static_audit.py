from experiments.argos_reproduction.multi_rule_static_audit import audit_response


def test_static_audit_rejects_host_or_dynamic_operations() -> None:
    audit, _ = audit_response(
        "```python\n"
        "def inference(sample):\n"
        "    exec('x=1')\n"
        "    return sample\n"
        "```"
    )
    assert audit["static_status"] != "static_valid"
    assert audit["prohibited_calls_absent"] is False
