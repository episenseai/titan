.PHONY: clean
clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

VENV_DIR := $(shell poetry env info -p)
.PHONY: install
install: clean
	@[ -d "$(VENV_DIR)" ] && rm -rf $(VENV_DIR) && echo "Deleted current virtualenv..." || true
	@poetry env use python
	@poetry run pip install -U pip setuptools wheel
	@poetry install || SYSTEM_VERSION_COMPAT=1 poetry install

.PHONY: format
format:
	@poetry run isort titan/ tests/
	@poetry run black titan/ tests/
