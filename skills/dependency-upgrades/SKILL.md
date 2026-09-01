---
name: dependency-upgrades
description: Upgrade, pin, or audit dependencies safely. Use when checking outdated packages, selecting versions, updating manifests and generated dependency state, screening advisories, or resolving upgrade breakages.
---

# Dependency Upgrade Best Practices

Upgrade dependencies in controlled, explainable batches. Prefer deliberate changes over broad blind bumps.

## Default Scope

- When the user requests a dependency upgrade without naming packages or limiting scope, update every direct dependency to the newest stable version that satisfies the repository's release-age policy, then regenerate the full dependency graph through the package manager. Do not stop after the packages shown by an outdated-dependency report.
- Treat the repository's configured minimum release age as authoritative. If it has none, use a 24-hour minimum release age unless the user explicitly chooses another policy.
- Transitive versions are controlled by the regenerated lockfile. Do not hand-edit them or force arbitrary transitive overrides; inspect and address them through their direct dependents, overrides, or resolutions when necessary.

## Discover First

- Read repository instructions, task runners, manifests, and generated-artifact rules before editing.
- Inventory each package-manager surface separately in multi-language repositories.
- Group upgrades into sensible batches and call out packages likely to require source changes.

## Screen Candidates

- Respect any repository minimum release-age policy unless the user explicitly overrides it.
- Prefer the newest stable release that meets that policy and passes advisory screening.
- Check authoritative advisories, maintainer notices, registry warnings, and compromise reports when available.
- Treat a suspected compromise as a blocker: state the package, affected version, evidence, and likely impact instead of quietly upgrading through it.
- Before completion, audit the finalized dependency graph and explicitly report the security result, including any unresolved advisories, deprecated packages, suspicious release-age or provenance signals, and mitigations.

## Upgrade Correctly

- Change manifests as the source of truth, then use the relevant package manager to regenerate lockfiles, resolved files, and generated artifacts.
- Never hand-edit lockfiles or other generated dependency state.
- Upgrade one high-risk surface at a time; do not mix unrelated runtime, tooling, generator, and framework changes without a reason.

## Validate And Repair

- Run the smallest useful build, lint, typecheck, or test after each batch.
- Adapt source code, schemas, wrappers, and tests to new public APIs instead of masking failures with casts, suppressions, warning downgrades, or immediate pins.
- Stop expanding scope when breakage becomes noisy; finish one breakage cluster before starting another.
- Fix upgrade-caused compatibility failures in source code, schemas, wrappers, and tests; do not leave the requested update incomplete merely because a public API changed.
- Finish with the repository's aggregate verification command and report upgraded batches, repaired breakages, commands, and any remaining risk.
