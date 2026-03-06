# gh-aw Support Files

This directory stores repository-local support files for GitHub Agentic Workflows.

## Purpose

Keep review aids, policy notes, and human-facing mirrors out of `.github/workflows/` so only real gh-aw source workflows live there.

## Structure

- `review-mirrors/`: Chinese review mirrors and maintainer-facing explanations for workflow source files.

## Current Files

- `review-mirrors/aw-pr-maintainer-review.zh.md`: Chinese review mirror for `.github/workflows/aw-pr-maintainer-review.md`.
- `review-mirrors/aw-release-preflight.zh.md`: Chinese review mirror for `.github/workflows/aw-release-preflight.md`.
- `review-mirrors/aw-ci-audit.zh.md`: Chinese review mirror for `.github/workflows/aw-ci-audit.md`.

## Rule

Files in this directory are for maintainer review and documentation only. They are not gh-aw workflow source files and should not be compiled.
