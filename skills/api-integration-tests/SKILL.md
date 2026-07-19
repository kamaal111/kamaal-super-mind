---
name: api-integration-tests
description: Write or refactor API endpoint integration tests through real application and persistence boundaries. Use when testing routes, handlers, authentication, validation, authorization, side effects, or endpoint contracts without broad mocking.
---

# Endpoint Integration Tests

Load the `software-testing` skill first and follow its discovery, boundary, and coverage rules — this skill only adds the endpoint invocation shape and a worked example.

## Locate The Endpoint

When invoked with a route or path (e.g. `/app-api/auth/sign-in`), find its handler, existing tests, and request/response contract before writing anything. Use `software-testing`'s "Discover Before Writing" guidance to find the app-construction fixture, database setup, and authentication/request helpers already in use, and reuse that harness rather than building a new one.

## Write The Test

Apply `software-testing`'s rules directly:

- Keep real routing, validation, services, repositories, and persistence; mock only genuine external I/O.
- Cover the checklist from `software-testing`'s "API, UI, And Persistence" section: success status/response/headers/persisted side effects, malformed or incomplete input, domain failures, cross-user authorization denial, and cookies/tokens/pagination/caching/logs where observable.
- Verify in order: the narrow suite, then broader backend checks, then the repository's aggregate gate.

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
