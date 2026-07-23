#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."
python3 scripts/validate_function_docs.py
python3 -m pytest -q tests/test_function_docs_validator.py
