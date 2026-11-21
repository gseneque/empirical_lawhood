# Follow a workflow's progress

SPDX-License-Identifier: CC-BY-4.0

EL reports operational progress to **stderr by default**, including noninteractive
terminals. Scientific JSON and other command results remain on stdout. The same
reporter supplies an optional atomic JSON snapshot for another terminal or a UI.
The [first investigation](../v1.0/define-investigation.md) also creates
`scratch/progress.json` in its explicitly selected workspace.

## Select the output

Put shared progress options **before the command group**:

```sh
uv run --no-sync empirical-lawhood \
  --progress-file /absolute/operational/run-progress.json \
  --project-root /absolute/selected-source \
  --operator-profile /absolute/operator-storage.json \
  campaign experiment-run --authoring-dir /absolute/authored-investigation

uv run --no-sync empirical-lawhood progress \
  --file /absolute/operational/run-progress.json
uv run --no-sync empirical-lawhood progress \
  --file /absolute/operational/run-progress.json --json
```

The selected file must be new, its parent must exist, and it must be outside
scientific inputs, packages and selected output roots. Repeated input options
are all checked before a progress file is created. No progress file is created
when the option is omitted.

Use `--no-progress` to suppress progress messages on stderr.
Error diagnostics remain on stderr. Select this option to parse a JSON error envelope.
A separately selected `--progress-file` still updates.

The inspector itself does not start a second monitor.
A shell can repeat the inspector with `watch`.

Command startup reports `cli.import` before loading the command tree. That early
observation uses stderr only: input and output selections must be validated
before an operational file is claimed. Help and completion do not start a
heartbeat. Python applications select a reporter explicitly, as shown below.

## Read the quantities correctly

A line identifies the phase, completed work, declared total if known, remaining
work, elapsed time, time in the phase, and time since a work report. Execution
also reports the complete task census separately from the active inner step.
Counts describe completed work in their stated unit; they are not estimates of
remaining wall time.

| Quantity | Interpretation |
| --- | --- |
| `123/400 bytes`, `remaining=277` | A known byte census; 123 bytes have actually been processed |
| `7/? iterations`, `remaining=unknown` | Seven iterations have been observed; the convergence time and required total are unknown |
| `workflow=5/12 tasks` | Five tasks have reached a terminal success or failure; unattempted blocked tasks remain incomplete |
| `workflow=3/5 lifecycle-steps` | The starter has returned from three of its five declared prepare/author/run/read/recover operations |
| `controller alive; work advancement unknown` | The monitoring owner has run its heartbeat; this does not prove the native engine has advanced |
| `no-report=...s` | Time since an actual counter/phase report, not time since the latest heartbeat |
| `RETURNED` | The operation returned; inspect its actual report for blocked work and scientific disposition |
| `FAILED` or `INTERRUPTED` | The invocation raised or was interrupted; partial counters are preserved |

The current phase and overall workflow have different denominators. A completed
byte write does not make an experiment scientifically complete. Recovered
successes count as completed tasks; they do not become new experiments. An
iteration ceiling, monetary allowance or memory allocation is never displayed
as the amount of scientific work required for convergence.

Heartbeat is normally every two seconds. Counter and phase output is coalesced
to at most one ordinary write per second. Invocation entry, its first actual phase
and terminal publication are immediate. Rapid nested phase changes are coalesced;
each phase is not promised a separate terminal line. Nested application operations
share their outer CLI owner and its
single heartbeat. Atomic snapshots cannot be read half-written. File telemetry
failure emits one warning and disables that sink while scientific work continues.
A killed process can leave `RUNNING`; a UI must compare `updated_at_utc` with its
own clock and label stale observations. Receipt readers own completion and recovery.

## Where progress comes from

| Workflow part | Available observations |
| --- | --- |
| Prepare and author | Public operation boundaries, existing input/validation census counters, source and artifact publication byte counters |
| Execute and recover | Complete task census, authenticated recovered successes, terminal failures, selected task identity when reported, inner native events over the existing ordered worker pipe |
| Read and assess | Owning verification and input-read counters; returned assessment remains a separate scientific product |
| Export and transfer | Generic file census, archive member/byte operations and publication; no extra whole-file hash pass is introduced for display |
| Remote preparation and evidence/log return | The same generic transfer machinery and JSON schema; local remote-supervision state is an operational observation, not a GPU advance counter |
| Rubisco construction and relaxation | Named native calls, OpenMM minimization iteration callbacks, accepted geometry iterations, complete reference returns and PySCF SCF iteration callbacks |
| Rubisco selected NVE integration | Completed integration intervals against the requested step count, without splitting or reordering native integration calls |

Worker threads explicitly inherit only the thread-safe telemetry owner. Scientific
verification contexts are not copied. Forked children cannot use an inherited
reporter or its locks; selected native workers send advisory messages through
the already authenticated, ordered request/acknowledgement pipe. These messages
carry no contact, result, replay or scientific acceptance authority. Output byte
messages and progress observations can interleave without a second pipe or thread.

The [capacity and transfer guide](capacity-and-transfer.md) covers generic input,
evidence and log packaging with the same progress stream.

## Native-library boundaries

The following distinctions are deliberate. They identify what is observable at
existing interfaces without additional force, energy, state or gradient evaluations.

