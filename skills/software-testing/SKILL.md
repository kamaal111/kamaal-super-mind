---
name: software-testing
description: Plan, write, debug, and verify reliable software tests. Use when adding or changing tests, fixing regressions, investigating failures, choosing test scope, or determining whether a change is adequately verified.
---

# Software Testing

Keep test work disciplined, reproducible, and aligned with the current repository. Repository instructions and established test patterns take precedence.

## Discover Before Writing

Identify the test runner, existing fixtures, factories, helper utilities, naming and assertion conventions, quick checks, and final quality gate. Inspect project instructions, task runners, manifests, CI workflows, and nearby tests before creating new infrastructure. Identify the primary unit under test and name the test file and suite after it.

For an API endpoint, find the existing app-construction fixture, database setup, authentication helpers, request helpers, and nearby integration suites first, and reuse that harness rather than starting a server process when the project already exposes an in-memory request client.

## Core Rules

1. Test observable behavior before implementation details. Reproduce the bug or expected behavior with a focused failing test when practical.
2. Do not claim a change works until the relevant tests and required checks pass.
3. Match local conventions for structure, helpers, test names, and assertions.
4. Keep tests deterministic: control time, randomness, network access, caches, global state, and asynchronous scheduling.
5. Fail fast during setup. Verify statuses, required values, and resource handles before relying on them.
6. Use descriptive test names and clear assertions instead of explanatory comments.
7. Start with the narrowest useful scope, then expand only when lower-level tests cannot prove the behavior.
8. Every test must contain at least one explicit assertion (`#expect`/`#require` or the language equivalent) on an outcome — state, return value, error, or interaction. If a call offers nothing meaningful to assert beyond "it didn't throw," and there's no idiomatic non-branching way to assert that directly, don't manufacture an assertion around it (e.g. wrapping in `#expect(throws: Never.self) { ... }`, or adding a one-off helper just to produce a boolean) — the test isn't proving anything real, so drop it instead of padding it out.
9. Never branch control flow inside a test body — no `if`, `guard`, `switch` with early return/continue, or conditional skips used to decide whether an assertion runs. If asserting on a case of an enum, `Result`, or optional requires unwrapping, use the framework's non-branching assertion form (e.g. `#expect(throws:)` around the throwing call, or `try #require(...)` to unwrap unconditionally) instead of pattern-matching with a fallback branch. A test's assertions must always execute, not depend on a runtime condition.

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
- When a feature sits on a client with an injectable transport, build the real client with a transport double rather than adding a feature-level protocol that fakes the entire client. This exercises the real request pipeline and error mapping.
- If a useful seam is not visible to the test target, widen only the minimum necessary visibility. Do not loosen private implementation methods or introduce a production abstraction solely to call internals from a test.
- Drive public initializers and public APIs. For asynchronous initialization, wait for observable state with a bounded polling loop or another deterministic synchronization mechanism; never use arbitrary sleeps.
- If an error path intentionally triggers a test-failing logger or assertion, do not work around the product behavior merely to test it; cover the nearest safe behavior and document the gap.

## API, UI, And Persistence

- For APIs, reuse app fixtures and assert status or result, payload shape, headers when relevant, persisted state, and cross-user authorization denial.
- For APIs, create prerequisite resources through real endpoints when practical, and cover malformed or incomplete input, domain failures such as duplicates or missing prerequisites, and cookies, tokens, pagination, caching, or logs when they are observable behavior. Assert the actual framework error contract rather than assuming every client error has the same shape.
- For UI, prefer user-facing roles, labels, accessible names, and realistic interactions over implementation selectors or internal method calls. Cover loading, empty, error, success, and permissions where applicable.
- When adding or changing a SwiftUI screen, add or update its snapshot test in the same change; read [references/swift-snapshot-testing.md](references/swift-snapshot-testing.md).
- For persistence, use project fixtures or factories, keep data minimal, assert writes in storage, and follow the repository's cleanup, transaction, migration, or container setup.
- Format request or response fixtures over multiple indented lines so failures remain readable.

## Debug And Verify

Reproduce failures with the smallest relevant command and read the full output before editing. Determine whether production code, the test, or setup is wrong. For flakiness, identify the uncontrolled dependency rather than adding sleeps, broad retries, or arbitrary waits. Update dependent tests when contracts or types change.

Run the narrow test first, then the broader suite or package, then every required quality gate. Run the repository’s aggregate verification command last when it exists. Report the behavior covered, tests run, final result, and remaining gaps.

## Language References

- For TypeScript examples using Vitest-style assertions, read [references/typescript.md](references/typescript.md).
- For Swift Testing examples with async test doubles, read [references/swift.md](references/swift.md).
- For SwiftUI snapshot testing with Point-Free SnapshotTesting, read [references/swift-snapshot-testing.md](references/swift-snapshot-testing.md).
