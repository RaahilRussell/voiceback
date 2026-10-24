.PHONY: install test run format

install:
	python3 -m pip install -e 'backend[dev]'

test:
	python3 -m pytest backend/tests

run:
	python3 -m uvicorn app.main:app --app-dir backend --reload

format:
	python3 -m ruff check backend inference --fix

