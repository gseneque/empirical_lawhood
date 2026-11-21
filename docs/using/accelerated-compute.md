# Select accelerated compute

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for optional GPU execution and deployment preparation.
It keeps operational selection separate from numerical acceptance and scientific authority.
Select the operation, environment and explicit storage paths before preparation.
The [CPU and GPU selection guide](../v1.0/cpu-and-gpu.md) gives the local CPU
configuration, expected output and the boundary between an operational switch
and a newly selected immutable molecular numerical engine.

## Remote execution within the researcher workflow

Preserve the existing EL researcher workflow when you select remote compute.
EL owns experiment design, preparation, authoring, prerequisites, scientific stage decisions, recovery, independent assessment and export.
The deployment layer supplies host allocation, environment installation and transfer of exact inputs and original evidence.
Select supported heavy operations, such as complete force evaluations, relaxation, equilibrium sampling and trajectories, for remote execution.

Use a complete operation or prepared batch as the remote execution unit.
Keep its internal force evaluations on the selected GPU host.
The current route places the existing EL controller and workers together on that remote host for the selected work.
It does not dispatch individual tasks from a continuously local scheduler to remote workers.
Reuse a compatible allocated host only through supported upstream lifecycle commands and the next operation's original admission checks.

Provide prepared execution configurations and documented commands for each authorized stage.
A single convenience command is optional.
Scientific stage decisions remain with the existing workflow, including decisions based on measured cost and returned evidence.
Return complete authenticated evidence, including failures, unknown completion, receipts and original costs, to the existing custody and assessment services.

Report readiness for the next remote stage separately from readiness of the complete scientific pathway.
Each stage requires its own implementation, inputs, acceptance and execution authority.
A missing downstream supplier does not itself prevent an earlier stage whose prerequisites are satisfied.
Completion of that earlier stage supplies no missing downstream evidence.

## Select the operation

