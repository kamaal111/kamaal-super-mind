# Installing Swift Snapshot Testing

Wire [`swift-snapshot-testing`](https://github.com/pointfreeco/swift-snapshot-testing) into the SwiftPM module whose screens you are snapshotting.

## 1. Add The Package Dependency

Add the package to the module's `dependencies` array, pinned to the next major version:

```swift
dependencies: [
    // ...existing dependencies...
    .package(url: "https://github.com/pointfreeco/swift-snapshot-testing", .upToNextMajor(from: "1.19.3")),
]
```

Keep the version aligned with any other module in the repository that already depends on it rather than floating a newer one independently.

## 2. Add The Product To The Test Target Only

`SnapshotTesting` belongs on the `.testTarget`, never on the shipping `.target`:

```swift
.testTarget(
    name: "FeatureTests",
    dependencies: [
        "Feature",
        .product(name: "SnapshotTesting", package: "swift-snapshot-testing"),
    ],
    exclude: ["__Snapshots__"],
),
```

Two things the manifest must do:

- **`exclude: ["__Snapshots__"]`** — the recorded PNG baselines are resources, not Swift sources. Excluding the directory keeps SwiftPM from trying to compile them and keeps the target's source list clean.
- **Match the target's `swiftSettings`** — mirror whatever upcoming features or warnings-as-errors settings the module already enables so snapshot tests build under the same rules as production code.

## 3. Import In The Test File

```swift
import SnapshotTesting
import SwiftUI
import Testing

@testable import Feature
```

Use `@testable import` for the module under test (and any module whose preview/testing helpers you drive).

## 4. Resolve And Verify

Let SwiftPM resolve the new dependency and confirm it builds through the repository's aggregate verification command.

While iterating, use the narrower snapshot recipes (see the main reference's Verify and Destinations sections) instead of the full aggregate each run.
