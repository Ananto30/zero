SHELL := /bin/bash

setup:
	python3 -m venv venv
	source venv/bin/activate && ( \
		pip install -r requirements.txt; \
		pip install -r tests/requirements.txt; \
		pip install black isort flake8 pylint; \
		)

test:
	python3 -m pytest tests --cov=zero --cov-report=term-missing -vv

format:
	isort . --profile black -l 99
	black .
	flake8 ./zero
	pylint ./zero

build-package:
	pip install -U setuptools wheel
	python3 setup.py sdist bdist_wheel

dist-package:
	pip install -U twine
	python3 -m twine upload dist/*
