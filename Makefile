.PHONY: run test smoke lint-clean

run:
	uvicorn web:app --reload --port 8080

test:
	pytest

smoke:
	python scripts/demo_smoke.py

lint-clean:
	python -m compileall -q opsguardian web.py agentcore_runtime/main.py
