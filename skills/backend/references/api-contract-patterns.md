# API Contract Patterns

Apply these patterns with the project's chosen HTTP framework, validation
library, contract format, logger, and test runner. Keep the responsibilities
intact; do not introduce a new technology merely to mirror this pseudocode.

## Declare The Contract At The Route Edge

Declare the method, path, request inputs, success and error responses, and
response headers together. Give externally visible fields descriptions and
representative examples. Give reusable payload shapes stable names so generated
documentation and clients can refer to them consistently.

```text
contract SignIn:
  method: POST
  path: /sign-in/email
  request body: SignInPayload
  responses:
    200: SessionResponse, with set-auth-token header
    400: invalid request
    401: authentication failed

shape SignInPayload:
  email: email address
  password: string, at least 8 characters

shape SessionResponse:
  user:
    id: user identifier
    email: email address
```

Make the route handler consume the framework's validated request representation
instead of parsing the raw request again downstream.

## Validate Outbound Data At The Response Boundary

Data from an internal dependency becomes an external boundary when it is
serialized into an API response. Map it into the declared response shape and
validate that result before returning it.

```text
handle session request:
  session = authenticated session from request context
  if session is absent:
    return the documented not-found or unauthenticated failure

  response = map session to SessionResponse
  validate response against SessionResponse
  return response with status 200
```

## Enrich One Request-Scoped Logger

Initialize one logger at request start with correlation fields, then enrich it
when authentication or routing discovers more context. Reuse that derived logger
throughout the request rather than repeatedly attaching individual fields.

```text
at request start:
  logger = logger with request_id, method, path, route

after authentication:
  logger = logger with user_id

on successful session lookup:
  log info with event=session.lookup, component=auth, outcome=success
```

## Test The Real Request Path

Use the established application, persistence, authentication, and log-capture
fixtures. In one integration test, assert the HTTP response, production
response contract, persisted effects, and structured log fields.

```text
given an authenticated user and a request identifier
when the client requests the session endpoint
then the response status is 200
and the body satisfies SessionResponse
and the persisted user can be found
and the logs for that request contain:
  event=session.lookup
  outcome=success
  request_id=<request identifier>
  user_id=<authenticated user>
```

Add separate tests for missing authentication, invalid requests, ownership
boundaries, and every documented status whose behavior matters to clients.
