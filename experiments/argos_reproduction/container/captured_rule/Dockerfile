FROM python:3.12.10-slim-bookworm

RUN python -m pip install --no-cache-dir numpy==2.2.6 \
    && groupadd --system sandbox \
    && useradd --system --gid sandbox --home-dir /nonexistent --shell /usr/sbin/nologin sandbox

WORKDIR /runner
COPY run_captured_rule.py /runner/run_captured_rule.py

USER sandbox:sandbox
ENTRYPOINT ["python", "-I", "/runner/run_captured_rule.py"]
