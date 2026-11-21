# Run locally on CPU or select a GPU backend

SPDX-License-Identifier: CC-BY-4.0

Local CPU execution remains the default. A copied operational configuration
selects whether a supported operation requests acceleration. Scientific inputs,
the numerical implementation, execution placement and retained custody have
separate identities; changing one does not silently rewrite the others.

## The configuration switch

Use the [existing operational example](../../configs/operational.example.yaml).
It already selects CPU operation:

```yaml
schema: empirical-lawhood/runtime/operational-configuration
version: 3.0.0
value:
  artifact_verification: reduced
  scientific_reconstruction: 'off'
  accelerated_compute: false
```

`false` requests the implemented CPU route; `true` requests the operation's
declared accelerated route. Omission selects `false`. The field is a boolean,
not a string. Original version 1 and 2 configurations remain readable and
select CPU operation without changing their bytes.

From the matching checkout or source distribution, validate your copy:

```sh
uv run --no-sync empirical-lawhood config validate \
  --config /absolute/work/operational.yaml \
  --consumer operational-configuration --format json
```

Put the global operational selection before the command group:

```sh
uv run --no-sync empirical-lawhood \
  --operational-config /absolute/work/operational.yaml \
  campaign rc-ladder-native-check \
  --config programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json \
  --output-dir /absolute/work/rc-cpu-check
```

Choose a fresh output directory and the environment from the
[installation guide](../getting-started.md). The RC control reports
`backend: rc-ladder.scipy-cpu`, `gpu_devices: 0`,
`disposition: NOT_REQUESTED` and `native_numerical_check_executed: true`.
It does not issue a campaign or qualify scientific evidence. Its retained
`invocation.json` records the exact operational selection. No CUDA device or
cloud account is required. The same configuration applies to the complete
[recursive investigation route](define-investigation.md); no alternate
scheduler, custody store or recovery procedure is needed.

If acceleration is requested for an operation that has only a CPU
implementation, that operation reports `UNSUPPORTED_OPERATION` with its actual
CPU backend and zero GPU devices. This is an explicit placement result, not a
claim of GPU execution. A frozen plan that actually requires a GPU is refused
when acceleration is disabled or the required device is unavailable.

## Capacity is selected separately from numerical settings

The shared local executor observes usable CPU affinity, container CPU quota,
available RAM and memory limits. It admits each unchanged task requirement
against that capacity. The public local-workspace constructor derives a worker
limit automatically; explicit lower concurrency limits remain available.
Routine CPU operation requires no device count or cloud deployment selection.

Scientific numerical thread counts, solver settings, tolerances, precision and
random streams retain their authored values. Increasing host cores does not
authorize a new thread count. A host that cannot contain the declared task is
refused with its capacity reason; no scientific approximation is substituted.

## Rubisco numerical engines

Rubisco's complete periodic-force operation implements these explicit choices:

| Selected engine | Electronic implementation | Molecular implementation | Invocation |
| --- | --- | --- | --- |
| `PeriodicNumericEngine` | CPU PySCF direct integrals | OpenMM Reference | `accelerated_compute: false` |
| `AcceleratedPeriodicNumericEngine` | GPU4PySCF direct integrals | OpenMM CUDA, double precision | `accelerated_compute: true` |
| `GpuReferencePeriodicNumericEngine` | GPU4PySCF direct integrals | OpenMM Reference | `accelerated_compute: true` |

Follow the [periodic force procedure](../../programmes/biology/photosynthesis/workflows/rubisco-response/periodic-force-probe.md)
to select the actual installed numerical environment and prepare original
inputs. Its `select_periodic_numeric_engine` API derives the engine type from
the same operational selection and binds the complete interpreter/package
census. CPU selection has no GPU-memory operands. GPU selection requires its
actual host/device allocations and, where selected, `molecular_platform='Reference'`.

