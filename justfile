default: gen-check

# regenerate all plugin manifests from plugin.meta.toml + harness.toml
gen:
    uv run harness-kit gen

# fail (exit 1) if any generated manifest is stale
gen-check:
    uv run harness-kit gen --check

# run the test suite
test:
    uv run pytest

all: gen-check test
