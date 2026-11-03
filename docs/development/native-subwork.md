# Durable native subwork

SPDX-License-Identifier: CC-BY-4.0

This guide describes progress inside an already authorized native task.
It supports adapter authors and operators who recover retained work.
Use the original roster, contact and receipts to determine the next permitted action.

The scheduler, native contact owner, artifact plane and task receipts retain their existing authority.
Subwork records provide no issue, execution, reveal, qualification or retry permission.

## Prepare available inputs before parent contact

The [prepared invocation helper](../../src/empirical_lawhood/infrastructure/prepared_native_invocation.py)
publishes explicitly selected canonical controls through the existing guarded
artifact plane. `NativeInputPublication` retains the scientific record ID,
record bytes, optional transport alias and exact lineage parents. Already
published operands enter as explicit `(ObjectIdentity, ArtifactManifest)` pairs.
The selected plane authenticates their original storage ownership.

The returned `PreparedNativeInvocation` joins each full scientific identity,
authenticated materialization and worker input port. Its input census, bindings
and ports are derived from those joined operands. Its `definition` method derives
native code/lock bindings and the complete input census from the selected
producing provenance. Historical and prospective revisions can retain the same
scientific record ID while using distinct authenticated transport aliases;
selection checks the full identity, including revision and fingerprint.
The prepared invocation implements the existing input-port factory and exposes
`verified_inputs` for the ordinary resolver. Passing it as the scheduler's
`input_port_factory` supplies the same prepared ports. A changed census,
binding or scan budget, or a consumed/closed port, refuses instead of reopening
another input set.

Call `validate_prepared_native_invocation` for every available selected definition
before ordinary parent contact. It invokes the same read-only bounded byte/source
validator as native `begin`. Missing direct inputs, substituted record revisions,
source/lock mismatches and access changes retain a complete metadata mismatch
census. Conditional operands receive that same validation after their parent
publishes them and before their own contact. The existing progress pipe carries
the complete typed input mismatch census separately from its short error message.

Preparation creates no parent contact, native entry, roster or authority. The
scheduler still admits the ordinary task, and `begin` still checks its actual
live creator and frozen selected roster. Compose a standard `TaskContext` from
the prepared `input_bindings` and `input_ports`; no manifest channel or second
worker system is needed. Close the prepared ports after their selected use.

## Freeze the selected work before entry

An adapter implementing `execute_with_native_subwork(context, native_subwork,
progress=None)` receives a coordinator-backed runtime port. `TaskContext`
still contains no stores, database sessions or filesystem paths.
`native_subwork.parent_contact` gives the actual entered task's immutable
contact, including its execution plan, task, attempt, implementation commit
and complete input materialization and dependency receipt census.

Construct the complete selected `NativeSubworkDefinition` tuple in stable
subwork ID order. Each definition retains the operation, configuration,
scientific sources, producing code and dependency lock, exact input
materializations, streams, and complete output contracts. Include the
authenticated `NumericalProducingProvenance` record as a source and parent
input. Its observed code, lock and Git head must match the definition and
actual task. Canonical configuration, source and stream record revisions are
checked against the authenticated bytes without loading scientific JSON
into memory.

An input's access boundary can differ from the native task's output boundary.
For example, an outcome-blind origin and committed prediction can feed a task
that produces sealed native responses. The ordinary executor qualifies each
input first; the progress coordinator retains its exact manifest and worker
binding. Native input validation compares known inputs to those complete frozen
parent manifests, including their original access and visibility. It requires
the complete original parent census and rejects changed or duplicate boundaries.
Explicit new conditional operands retain the parent output scope. A missing
frozen boundary does not grant another access role. Live-parent, selected-roster,
source, stream and execution-authority checks still precede native contact.

Freeze the one initial `selected.native-subwork` roster with
`native_subwork.freeze_roster(roster, definitions=definitions)`. The roster
pins the complete identity census and retains every full definition before
entry, including units that remain unentered. An incomplete or substituted
definition tuple refuses. Repeating a selection cannot enlarge its immutable
denominator.
Every frozen member keeps its full definition even before entry. A missing
definition, including an empty or deleted unit directory, refuses inspection,
recovery and entry. Repeating the roster freeze cannot recreate lost custody.

For each selected call, first inspect or recover its existing progress.
A recovered exact completion supplies its retained evidence. For new work,
use `begin(definition)`, then acknowledge `contact(entry)` before invoking
the native effect. The coordinator resolves the exact input manifests from
actual worker materializations. An adapter does not construct custody paths.
The coordinator checks current execution permission and the exact original
owned attempt lease before each contact, including later conditional leaves.

