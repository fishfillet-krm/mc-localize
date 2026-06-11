# AGENTS.md

## Project Overview

mc-localize is maintained with human approval gates and AI-assisted development.

## Technology Stack

Python

## Directory Structure

- `src/`
- `tests/`
- `.github/`

## Development Commands

- Install: `python -m pip install -e .`
- Build: `Not detected; confirm with the maintainer.`
- Test: `PYTHONPATH=src python -m unittest discover -s tests`
- Lint: `Not detected; confirm with the maintainer.`
- Format: `Not detected; confirm with the maintainer.`

## Working Rules

- Codex should propose a plan before making large changes.
- Codex should keep changes small and reviewable.
- Codex should run tests before suggesting a pull request.
- Do not make unrelated formatting or refactoring changes.
- Do not overwrite user work or use destructive Git commands.

## Human Approval Required

Codex must not change public APIs, authentication, authorization, release settings, deployment, billing, or security-sensitive code without explicit human approval.

## Pre-PR Checklist

- [ ] Change is small and focused
- [ ] Tests were added or updated
- [ ] Existing tests pass
- [ ] Lint and build pass
- [ ] Documentation is updated if needed
- [ ] No unrelated changes are included
