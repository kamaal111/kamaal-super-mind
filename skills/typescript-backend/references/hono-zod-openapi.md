# Hono, Zod, And OpenAPI Examples

These examples are adapted from the project's TypeScript server. Use them when a
project uses compatible Hono, Zod, OpenAPI, and structured-logging patterns;
otherwise keep the same responsibilities and follow that project's framework.

## Declare The Contract At The Route Edge

Keep method, path, request body, response status, headers, and response schemas
in one OpenAPI route definition. Document every public schema field and give
each reusable root schema a stable OpenAPI identity, title, description, and
representative object example. A handler can then receive validated data rather
than parsing a raw request body again.

```ts
import { createRoute, z } from "@hono/zod-openapi";

const SignInPayloadSchema = z.object({
  email: z.string().email().openapi({
    description: "Email address for the account",
    example: "person@example.com",
  }),
  password: z.string().min(8).openapi({
    description: "Account password with at least eight characters",
    example: "correct-horse-battery-staple",
  }),
}).openapi("SignInPayload", {
  title: "Email Password Sign In",
  description: "Request body for signing in with email and password",
  example: {
    email: "person@example.com",
    password: "correct-horse-battery-staple",
  },
});

const SessionSchema = z.object({
  user: z.object({
    id: z.string().openapi({
      description: "Unique identifier for the authenticated user",
      example: "user_123",
    }),
    email: z.string().email().openapi({
      description: "Email address for the authenticated user",
      example: "person@example.com",
    }),
  }),
}).openapi("SessionResponse", {
  title: "Session Response",
  description: "The current authenticated session and user details",
  example: { user: { id: "user_123", email: "person@example.com" } },
});

export const signInRoute = createRoute({
  method: "post",
  path: "/sign-in/email",
  request: {
    body: { content: { "application/json": { schema: SignInPayloadSchema } } },
  },
  responses: {
    200: {
      description: "Sign in successful",
      content: { "application/json": { schema: SessionSchema } },
      headers: z.object({ "set-auth-token": z.string() }),
    },
    400: { description: "Invalid request" },
    401: { description: "Authentication failed" },
  },
});
```

## Validate Outbound Data At The Handler Boundary

Even data obtained from an internal dependency becomes an API boundary when it is
serialized into a response. Parse it with the declared response schema before
returning it.

```ts
function sessionHandler(c: AppContext) {
  const session = c.get("session");

  if (!session) {
    throw new NotFoundError();
  }

  return c.json(SessionSchema.parse(session), 200);
}
```

## Enrich One Request-Scoped Logger

Initialize a logger with correlation fields at request start, then derive a child
logger when authentication discovers the user. This keeps every later event
correlatable without passing individual fields to each log call.

```ts
function requestLogger(c: AppContext) {
  const logger = createLogger({
    request_id: c.get("requestId"),
    method: c.req.method,
    path: c.req.path,
    route: matchedRoute(c),
  });

  const userId = c.get("session")?.user.id;
  return userId ? logger.child({ user_id: userId }) : logger;
}

function logSuccessfulSessionLookup(c: AppContext) {
  requestLogger(c).info(
    { event: "session.lookup", component: "auth", outcome: "success" },
    "Retrieved the authenticated user session.",
  );
}
```

## Test The Real Request Path

Use the established app, database, auth, and log-capture fixture. Assert the
HTTP response, production response schema, persisted state, and structured log
fields together.

```ts
it("returns the authenticated user session", async () => {
  const user = await createTestUser(app, database);
  const { headers, requestId } = withRequestId({
    Cookie: sessionCookieFor(user),
    "User-Agent": "integration-test-client",
  });

  const response = await app.request("/session", { method: "GET", headers });

  expect(response.status).toBe(200);
  const body = SessionSchema.parse(await response.json());
  expect(body.user).toMatchObject({ id: user.id, email: user.email });

  await expect(database.users.findById(user.id)).resolves.toBeDefined();
  expect(getLogsForRequestId(requestId)).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        event: "session.lookup",
        outcome: "success",
        request_id: requestId,
        user_id: user.id,
      }),
    ]),
  );
});
```

Add separate tests for missing authentication, invalid requests, ownership
boundaries, and every documented status whose behavior matters to clients.
