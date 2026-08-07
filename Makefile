.PHONY: test lint check run mutations

test:
	python -m pytest

lint:
	python -m ruff check .
	python -m ruff format --check .

check: test lint

run:
	python -m authoritybench.cli run

mutations:
	python -m authoritybench.cli mutations
