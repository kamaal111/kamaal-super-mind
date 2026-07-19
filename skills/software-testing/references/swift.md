# Swift Testing Examples

Adapt these examples to the package's existing framework and naming conventions. Keep business behavior real and replace only the external boundary.

## Conventions

- Prefer Swift Testing (`@Suite`, `@Test`, and descriptive backticked test names) unless the target is already XCTest or XCUITest.
- Use actors for spies that record async calls or mutable state. Serialize a suite when a shared transport handler or other mutable fixture cannot be isolated.
- For asynchronous initialization, wait for observable state with a bounded `Task.yield()` loop instead of an arbitrary sleep.
- Ensure test-only configuration does not rely on application bundle metadata, environment assumptions, or logger behavior that differs under a package test runner.
- Decode captured JSON with the production `Codable` payload type. Add necessary conformance to the real type instead of duplicating it as a test-only model.
- Use `try result.get()` for successful `Result` values and the framework's expected-throwing assertions for expected failures.
- Use required-value assertions (`try #require(...)`) for captured requests and fixture values instead of force unwraps.
- In a request-boundary test, assert method, path, operation identifier when available, decoded production payload, returned result, and the relevant observable side effect.

## Test an async service with an actor spy

```swift
import Testing

@Suite("Availability Service Tests")
struct AvailabilityServiceTests {
    @Test
    func `Returns the availability reported by the transport`() async throws {
        let transport = AvailabilityTransportSpy(
            response: .init(sku: "book-123", available: true)
        )
        let service = AvailabilityService(transport: transport)

        let result = try await service.checkAvailability(sku: "book-123").get()

        #expect(result == .init(sku: "book-123", available: true))
        #expect(await transport.requestedSKUs == ["book-123"])
    }
}

actor AvailabilityTransportSpy: AvailabilityTransporting {
    let response: Availability
    private(set) var requestedSKUs: [String] = []

    init(response: Availability) {
        self.response = response
    }

    func fetchAvailability(sku: String) async throws -> Availability {
        requestedSKUs.append(sku)
        return response
    }
}
```

## Test a failure separately

Give meaningful error behavior its own test instead of branching assertions inside a success test.

```swift
@Test
func `Returns an unavailable error when the transport reports a missing item`() async throws {
    let service = AvailabilityService(transport: MissingItemTransport())

    await #expect(throws: AvailabilityError.unavailable) {
        try await service.checkAvailability(sku: "missing").get()
    }
}
```

Use actors for async mutable spies, `#require` for indispensable values, and the production payload or error types rather than test-only copies.

## Never branch to reach an assertion

Don't use `guard case`/`if case` with an `Issue.record` + `return` fallback to unwrap a `Result` or enum case — that makes the assertion conditional on a runtime branch instead of something that always runs. Prefer `#expect(throws:)` around the throwing call (shown above), or `try #require(...)` to unwrap unconditionally when there's no throwing entry point:

```swift
// Avoid: assertion only runs if the guard succeeds.
let result = await client.signIn(with: payload)
guard case .failure(let error) = result else {
    Issue.record("Expected sign in to fail.")
    return
}
#expect(error == .badRequest(validations: []))

// Prefer: the assertion always executes.
await #expect(throws: SignInErrors.badRequest(validations: [])) {
    try await client.signIn(with: payload).get()
}
```

## Drop a test that has nothing real to assert

If a call under test returns `Result<Void, _>` and there is no observable state, return value, or interaction to check beyond "it didn't throw," don't invent an assertion to satisfy the letter of the rule — not `#expect(throws: Never.self) { try await call().get() }`, and not a throwaway `Result.isSuccess`-style helper built solely to produce a boolean. Either the success path is already covered by a more specific test that does assert something real (e.g. a follow-on state change), or it isn't worth a test at all. Delete it rather than pad it out.
