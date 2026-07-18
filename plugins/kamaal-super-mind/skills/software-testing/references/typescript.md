# TypeScript Testing Examples

Adapt these examples to the repository's existing runner, fixtures, and types.

## Test a service through its external boundary

Keep the service's validation and behavior real while replacing only the remote transport.

```ts
import { describe, expect, it } from "vitest";

class InventoryTransportSpy {
  requests: Array<{ sku: string }> = [];

  async fetchAvailability(sku: string) {
    this.requests.push({ sku });
    return { sku, available: true };
  }
}

it("returns availability using the requested SKU", async () => {
  const transport = new InventoryTransportSpy();
  const service = new InventoryService({ transport });

  const result = await service.checkAvailability("book-123");

  expect(result).toEqual({ sku: "book-123", available: true });
  expect(transport.requests).toEqual([{ sku: "book-123" }]);
});
```

## Test a real API boundary

Use the application's fixture, authentication helper, and database utility. Assert both the response and persisted state.

```ts
it("creates a saved item for the authenticated user", async () => {
  const user = await createUser();

  const response = await app.request("/saved-items", {
    method: "POST",
    headers: authenticatedHeaders(user),
    body: JSON.stringify({ name: "Reading list" }),
  });

  expect(response.status).toBe(201);
  const body = await response.json();
  expect(body).toMatchObject({ name: "Reading list", ownerId: user.id });

  await expect(database.savedItems.findById(body.id)).resolves.toMatchObject({
    name: "Reading list",
    ownerId: user.id,
  });
});
```

Add a separate test for malformed input and one proving a different user cannot read or mutate the created resource.
