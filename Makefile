SHELL := /bin/bash

setup:
	python3 -m venv venv
	source venv/bin/activate && ( \
		pip install -r requirements.txt; \
		pipenv install -r tests/requirements.txt; \
		pip install black isort; \
		)

test:
	python3 -m pytest tests --cov=zero --cov-report=term-missing -o log_cli=true 

format:
	python3 -m black . --line-length 120
	python3 -m isort . --profile black --line-length 120