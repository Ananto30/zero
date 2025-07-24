SHELL := /bin/bash

setup:
	python3 -m venv venv
	source venv/bin/activate && ( \
		pip install -r requirements.txt; \
		pip install -r tests/requirements.txt; \
		pip install black isort flake8 pylint pytype mypy; \
		)

test:
	python3 -m pytest tests --cov=zero --cov-report=term-missing --cov-config=.coveragerc -vv --durations=10 --timeout=280

docker-test:
	docker build -t zero-test -f Dockerfile.test .
	docker run --rm zero-test

format:
	isort . --profile black -l 99
	black .

install-lint:
	python -m pip install --upgrade pip
	pip install -r requirements.txt  # needed for pytype
	pip install black isort flake8 pylint pytype mypy pydantic>=2.0

lint:
	flake8 ./zero
	pylint ./zero
	pytype ./zero
	mypy ./zero

build-package:
	pip install -U setuptools wheel
	python3 setup.py sdist bdist_wheel

dist-package:
	pip install -U twine
	python3 -m twine upload dist/*
