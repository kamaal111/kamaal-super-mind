# Swift Snapshot Testing

Create deterministic visual regression tests at the view boundary with Point-Free's [`swift-snapshot-testing`](https://github.com/pointfreeco/swift-snapshot-testing). Use them for fixed, representative states; leave interaction flows to UI tests and behavior to unit tests.

Use Swift Testing unless the target already uses XCTest. Add `SnapshotTesting` only to the test target; exclude `__Snapshots__` from SwiftPM source compilation when necessary. For the exact `Package.swift` dependency and test-target wiring, see [installing-swift-snapshot-testing.md](installing-swift-snapshot-testing.md).

## Write The Test

Create the screen in a realistic, stable state:

- Set model inputs explicitly.
- Inject a deterministic test double for any network, persistence, or clock dependency the screen reads. Do not use live network, Keychain, current time, or random data.
- Capture every state in both light and dark (see below); do not settle for one appearance.
- Keep one assertion per intended platform/reference.

Keep each `@Test` short: build the state, assert any preconditions that prove the state is real, then hand a `@ViewBuilder` closure to a shared `assert` helper. Push all platform and color-scheme branching into that helper so the tests read as a catalog of states.

```swift
@Suite("Profile Screen Snapshot Tests")
@MainActor
struct ProfileScreenSnapshotTests {
    @Test
    func `Renders the signed-in state`() async {
        let session = UserSession(client: .preview())
        _ = await session.signIn(email: "jane@example.com", password: "Password123!")

        #expect(session.isSignedIn)
        assert(testName: #function) { makeScreen(session: session) }
    }
}
```

Pass `#function` as `testName` so the reference file name tracks the test name automatically. Name each `named:` reference for its product role and appearance, not the implementation detail — `iPhone-light`, not `iPhone13`. Add iPad references only when that layout is intentionally supported and reviewed.

## Cover Light And Dark

Every state is two references: light and dark. Loop over both schemes inside one `assert` helper and let it branch per platform, so no individual test repeats the ceremony and no appearance is silently dropped.

```swift
private func assert<Screen: View>(testName: String, @ViewBuilder screen: () -> Screen) {
    for scheme in [ColorScheme.light, .dark] {
        #if os(macOS)
            assertSnapshot(
                of: makeMacOSScreen(screen: screen(), scheme: scheme),
                as: .image,
                named: "\(scheme)",
                testName: testName
            )
        #elseif os(iOS)
            assertSnapshot(
                of: screen(),
                as: .image(
                    layout: .device(config: .iPhone13),
                    traits: UITraitCollection(userInterfaceStyle: scheme == .dark ? .dark : .light)
                ),
                named: "iPhone-\(scheme)",
                testName: testName
            )
        #endif
    }
}
```

On iOS, drive appearance through `UITraitCollection(userInterfaceStyle:)` in the image trait so the whole trait environment (not just `.preferredColorScheme`) matches the scheme.

## macOS Canvas

Snapshot an `NSHostingView` on macOS and give it an explicit desktop-shaped frame. Do not reuse a phone-sized canvas. Parameterize it by `ColorScheme` so the same helper serves both references — set the appearance, `preferredColorScheme`, and the backing-layer color together, or the empty canvas around the view renders the wrong shade.

```swift
private func makeMacOSScreen<Screen: View>(screen: Screen, scheme: ColorScheme) -> NSHostingView<some View> {
    let hostingView = NSHostingView(rootView: screen.preferredColorScheme(scheme))
    hostingView.appearance = NSAppearance(named: scheme == .dark ? .darkAqua : .aqua)
    hostingView.frame = NSRect(x: 0, y: 0, width: 1_280, height: 960)
    hostingView.wantsLayer = true
    hostingView.layer?.backgroundColor = (scheme == .dark ? NSColor.black : NSColor.white).cgColor
    return hostingView
}
```

Choose dimensions that reveal the desktop layout, then inspect the recorded PNG. A snapshot that is merely a taller phone canvas is not useful macOS coverage.

## Drive Realistic State

Reach each state through the app's real seams, not by stubbing the transport:

- Inject a configurable **preview client** to fix the outcome of a flow — `.preview()` for the happy path, `.preview(signInOutcome: .invalidCredentials)` or `.preview(signInOutcome: .validationErrors([issue]))` for failures. Pair it with a spy for persistence side effects.
- Produce error and validation states the way the user does: populate the model's inputs, then `await model.submit(using:)`, and snapshot the resulting model. A small `makeSubmittedModel` helper keeps each test to the inputs that matter.
- Inject the driven dependency into the view under test with the same modifier or environment the app uses (e.g. `.environment(session)`), wrapping in `NavigationStack` when the real screen has one.

```swift
private func makeSubmittedModel(
    session: UserSession,
    email: String = "",
    password: String = ""
) async -> SignInScreenModel {
    let model = SignInScreenModel()
    model.email = email
    model.password = password
    await model.submit(using: session)
    return model
}
```

New preview-client outcomes need their own unit tests for the preview client itself — a snapshot is not a substitute.

## Record Baselines Deliberately

Run the focused test once to observe a missing or changed reference. Record only after visually reviewing the intended state.

Use SnapshotTesting's explicit recording mode temporarily when the test runner does not pass `SNAPSHOT_TESTING_RECORD` through to the test process:

```swift
assertSnapshot(of: value, as: .image, record: .all)
```

Recording intentionally reports an issue after writing the image. Remove `record: .all` immediately, then rerun the same focused test normally to prove the committed reference matches. Never leave recording mode in source.

Keep only active baselines in `__Snapshots__/`. Delete renamed or removed device references, including stale staged files, so later commits cannot retain obsolete coverage.

## Verify

1. Run the focused macOS snapshot command.
2. Run the focused iOS snapshot command.
3. Inspect materially changed PNGs visually.
4. Run the repository's aggregate verification command.

Report the platforms and states covered, every reference added or removed, and the exact verification results. Do not claim success from a run that used an environment override when the default recipe has not passed.
