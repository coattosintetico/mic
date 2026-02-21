format:
	uv run ruff check --fix
	uv run ruff format
.PHONY: format

run:
	@uv run python main.py
.PHONY: run

install:
	@uv tool install -e .
.PHONY: install
