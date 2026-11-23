PYTHON ?= python3
# Respect $TMPDIR when set; fall back to Termux path on Android, /tmp on Linux.
TMPDIR ?= $(shell if [ -n "$$TERMUX_VERSION" ]; then echo "/data/data/com.termux/files/usr/tmp"; else echo "/tmp"; fi)
export TMPDIR

.PHONY: run check lint test clean

run:
	$(PYTHON) -m solvamath

lint:
	ruff check .

test:
	SOLVAMATH_DATA_DIR="$(TMPDIR)/solvamath-test-state" $(PYTHON) -m pytest -q

check: lint test
	$(PYTHON) -m solvamath --version
	SOLVAMATH_DATA_DIR="$(TMPDIR)/solvamath-test-state" $(PYTHON) -m solvamath --stats

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