Stream each declared output with `publish_output`, retaining its actual
complete bytes and selected size/hash when known. Finish with `complete`,
its known operational return/error, actual measured or unknown cost, cost
scope, peak memory when measured, and a complete partition of selected
streams into consumed, unconsumed and unknown. A returned scientific
negative can have operational `SUCCEEDED`; a caught native error has
`FAILED`. Neither label supplies an independent scientific assessment.
The byte and source-chunk allowances must be positive integers. Transport
splits valid source chunks to fit the whole-output allowance and its 1 MiB
pipe bound; a tiny output can use the default source-chunk allowance. Splitting
does not relax the declared source-chunk limit or the complete byte census.

## Observe the call separately from publication

The store retains one exact `PreparedInvocationContract` for the parent before
its first instrumented call. It binds the actual plan, original task, attempt,
configuration, input and output ports, source, environment, resources and
initial native work. Each `NativeSubworkCallEntry` references that invocation
and its exact definition and contact. Each `NativeSubworkCallReturn` references
the original call-entry fact.

After contact, use `invoke_native_subwork(native_subwork, entry, native_function,
...)` around the actual native call. It requests a call-entry observation at
the worker boundary immediately before invocation. The coordinator authenticates
the retained contact and invocation and checks current execution permission and
the original owned lease again before accepting this boundary. A process can
still die between acknowledgement and the native call: entry alone proves no
return, completed effect or permission to repeat it. Task dispatch and process
launch are separate observations.

The wrapper samples raw return/error UTC immediately after the native call,
before scientific classification, array encoding or output publication. A
raised error retains its actual class name without its message. An isolated
process retains its actual integer return code, without inventing a Python
error class for a nonzero exit. A later array
or publication failure is not a native-call error. Retaining a return, publishing
already returned outputs and reading completed custody require their actual
access and resource controls; they do not request a new acquisition grant.

`inspect` exposes the authenticated `call_entry` and `call_return` separately
from scientific output, completion and receipt custody. A known raw return can
coexist with incomplete outputs or no completion receipt. Preserve that state;
lost required outputs do not become complete or replayable. An interrupted fact
acknowledgement also does not establish that the fact is absent: inspect its
actual retained bytes. Missing facts from an earlier invocation stay missing;
dispatch events, file times and completion receipts cannot supply their UTC
observations.

## Conditional children

Operands can become available during a live parent call. Publish such an
operand through the parent's declared output port, then freeze a conditional
roster with that parent's exact definition identity and live entry token.
Supply every conditional definition through `definitions=`. Each conditional
definition binds the newly authenticated configuration and exact input
materializations before its contact.

The conditional child can consume outputs published by its exact still-live
parent, the exact input manifests already admitted to that parent, and outputs
of known completed children. The coordinator retains those admitted inputs
only for the parent's live descendants; it does not promote them to a pool of
uncompleted task outputs. Uncompleted sibling outputs
are unavailable. A persisted parent record, closed parent entry, foreign
creator token or retired task cannot authorize another child. The initial
unit census remains intact alongside the conditional roster. Conditional
segments are nested work, not additional independent scientific units.

## Read retained progress without replay

`ExternalNativeSubworkStore.iter_roster_definitions` reads the complete
selected operands from guarded custody, one definition at a time.
`iter_roster_states` retains each selected unit in the compact denominator.
`inspect` authenticates progress and manifests without decoding scientific
array payloads. `recover` returns exact completed receipts and refuses
contact without completion. The local operational catalog is unnecessary
for these reads; relocating the complete root preserves relative paths and
canonical receipt bytes.

| Retained state | Meaning and next boundary |
|---|---|
| `NOT_ENTERED` | Selected full operands exist, with no subwork begin. Persisted task contact still grants no new entry. |
| `BEGUN` | Begin exists, with no retained subwork contact. Only the still-live approved creator can proceed. |
| `UNKNOWN_COMPLETION` | Contact exists without its exact completion receipt. A separate raw return may be known while required output custody is incomplete. Preserve both facts; no automatic replay. |
| `COMPLETED` | Exact completion, output/omission and stream censuses, and receipt authenticate. Reuse those bytes without calculation. |

