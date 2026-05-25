.PHONY: generate check check-attribution help

# Default target.
generate:
	python3 scripts/generate_all_in_one.py

# Fail (exit 1) if any file in the skill mentions a forbidden external-tool name.
# Skill content must stay attribution-free per CLAUDE.md.
# The forbidden list lives in scripts/forbidden-names.txt — one regex per line.
check-attribution:
	@hits=$$(grep -rli --exclude-dir=.git --exclude=forbidden-names.txt \
		-f scripts/forbidden-names.txt . || true) ; \
	if [ -n "$$hits" ]; then \
		echo "❌ forbidden attribution found:" >&2 ; \
		echo "$$hits" >&2 ; \
		exit 1 ; \
	fi
	@echo "✅ no forbidden attribution"

# Regenerate, run the attribution gate, then fail if the tracked outputs are now dirty.
check: generate check-attribution
	git diff --exit-code patterns/ALL_IN_ONE.md examples/ALL_EXAMPLES.md patterns/README.md

help:
	@echo "Targets: generate (default) | check | check-attribution | help"
