POETRY_RUN = poetry run

all: build

.venv: pyproject.toml
	uv tool install poetry --force
	poetry config virtualenvs.in-project true
	poetry install
	touch .venv

install: .venv

run: .venv
	$(POETRY_RUN) python a_maze_ing.py config.txt

debug: .venv
	$(POETRY_RUN) python -m pdb a_maze_ing.py config.txt

clean:
	rm -rf .venv .mypy_cache .pytest_cache dist
	find . -type d -name "__pycache__" -exec rm -rf {} +

fclean: clean
	rm -rf .venv
	rm -f *.tar.gz
	rm -f *.whl

re: fclean all

lint: .venv
	$(POETRY_RUN) flake8 . --exclude='./.venv'
	$(POETRY_RUN) mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude './.venv'

lint-strict: .venv
	$(POETRY_RUN) flake8 . --exclude='./.venv'
	$(POETRY_RUN) mypy . --strict --exclude './.venv'

build: .venv
	poetry build
	cp -r dist/mazegen-*.tar.gz .
	cp -r dist/mazegen-*.whl .

.PHONY: install run debug clean lint lint-strict build
