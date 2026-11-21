# CI and selected profiles

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for hosted verification jobs and their input requirements.
It separates bounded CI checks from explicitly selected workflow, scale, native and held checks.
Use it to select a job and retain its evidence packet.

[Release checks](../../.github/workflows/release-check.yml) runs `portable-ci-check` on pushes and pull requests.
It uses Ubuntu 24.04 x86-64, CPython 3.11.14 and uv 0.11.28.
The `ci` profile verifies bounded contracts, independent numerical references,
coverage-path configuration, static errors, generators and documentation.
It builds the wheel through the sdist and runs the existing installed-wheel checks outside the checkout.
Those checks include the exposed reactor example.
This profile provides no complete portable coverage claim or scientific qualification.

For a local `ci` or `portable` gate on the supported AVX2/FMA host, select the
[declared frozen RC numerical profile](../using/environments.md#frozen-rc-numerical-input-profile)
before running the release command:

```sh
export OPENBLAS_CORETYPE=HASWELL
export NPY_DISABLE_CPU_FEATURES=X86_V4,AVX512_ICL,AVX512_SPR
```

The hosted job already supplies these variables. The locked package versions
alone do not select the original CPU dispatch. An exact-input mismatch is a
refusal to reproduce that exposed example; do not regenerate its frozen hashes
to fit a different host profile.

The [verification-purpose plugin](../../scripts/test_purposes.py) reports
`conformance` and `numerical` independently of CI/integration/scale cost profiles.
Numerical cases name their mathematical oracle; required CI references cannot
silently lose that declaration. The [testing guide](testing.md#verification-purpose-and-execution-profile)
defines the reviewed subset and its limits. Purpose is retained with each
selected and executed case, rather than inferred from a filename or a passing build.

The [profile selector](../../scripts/test_profiles.py) assigns bounded CI and scale modules. Other portable modules belong to integration.
Every push, tag and pull request runs the bounded CI profile and the installed-package checks.
Branch pushes and pull requests also run eligible cases from changed modules declared `bounded` in the
[test change decisions](../../scripts/test_change_decisions.json). An edit to a bounded test runs its current bytes.
For a new branch, CI uses the merge base with the default branch when available. Tags run the bounded profile directly.
A manual integration, scale, native or held job keeps its run when another commit arrives on the same branch.

To reproduce the automatic branch comparison locally, pass `--bounded-changes-since BASE_COMMIT` with
`--profile ci`. The selection packet records the compared modules and their profiles. The execution packet records
which cases actually ran and their outcomes. Portable CI excludes native and held cases.

### Optional exact-source audit

Select an audit when a review needs evidence for the whole change. The audit checks exact module digests,
declared native and held exclusions, and passing receipts for integration or scale cases. A changed shared fixture
or `conftest.py` can require complete portable evidence. The audit verifies that a shared fixture contains fixtures
and preserves the record of any test bodies in the previous revision.

For a local audit, supply the comparison commit and its exact-source partition manifest or complete portable evidence.

```sh
uv run --no-sync python scripts/release_check.py --profile ci \
  --changed-tests-base BASE_COMMIT \
  --changed-test-evidence /absolute/passing-profile/release-manifest.json \
  --output-dir /absolute/new-ci-packet
```

Repeat `--changed-test-evidence` for required shards. Evidence reuse authenticates source, bound logs and executed-case coverage.
For a hosted audit, select `changed_test_audit_base` during manual dispatch. Supply any existing evidence with
`changed_test_evidence_runs`. Ordinary CI requires only the checked-out repository and its declared dependencies.

The CI job retains the [frozen RC numerical profile](../using/environments.md#frozen-rc-numerical-input-profile).
It verifies exact original descriptor and fibre hashes before tests.
The hosted job allows two hours for setup, test execution, both builds and the installed checks.

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

Hosted artifacts retain manifests, selection and execution censuses, logs and disclosed fixtures for 30 days.
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