Lost earlier progress records, orphaned products, incomplete publication,
changed sources or revisions, and modified output bytes refuse recovery.
An independently retained completion receipt also prevents missing definition
or roster directories from being mistaken for a new unentered slot.
Closing the process transport retires its creating task token.

## Supply complete retained outputs to an ordinary assessor

`resolve_completed_definition(identity)` reads the original full definition
through its immutable identity and exact completion receipt. It preserves
conditional input materialization IDs; consumers do not rebuild them from
configuration labels or filenames. A missing, substituted or uncompleted
definition refuses. The worker port also checks its actual active parent task.

`iter_completed_output(definition, output_id, maximum_chunk_bytes=...)` supplies
the whole declared, retained output in bounded chunks. It authenticates the
complete primary receipt and physical bytes before delivery, checks the same
open descriptor during and after delivery, and closes it on incomplete
consumption. Full retained adverse outputs are eligible operands for assessment.
Omitted outputs, partial prefixes and unknown completion cannot supply a full
product. Receipt-only direct recovery can read a relocated complete root without
a live creator or native replay.

An adapter needing both native progress and ordinary streamed products implements
`execute_streaming_with_native_subwork(context, native_subwork, emitter,
progress=None)`. The local process executor supplies the existing progress port
and ordinary output emitter together. This lets the producer relay authenticated
completed nested bytes into its declared ordinary output, which a separate PURE
assessment task can consume through normal compiler dependencies. Neither relay
nor publication assesses those bytes or grants later-use admission.

The selected finite parent output allowance covers both retained native outputs
and ordinary output copies. Unrestricted selections acquire no new numeric ceiling.
If the ordinary worker is lost after nested completion, the original nested
receipt remains recoverable; the missing ordinary task result stays adverse or
unknown at its own scope. Exposed relay allocation checks measure transport
buffers, not a scientific native engine's working-memory requirement.

## Run a selected isolated interpreter

`IsolatedNativeEntrySelection` pins the actual interpreter, entry source,
invocation bytes and exact environment. The adapter supplies authenticated
selection bytes as a task input or a live parent's published operand, then
freezes and begins a lifecycle definition whose configuration is exactly the
selection identity. Its declared canonical ports include `IsolatedNativeProcessStart`
and `IsolatedNativeEntryReturn`. This uses the existing conditional roster;
the launcher cannot substitute another selection after freezing.

`run_isolated_native_entry` runs inside the admitted worker and delegates the
selected child's progress to the original coordinator. This selected profile
requires Linux inherited descriptors and the existing infrastructure's anonymous
sealed-input primitives. The actual child PID, creator PID, process group and
available PID namespace are published before acknowledging domain entry.
Interpreter, source, environment and invocation substitutions refuse. Nonregular
selected files refuse before launch. Entry source executes from authenticated
bytes, preventing a valid stale bytecode cache from replacing it.

The new domain entry receives `(native_subwork, immutable_invocation_port)`.
The full invocation is copied and hashed through bounded reads from one stable
descriptor, then sealed against writing, shrinking or growing before the
handshake. The path-free port supports selected read sizes and chunk iteration;
changing the original file cannot change the entered operands. The anonymous
backing retains every byte and consumes physical memory. Domain input size and
engine working memory still need actual resource assessment.

The caller retains complete stdout/stderr through explicitly selected streams
and publishes their available bytes before scientific return guards. A known
process return supplies measured inclusive CPU/wall clocks, while native peak
memory remains unknown unless separately measured. It cannot complete a nested
contact lacking its own receipt. Malformed progress refuses and the bridge kills
and reaps its owned direct child; the outer executor retains whole-group cleanup.
Dependencies, native libraries, physical preparation and numerical adequacy remain
domain prerequisites beyond the selected entry's authentication.

For the prepared isolated route, the lifecycle call-entry observation precedes
the selected child's `Proceed`. Its observed raw process-return UTC is sampled
immediately after the owned `wait`, before cost calculation and return-output
publication. Nested leaf facts require their own instrumented native call
boundary; process exit does not supply missing leaf evidence. The development route with
no `PreparedInvocationContract` retains its existing process observations but
has no exact invocation-bound call facts. It does not infer those facts or
original execution permission from its contact or local witness files.

