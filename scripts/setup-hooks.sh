#!/usr/bin/env bash
# Setup git hooks - Works on Windows (Git Bash), Mac, Linux
# Usage: ./scripts/setup-hooks.sh

echo "🔧 Setting up git hooks..."

# Create hooks directory if needed
mkdir -p .git/hooks

# Copy pre-commit hook
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Install pre-commit framework
poetry run pre-commit install

echo "✅ Git hooks installed!"
echo ""
echo "Hooks will run automatically on 'git commit'"
echo "To skip hooks: git commit --no-verify"

