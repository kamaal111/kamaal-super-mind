---
name: swift-testing
description: Write or refactor focused Swift tests. Use when adding, updating, debugging, or verifying tests for Swift source, packages, clients, async behavior, request serialization, response parsing, error mapping, or persistent side effects.
---

# Swift Testing

Write deterministic Swift tests that prove observable behavior while isolating only external boundaries. Follow repository-specific testing and Swift guidance when it is stricter.

## Discover Before Writing

- Read the source under test, its direct collaborators, package manifest, and nearest Swift tests.
- Identify the primary unit under test and name the test file and suite after it.
- Use the project's established framework. Prefer Swift Testing (`@Suite`, `@Test`, and descriptive backticked test names) unless the target is already XCTest or XCUITest.
- Find the narrow iteration command, broader package or application check, and final aggregate verification command before editing.

## Choose The Right Boundary

- Keep business logic, request serialization, response parsing, and error mapping real.
- Replace only the narrowest external-I/O boundary: usually a transport, URL session, persistence adapter, clock, filesystem, or service client supplied by the existing design.
- When a feature sits on a client with an injectable transport, build the real client with a transport double rather than adding a feature-level protocol that fakes the entire client. This exercises the real request pipeline and error mapping.
- If a useful seam is not visible to the test target, widen only the minimum necessary visibility. Do not loosen private implementation methods or introduce a production abstraction solely to call internals from a test.
- Drive public initializers and public APIs. For asynchronous initialization, wait for observable state with a bounded `Task.yield()` loop or another deterministic synchronization mechanism; never use arbitrary sleeps.

## Persistent Effects And Async State

- Treat credential stores, caches, files, and preferences as narrow dependencies. Use the production adapter in normal construction and an observable test double in tests.
- Never let unit tests write a person's real persistent store.
- Use actors for spies that record async calls or mutable state. Serialize a suite when a shared transport handler or other mutable fixture cannot be isolated.
- Ensure test-only configuration does not rely on application bundle metadata, environment assumptions, or logger behavior that differs under a package test runner.
- If an error path intentionally triggers a test-failing logger or assertion, do not work around the product behavior merely to test it; cover the nearest safe behavior and document the gap.

## Write Behavior-Focused Tests

- Write a separate test for every success and meaningful error behavior.
- In a request-boundary test, assert method, path, operation identifier when available, decoded production payload, returned result, and the relevant observable side effect.
- Decode captured JSON with the production `Codable` payload type. Add necessary conformance to the real type instead of duplicating it as a test-only model.
- Use `try result.get()` for successful `Result` values and the framework's expected-throwing assertions for expected failures.
- Keep assertions flat. Do not hide them inside `if`, `guard`, or `switch` branches. Use required-value assertions for captured requests and fixture values instead of force unwraps.
- Format JSON fixtures over multiple indented lines so failures remain readable.

Example:

```swift
@Suite("Profile Client Tests")
struct ProfileClientTests {
    @Test
    func `Stores a session after a successful sign in`() async throws {
        let sessionStore = SessionStoreSpy()
        let transport = SignInTransport.success()
        let client = makeClient(transport: transport, sessionStore: sessionStore)

        try await client.signIn(email: "person@example.com", password: "secret").get()

        let request = try #require(await transport.recordedRequest)
        #expect(request.method == .post)
        let storedSession = try #require(await sessionStore.storedSession)
        #expect(storedSession.accessToken.isEmpty == false)
    }
}
```

## Verification And Report

1. Run the narrow package or target suite while iterating.
2. Run the broader affected application or package checks.
3. Run the repository aggregate verification last when required.
4. If a wider check fails outside the changed target, report the exact command and cause; do not call the work fully verified.

State the tested behavior, replaced boundary, observed test-double effect, every verification command, and any remaining test-environment limitation.