The additive return-retention repair publishes the existing lifecycle
`process.return` observation even when handshake or progress validation fails,
after reaping its owned child. If return publication itself fails, the raised
error still carries the observed return and failure phase for a controlled
caller. The lifecycle and unresolved nested contacts retain UNKNOWN; neither
the known exit nor a retained output grants replay or completion. One final
focused invocation passes22 checks, including bootstrap exit17, malformed
handshake/progress and three return-publication failures. Its source acceptance is
`/tmp/el-domain-entry-audit-20261011/tp3-known-child-return-source-acceptance01.json`,
SHA-256 `d47872a628a214b15b6f70600d9a8ea485c43b560a12afc30f0a6f6a8da22cfe`.
This is historical acceptance for the scoped bridge repair.
The original TP3 review left controlled worker diagnostics and process-ownership guards outside that evidence scope.
Use the current checks linked below and the selected release packet to assess the installed implementation.

One frozen exposed invocation passed 18 checks with 215 unchanged loaded
source/test/input bindings:
`/tmp/el-rubisco-loop-implementation-20261011/shared-isolated-engine-final01-readout.json`,
SHA256 `73de14d6d82601cbf6969da8c46a51263be74f7803c10a16a37662dbeaa0de43`.
Its independent review is `shared-isolated-engine-independent-review01.json`,
SHA256 `a14538937fca1400de5f725fc59c9570d077d832c3a58b0394cd75495cd5961e`.
Controls include process-loss dispositions, source/environment substitutions,
stale bytecode, mutable invocation, malformed progress, exceptional reaping,
nonregular files and complete invocation copying with measured bounded Python
allocation. This is Linux software acceptance, with zero domain acquisition;
it grants no scientific qualification or whole-release acceptance.

## Partial output and cost

A worker can die or catch an error after an output stream opens. The
coordinator retains the received prefix, including an empty prefix, under
`NATIVE_SUBWORK_PREFIX`. Its separate metadata binds the entered definition,
contact, selected whole-output port and expected contract, actual received
size/hash and interruption reason. This custody-only profile makes no
scientific array, public-source, parser or semantic assessment claim.

The declared scientific output remains omitted. A caught error can retain a
`FAILED` completion receipt containing the prefix and its metadata. Process
loss retains unknown completion. Partial prefixes cannot create a successful
scientific output, fresh evidence, an admitted model or retry permission.
If prefix publication itself fails, occupied transport scratch is retained
for explicit custody diagnosis.

Costs belong to their declared windows. Worker CPU excludes coordinator CPU;
wall time can include custody; retained scientific output bytes and physical
custody storage are distinct quantities. Nested initializer/segment costs
must not be added again to an inclusive parent window. Unknown cost stays
unknown. A mid-trajectory restart additionally requires an adapter's exact
full state and stochastic continuation contract.

## Evidence and remaining scientific work

The [installed exposed adapter](../../src/empirical_lawhood/adapters/methods/native_subwork_conformance.py)
and [spawned crash/recovery checks](../../tests/runtime_platform/test_native_subwork.py)
exercise positive, negative and unevaluable returned bytes, complete frozen
operands, live derived conditional configuration, process loss, caught memory
errors, empty/partial prefixes, source/revision substitutions and relocated
recovery. The [parent contact checks](../../tests/runtime_platform/test_native_effect_contact.py)
separately verify scheduler recovery after complete catalog loss.
These are software conformance fixtures with no scientific qualification.
The [completed-output relay checks](../../tests/runtime_platform/test_native_subwork_completed_relay.py)
add full-byte and original-definition recovery, active-parent binding, combined
native/ordinary streaming, finite output accounting, corruption and ordinary
worker-loss controls.

Ordinary parent and nested native completion retain separate evidence.
A known nested completion can survive a missing or unsuccessful ordinary parent receipt.
The retained parent contact still records its original operational uncertainty.
Neither the nested receipt nor a known process exit can fabricate parent completion.

Reconcile RNG dispositions across the complete original selected stream census.
In the aggregate census, consumed streams take precedence over another call's explicit nonuse.
Preserve each call's original stream records unchanged.
Retain unknown-contact streams as potentially consumed.
Keep remaining reservations separate from proven consumption and authenticated explicit nonuse.

Each scientific adapter still owns its selected unit/branch census, full native
state and source preflight, numerical convergence, independent assessment and
subsequent consumer admission. Historical unreceipted work needs explicit
disposition; installing this progress seam does not make an earlier interrupted
run recoverable at subcall granularity or authorize reacquisition.

See [architecture](architecture.md), [results and failures](../using/results-and-failures.md)
and the [extension recipe](extending-the-engine.md) for the surrounding owners.