Copy the [operational example](../../configs/operational.example.yaml) to your selected working directory.
Set `value.accelerated_compute` to the boolean `true` for a supported GPU operation.
Use `false` or omit the field for the existing CPU route.
The [configuration guide](configuration.md#optional-accelerated-compute) explains original configuration revisions and invocation custody.

```text
empirical-lawhood config validate --config /absolute/work/operational.yaml --consumer operational-configuration --format json
empirical-lawhood config prepare --config /absolute/work/operational.yaml --consumer operational-configuration --output-file /absolute/work/operational.json --format json
```

Put `--operational-config /absolute/work/operational.json` before the command group.
The field selects supported adapter behavior; it does not provision a machine.
Validation, help, configuration preparation and static discovery inspect no device or provider.
The API uses `accelerated_compute_operation(True)` from `empirical_lawhood.execution.operational_configuration` for the same invocation scope.

| Operation | Selected behavior |
| --- | --- |
| Rubisco periodic force probe and explicit density restart | Separate accelerated configurations select direct GPU4PySCF integrals and an explicit OpenMM platform |
| Rubisco active-state relaxation, equilibrium sampling and unbiased reference trajectories | Separate accelerated configurations use the complete GPU operator, original lifecycle and independent readers |
| RC ladder native comparison | Executes its existing SciPy calculation and reports `UNSUPPORTED_OPERATION` when acceleration was requested |
| Other existing operations | Their declared CPU route remains available; the flag supplies no new numerical implementation |

Use the [periodic force guide](../../programmes/biology/photosynthesis/workflows/rubisco-response/periodic-force-probe.md) for molecular preparation and authoring.
Select `AcceleratedPeriodicNumericEngine` with explicit host-memory, device-memory and numerical-thread allowances.
This original selection uses OpenMM CUDA double precision.
For GPU electronic work with complete binary64 MM, select `GpuReferencePeriodicNumericEngine` through `select_periodic_numeric_engine(molecular_platform='Reference')`.
That separate engine uses the OpenMM Reference platform for the complete molecular contribution.
It retains the full atom population, parameters, periodic method and selected tolerances.
It performs no automatic fallback from an existing CUDA selection.
The independent reader checks the selected platform against the actual apparatus record.
The selected engine must agree with the invocation flag.
A CPU configuration cannot silently become a GPU attempt.
Select and author a separate CPU attempt when CPU execution is required.

The relaxation and sampling authoring functions derive their backend from the selected prototype engine.
Select the same backend in the invocation's `accelerated_compute` flag.
Each GPU task binds one device and the prototype's exact host-memory allocation.
The readers authenticate original force costs as well as the selected physical or sampling trace.
Missing costs remain explicit assessment failures or unavailable observations.
Successful software controls do not establish a relaxed molecular basin, physical rates or enzyme throughput.

## Select the environments

The [controller project](../../configs/accelerated-compute/controller/pyproject.toml) and [worker project](../../configs/accelerated-compute/worker/pyproject.toml) have separate `uv.lock` files.
Both select Python 3.11.14 on Linux x86-64.
Keep the original CPU reference installation unchanged.
Select external environment, cache and temporary directories before synchronization.
Replace the example paths with your actual selections.

```sh
UV_CACHE_DIR=/absolute/cache TMPDIR=/absolute/tmp UV_PROJECT_ENVIRONMENT=/absolute/controller-env uv sync --locked --python 3.11.14 --project configs/accelerated-compute/controller
UV_CACHE_DIR=/absolute/cache TMPDIR=/absolute/tmp UV_PROJECT_ENVIRONMENT=/absolute/gpu-env uv sync --locked --python 3.11.14 --project configs/accelerated-compute/worker
```

After environment selection, use `uv run --no-sync` or the selected interpreter directly.
The controller pins SkyPilot `1.0.0.dev20261103`, commit `796c5bcc8041a9dcf92c1182fabbafd9a5ab9ed2`.
Its selected on-demand Runpod implementation uses REST v2.
The [offline control](../../scripts/check_skypilot_runpod.py) verifies the actual installed parser and request construction without provider contact.
Mocked responses establish no actual access, allocation or spend.

Runpod's pod-list response can omit direct SSH details for a running pod.
The selected [controller correction](../../configs/accelerated-compute/controller/runpod-pod-detail.patch)
resolves that same pod through its detail endpoint and refuses a changed pod ID.
Apply it to a separate copy of the pinned controller, preserving the original installation.
The source inspector records the exact correction digest separately from the upstream commit.
Run the offline control in that selected copy before using it for actual provisioning.
After interrupting a pending connection-discovery request, resolve the original pod and
reuse the same upstream cluster; do not create a replacement merely because discovery stalled.

The worker pins GPU4PySCF 1.8.1, PySCF 2.14.0, CuPy 13.4.1, OpenMM 8.3.1 and their CUDA dependencies.
OpenMM CUDA 8.3.1 uses a signed byte count when it clears PME buffers.
The adapter refuses grids whose complete binary64 buffer exceeds that count, before electronic evaluation.
OpenMM CUDA also accumulates forces in fixed-point storage with a finite range.
The explicit Reference MM selection avoids these CUDA limits and its float32 nonbonded parameter storage.
OpenMM Reference 8.3.1 also uses signed integer indices for its complete PME grid.
The adapter refuses larger grids unless the actual loaded library advertises the separately assessed index-width correction.
Its host-memory allocation must also contain the complete complex grid.
That necessary memory check does not bound all other native allocations.
Switching platforms alone does not establish admission for every refinement.
Numerical admission does not establish molecular preparation or chemical accuracy.
The selected GPU4PySCF binary requires compute capability 7.0 or later.
A GTX 1060 can run the selected OpenMM smoke controls but cannot run this quantum GPU backend.
Its quantum preflight refuses before native scientific entry.

### Large Reference PME grids

Use a separate environment when a selected Reference grid exceeds the original signed index range.
The [OpenMM correction](../../configs/accelerated-compute/worker/openmm-reference-pme-index64.patch) changes complete-grid indexing to `size_t`.
It preserves the PME equations, floating-point expressions, interpolation order, FFT, grid dimensions and selected tolerances.
It exports `empirical_lawhood_reference_pme_index_bits` for actual native admission.
An unmodified library retains the original refusal.

Apply the patch to pristine OpenMM 8.3.1 sources in an explicitly selected build directory.
The original `ReferencePME.cpp` SHA-256 is `f4c53d129a6a3235726b3c2d537db0a08ea30bdcab99cc32fbc785a0794eceb6`.
Build `OpenMM`, `TestReferenceNonbondedForce` and `TestReferenceDispersionPME` with the selected worker's C++ ABI.
The locked wheel uses `_GLIBCXX_USE_CXX11_ABI=0`.
Run both upstream tests and compare charged and neutral Reference energies and forces against the unchanged library.
Verify import and native admission in the exact worker environment before selecting the new engine.

Retain the source archive, patch, compiler, commands, library digest and all control results.
Keep the original environment unchanged and select the new complete file census through `select_periodic_numeric_engine`.
Use `molecular_platform='Reference'` with an explicit sufficient `host_memory_bytes` allocation.
Changed library bytes create a distinct engine identity.
Small software controls do not establish accuracy for an unmeasured large-grid refinement.

The [container recipe](../../configs/accelerated-compute/Dockerfile) installs the locked worker dependencies and registers their CUDA library directories.
Build from the selected source distribution after installed acceptance.
Select the container daemon's storage before the build.
Retain the complete build log and resulting registry digest.
The recipe alone is not an accepted built image.

### Transfer an offline worker bundle

A private image registry is optional.
The deployment can select a digest-pinned public Python image and an offline worker bundle.
This route uses the same Python version and installation prefixes as the dependency image.

Select deployment revision `2.0.0`.
Set `worker_bundle` to the bundle specification's relative path inside the payload.
The specification has revision `1.0.0` and these fields:

| Field | Required operand |
| --- | --- |
| `base_image` | The deployment's exact public image reference, including its digest |
| `source_image_sha256` | The accepted dependency image's manifest digest, without the `sha256:` prefix |
| `source_lock`, `source_lock_sha256` | The retained original worker lock path and its exact digest |
| `requirements` | The complete version-pinned requirements file with hashes for the selected wheels |
| `wheels`, `uv_wheel` | The offline wheel directory and selected installer wheel |
| `system_package` | The selected Debian `libgomp1` package |
| `installed_versions` | The complete mapping of worker distribution names to exact versions |

Resolve each bundle path relative to its specification.
Retain the original locked export and any locally built wheel's source, builder and result digests.
Build source-only dependencies before deployment.
Use the resulting wheel hash in the offline requirements.
Keep the source archive and its original lock binding.

The prepared task authenticates the complete payload before it runs the generated bootstrap.
The bootstrap uses the upstream package installers with network access disabled.
It installs dependencies at `/opt/el/worker` and the installer at `/opt/el/tools`.
It registers CUDA library paths and verifies every installed dependency version.
The existing deployment then installs the accepted engine wheel and verifies the complete transferred payload again.

Exercise the bootstrap from the exact public base with networking disabled before deployment.
Retain its command, log, package census and source bindings.
This check establishes installation behavior and CPU imports.
Actual GPU allocation, libraries, derivatives and scientific results require their separate runtime checks.
Include public-image startup, file transfer, installation and storage in the selected spend policy.

### JAX CUDA12 TORAX worker profile

The R17 Gym–TORAX and R22 direct-TORAX experiments use the same authenticated
payload, shared execution plan, SkyPilot/Runpod placement, supervision and return
transport. Their code-owned backend declaration is
`empirical_lawhood.api.accelerated_deployment.JAX_TORAX_BACKEND`. Pass this
declaration to `RunpodDeploymentSelection.for_execution_plan` rather than a
periodic molecular backend. The resulting revision `6.0.0` binds
`numerical_backend: jax.torax.cuda12.float64`, the original plan digest, numerical
threads and one explicit accelerator. Author the scientific GPU operation before
deriving placement; an offline selection grants no native or spend authority.

The hosted profile ID is `jax-cuda12-torax-float64`. It requires a transferred or
retained offline worker bundle, selected through the same fields above. Build
its complete hash-pinned requirements and wheelhouse from the root `uv.lock`
with the `open-simulators` and `open-simulators-gpu` groups, for the supported
Linux x86_64/Python 3.11.14 worker. Do not mix the conflicting
`mast-torax-response` Torch group into this environment. The repository's
`execution/remote/worker_profiles.py` declares the required exact versions of
GymTORAX, TORAX, JAX/JAXLIB, the CUDA12 plugin/PJRT, NumPy/SciPy/xarray and the
CUDA12 NVIDIA library closure. It is checked against the existing lock by a
pure metadata conformance control.

For example, from the selected source checkout, export the existing locked
requirements without installing or running an engine:

```sh
uv export --frozen --no-default-groups --group open-simulators \
  --group open-simulators-gpu --no-emit-project --format requirements-txt \
  --output-file /absolute/selected/jax-worker.requirements.txt
```

Supply the full Linux wheel census, installer
wheel, selected `libgomp1` package, source lock and its digest, complete
`installed_versions` map, and authentic image provenance required by
`WorkerBundle`. The requirements export alone is not an installable wheelhouse.
No fabricated image digest or software package substitutes for these inputs.
The candidate implements their preparation and verification route; it does not
include a newly accepted native GPU image.

The JAX bootstrap preserves offline hash verification and the complete installed
distribution comparison. Its final import subprocess selects `JAX_PLATFORMS=cpu`
and imports the required Python modules without enumerating or exercising GPUs.
It omits the periodic CuTensor library-path and PySCF/OpenMM import assumptions.
The actual task receives `JAX_PLATFORMS=cuda`, `JAX_ENABLE_X64=true`,
`XLA_PYTHON_CLIENT_PREALLOCATE=false` and a selected persistent
`JAX_COMPILATION_CACHE_DIR`. The shared worker environment retains these settings
as part of its numerical selection. A native JAX entry then verifies actual
CUDA backend, float64 mode, exact required libraries and one visible admitted
GPU. Missing dependencies or a CPU fallback refuse the native operation.

The offline controls check bundle metadata and installer rendering. A GPU comparison requires installation in the selected image, native import and remote execution with the declared numerical settings. R17 and R22 retain a separate GPU qualification for each family. The periodic worker uses its own package and library requirements.

### Reuse a retained worker bundle

Use deployment revision `5.0.0` when the original bundle remains on the selected persistent volume.
Select an explicit `accelerator` and `retained_worker_bundle` reference.
Omit `worker_bundle` for this route.
Put the reference, original transfer manifest and exact bundle specification inside the new payload.
The reference has these fields:

| Field | Required operand |
| --- | --- |
| `version` | `1.0.0` |
| `remote_root` | Absolute path to the retained bundle on the selected volume |
| `original_manifest`, `original_manifest_sha256` | Payload-relative original transfer manifest and independently retained digest |
| `original_prefix` | The complete bundle subtree within that original manifest |
| `bundle_specification` | Payload-relative copy of the original `worker-bundle.json` bytes |

Preparation derives the complete bundle census from the authenticated original manifest.
It checks the copied specification and dependency-lock binding.
The task verifies every retained file before and after the existing offline bootstrap.
Changed, missing, extra or linked members refuse reuse.
The new payload transfers the small reference documents instead of the retained wheels.
It does not assume that a mounted volume contains the selected bytes.

### Restore a separate numerical environment

Use `deployment restore-environment` for the separate-prefix installation pattern used by the Reference PME correction.
Keep the original worker unchanged.
Select a fresh destination and exact original and replacement library digests.
Place the restoration recipe and all installation inputs in the sealed deployment payload.

The recipe has revision `1.0.0` and these fields:

| Field | Required operand |
| --- | --- |
| `base_environment`, `destination`, `installer` | Absolute original prefix, fresh prefix and selected offline `uv` executable |
| `maximum_bytes`, `maximum_entries`, `free_reserve_bytes` | Positive clone/census bounds and filesystem reserve |
| `engine_wheel` | Object with payload-relative `source` and original `sha256` |
| `replacements` | Objects with `source`, `sha256`, prefix-relative `destination` and `original_sha256` |
| `source_distributions` | Objects with `source`, `sha256`, fresh absolute `destination`, `maximum_bytes` and `maximum_entries` |

Use the exact accepted engine wheel, even when its version string matches the original installation.
The command reinstalls that wheel offline without dependency resolution.
It verifies the complete original environment before and after the copy and installation.
Source archives cannot contain links, special files, redirected names or packaged work plans.
Failed attempts remain at their selected destinations.

```text
empirical-lawhood deployment restore-environment --selection /absolute/payload/restore.json --payload /absolute/payload --manifest /absolute/control/payload-manifest.json --sha256 SELECT_RETAINED_MANIFEST_SHA256 --output-dir /absolute/output/environment-restoration
```

Generated tasks also supply the authenticated digest through `EL_DEPLOYMENT_PAYLOAD_SHA256`.
Only `restore-environment` accepts that variable in place of `--sha256`.
Select this command as the initial deployment operation when restoration must precede scientific stages.
The restored prefix still requires installed-source acceptance and the domain's actual engine admission.
Restoration performs no energy, gradient or trajectory evaluation.

## Derive hosted resources from the existing execution plan

For new handoffs, use the supported `RunpodDeploymentSelection.for_execution_plan`
constructor from `empirical_lawhood.api.accelerated_deployment`. Supply the
complete compiled plan returned by the existing investigation route. A current
resource envelope, when present, supplies its exact concurrency and aggregate
memory ceiling. Do not edit the plan to obtain a different host allocation.

```python
from empirical_lawhood.api.accelerated_deployment import (
    RunpodDeploymentSelection, prepare_accelerated_deployment,
)

# `execution_plan` and `resource_spec` are retained, derived records from the
# existing investigation. `placement` contains the already selected operation,
# source wheel, persistent volume, pinned image, accelerator and remote paths.
# It contains no resources, maximum_files or container_disk_gb entries.
selected = RunpodDeploymentSelection.for_execution_plan(
    execution_plan,
    resource_spec=resource_spec,
    payload_root=payload_directory,
    numerical_threads=1,  # Preserve the investigation's actual frozen setting.
    backend=selected_backend,  # The same code-owned declaration as its native engine.
    **placement,
)
report = prepare_accelerated_deployment(
    selected, payload_root=payload_directory, output_directory=prepared_directory,
)
```

The public constructor derives CPU, RAM, GPU count, source-transfer allowance,
output allowance and file census. The selected accelerator model, environment,
source and scientific operation remain explicit. The API exposes
`PERIODIC_CUDA_BACKEND` and `PERIODIC_REFERENCE_MM_BACKEND` as the existing
native adapter declarations. Select the one already bound by the investigation;
changing between them changes a numerical choice and requires a separate
scientific selection. An unsupported backend key is refused before preparation.
The current offline worker installer is specifically the periodic PySCF/OpenMM
CUDA environment. It requires both packages in its exact installed-version
declaration before rendering or setup. Historical bundle records remain
readable; another native environment requires an explicit integration. Its conservative host envelope
can contain every task reservation permitted by the resource envelope; without
an envelope, the complete task census supplies a conservative upper bound.
The existing scheduler retains sole ownership of execution and serializes
reservations of the single GPU. The operation still performs its ordinary
source, access, actual-host admission and recovery checks.

RAM includes a documented 512 MiB controller reserve above the derived worker
reservations. Container disk defaults to two copies of the observed payload
plus a 10 GiB installation reserve, rounded upward to GiB. This reserve is an
operational policy, not evidence about a native installer's expanded size.
Large native installations can select a larger `container_disk_gb`; actual
storage capacity still requires admission. `cpu_cores` and `memory_bytes`
overrides may enlarge the derived host envelope, without changing any task
budget. Spending limits and the selected current offer remain independent.

New derived selections serialize as revision `6.0.0`, with the exact compiled
plan digest, selected `numerical_backend` key and explicit `numerical_threads`.
All numerical thread environment
variables use that selected value, independently of host CPU allocation. The
constructor refuses a count larger than any task's CPU allocation. Methods
with their own frozen worker-environment selectors keep those selectors and
runtime comparisons; the deployment does not replace their numerical contracts.
Historical deployment revisions retain their original encoding and behavior.

CPU-only plans, methods requesting multiple GPUs, missing finite memory/source/
output allowances, and insufficient overrides return explicit `HOSTED_*`
capability reasons. Sizing does not supply missing numerical assumptions or
qualify a method for CUDA. The preparation report remains
`PREPARED_NOT_LAUNCHED`; it binds the sizing plan and grants no spending or
scientific execution authority. Offline sizing and transport tests are software
conformance evidence. Numerical equivalence on an actual hosted GPU remains a
separate acceptance run using the selected native environment.

## Resource and numerical boundaries

Actual GPU entry requires exactly one visible whole GPU and the declared dependencies.
Admission observes its UUID, driver, capability and available memory.
The existing scheduler admits host resources and preserves the worker selection.
Missing resources or a backend mismatch refuse before native entry.
The selected path has no automatic CPU fallback.

CUDA reserves virtual address space beyond host RAM use.
GPU workers therefore do not claim host-memory isolation through `RLIMIT_AS`.
Host checks use actual RSS, available memory and applicable cgroup limits.
Strict isolation refuses GPU work because the engine does not enforce whole-device memory isolation.
The CuPy pool allowance applies only to that pool.
It does not bound all OpenMM, driver or native-library allocations.

The GPU electronic path preserves direct integrals, total spin density, charged-background energy, grid response and complete embedding derivatives.
The direct point-charge potential and its derivatives use the pinned GPU integral kernels with no Gaussian charge exponent.
The adapter supplies the point-charge operand omitted by the upstream periodic wrapper and binds both QM and MM derivatives to the selected gradient instance.
Each SCF potential is rebuilt from the complete current density through the selected GPU method.
This avoids accumulation of screened J/K increments while preserving the selected model and convergence tolerances.
Actual convergence and complete-force accuracy still require independent assessment.
The periodic Ewald potential and gradient process every reciprocal vector in bounded blocks.
Block selection uses current device headroom and a scratch-space estimate of at most 2 GiB.
The original reciprocal mesh, charge population, Ewald exponent and double precision remain selected.
This bound does not cover other native allocations or establish complete force acceptance.
The existing coupling owns shifted charges, link-cap pullback and the complete MM remainder.
OpenMM selects `Precision=double` explicitly.
Its upstream nonbonded parameter storage remains float32 and is reported as `UPSTREAM_FLOAT32`.
That parameter rounding requires a separate assessment for actual molecular parameters.
Double kernel precision alone does not establish an unchanged molecular potential.

Each accelerated force return retains synchronized device time, host RSS, device-memory observations and explicit adapter transfer counts.
Transfer counts cover adapter boundaries, not undocumented transfers inside libraries.
Cost records retain complete returns and failures.
These observations establish no enzyme throughput or cost estimate.
Numerical convergence and existing unknown-completion protections remain required.
No experiment deadline, total SCF allowance or native-lease ceiling is added.

## Prepare one upstream task

Copy the [deployment selection](../../configs/accelerated-compute/selection.example.json).
Replace every placeholder with the actual selected region, datacenter, image digest and existing persistent volume.
For the offline bundle route, select the public base digest and the prepared bundle specification instead.
Select explicit host, device, input and output allowances.
The example selects one A100 80 GB as a benchmark candidate.
It supplies no current availability or price claim.
Revisions `1.0.0` and `2.0.0` retain their original A100 PCIe selection.
For an explicit variant, select revision `3.0.0` and set `accelerator` to `A100-80GB` or `A100-80GB-SXM`.
Revision `3.0.0` also permits the existing optional `worker_bundle` selection.
Revision `4.0.0` selects `H100`, `H100-SXM`, `H100-NVL`, `H200-SXM`, `B200`, `RTXPRO6000` or `RTXPRO6000-WK`.
These names follow the pinned upstream controller's CUDA GPU catalogue.
A100 selections retain revision `3.0.0`.
Each alternative still requires actual memory admission and the operation's numerical controls.
Compare native FP64 throughput when the selected operation uses double precision.
AI performance figures do not establish FP64 throughput or complete operation cost.
Verify the selected provider offer and actual GPU against that variant and the required memory.
Bind a current quote with its exact Decimal string and original digest before authorized deployment.

Place the accepted wheel, prepared operational input and complete operation inputs under one new payload directory.
Use the existing operation's returned paths and input contracts.
Keep payload, output and deployment metadata in disjoint directories.

```text
empirical-lawhood deployment prepare --selection /absolute/work/deployment.json --payload /absolute/work/payload --output-dir /absolute/work/prepared-deployment
```

The command writes `task.yaml`, `selection.json`, `SHA256SUMS`, `payload-manifest.json`, `payload.tar` and `preparation.json`.
It records `PREPARED_NOT_LAUNCHED` and the remaining entry requirements.
The task keeps the existing controller and workers on one machine.
SkyPilot supplies provisioning and file transfer; the existing engine supplies execution, receipts and recovery.
The task verifies transferred input bytes before execution.
The complete archive includes payload members excluded by Git or SkyPilot ignore files.
Select local and container capacity for that archive as well as the persistent payload.
SkyPilot transfers individual files to temporary storage before setup authenticates the archive and extracts it onto the selected volume.
The persistent payload directory must be an ordinary directory, because SkyPilot can place absolute file mounts behind links into container storage.
Setup authenticates an existing payload without overwriting it.
Preparation grants no authority to spend, acquire scientific outcomes or repeat an unknown attempt.

Before any launch, verify all of the following through the selected upstream controller:

- Current provider credentials and the authorized spend selection.
- The built image digest and its installed-source acceptance.
- The actual datacenter, host allocation, GPU identity and available memory.
- The existing volume ID, volume name, mount and capacity.
- The complete prepared task and authenticated input census.
- The operation's original source, access, execution and scientific prerequisites.

Runpod launches remain outside local preparation acceptance.
Once separately authorized, submit the prepared task with the pinned upstream `sky launch` command.
Use upstream status and the original engine records to resolve interrupted contact.
Do not repeat a launch or native operation merely because a response was lost.

## Supervise an authorized monetary allocation

Use the shared `deployment observe-budget` and `deployment watch-budget` commands for later GPU stages.
Reuse the existing pinned controller and original allocation records.
Do not copy a prior stage's budget script and substitute new resource names.
The [deployment architecture](../development/architecture.md#remote-deployment-services) separates accounting, provider observations and lifecycle actions.

Select the actual allocation only after its original Pod ID and cluster generation are known.
Record request-start times that include setup, idle time and unsuccessful attempts.
Select the retained volume's accounting start explicitly.
Keep storage charges outside that interval in their original accounting record.
The selection grants no spending or scientific authority.

The supervision document has revision `1.0.0` and these fields:

| Field | Required operand |
| --- | --- |
| `allocation` | Revision `1.0.0` allocation object described below |
| `authorization_path`, `authorization_sha256` | Absolute original owner-authorization record and its retained digest |
| `controller_python` | Absolute interpreter in the selected pinned controller environment |
| `controller_source_paths` | Absolute source roots for the accepted engine and any separately retained controller correction |
| `controller_config` | Absolute selected SkyPilot configuration |

The allocation binds `deployment_id`, `cluster_name`, `cluster_hash`, `pod_id`, `pod_name`, `volume_id`, `volume_mount` and `zone`.
Use the actual SkyPilot `cluster_hash` and original provider Pod name.
SkyPilot's handle reports node IDs such as `<pod-id>-0`; these are not provider Pod IDs.
The lifecycle guard checks the original provider census, single head node and cluster generation together.
It also binds `compute_started_utc`, `volume_accounting_started_utc` and `budget`.
Times require explicit UTC offsets.
The budget retains these exact nonnegative Decimal strings:

- `total_usd`, `return_reserve_usd`, `retirement_margin_usd` and `previous_attempts_usd`.
- `compute_hourly_usd`, `container_hourly_upper_usd` and `volume_hourly_upper_usd`.
- `accounting_floor_usd`, when an earlier monitoring lifetime supplies a retained lower bound. Its default is `0`.

Select positive `poll_seconds`, `request_timeout_seconds` and `action_timeout_seconds` for operational supervision.
Their defaults are 30, 20 and 180 seconds.
They are not native execution or scientific iteration deadlines.
The retirement margin must cover the selected observation and action latency estimate.
Provider failure can still prevent timely retirement.
Do not describe the monetary policy as an absolute billing guarantee.

The owner record must bind the same deployment, zone, retained volume, cap, return reserve, retirement margin and maximum compute rate.
Its fields are `status: OWNER_AUTHORIZED`, `deployment_id`, `zone`, `keep_volume_id`, `budget_total_usd`, `return_reserve_usd`, `retirement_margin_usd` and `maximum_compute_hourly_usd`.
Its `financial_actions` must contain `CANCEL_SELECTED_JOBS` followed by `RETIRE_SELECTED_COMPUTE_KEEP_VOLUME`.
Retain the actual owner instruction with that record.
Matching JSON fields alone do not establish that authorization occurred.

Supply the provider credential through `RUNPOD_API_KEY` in the selected process environment.
Do not put credentials in arguments or selection documents.
Keep the output directory private because original provider responses can contain operational environment values.

```text
empirical-lawhood deployment observe-budget --selection /absolute/work/supervision.json --output-dir /absolute/work/cost-observation
empirical-lawhood deployment watch-budget --selection /absolute/work/supervision.json --output-dir /absolute/work/budget-supervision
```

The first command uses bounded GET requests only.
The second command requires the original owner authorization before its monitoring lifetime begins.
Start the monitor after allocation and before scientific dispatch.
Retain its event stream, current report, original provider responses and action logs.
Use fresh output directories for observations and monitoring lifetimes.

Accounting uses the larger provider or elapsed amount for each resource separately, then adds earlier attempts.
It covers each intersected storage billing hour and cannot decrease within one monitoring lifetime.
At `total_usd - return_reserve_usd`, the monitor cancels selected jobs once and continues through evidence return.
At `total_usd - retirement_margin_usd`, it requests compute retirement through the pinned SkyPilot owner.
An observation failure also requests retirement of the original selected allocation.
Before each action, the controller checks the cluster generation, provider Pod ID and Runpod backend.
No action deletes the network volume.

A cancellation response does not establish native completion.
Retain interrupted or uncertain native contacts through the existing domain recovery procedure.
Do not replay them automatically.
The monitor reports retirement only after the original Pod is absent and the selected volume remains in its datacenter.
Failed commands or unconfirmed postconditions produce `RETIREMENT_UNRESOLVED` and a nonzero exit.
Resolve that original allocation immediately through the retained provider and controller records.

Evidence-storage failure also ends ordinary monitoring and requests authorized compute retirement.
This includes failure to create the initial destination, an observation directory or the current event record.
The controller action uses the original selection and independently checks its exact bytes and current authorization.
It captures at most one MiB per output channel in memory before it publishes the action log.
A failed log write does not prevent the action. The event reports `action_log: UNAVAILABLE` when that log cannot be retained.
An unavailable cancellation log causes retirement without another cancellation attempt.
These operational process limits do not change scientific task limits.

Retain the original selection, authorization and controller installation separately from disposable monitoring outputs.
They must remain readable and unchanged for an emergency action.
Missing authority or changed allocation bindings still refuse the action.
If the normal event destination fails, the monitor attempts to emit the unresolved outcome through its event stream.
A broken event consumer cannot prevent the emergency action or replace its nonzero unresolved exit.
Missing provider confirmation or failed final evidence publication leaves retirement unresolved, even after a successful controller command.
Inspect the original allocation and retained volume through the documented controller/provider route before reporting financial closure.

Do not edit a running monitor's selection or authorization.
For a budget amendment, retain the original accounting intervals and separately covered earlier attempts.
Set `accounting_floor_usd` to the prior lifetime's latest accounted amount.
This maximum preserves earlier accounting without double counting its overlapping interval.
Retain both lifetimes and complete an explicit handover before closing the earlier monitor.
After normal compute retirement, let the active monitor confirm the provider postconditions.
Report continuing volume charges separately from retired compute.

## Return original evidence

Use the operation's supported result or export procedure before selecting a closed transfer.
Retain original receipts, failures, incomplete attempts and complete output denominators.
Seal the selected remote export to a manifest outside that export:

```text
empirical-lawhood deployment seal-files --root /absolute/remote/export --manifest /absolute/remote/return-manifest.json --maximum-bytes 10737418240 --maximum-files 10000
```

Retain its returned manifest digest independently of the copied files.
Transfer the complete export and manifest through the selected upstream transport.
Use a fresh local destination and verify every member:

```text
empirical-lawhood deployment verify-files --root /absolute/local/export --manifest /absolute/local/return-manifest.json --sha256 SELECT_RETAINED_MANIFEST_SHA256
```

The command refuses missing, extra, linked or changed files.
`BYTE_VERIFIED` establishes transport integrity only.
Use the original domain reader for completion and scientific assessment.
The transfer manifest cannot replace primary receipts, access checks or original-result reconstruction.

For a closed output tree containing links, use the shared original-archive carrier first:

```text
empirical-lawhood deployment archive-originals --root /absolute/remote/originals --output-dir /absolute/remote/return-package --maximum-bytes 21474836480 --maximum-entries 100000
empirical-lawhood deployment seal-files --root /absolute/remote/return-package --manifest /absolute/remote/return-manifest.json --maximum-bytes 23200000000 --maximum-files 2
```

Select the byte and entry allowances from actual capacity before use.
Include the archive header allowance of `maximum_entries * 16384 + 10240` bytes, plus the census, in transport capacity.
The example numbers are selections, not measured storage requirements.
The archive retains regular files, hardlink relationships, symlink targets and empty directories.
It does not follow symlinks or infer that native writers have stopped.
Establish closure through the original operation before this command.
Changed originals refuse publication and retain the failed archive attempt.

Transfer the complete two-file package and independently retained manifest through the existing transport.
Then authenticate the return and all original members without extraction:

```text
empirical-lawhood deployment verify-originals --package /absolute/local/return-package --manifest /absolute/local/return-manifest.json --sha256 SELECT_RETAINED_MANIFEST_SHA256
```

`COMPLETE_ORIGINAL_ARCHIVE_MEMBER_RETURN_VERIFIED` establishes complete member transport for that selected tree.
Use original receipts and the supported domain reader for scientific completion and interpretation.
Earlier independently verified returns remain valid separate packages.
Reuse them through their original manifests instead of relabeling or altering their originals.

## Acceptance and remaining steps

The [testing guide](../development/testing.md#accelerated-compute-controls) separates portable checks, local CUDA controls and remote quantum controls.
Local OpenMM controls establish a small numerical comparison, including parameter-rounding disclosure.
They establish no complete enzyme force or scientific rate.
On the selected supported GPU, run the cold/seeded RKS and UKS controls first.
Retain charged-cell, periodic-invariance and complete QM/MM finite-difference results.
Then assess actual molecular parameter precision and the complete enzyme force/cost observation under its scientific procedure.

## References and research

[SkyPilot pinned source](https://github.com/skypilot-org/skypilot/tree/796c5bcc8041a9dcf92c1182fabbafd9a5ab9ed2) owns provisioning and the selected Runpod REST v2 implementation.
[GPU4PySCF 1.8.1](https://github.com/pyscf/gpu4pyscf/tree/v1.8.1) supplies the selected direct electronic implementation.
[OpenMM 8.3.1](https://github.com/openmm/openmm/tree/8.3.1) owns CUDA precision and nonbonded parameter storage.
Its [PME allocation](https://github.com/openmm/openmm/blob/8.3.1/platforms/common/src/CommonCalcNonbondedForce.cpp)
and [CUDA buffer clearing](https://github.com/openmm/openmm/blob/8.3.1/platforms/cuda/src/CudaContext.cpp) define the checked buffer-size limit.
The [Reference PME implementation](https://github.com/openmm/openmm/blob/8.3.1/platforms/reference/src/SimTKReference/ReferencePME.cpp)
defines its separate signed grid-index limit.
The project-owned wrapper adds the declared charged-background term and retains its independent controls.