Changing the flag on an **already frozen GPU investigation** cannot convert it
into a CPU investigation: its engine record and complete package census would
disagree. Author a new attempt with the CPU engine while retaining the original
scientific model and declared numerical settings. Preserve the original attempt
and all completed or uncertain native effects. The same rule applies when
changing the OpenMM platform. A constrained electronic state currently supported
only by the GPU implementation retains that explicit capability refusal on CPU.

This distinction is consequential: a local CPU run of supported work needs only
the operational selection and its appropriate existing environment; converting
an immutable molecular numerical apparatus requires a newly authored selection.
The software does not assert CPU/GPU numerical equivalence without the selected
independent controls.

## Place unchanged supported GPU work remotely

The [accelerated-compute procedure](../using/accelerated-compute.md) owns the
complete SkyPilot/Runpod preparation, staging, supervision and return route.
Use the same frozen GPU scientific work for a compatible local GPU host or the
remote host. `RunpodDeploymentSelection.for_execution_plan` derives conservative
CPU, RAM and transfer allowances from that plan and its resource envelope.
The exact numerical backend and thread count remain bound independently of the
host size. An explicit larger host override does not rewrite task budgets.

Hosted deployment supports one GPU and two explicitly implemented worker
profiles: the periodic PySCF/OpenMM profile and the JAX CUDA12/TORAX float64
profile. It refuses a CPU-only remote plan, multiple-GPU requirements or an
unsupported numerical backend. These are limits of the hosted route; they do
not remove local CPU execution.

For the new R17/R22 experiment operations, use the code-owned
`empirical_lawhood.api.accelerated_deployment.JAX_TORAX_BACKEND` with
`RunpodDeploymentSelection.for_execution_plan`. Its CPU backend is
`jax.torax.cpu.float64`; its accelerated backend is
`jax.torax.cuda12.float64`. The selected scientific plan, numerical threads,
typed native payloads and existing result/recovery lifecycle remain the same
operands of remote placement. Select a new operational execution attempt when
changing device; do not relabel a completed or uncertain attempt.

The JAX hosted profile requires an authenticated transferred or retained
offline worker bundle. It validates the locked JAX CUDA12 plugin/PJRT and NVIDIA
library versions, selects CUDA plus float64, and declares an explicit persistent
compilation-cache path. Its bootstrap does only dependency-census and CPU-import
checks; actual GPU admission and numerical validation belong to the native
execution handoff. It does not inherit the periodic profile's CuTensor,
GPU4PySCF or OpenMM assumptions. See the
[JAX worker bundle procedure](../using/accelerated-compute.md#jax-cuda12-torax-worker-profile).

Before a task is presented as prepared, storage compares every actual payload
archive member with the sealed original census and authenticates the complete
archive carrier in the same bounded streaming read. A source file restored
after a transient mutation cannot make a corrupted archive acceptable. Closing
source checks, remote complete-census verification, actual host admission,
original operation authority and unknown-completion protections remain active.

Offline preparation establishes source, configuration and transfer consistency.
Actual provider access, current offer, GPU installation, measured native
performance, spending authority and numerical agreement require their original
entry and acceptance evidence.

## M50 continuity

The [M50 migration record](../release/m50-migration.md) identifies the original operating record.
Its 13 November 2026 amendment raised the account to
**USD 55**, superseding earlier USD 50 future selections. The original 10 prefix,
8 initial-primary, 12 later-diagnostic and 4 withheld-return ceilings remain;
the optional four-return refinement needs its own supported decision.

The latest history records local focused verification, original environmental
design preparation and the bounded R4 processing/staging acceptance. It waives
the repeated full local lifecycle and retains a focused installed environmental
control for the remaining R3 scope. V1.0 consolidation does not reopen those
decisions, repeat completed acquisitions or turn software checks into molecular
findings. The new source identity must be bound explicitly before new execution.
Actual remote allocation and native numerical acceptance retain their own gates.

Work plans are kept in original custody, outside release packages. Public
scientific procedures and the [implementation coverage map](../release/implementation-coverage.md)
remain the supported shipped routes.
