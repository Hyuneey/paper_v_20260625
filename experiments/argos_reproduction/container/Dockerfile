FROM python:3.10-slim

RUN python -m pip install --no-cache-dir numpy==1.26.4

WORKDIR /sandbox
COPY run_fixed_rule.py /sandbox/run_fixed_rule.py

ENTRYPOINT ["python", "-I", "/sandbox/run_fixed_rule.py"]
