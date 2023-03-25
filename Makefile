SHELL := /bin/bash

setup:
	python3 -m venv venv
	source venv/bin/activate && ( \
		pip install -r requirements.txt; \
		pip install -r tests/requirements.txt; \
		pip install black isort flake8; \
		)

test:
	python3 -m pytest tests --cov=zero --cov-report=term-missing -vv

format:
	python3 -m black . --line-length 120
	python3 -m isort . --profile black --line-length 120
	python3 -m flake8 ./zero --max-line-length 120