| Native boundary | Actual progress | What remains unknown |
| --- | --- | --- |
| OpenMM `LocalEnergyMinimizer` | Passive official `MinimizationReporter` callbacks; number of callbacks and native iteration index | Required convergence iterations and time. The native index can restart when constraint penalties change. The callback preserves the original stop decision. |
| EL geometry minimizer | Existing accepted-state/iteration callbacks and completed reference evaluations | Number of future accepted steps or trial evaluations; maximum iterations is not a convergence denominator |
| PySCF SCF | Existing per-cycle callback, with cumulative chunk cycles | Remaining cycles until the selected energy/orbital/state conditions are met |
| PySCF individual integral, matrix contraction and derivative kernels | Entered named phase; any existing returned inner observations; parent heartbeat during opaque work | Internal kernel fraction between exposed callbacks. EL does not request another numerical result merely to display progress. |
| OpenMM `Integrator.step(n)` | Requested steps and completed existing call/interval | Intermediate advance inside that individual native call; calls are not split for telemetry |
| ONNX, SafeTensors and third-party schema/format parsers | Named publication-validation phase and returned result; existing EL canonical scanner reports bytes at its buffer boundaries | Internal fraction within a third-party parser call when its API exposes no callback; telemetry adds no extra read or validation pass |
| Amber subprocesses and PDBFixer/native constructors | Named call entry/return, existing retained logs, controller heartbeat | Internal fraction when the selected API provides no progress hook |
| Remote provider API, transfer subprocess or hosted engine without emitted events | Current local supervision/transfer phase and returned events/bytes | Remote engine advance between delivered observations; a live local monitor cannot establish remote liveness |

OpenMM documents the callback and constraint-related iteration resets in its
[MinimizationReporter reference](https://docs.openmm.org/latest/api-python/generated/openmm.openmm.MinimizationReporter.html)
and [reporting example](https://openmm.github.io/openmm-cookbook/latest/notebooks/cookbook/report_minimization.html).
The [minimizer API](https://docs.openmm.org/latest/api-python/generated/openmm.openmm.LocalEnergyMinimizer.html)
separates its stopping settings from the reporter. The passive callbacks add no
coordinate/gradient copying or new state query in EL. Real native callback
marshalling cost still requires measurement in the selected engine environment;
focused callback tests do not qualify native performance or scientific convergence.

## Follow progress in the workbench

Open **Tools → Invocations** in the [research workbench](research-workbench.md).
Select the original context and invocation handle.
The cards show the reported phase, exact counts, failed counts and separate workflow census.
Unknown totals have no percentage.
The recent-step list preserves failed and interrupted steps within its bounded window.
Its summary states how many earlier steps were omitted.

Active cards refresh every two seconds.
Reports older than ten seconds show a stale label, including when a state request stalls.
Repeated copies of one report do not reset its age.
The browser retains the last bound report during transient errors and incomplete publication.
An older sequence cannot replace a newer report.

A hidden tab or context change disposes its state requests and timers.
Returning to the view obtains current state.
A retained invocation return stops automatic polling.
It does not establish scientific success.
Use **Exact invocation and progress values** for the complete observation.
Reopen original results for scientific findings.

## Reuse from Python and other UI readers

```python
import sys
from pathlib import Path
from empirical_lawhood.execution.progress import progress_step, report_workflow_progress
from empirical_lawhood.storage.progress import OperationalProgressReporter, read_progress

with OperationalProgressReporter(Path('/absolute/operational/status.json'),
                                 'selected analysis', stream=sys.stderr):
    report_workflow_progress(done=0, total=1, unit='operations')
    with progress_step('analysis.inputs', total=len(inputs), unit='files') as step:
        for item in inputs:
            consume_original(item)
            step.advance()  # only after the actual work has completed
    report_workflow_progress(done=1, total=1, unit='operations')

snapshot = read_progress(Path('/absolute/operational/status.json'))
```

Call `progress_step(..., total=None)` for genuinely unknown work; never supply a
policy ceiling as a denominator. A nested step restores its parent's original
counter and start time. `advance` never runs automatically on successful exit.
`report_progress` is an advisory port whose sink errors cannot stop the scientific
operation. Pure scientific components accept ordinary callbacks; their adapter
or application owner projects those observations into the progress port.

The strict current schema is `empirical-lawhood/operational-progress.v2`.
Its scalar fields are `operation`, `phase`, `status`, `pid`, `sequence`,
`updated_at_utc`, `done`, `total`, `failed`, `percent`, `unit`, `detail`, `task_id`,
`elapsed_seconds`, `phase_elapsed_seconds`, `activity_age_seconds`, `heartbeat`,
`workflow_done`, `workflow_total`, `workflow_failed`, `workflow_percent` and
`workflow_unit`. Unknown values are JSON `null`; percentages exist only for
known nonzero totals. `task_id` is advisory and may be null; it never supplies
an invocation, attempt or scientific identity that was not actually reported.

`completed_steps` retains the most recent 64 terminal summaries with `phase`,
`done`, `total`, `unit`, `elapsed_seconds` and `status`.
`completed_steps_total` and `completed_steps_omitted` expose truncation explicitly.
This bounds memory, file size and UI read cost independently of experiment length.
It is an operational history window, not a complete scientific event journal.
The snapshot's 64 KiB parser bound protects only this telemetry format; it does
not limit scientific input, output or execution. Application invocations attach
the same snapshot to their existing handle and sequence binding. UI readers use
this strict reader or the existing invocation-progress API, without opening
scientific artifacts or revalidating entire results. There is no v1 reader or
reporter-name compatibility alias in the candidate.
