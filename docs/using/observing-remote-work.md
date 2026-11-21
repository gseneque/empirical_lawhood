# Observe remote work and return original evidence

SPDX-License-Identifier: CC-BY-4.0

Use the research explorer to inspect an externally started run without keeping
its browser open. The collector reads original execution/native metadata and
existing supervision records. A sealed snapshot is transferred to the local
operator and explicitly imported. Browser refresh reads that local snapshot.

The [accelerated-compute procedure](accelerated-compute.md) owns deployment,
allocation, budget supervision and retirement. This observer makes no provider
call, starts no scientific task and performs no financial lifecycle action.
Closing either the browser or collector leaves the supervisor independent.

## Select the work before dispatch

Follow the scientific guide to author the wave and obtain its packet, run,
decision and intent identities. Use [collection registration](research-workbench.md#register-an-investigation)
before a result exists. Keep one selection per wave, including stopped, declined
and returned waves, under the same operational `investigation_id`.

Each optional stage has `id`, `label`, positive integer `revision`, `state`,
`depends_on`, a pinned editorial `source`, and original `decision` and `intent`
identities or explicit nulls. States are `PLANNED`, `SELECTED`, `DECLINED`,
`AUTHORED`, `RETURNED` or `UNAVAILABLE`. A changed stage needs a later revision.
The recorded dependencies determine order; numbering does not imply an execution
or scientific supply edge. An absent or declined stage remains visible.

The selection's `deployment` contains:

| Field | Original selection |
|---|---|
| `deployment_id`, `run_id`, `packet_sha256` | Actual deployment and authored wave bindings. |
| `allocation`, `job_card` | `{path,sha256}` pins to the selected operational documents. These are not scientific identities. |
| `controller_source_sha256`, `worker_source_sha256` | Actual source selections; the collector checks the worker against original execution provenance. |
| `observation_path`, `return_path` | Explicit local operational files below the context's guarded `observation_root`. |

The job card contains an `observation` object with `cadence_seconds`,
`stale_after_seconds`, both source digests and `selected_gpu`. Select 30 seconds
and 120 seconds as the normal observation cadence and stale threshold. The
contract permits 2–3600 seconds and requires staleness of at least two cadences.
Current GPU utilization, memory, process and phase remain unavailable unless an
accepted original observation supplies them. A selected GPU name is not telemetry.

Use actual current allocation, job-card and supervision records. Historical
provider quotes and old observations cannot supply the current selection.

## Start the separate collector

Create an explicit remote context with its installed interpreter, original
scientific profile, operational profile, input root and observation root.
The operational profile must permit writes at that remote destination.
Select the matching installed source for `project_root`, or omit it for a
read-only source selection. The original scientific reader still checks custody.

Save an operational selection with schema
`empirical-lawhood/operational/observation-selection`, version `1.0.0` and these
top-level fields:

| Field | Meaning |
|---|---|
| `binding` | The deployment fields above, `investigation_id`, `selection_id`, `allocation_sha256` and `job_card_sha256`. `api.operational_observation.registered_binding(entry)` derives this from the registered entry. |
| `directory` | Original remote authoring directory returned by the workflow. |
| `allocation`, `job_card` | Pins to the same documents in remote custody. |
| `supervisors` | Up to sixteen ordered `{directory,selection_sha256}` records. Each later supervisor must retain its predecessor's accounting floor. |
| `cadence_seconds`, `stale_after_seconds` | Exactly the job card's selected values. |
| `task_offset`, `native_offset`, `row_limit` | Explicit metadata window; start at 0 with at most 200 rows. |
| `domain_panel` | Null when unavailable, otherwise `{panel_id,panel_version,observation_version}` selecting an installed domain callback. |

Start with the selected interpreter, not a newly synchronized environment:

```sh
/absolute/remote-environment/bin/python -m empirical_lawhood.workbench.observer \
  --context /absolute/remote-inputs/context.json \
  --selection /absolute/remote-inputs/observation-selection.json \
  --output-dir /absolute/remote-observations/collector-01 \
  --watch
```

The destination must be new and lie below the selected observation root.
Without `--watch`, the command publishes one observation. It prints the returned
directory, manifest digest and snapshot digest, and updates its own
`latest-export.json`. Each complete publication has a collector ID, monotonic
sequence, original source time and previous snapshot digest. Each snapshot is
bounded to one MiB; it contains no cloud credential or raw provider response.

Restart in a new collector directory, passing
`--previous-snapshot-sha256` with the last accepted snapshot digest. Never reset
the old collector's sequence in place. The local import must explicitly accept
that same restart binding. Retired collector IDs cannot re-enter.

## Transfer and open an observation

Transfer the complete returned snapshot directory with the existing
[sealed transfer procedure](accelerated-compute.md). Preserve its contents and
retain the expected manifest digest through a separately selected handoff.
Use an incoming directory below the local context's selected `input_root`.

Issue the terminal/API operation `observation.import` with `selection_id`,
absolute `directory` and `expected_manifest_sha256`. Subsequent imports also
select `expected_current_sha256` from `observation.read`; collector replacement
adds `restart_from_snapshot_sha256`. Import checks complete bytes, original
bindings, allocation body, sequence and collector history before atomic replacement.
A partial, oversized, substituted or regressed transfer leaves the preceding
accepted observation unchanged. This operation is unavailable to browser refresh.

Choose **Observe registered work** in Results. It needs no browser-created
invocation or completed scientific result. The view retains separate run, task,
attempt, native contact and collector identities. Raw call return, output
publication, completion receipt, complete force return and independent assessment
are separate states. Advisory minimizer output is not a checkpoint.

The browser permits one request at a time and refreshes no faster than the
source cadence or ten seconds, whichever is longer. Inactive views stop and
clear their observations. Reopening requires a fresh permitted read. Late
responses from another context are discarded. Original scientific, inquiry and
cost reconstruction readers are never polled for remote progress.

Source and transfer times are displayed separately. Quiet or stale observations
do not imply completion. Unknown native contact remains unknown. A selected
domain reader that is missing or incompatible returns an explicit unavailable
state; the UI does not fill it from a plan or earlier molecular run.

## Spending and independent lifetimes

The panel displays the original allocation, actual billed observations,
conservative accounted amount, reserve, liabilities and remaining amount.
Negative remaining amounts remain negative. Accounting estimates are not invoices;
missing billing and unsettled liabilities remain unknown. The monetary observation
has its own age and accounting interval.

Scientific completion does not close finance or evidence return. Financial stop,
cancellation, unresolved retirement and confirmed compute absence are distinct.
A retained volume can continue charging after compute retirement. Only the
original supervisor and confirmed lifecycle observations establish these states.
The observer neither recomputes budget policy nor selects a new financial action.

## Return the original result

Return scientific packages through their owning custody procedure. Snapshot
transfer alone supplies no original result or assessment. Append the returned
local reader to the same registered selection, preserving the remote locator,
decision, intent and deployment. Use the current retained-access profile when
the original study was relocated.

`observation.record-return` accepts `selection_id`, `text` containing one event,
and the current `expected_return_sha256` after the first event. Its six stages
are `REMOTE_PUBLICATION`, `SEALED_EXPORT`, `TRANSFER`, `BYTE_VERIFICATION`,
`INDEPENDENT_READING` and `CONTRIBUTION`.

| Action inside `text` | Meaning |
|---|---|
| `{stage,action:"STARTED"\|"FAILED"\|"UNAVAILABLE"\|"DECLINED",source?,close?}` | Explicit operator observation, optionally pinned to an input. It supplies no scientific or transfer verdict. `close` must be an explicit boolean. |
| `{stage,action:"VERIFY_FILES",root,manifest,manifest_sha256}` | Existing complete transfer verification for one of the first four stages, beneath the selected input root. |
| `{stage:"INDEPENDENT_READING",action:"READ_ORIGINAL",reader_index}` | Fresh owning read of the selected registered original, bound to the deployment's authored wave. |
| `{stage:"CONTRIBUTION",action:"READ_CONTRIBUTION",reader_index}` | Fresh original contribution inspection. It does not grant consumer admission or scientific promotion. |

The journal retains immutable event receipts and a guarded current projection.
An independent read refusal leaves the corresponding stage unresolved. The
**Open returned original** control opens an explicitly registered local reader.
Its scientific findings, contribution limits and exact records remain available
after the remote job has ended.

## Domain extensions and verification

The [presentation extension](../development/workbench-presentations.md) defines
the six-question and operational coverage contracts.
Rubisco's [preparation-response extension](../../programmes/biology/photosynthesis/workflows/rubisco-response/preparation-response-v1.md#implementation-and-retained-acceptance)
implements safe-checkpoint reading, independent Q1–Q6 assessment, destination assessment and bounded domain observation.
Select panel `rubisco.preparation-response` at revision `1.0.0` for its authored or original supplier wave.
Its callback binds the original packet, run and worker source.
It preserves genotype/checkpoint positions, direction/scale/side effects, allowances and unknown or incomplete returns.
Complete-force counts use published independent readouts; live seals and completion receipts alone do not establish that count.
For a continued prefix, the allowance is the original purchase and the count includes its retained completed input returns.
Those inherited returns are not new work in the continuation wave. Unknown new contact leaves the total unavailable.
Response-point counts cover only the selected wave. Read the displayed count scope before comparing stages.

Installed component evidence covers prefix observations and twenty original software-control response returns at their recorded source revisions.
The actual authored molecular prefix remains unentered in the retained evidence, with all six questions unanswered.
The original conditional-root panel retains its separate contract and unavailable supplier bindings.
Those bindings do not mean that the preparation-response extension is absent.

Use the [maintained browser checks](../development/testing.md#research-explorer-browser-checks)
with explicit external outputs.
Complete combined installed acceptance remains pending and must precede rental.
Actual deployment, observation/import, supervision and return acceptance must precede molecular dispatch.
UI acceptance, domain component controls and molecular findings retain separate evidence scopes.
