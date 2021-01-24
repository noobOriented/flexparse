.DEFAULT_GOAL := all

.PHONY: lint
lint:
	flake8

.PHONY: test
test:
	pytest flexparse/ --cov=flexparse/ --cov-fail-under=80 --cov-report term-missing
