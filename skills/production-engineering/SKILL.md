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
4. Identify the established patterns in nearby code and comparable features before choosing an implementation. Follow the guidance below when extending them.

## Follow Existing Codebase Patterns

- Prefer the codebase's established patterns over your own stylistic or architectural preferences. Match naming, file organization, abstraction level, dependency usage, data flow, validation, error handling, logging, and test style in the area being changed.
- Use nearby implementations and comparable features as concrete examples. Reuse existing helpers and extension points before introducing another abstraction, dependency, or parallel approach to the same problem.
- Keep changes focused on the requested behavior. Do not redesign surrounding code, introduce a preferred architecture, or restyle unrelated code merely because another approach seems cleaner or more familiar.
- When conventions differ across the repository, follow the relevant maintained code in the affected area and explicit repository instructions. Do not copy a known defect or unsafe behavior for consistency. Depart from an established pattern only when the task, correctness, security, or a demonstrated limitation requires it; keep the departure narrow and explain the reason in the completion report.

## Prefer Pure Functions And Immutable Data

- Prefer pure functions for calculations, validation, and transformations: take explicit inputs and return results without changing caller-owned data or external state.
- Treat parameters and their reachable data as read-only. Return new values instead of mutating arguments, including nested objects and collections.
- Pass dependencies explicitly. Keep I/O and intentional state changes at clear boundaries with an explicit owner and contract; avoid hidden writes to globals, captured variables, or shared state from transformation logic.
- Local mutation is acceptable when confined to values created and owned by the function, with no externally observable mutation, and it improves clarity or performance. A local reference to caller-owned data is not local ownership.
- Prefer straightforward composition over elaborate functional abstractions. Do not force loops into `map` or `reduce`, add an FP library, or copy large structures mechanically merely to appear functional.

## Keep Performance In Mind

- Consider traversal count, intermediate allocations, repeated computation, and algorithmic complexity while writing code. Prefer a clear single-pass transformation over eager filtering followed by mapping when the intermediate collection has no independent use.
- Judge the actual API's evaluation model, not the number of chained calls. Prefer idiomatic lazy pipelines when they avoid intermediate collections: Rust iterator `filter`/`map` adapters and Java stream `filter`/`map` stages can process elements in one traversal when consumed. Do not collect between stages unnecessarily; operations such as sorting may still require buffering.
- Where collection operations are eager, use an idiomatic combined operation or a straightforward loop with a locally owned result. Do not force a complicated `reduce`, introduce a dependency, or mutate caller-owned data merely to combine passes.
- Preserve ordering, short-circuiting, error behavior, and callback semantics. Combining eager passes interleaves predicates and transformations, so only do so when that preserves the contract; keep transformation callbacks pure.
- Prefer efficient defaults without requiring a benchmark for every loop. Measure representative workloads before claiming a speedup or accepting a more complex optimization; a single pass does not automatically make an implementation faster.

## Preserve Correctness

