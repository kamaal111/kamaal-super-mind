---
name: software-testing
description: Plan, write, debug, and verify reliable software tests. Use when adding or changing tests, fixing regressions, investigating failures, choosing test scope, or determining whether a change is adequately verified.
---

# Software Testing

Keep test work disciplined, reproducible, and aligned with the current repository. Repository instructions and established test patterns take precedence.

## Discover Before Writing

Identify the test runner, existing fixtures, factories, helper utilities, naming and assertion conventions, quick checks, and final quality gate. Inspect project instructions, task runners, manifests, CI workflows, and nearby tests before creating new infrastructure.

## Core Rules

1. Test observable behavior before implementation details. Reproduce the bug or expected behavior with a focused failing test when practical.
2. Do not claim a change works until the relevant tests and required checks pass.
3. Match local conventions for structure, helpers, test names, and assertions.
4. Keep tests deterministic: control time, randomness, network access, caches, global state, and asynchronous scheduling.
5. Fail fast during setup. Verify statuses, required values, and resource handles before relying on them.
6. Use descriptive test names and clear assertions instead of explanatory comments.
7. Start with the narrowest useful scope, then expand only when lower-level tests cannot prove the behavior.

## Design Workflow

Follow red-green-refactor:

1. Add or update the test that captures the behavior.
2. Confirm it fails for the expected reason when practical.
3. Make the smallest production change that passes it.
4. Refactor only after the behavior is protected.

Use unit tests for isolated logic, integration tests for routing, persistence, middleware, and dependency wiring, and end-to-end tests only for flows that cannot be proven at a lower level. Cover success, important edge cases, meaningful errors, authorization, side effects, and the regression that motivated the change.

## Boundaries And Reliability

- Replace only the narrowest external-I/O boundary. Keep production serialization, parsing, and business behavior real.
- Use fakes or stubs for external services unless an established integration environment is the behavior under test.
- Inject observable test doubles for credentials, files, or other persistent effects; never use a person's real persistent store in unit tests.
- Prefer existing global setup and fixtures to fresh per-test mock scaffolding. Extract a shared helper only after real repetition appears.
- Keep success and failure assertions in separate tests. Keep assertions flat so a failure identifies one behavior.
- Disable or isolate caches that could mask later responses. Serialize suites or otherwise isolate shared mutable test state.

## API, UI, And Persistence

- For APIs, reuse app fixtures and assert status or result, payload shape, headers when relevant, persisted state, and cross-user authorization denial.
- For UI, prefer user-facing roles, labels, accessible names, and realistic interactions over implementation selectors or internal method calls. Cover loading, empty, error, success, and permissions where applicable.
- For persistence, use project fixtures or factories, keep data minimal, assert writes in storage, and follow the repository's cleanup, transaction, migration, or container setup.

## Debug And Verify

Reproduce failures with the smallest relevant command and read the full output before editing. Determine whether production code, the test, or setup is wrong. For flakiness, identify the uncontrolled dependency rather than adding sleeps, broad retries, or arbitrary waits. Update dependent tests when contracts or types change.

Run the narrow test first, then the broader suite or package, then every required quality gate. Run the repository’s aggregate verification command last when it exists. Report the behavior covered, tests run, final result, and remaining gaps.

## Language References

- For TypeScript examples using Vitest-style assertions, read [references/typescript.md](references/typescript.md).
- For Swift Testing examples with async test doubles, read [references/swift.md](references/swift.md).
