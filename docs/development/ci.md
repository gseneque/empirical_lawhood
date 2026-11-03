# CI and selected profiles

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for hosted verification jobs and their input requirements.
It separates bounded CI checks from explicitly selected workflow, scale, native and held checks.
Use it to select a job and retain its evidence packet.

[Release checks](../../.github/workflows/release-check.yml) runs `portable-ci-check` on pushes and pull requests.
It uses Ubuntu 24.04 x86-64, CPython 3.11.14 and uv 0.11.28.
The `ci` profile verifies bounded contracts, static errors, generators and documentation.
It builds the wheel through the sdist and runs the existing installed-wheel checks outside the checkout.
Those checks include the exposed reactor example.
This profile provides no complete portable coverage claim or scientific qualification.

The [profile selector](../../scripts/test_profiles.py) owns explicit CI and scale module declarations.
Every other portable module belongs to `integration`, including new modules until review.
The three profiles partition the complete portable case census without dropping tests.
Native and held cases retain their separate selectors and prerequisites.
Review fixture cost and contract coverage before adding a module to CI.

The CI job retains the [frozen RC numerical profile](../using/environments.md#frozen-rc-numerical-input-profile).
It verifies exact original descriptor and fibre hashes before tests.
Its 45-minute limit is an operational budget, not a measured hosted duration or a passing result.

`workflow_dispatch` always runs bounded CI and can select one additional profile:

| Selection | Hosted work | Evidence limit |
|---|---|---|
| `ci` | Bounded checks and installed artifacts | No complete portable suite or critical-coverage claim |
| `integration` | Four module shards of remaining portable workflow checks | All four passing shards are needed for this profile |
| `scale` | Four module shards of explicit population, payload, memory and compiler checks | All four passing shards are needed for this profile |
| `native-open` / `native-brian2` | Selected native stack and checks | Required absent prerequisites fail |
| `held-reactor` / `held-response` | Maintainer-managed held-input runner | Requires permitted original inputs and actual access |

Integration and scale jobs each permit 240 minutes.
The deterministic module hash keeps all cases from a module in the same shard.
It does not promise equal elapsed times.
`fail-fast: false` preserves other shards when one fails.
Compare the source, profile, shard count and eligible census hash across all four packets.
Require every shard index exactly once and every selected check to pass.
Unselected, queued, interrupted or failed jobs supply no passing profile evidence.

The complete `portable` selector remains available through the local [release procedure](../release/release-artifacts.md).
It retains its existing critical-coverage measurement and precommit-evidence reuse contract.
Partition passes do not substitute for that coverage receipt.
Do not repeat a completed full suite for a focused correction.
Preserve its original outcome and bind affected checks separately.

Hosted artifacts retain manifests, selection censuses, logs and disclosed fixtures for 30 days.
CI also retains exact build inventories and artifacts.
Download the selected evidence before retention expires.
Failed checks upload available diagnostics.
Artifact existence alone is not success.
Allow space for environments, fixtures and retained archives on the actual selected filesystem.
Large workflow and scale fixtures can need substantially more than bounded CI.

Held profiles run on a maintainer-managed Linux x86-64 runner labeled `empirical-lawhood-held` through the `held-inputs` environment.
Before enabling this runner, configure environment reviewers and permitted read-only sources.
Configure guarded mounts, native software and explicit input variables from [testing](testing.md).
Never run an untrusted pull request on this runner.
Held packets remain on the permitted runner for review.
No raw sources, outcomes, keys or private logs are uploaded publicly.

Historical source-amended Matrix recovery is not a selectable release profile.
Use [current-run recovery acceptance](testing.md#current-run-recovery-acceptance) with the settled installed candidate and exposed controls.
It must pass before fresh scientific acquisition and supplies no scientific authority.

After an authorized push and a passing run, select `portable-ci-check` in branch protection or the repository ruleset.
Replace any required `portable-release-check` name when activating this workflow change.
Make sure that a deliberately failing proposed change is blocked.
Workflow YAML does not configure repository protection.
This local change claims no hosted run or remote settings change.

Action references remain pinned commits.
Cache keys use `uv.lock`; a warm cache does not relax locked installation.
Hosted jobs use network installation.
Use `--offline` only with a separately verified complete local cache.

## References and research

The [release runner](../../scripts/release_check.py) owns selected-source packets and artifact checks.
The [test selector](../../scripts/test_profiles.py) owns portable partitions and module shards.
The [scientific integrity guide](../reference/scientific-integrity.md) defines separate evidence and authority boundaries.