- Identify the contract and owner of the behavior before changing it.
- Search for a shared owner before copying non-trivial logic. Move reusable behavior to the lowest suitable layer and remove the old copy unless the difference is intentional and explicit.
- Validate unknown data at boundaries and preserve typed data flow. Do not use casts, type assertions, lint disables, or suppression comments to force an invalid design through.
- Prefer compile-time guarantees over runtime crash paths in every language. Use the language's type system, exhaustive pattern matching, total typed mappings, or construction rules to make invalid states unrepresentable and missing cases fail compilation or typechecking. Do not replace compiler-checkable completeness with assertions, panics, traps, forced unwraps, or catch-all exceptions merely to shorten an implementation. Where the language cannot express the guarantee, validate explicitly and handle real failures deliberately; external input still needs runtime validation.
- Treat uncertain ownership of user-scoped data as a security issue. Scope reads and writes through the authenticated ownership boundary.
- Fail clearly when required data is unavailable; do not return misleading success values or placeholder data.
- Never revert, overwrite, or "clean up" uncommitted changes you did not write yourself, even if they look unrelated, stray, or in-progress. Leave them in place and report them in `Doubts / remaining gaps` instead of touching them.
- Never assume you are working alone on the project. Assume the user, or another agent, may be editing the same repository in parallel, even when nothing in your context says so. Do not remove or overwrite code you did not modify yourself — not for a clean slate, a simpler diff, or an unblocked path. If work in progress is blocking you, do not remove it to get past it. Keep working toward the task through the rest of your changes and verification; if the parallel change truly prevents you from fully verifying your solution, note that in `Doubts / remaining gaps` rather than stopping early.
- Treat `commit` and `stash` as destructive Git operations, alongside `reset`, `clean`, restore or checkout that overwrites files, branch deletion, history rewriting, and force-push. Do not run any of them unless working in an isolated worktree or the user explicitly authorizes the exact operation.
- Aim for one commit per pull request. Before adding another commit to a branch that will become a single PR, prefer amending or re-staging into the existing commit over stacking a new one, unless the user asks for separate commits or the work genuinely spans multiple independent PRs.

## Use Specialized Skills

Load the relevant plugin skill instead of recreating its workflow:

- `software-testing` for any test change or verification strategy, including Java, Swift, and TypeScript testing
- `plan-mode` for implementation-ready plans that another agent can execute without prior context
- `api-integration-tests` for endpoint integration coverage
- `swift-snapshot-tests` for SwiftUI screen snapshot coverage
- `swift-best-practices` for Swift implementation work, including immutable value transformations, exhaustive enum mappings, and compile-time invariants
- `typescript-best-practices` for TypeScript implementation work, including read-only inputs, `never` exhaustiveness checks, and total typed mappings
- `java-best-practices` for Java implementation work, including immutable data, optional values, sealed state or result hierarchies, and exhaustive switches
- `backend` for backend-service work in any language or framework
- `database` for schemas, migrations, queries, repositories, and user-scoped persistence
- `logging` for successes, failures, and workflow milestones; its structured-logging reference covers queryable backend events and context propagation
- `generated-api-client-endpoint` for generated client endpoints
- `dependency-upgrades` for dependency work
- `git-commit-message` for drafting Conventional Commit messages or pull-request text
- `reword-git-commit` for rewriting an existing commit message as a Conventional Commit from its diff
- `resolve-merge-conflicts` for resolving merge, rebase, or cherry-pick conflicts in place without destructive Git commands
- `commit` for inspecting and committing pending work with scope and branch safety
- `pull-request` for opening or updating single-commit PRs and keeping their title and description synchronized with the commit message, excluding sign-off trailers
- `refactor-pr-duplication` for reviewing completed task changes (including local work without a PR) or a specified PR against the codebase and consolidating duplicated logic into shared implementations; automatic completion hooks request this review once after implementation. Treat it as a checkpoint, then continue any remaining authorized work, including requested PR monitoring; review gaps must not halt unaffected work
- `monitor-pr` only when the user explicitly asks to monitor a PR, repair failing checks, and push fixes; never automatically after PR creation or updates
- `gitbutler-cli`, `gitbutler-multi-agent`, or `gitbutler-session-commit` for GitButler work

## Verify And Report

- Run the narrowest relevant check while iterating, then the repository-required final aggregate verification for code changes. Do not claim code completion while that required verification fails.
- For documentation-only or skill-only changes, skip code verification unless the repository or user requires it, and say that it was skipped.
- Structure the final response with exactly these headings, in this order: `Understanding`, `Changes`, `Verification`, `Doubts / remaining gaps`. Read [references/final-report-shape.md](references/final-report-shape.md) for the required content of each section and compliant/non-compliant examples.
- Write `None` explicitly under `Doubts / remaining gaps` when there are no doubts or gaps; never omit the heading.
