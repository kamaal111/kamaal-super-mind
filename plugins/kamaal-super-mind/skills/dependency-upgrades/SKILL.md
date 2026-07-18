---
name: dependency-upgrades
description: Upgrade, pin, or audit dependencies safely. Use when checking outdated packages, selecting versions, updating manifests and generated dependency state, screening advisories, or resolving upgrade breakages.
---

# Dependency Upgrade Best Practices

Upgrade dependencies in controlled, explainable batches. Prefer deliberate changes over broad blind bumps.

## Discover First

- Read repository instructions, task runners, manifests, and generated-artifact rules before editing.
- Inventory each package-manager surface separately in multi-language repositories.
- Group upgrades into sensible batches and call out packages likely to require source changes.

## Screen Candidates

- Respect any repository minimum release-age policy unless the user explicitly overrides it.
- Prefer the newest stable release that meets that policy and passes advisory screening.
- Check authoritative advisories, maintainer notices, registry warnings, and compromise reports when available.
- Treat a suspected compromise as a blocker: state the package, affected version, evidence, and likely impact instead of quietly upgrading through it.

## Upgrade Correctly

- Change manifests as the source of truth, then use the relevant package manager to regenerate lockfiles, resolved files, and generated artifacts.
- Never hand-edit lockfiles or other generated dependency state.
- Upgrade one high-risk surface at a time; do not mix unrelated runtime, tooling, generator, and framework changes without a reason.

## Validate And Repair

- Run the smallest useful build, lint, typecheck, or test after each batch.
- Adapt source code, schemas, wrappers, and tests to new public APIs instead of masking failures with casts, suppressions, warning downgrades, or immediate pins.
- Stop expanding scope when breakage becomes noisy; finish one breakage cluster before starting another.
- Finish with the repository's aggregate verification command and report upgraded batches, repaired breakages, commands, and any remaining risk.
