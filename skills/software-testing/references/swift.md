# Swift Testing Examples

Adapt these examples to the package's existing framework and naming conventions. Keep business behavior real and replace only the external boundary.

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
