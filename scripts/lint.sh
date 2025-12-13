#!/usr/bin/env bash
# Lint and format code - Works on Windows (Git Bash), Mac, Linux
# Usage: ./scripts/lint.sh [--fix]

if [ "$1" == "--fix" ]; then
    echo "🔧 Fixing code style..."
    poetry run isort src/
    poetry run black src/
    echo "✅ Done! Run without --fix to verify."
else
    echo "🔍 Checking code style..."
    echo ""

    echo ">> isort"
    poetry run isort --check-only --diff src/

    echo ""
    echo ">> black"
    poetry run black --check --diff src/

    echo ""
    echo ">> flake8"
    poetry run flake8 src/ --max-line-length=100 --ignore=E501,W503

    echo ""
    echo ">> mypy"
    poetry run mypy src/ --ignore-missing-imports

    echo ""
    echo ">> pylint"
    poetry run pylint src/ --max-line-length=100 --disable=C0114,C0115,C0116

    echo ""
    echo "✅ All checks complete!"
fi
