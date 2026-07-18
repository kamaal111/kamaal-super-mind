---
name: api-integration-tests
description: Write or refactor API endpoint integration tests through real application and persistence boundaries. Use when testing routes, handlers, authentication, validation, authorization, side effects, or endpoint contracts without broad mocking.
---

# Endpoint Integration Tests

Write endpoint tests through the real request path and persistence layer.

## Discover The Harness

- Find the existing app-construction fixture, database setup, authentication helpers, request helpers, and nearby integration suites first.
- Reuse the established harness. Extend it only when the endpoint cannot be tested cleanly through its existing surface.
- Do not start a server process when the project exposes an in-memory request client.

## Operating Rules

- Use real routing, validation, services, repositories, and persistence. Mock only genuine external I/O.
- Create prerequisites through real endpoints when practical and keep setup deterministic and minimal.
- Name tests for observable behavior, not implementation details.

## Coverage

Cover the happy path first, then the contract-defining failures:

- successful status, response, headers, and persisted side effects
- malformed or incomplete input
- domain failures such as duplicates and missing prerequisites
- authentication and ownership, including cross-user denial for user-scoped resources
- cookies, tokens, pagination, caching, or logs when they are observable behavior

Assert actual framework error contracts rather than assuming every client error has the same shape. Reuse shared assertions and extract helpers only when repetition is real. Run the narrow suite, broader backend checks, then the repository aggregate gate.

## Generic Example

This example tests an authenticated endpoint that creates a saved item. The
syntax is illustrative; use the repository's real app fixture, database helper,
and assertion library.

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

  const savedItem = await database.savedItems.findById(body.id);
  expect(savedItem).toMatchObject({ name: "Reading list", ownerId: user.id });
});

it("does not allow a different user to update the saved item", async () => {
  const owner = await createUser();
  const otherUser = await createUser();
  const savedItem = await createSavedItem({ ownerId: owner.id });

  const response = await app.request(`/saved-items/${savedItem.id}`, {
    method: "PATCH",
    headers: authenticatedHeaders(otherUser),
    body: JSON.stringify({ name: "Changed" }),
  });

  expect(response.status).toBe(404);
  expect(await database.savedItems.findById(savedItem.id)).toMatchObject({
    name: savedItem.name,
    ownerId: owner.id,
  });
});
```

The first test proves the response and persisted side effect. The second proves
that ownership is enforced in the real request path and that a failed request
does not mutate another user's record.
