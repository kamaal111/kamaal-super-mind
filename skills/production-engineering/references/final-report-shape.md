# Final Report Shape

The final response for any task under this skill must use these four headings,
in this order, with nothing else at the top level. Fill each one in; do not
skip, merge, or reorder them, and do not rename them.

```
## Understanding
## Changes
## Verification
## Doubts / remaining gaps
```

- **Understanding** — one or two sentences restating the goal as you understood
  it. This is what lets the user catch a misread task before judging the diff.
- **Changes** — the concrete edits made, by file or area. Not a narration of
  steps taken; a summary of what is different now.
- **Verification** — every command actually run and its result, including a
  command that failed and how it was resolved. If verification was skipped
  (documentation-only or skill-only change), say so explicitly here instead of
  omitting the section.
- **Doubts / remaining gaps** — every doubt, tradeoff, environment issue, or
  gap left behind. Write `None` explicitly when there genuinely are none; do
  not omit the heading.

## Compliant Example

```
## Understanding
Add rate limiting to the `/v1/uploads` endpoint so a single API key can't
exhaust worker capacity.

## Changes
- `src/routes/uploads.ts`: wrapped the handler with the existing
  `rateLimit` middleware, keyed by API key, 20 req/min.
- `src/routes/uploads.test.ts`: added a test asserting a 429 on the 21st
  request within a window.

## Verification
- `npm run test -- uploads` → passed (12 tests)
- `npm run lint` → passed
- `npm run typecheck` → passed

## Doubts / remaining gaps
The 20 req/min limit is a guess matched to the existing `/v1/downloads`
limiter; confirm it's the right number for uploads specifically.
```

## Non-Compliant Example (do not do this)

```
I added rate limiting to the uploads endpoint using the existing
middleware, keyed by API key. Tests pass and lint is clean. Let me know if
you want a different limit — I picked 20/min to match the downloads route.
```

This covers the same facts but fails the shape contract: no headings, so an
automated or skimming reviewer cannot locate the verification results or
confirm a doubts section was actually considered, and it is easy for future
sections (like doubts) to get silently dropped under time pressure since
there is no required slot for them to occupy.
