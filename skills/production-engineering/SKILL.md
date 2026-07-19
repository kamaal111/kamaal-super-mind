---
name: production-engineering
description: Apply cross-project engineering guardrails before and after production software changes. Use for repository discovery, scope control, shared-logic ownership, validation integrity, final verification, and completion reporting; use the plugin's specialized skills for language, testing, CI, dependency, or Git workflows.
---

# Production Engineering

Use this skill as a thin baseline for safe repository work. It deliberately does not duplicate the detailed procedures in the plugin's specialized skills.

## Start Safely

1. Read repository instructions, task-runner commands, manifests, nearby implementation, and nearby tests before editing.
2. Work from the repository root unless the project directs otherwise. Do not search, read, or crawl outside it without explicit user direction—for example, never run `find /`, scan a home directory, or crawl unrelated local paths.
3. Prefer repository-provided commands and the project's selected package managers. Do not start long-running services or background processes unless the user explicitly asks and the repository provides an approved workflow.
4. Match nearby naming, structure, validation, error handling, and test style unless there is a concrete reason to introduce a new pattern.

## Preserve Correctness

- Identify the contract and owner of the behavior before changing it.
- Search for a shared owner before copying non-trivial logic. Move reusable behavior to the lowest suitable layer and remove the old copy unless the difference is intentional and explicit.
- Validate unknown data at boundaries and preserve typed data flow. Do not use casts, type assertions, lint disables, or suppression comments to force an invalid design through.
- Treat uncertain ownership of user-scoped data as a security issue. Scope reads and writes through the authenticated ownership boundary.
- Fail clearly when required data is unavailable; do not return misleading success values or placeholder data.

## Use Specialized Skills

Load the relevant plugin skill instead of recreating its workflow:

- `software-testing` for any test change or verification strategy, including Swift and TypeScript testing
- `api-integration-tests` for endpoint integration coverage
- `swift-snapshot-tests` for SwiftUI screen snapshot coverage
- `swift-best-practices` for Swift implementation work
- `typescript-backend` for TypeScript server work
- `generated-api-client-endpoint` for generated client endpoints
- `dependency-upgrades` for dependency work
- `git-commit-message` for drafting commit or pull-request text
- `gitbutler-cli`, `gitbutler-multi-agent`, or `gitbutler-session-commit` for GitButler work

## Verify And Report

- Run the narrowest relevant check while iterating, then the repository-required final aggregate verification for code changes. Do not claim code completion while that required verification fails.
- For documentation-only or skill-only changes, skip code verification unless the repository or user requires it, and say that it was skipped.
- State the outcome understood, what changed, every verification command and result, and any doubts, tradeoffs, environment issues, or remaining gaps.
