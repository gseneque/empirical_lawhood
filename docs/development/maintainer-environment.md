# Reuse environments during consolidation

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for reusing a selected environment and storage root.
It also records the maintainer's local consolidation settings.
Select your paths, then verify the interpreter and imported package.

## Prerequisites and first action

Use the route profile in [environments](../using/environments.md).
Use the [experiment procedure](../using/designing-and-running-an-experiment.md#researcher-procedure) for scientific work.
Use [Contributing](../../CONTRIBUTING.md), [testing](testing.md) and the [release procedure](../release/release-artifacts.md) for software work.
These public procedures require no local work plan.
Preserve the current working state before implementation.
Select the checkout, matching environment, operator profile and explicit output destinations.
An example path is not an available environment or storage selection.

The maintainer uses one checkout and the EL disk during consolidation.
Those local constraints appear under [Storage and retained evidence](#storage-and-retained-evidence).
Other researchers select their own supported paths and profiles.

The 14 October 2026 inspection found about 4.2 GiB free on the root filesystem.
The main environment occupied about 904 MiB.
The checkout and `/tmp` used the same filesystem.
These are observations, not current capacity guarantees.

Replace these example paths with your actual selections.
Keep output and scratch destinations outside the source checkout.
Inspect the selected mount and capacity before substantial output:

```sh
export EL_SOURCE_ROOT=/absolute/path/to/empirical_lawhood
export UV_PROJECT_ENVIRONMENT=/absolute/path/to/matching-environment
export EL_REQUIRED_MOUNT=/absolute/path/to/selected-mount
export EL_OPERATIONAL_ROOT=/absolute/path/to/selected-mount/empirical-lawhood
findmnt --target "$EL_REQUIRED_MOUNT"
df -h "$EL_OPERATIONAL_ROOT"
```

Verify write access and the profile's mount requirements through the documented [storage checks](../using/configuration.md).
If selected storage is unavailable, stop output-producing work.
Do not silently use a different filesystem.

Select the existing main environment without synchronization:

```sh
cd "$EL_SOURCE_ROOT"
test -x "$UV_PROJECT_ENVIRONMENT/bin/python"
uv run --no-sync python - <<'PY'
import importlib.metadata as metadata
import os
from pathlib import Path
import platform
import sys
import empirical_lawhood

source = Path(os.environ["EL_SOURCE_ROOT"]).resolve()
expected = source / "src" / "empirical_lawhood" / "__init__.py"
actual = Path(empirical_lawhood.__file__).resolve()
assert actual == expected, (actual, expected)
assert platform.python_version() == "3.11.14"
assert metadata.version("numpy") == "2.4.6"
assert metadata.version("scipy") == "1.17.1"
print("interpreter:", sys.executable)
print("source:", actual)
print("distribution:", metadata.version("empirical-lawhood"))
PY
```

These checks establish the selected main interpreter, numerical versions and package origin.
They do not establish every route dependency, exact selected-source identity or scientific entry authority.
Use each route's actual preflight before native contact.

## Shared environment rules

Use `uv run --no-sync` after selecting the environment.
The coordinator alone manages required dependency changes.
Do not run concurrent synchronization or editable reinstalls from different checkouts against the shared environment.
Keep dependencies unchanged while active native attempts use that environment.

A changed lockfile or incompatible dependency requirement needs a new environment decision.
Verify the selected profile before reusing an environment for another route.
Reuse existing specialist environments where their profiles match.
Keep Brian2's separate NumPy pin and interpreter separate from the main environment.

Use [testing](testing.md) for numerical thread limits before imports.
Use the registered CLI bootstrap and actual worker controls where the route requires them.
Dependency reuse does not change those controls.

Select the worker count required by the chosen scientific workflow.
New Matrix programme runs require at least four workers in the operator profile.
Copy and configure the [operator storage example](../../configs/operator-storage.example.json) for the actual host.
Select it explicitly with `--operator-profile`; the runtime has no implicit machine-specific profile.
Verify current affinity, CPU quota and memory against the selected task contracts before execution.
Matrix programme runs require four distinct physical cores and one numerical thread per worker.
Verify physical package/core pairs and the actual workers' inherited affinity.
Keep the same worker selection through preparation, authoring, run and recovery.
An existing admitted run retains its original sealed limits, including completed serial E3 and its zero-entry recovery.
The selected count also bounds independent snapshot byte verification in the
controller. Access refreshes and publication stay coordinated, and nested byte
verification remains serial. This does not change numerical threads or grant
native retry authority. Worker count alone does not establish actual Ready/Proceed admission.
Retain the selected implementation's actual worker controls and complete recovery receipts.

Do not synchronize dependencies merely to inspect files or fix prose. Reuse the
existing cache where possible; explicitly select any new substantial cache on
the chosen storage. For a check intended to produce no artifacts, use the already selected
interpreter directly with bytecode disabled if invoking uv would require writes.

## Single-checkout source selection

The maintainer's consolidation uses the sole root checkout, without additional worktrees or clones.
Reuse its environment without redirecting the editable installation.
In other deployments, select one exact source for each environment and dependent operation.

Actual workers must authenticate their selected installed implementation and
dependency environment at admission. A parent interpreter probe does not
establish worker identity. Settle scientific inputs before freezing the candidate,
then pass the positive installed public lifecycle and settled correctness gate
before fresh acquisition. Use the same exact candidate throughout that programme
and suspend edits to its installation while dependent processes remain active.

Historical source snapshots do not themselves authorize another execution.
Use only the [documented continuation](../../programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md) whose prerequisites match the retained attempt.
Preserve the original producing source, completed contacts and uncertain attempts.
Never infer replay permission from a missing terminal or parent output.

The explicit [retained-E3 controller repair](../../programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md#repair-a-failed-pure-retained-e3-adoption)
keeps the already selected scientific worker frozen while separately binding
the repaired installed parent controller. This narrow operational transition
preserves original producing sources and requires the worker's actual admission
checks. Its interpreter observation alone establishes no worker or scientific
acceptance. The original installation and FAILED terminal remain unchanged.

The [PURE development output repair](../../programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md#repair-a-pure-development-output-allowance)
also binds a separate controller and the original frozen worker environment.
It requires all original native tasks to have completed.
Only a recorded output allowance changes for selected resource-refused PURE calculations.
The original `BLOCKED` terminal and all scientific source bytes remain unchanged.

The explicit [interrupted development controller repair](../../programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md#resume-interrupted-development-with-a-repaired-controller)
also retains the original frozen worker, while allowing original uncontacted native tasks to finish.
Validate the replacement controller before a controller-only interrupt, then let active workers drain.
Its complete original custody census refuses uncertain native contact and preserves every completed acquisition.
It permits only the documented programme continuation metadata changes among adapter sources.
It changes no numerical owner, kernel, dependency lock or frozen scientific task.

The [separate native continuation](../../programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md#select-a-separate-native-continuation)
uses the same frozen-worker source checks after explicit selection of a reviewed proposal.
It retains original incomplete attempts in their original storage and gives each selected case one separate native namespace.
Preparation and default validation grant no execution.
The ordinary no-reacquisition recovery remains unchanged.

Inspect each selected check and its fixtures for writes. Select test temporary
directories and retained check outputs on the selected storage; configure `TMPDIR`, pytest's
`--basetemp` and any separate cache/output options when those tools require them.
Select uv and Ruff caches with `UV_CACHE_DIR` and `RUFF_CACHE_DIR`.
If coverage runs, set `COVERAGE_FILE` to a file in the selected packet.
Disable bytecode with `PYTHONDONTWRITEBYTECODE=1`.
For genuinely in-memory tests, use the selected interpreter with bytecode and
plugin autoloading disabled, no pytest cache, no faulthandler temporary file, no
temporary-directory fixtures and Python-level capture. Report results to the
console. Ordinary PURE/non-native tests may still write custody files and are
not automatically artifact-free. Generator `--check` modes compare source projections;
their imports must also run without bytecode or other side effects.

## Storage and retained evidence

Select output, scratch, test and evidence destinations explicitly.
Guarded commands require an explicit [operator storage profile](../../configs/operator-storage.example.json).
Set `required_mount_path` to the actual required mount and `external_root_locator` to the selected project root.
Keep artifact and scientific-scratch namespaces disjoint.
Validate the actual profile and mount through the documented [configuration procedure](../using/configuration.md).
The portable example contains placeholders and grants no authority.
Measure available space on their actual filesystems.
Coordinate large tests and native jobs against measured free space and memory.
Do not impose new scientific sample limits to fit an operational accident.

The maintainer selected the following local settings on 17 October 2026:

| Selection | Local value; not supplied by a fresh checkout |
|---|---|
| Checkout | `/home/chevre/gs-ml/empirical_lawhood` |
| Main environment | `/home/chevre/gs-ml/empirical_lawhood/.venv` |
| Required mount | `/media/chevre/EL` |
| Operational root | `/media/chevre/EL/empirical-lawhood` |
| Retained default profile | `/media/chevre/EL/empirical-lawhood/operator-profiles/el-four-core-default.json` |

For this consolidation, all new operational outputs remain on EL.
If EL is unavailable, stop those writes; do not use the root volume.
An existing admitted run keeps its own selected profile and sealed limits.
The external default profile is local custody, not a packaged prerequisite for other researchers.

EL was verified writable outside the sandbox. Use that context for this maintainer's operational writes;
a sandbox-only read-only view is not evidence that the actual disk is unwritable.
The 20 October execution-entry check wrote and synced an unnamed temporary probe
beneath the project root, then closed it. The actual disk was writable and had
about 155 GiB available. These observations do not replace later mount, access,
memory and full selected-graph capacity checks before substantial output.

The 14 October inspection found about 268 GiB free on SEMIOS, using VFAT and
appearing read-only in that tool session. SEMIOS is no longer the default for
new outputs. Existing retained paths and receipts remain bound to their original
locations; selecting EL does not migrate them. The researcher has now authorized
read-only access to SEMIOS for original evidence. Operational outputs remain on EL.
On 25 October the owner separately selected SEMIOS for the Markdown-plan cleanup
backup/archive. Its verified byte copies are bound by the
[cleanup custody record](history/plan-cleanup-custody-20261025.json). This scoped archive
selection does not move scientific outputs or change the default operational disk.
Keep environments and owner-controlled trust storage on a filesystem with the required POSIX behavior.
Use an existing supported bulk-data backend where its custody requirements permit VFAT.

Retain exact completed data through manifests and references instead of repeated whole-directory copies.
Archive required historical code and records before retiring active implementations.
Inventory old worktrees, caches and test scratch before removing anything.
Verify that a removal candidate is disposable and has no live process or retained evidence dependency.
Do not delete original scientific outputs, uncertain attempts or their provenance to recover space.

## Validation and final release

Use the shared environment for affected development checks while its profile remains valid.
Run documentation checks without creating another environment:

```sh
uv run --no-sync python scripts/check_documentation.py
```

The final release procedure still checks an isolated installation and built artifacts.
Run it after the source settles, under [CONTRIBUTING](../../CONTRIBUTING.md).
The [release runner](../../scripts/release_check.py) supports an explicit `--environment-root` on a suitable writable filesystem.
That option creates fresh release environments and does not reuse this development environment.
Select the release packet and environment destinations according to the runner's path requirements.
The runner now selects the committed source in this checkout, discloses the
untracked local plan separately and retains the exact current source archive.
The source distribution and wheel carry the same build-source metadata;
installed execution selects that candidate without reconstructing a Git bundle.
Current run entries refer to one retained candidate record. Its
focused controls do not establish release conformance. Select the new release
packet and any fresh environment root on selected storage after the source settles, then run
the complete gate.

Do not claim installation or release conformance from a shared development environment alone.
If capacity prevents a required gate, retain its explicit open status and complete independent work.

## References and research

- [uv project configuration](https://docs.astral.sh/uv/concepts/projects/config/): absolute environment selection and shared-environment caveats.
- [uv locking and synchronization](https://docs.astral.sh/uv/concepts/projects/sync/): `--no-sync` behavior.
- [Git worktrees](https://git-scm.com/docs/git-worktree): linked source checkouts and shared repository storage.
