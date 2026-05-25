.PHONY: generate check help

# Default target.
generate:
	python3 scripts/generate_all_in_one.py

# Regenerate, then fail if the tracked outputs are now dirty (CI staleness gate).
check: generate
	git diff --exit-code patterns/ALL_IN_ONE.md examples/ALL_EXAMPLES.md patterns/README.md

help:
	@echo "Targets: generate (default) | check | help"
