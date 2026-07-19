---
name: swift-snapshot-tests
description: Add or update a SwiftUI snapshot test for a given screen. Use when asked to snapshot-test a specific SwiftUI view or screen, cover its light/dark or macOS/iOS appearance, or record missing baselines.
---

# Swift Snapshot Tests

Load the `software-testing` skill first and follow its discovery, boundary, and coverage rules — this skill only adds the screen invocation shape.

## Locate The Screen

When invoked with a screen name or path (e.g. `ProfileScreen` or `Sources/Feature/ProfileScreen.swift`), find the view, its model, the dependencies it reads (session, client, store), and any existing snapshot test or `__Snapshots__` baseline before writing anything. Use `software-testing`'s "Discover Before Writing" guidance to find the test target's existing fixtures and preview clients rather than inventing new ones.

## Write The Test

In the `software-testing` skill, read its swift-snapshot-testing reference and apply it directly:

- Drive the screen into a realistic, stable state through its real seams (a preview client, injected session, or model inputs) rather than stubbing the view itself.
- Cover every state in both light and dark, and add the macOS canvas alongside iOS when the screen ships on both platforms.
- Keep one `@Test` per state; push platform and color-scheme branching into a shared `assert` helper.
- Record baselines deliberately: run the focused test once to observe the missing or changed reference, review the PNG, then remove any temporary recording mode.

If the module does not yet depend on `SnapshotTesting`, look in that same skill for its installation reference to see how to wire it in.

## Verify

Run the focused snapshot test for each platform covered, inspect materially changed PNGs visually, then run the repository's aggregate verification command. Report the states covered, every reference added or removed, and the exact verification results.
