# Matrix E1–E6 researcher programme

SPDX-License-Identifier: CC-BY-4.0

Programme: [Emergent structure — stochastic matrices](../../README.md).

The researcher programme selects the original whole-programme commitment C,
one programme directory and explicit operational settings. D, including the
E5/E6 account, is selected once through C. The public runner derives later
inputs from authenticated original results and calls the ordinary phase owners.
D version 3 includes the dense paired FACTOR58 target, seven mechanical
descriptions, E4 structural choices version 4 and the fixed SR/BR relation.
Before DEV authoring, the ordinary input deriver publishes its blind target and
retains the selection for DEV, CAL and CONF. Later phases authenticate that same
original selection. See the [full-factor guide](../matrix-response-experiment/full-factor-followup.md)
for the accuracy, response-horizon and structural-readout contracts. The
[scientific specification](../../records/matrix-programme.md) gives the
native equations, complete phase census, primary family and claim boundaries.
The [whole-design example](scientific-design.example.json) carries all amended
mathematics and the 980-group maximum. Its disclosed streams and zero-valued
template bytes are exposed software inputs; they cannot supply fresh evidence
or an available physical instrument.

Before selecting C, use the [prospective E1 allocation](e1-inputs.md) to bind
E1's mathematical criterion to its actual allocation, then freeze D and use the
[programme input compiler](input-assembly.md). C retains every original phase
reservation, exact numerical selection, future response panel and the E6 policy
published before TRAIN. Select a complete exposure census and disjoint actual
streams before claiming fresh evidence. Renaming an exposed seed does not
create freshness.

The current specification consumer is `matrix-researcher-programme` and its
record version is `4.0.0`. The protocol identifier remains
`matrix.researcher-programme.v2`. The specification has four fields:

| Field | Selection |
| --- | --- |
| `specification_id` | Stable identity of this original programme selection |
| `directory` | One relative programme home beneath the selected artifact root |
| `input_commitments` | The exact actual C publication and record identity |
| `operations` | Current typed E1, E2, TRAIN, E3, E4, prepared and source-metadata settings |

Operational settings include finite metadata/source budgets, scientific root
and campaign declarations, phase resource reservations, concurrency and native
progress controls. E1, E2 and TRAIN operational selections contain no C handle.
The runner binds each ordinary child assembly specification to the programme's
single original C selection. Source metadata machine controls are selected once.
Later source qualification, entry, issue and reveal acts retain their own
genuine prerequisites. Select E3 computability evidence for the actual paired
views of D's CALIBRATION coordinate and the selected envelope. Programme
preparation checks this scope before child derivation or native entry; a matching
scope does not establish computability readiness or capacity.

An authored E4 phase remains unassessed until its waves and structural analysis
have retained results. Supply the actual wave authorities at that boundary;
missing future results do not prevent the programme from reporting it. A later
run recovers each component that already has execution custody and starts only
components without it. Current reveal and retained integrity checks still apply.

Copy [the current specification example](specification.example.json) and
[outer selector](sources.example.json). The example contains exposed,
unwritten publication handles and explicit illustrative resource selections.
Replace them with the actual C and operator settings; it is not source custody,
capacity evidence or a ready scientific programme.

There is no editable active slot, manual predecessor list, per-phase task map
or replacement programme specification after each result. The runner retains
immutable bindings to actual derivation outputs and actual original run
locators. Ordinary child packages, receipts, publications and scientific readers
establish state. A programme binding establishes no completion or authority.

Use the [locked main environment](../../../../../docs/using/environments.md) and select your
own operator profile admitting at least four distinct physical cores. Select
one numerical thread per worker and keep the same admitted worker count through
preparation, authoring and execution. Choose explicit input, output, temporary
and cache paths on the storage declared by your profile; verify actual mount,
write access and capacity. The examples below select four workers.
The [operational verification mode](../../../../../docs/using/configuration.md#operational-artifact-verification)
defaults to `reduced` independently of this frozen programme specification.
Use the global `--artifact-verification strict` option for full intermediate hashing.
Both modes retain current access, full final byte checks and ordinary worker delivery.
[Output reservations](../../../../../docs/using/configuration.md#output-reservations-and-actual-storage)
are advisory and do not establish required disk capacity.
Actual mount, write and profile free-space checks remain active; frozen task output ceilings remain unchanged.
The same selected count bounds independent bookkeeping verification. Canonical
format checks use processes; source and publication joins use operation-local
indices and shared immutable read contexts. Access refreshes, durable publication
and scientific dependencies remain coordinated. A worker count is a concurrency
ceiling, not an assurance that every operation can run in parallel. Ordinary
run/read commands use these paths without a separate performance mode.
Verification queues refill available slots when checks complete. Product export
refreshes access for each item and verifies complete snapshots at publication
and completion. These changes preserve exact bytes and original producing records.
Retained-E3 record derivation reuses authenticated operands within one open read.
Full custody checks remain before publication and at the owning scope's exit.
Select `PROGRAMME_CATALOG` from the programme's retained catalog selection when reading prospective phases.
It is relative to the selected operator profile's scientific scratch.
An installed reader also needs its matching source distribution as `PROJECT_ROOT`.

Canonically prepare the copied specification
through [configuration](../../../../../docs/using/configuration.md), with an empty outer
`ExperimentFileInputSelection` for `matrix.researcher-programme.v2`.

Set `$PROJECT_ROOT` to your selected checkout or matching installed source distribution.
Use the same explicit operator profile, source and storage selections throughout the commands below.

```sh
uv run --no-sync empirical-lawhood config prepare \
  --consumer matrix-researcher-programme --config "$COPIED_PROGRAMME" --output-file "$PROGRAMME"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-explain \
  --input "$PROGRAMME" --sources "$PROGRAMME_SOURCES" --workers 4
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-author \
  --input "$PROGRAMME" --sources "$PROGRAMME_SOURCES" --source-snapshot "$SOURCE_SNAPSHOT" \
  --environment-id "$ENVIRONMENT_ID" --workers 4 --output-dir "$PROGRAMME_AUTHORED"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-run \
  --authoring-dir "$PROGRAMME_AUTHORED" --workers 4 --yes
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" \
  --catalog-relative-path "$PROGRAMME_CATALOG" campaign experiment-read \
  --authoring-dir "$PROGRAMME_AUTHORED"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-recover \
  --authoring-dir "$PROGRAMME_AUTHORED" --workers 4 --yes
```

Authoring retains the original programme and checks C. Run and recover each
advance a bounded set of eligible operations. They derive ordinary inputs,
author eligible children and stop at explicit missing scientific or authority
prerequisites. Recovery reuses the original child run and retained attempts;
it does not replace an uncertain native effect with a new attempt. Read only
reopens original reports and dispositions. It does not publish, derive,
author, recover or acquire.

Select `--yes` for Matrix programme execution and recovery, including development phases.
Without it, advancement can derive inputs and author metadata, but stops before phase execution.
Use `experiment-read` for inspection without these metadata effects.
For an issued child's resource preview, select its direct `--plan` route without `--yes`.
Read the returned status and reason codes before interpreting the command's exit status.

Run, recover and advancing author/derive calls return `read_scope=OPERATIONAL_ADVANCE`.
They authenticate phase execution plans, the complete frozen receipt and
attempt census, and terminal records to avoid dispatching completed acquisitions.
Those phase observations say `EXECUTION_RECORDS` and
`scientific_completion=DEFERRED_TO_FULL_READ`; they do not validate scientific
payloads or establish qualification. Input consumers authenticate the original
products needed for each new calculation. E4 fit and freeze use the sealed
causal features and scores from the original acquisition. E5 nomination joins
every assigned case to its original receipt and frozen decision rule.
The complete terminal reduction must match the retained nomination, including adverse decisions.
Current access checks remain required at each consuming boundary.

The default skips retrospective array reconstruction and exhaustive diagnostic reports.
It still executes required new structural tasks, fits, calibration and scientific decisions.
E4 operational completion includes its original required PURE structural child.
An absent structural child leaves the phase incomplete.
Composite CAL and CONF status also requires every selected component's actual terminal records.
DEV product locators retain their original declarations, receipts and canonical bytes.

`OPERATIONS_COMPLETE` means that the operational frontier is settled. Obtain
the scientific report through `--scientific-reconstruction full` with `experiment-read` or product export.
This opt-in includes retrospective numerical reconstruction and exhaustive reports. Reports identify
`scientific_read_completed` separately for each phase. No scientific verification
result is cached between invocations, and an operation report is never effect
or outcome-access authority.

| Phase | Original dependency and ordinary owner |
| --- | --- |
| E1 | Independent compact prospective E1, derived from C |
| E2 | Independent native utility, derived from C |
| TRAIN | Native training acquisition from C, followed by actual bank export |
| E3 | Configured protected input assembly from actual original TRAIN |
| E4 DEV | The complete original matched population and original E3 products |
| E4 revision | Actual complete DEV, including its full-factor structural assessment |
| E4 CAL | Distinct source closeout and protected CAL after an eligible frozen SR/BR fit, or the closed triggered revision |
| E4 CONF | Distinct source closeout and the complete original confirmation population |
| E5 DEV | Actual original E3/E4 predecessors and C-backed initialization |
| E5 CONF | Actual DEV nominee, separate initialization/source closeout and protected assessment |
| E6 | Original pre-TRAIN reserves and policy, separate initialization/source closeout and both transfer regimes |

The full-factor structural assessment belongs to each ordinary entered E4
result. Its complete history accounting, numerical failures and adverse
witnesses are retained. There are no separate operator-selected structural
slots. An adverse completed result satisfies ancestry where the scientific
protocol permits it; operational success never implies a favourable result or
scientific qualification.

For the amended matched design, `FIT_AVAILABLE` admits separate source-CAL/CAL
and requires its actual result before source-CONF/CONF. CONF measures the fixed
SR/BR pair; adverse comparisons and infinite bounds preserve that account for
eligible later work. `FIT_UNAVAILABLE` leaves all dependent E4 and E5/E6 phases
unentered because the required pair is unconstructible. S0/B0 remain references.
The relation report reads original fitted products and consumed CONF policies;
it does not fit a new model after outcomes. CAL/CONF families are sampled
uniformly per group and their realised counts are retained without redrawing.

For the closed paired15 procedure, an actual `NOT_TRIGGERED` or `UNEVALUABLE` DEV revision leaves source-CAL/CAL
unentered. The original CONF still runs and retains the original E3 account.
A triggered revision requires actual separate CAL before CONF. E5 CONF requires
its actual recipe nomination. A complete E5 DEV `NONDISCRIMINATING_OPPORTUNITY`
or `UNEVALUABLE_OPPORTUNITY` leaves CONF initialization, source closeout and
assessment unentered. Eligible ORIGINAL_E3 E6 still continues; it has no
dependency on favourable E5 confirmation or an E5 nominee. For a frozen REVISION
account, actual E4 revision nonentry or a complete CONF decision selecting no
revision package leaves all E5/E6 phases unentered. The account remains frozen
in D and never falls back to E3. Missing, partial, corrupt or unauthorized
products establish no conditional nonentry. A contradictory retained entered
phase refuses rather than being rewritten as unentered.

At a genuine protected boundary, prepare a canonical
`MatrixProgrammeOperationSelection` with consumer
`matrix-programme-operation-selection`, pinned to the actual authored programme
plan. Its `authorities` select real issued package paths, current reveal IDs
and any required original-parent paths. Its `access` selects actual E4 or
prepared prospective root, entry and formal operands. For E4 collection,
select the genuine produced-input qualifications and source configurations;
the runner obtains the observation roster from actual original wave reads.
These selections confer no permission themselves.

Pass that later record with `--programme-request` to run, read or recover.
Every child repeats its actual issue, execution, resource, source, parent and
reveal checks. The runner never issues or reveals on the operator's behalf.
Derived bodies containing fitted models retain their actual parent access and
visibility, with current original custody checked before protected bytes and
through dependent publication.

Programme reports keep operational completion, source/instrument premises,
scientific outcomes and qualification separate. Denominators come from the
owning readers. Unknown counts remain unknown; nested populations are never
added together. Negative, unevaluable, missing, unentered and nonuse results
remain visible.

## Continue after a source change before TRAIN

The supported source continuation preserves completed original E1/E2 and creates
a separate programme for the remaining work. It requires an original programme
with exactly E1/E2/TRAIN authored, complete successful E1/E2 execution custody,
no TRAIN run namespace and no later binding, derived-input or child namespace.
It rejects uncertain or partial original future entry and chains of source
continuations. Stop the original controller before deriving this handoff.

Copy [the continuation selection](source-continuation.example.json) and its
[empty selector](source-continuation.sources.example.json). Replace `predecessor`
with the exact original `matrix-programme.json` identity and publication handle,
and choose a disjoint new `directory` beneath the same guarded root. The example
handle is unwritten and cannot establish original custody. The current source,
worker count and environment must be selected explicitly; workers, environment
and operational selections remain the originals.

```sh
uv run --no-sync empirical-lawhood config prepare \
  --consumer matrix-programme-source-continuation --config "$COPIED_CONTINUATION" \
  --output-file "$CONTINUATION"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$CONTINUATION" --sources "$CONTINUATION_SOURCES" \
  --metadata-directory "$CONTINUED_PROGRAMME/continuation-inputs" \
  --output-selection "$CONTINUED_PROGRAMME/continuation-inputs/inputs/sources.json" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-author \
  --input "$CONTINUED_PROGRAMME/continuation-inputs/inputs/specification.json" \
  --sources "$CONTINUED_PROGRAMME/continuation-inputs/inputs/sources.json" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4 \
  --output-dir "$CONTINUED_PROGRAMME"
```

The metadata deriver retains D, all original reservations and native settings,
history and future streams, folds, availability and support publications. It
changes producing provenance and its derived response-source and E6-policy
bindings through their owning constructors. It does not allocate new streams,
read scientific outcome bodies, acquire, issue or reveal. The target uses
`matrix.researcher-programme.continued.v1` and requires its exact
`source-continuation.json`; deleting that record cannot enable replacement E1/E2.
The original programme, authored TRAIN packet and all original execution custody
stay unchanged.

Each metadata operation authenticates the complete original execution census once.
Preparation and authoring share that context until publication finishes.
Final checks revalidate exact control bytes, publication custody, absent future paths and current input access.
Changed custody refuses the operation.
This temporary reuse supplies no permission and does not replace a full scientific read.
New development children use `AUTHORING_RECORDS` in the authoring report.
This scope authenticates the newly published packet and checks that its run namespace remains absent.
It establishes neither execution completion nor a scientific result.

Use the ordinary run/read/recover/export commands against the continued home.

## Continue with completed TRAIN after a source repair

Use `matrix.programme.retained-training-continuation` when E1, E2 and TRAIN
have complete successful original execution custody and all three original
TRAIN banks exist. The predecessor may be the original, a before-TRAIN continued,
or a prospectively amended programme. No original E3 or later child or phase
binding may exist. A failed E3 metadata derivation is preserved in its original
directory; it is not a completed or entered child. Stop the original controller
before this handoff. A previous completed-TRAIN handoff cannot be chained.

Copy [the retained-TRAIN selection](retained-training-continuation.example.json)
and its [empty selector](retained-training-continuation.sources.example.json).
Replace the unwritten predecessor with the actual original `matrix-programme.json`
identity and publication handle, and select a disjoint new programme home.
Use the original worker count, environment and operational selections, with
the repaired source snapshot:

```sh
uv run --no-sync empirical-lawhood config prepare \
  --consumer matrix-programme-retained-training-continuation \
  --config "$COPIED_CONTINUATION" --output-file "$CONTINUATION"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$CONTINUATION" --sources "$CONTINUATION_SOURCES" \
  --metadata-directory "$CONTINUED_PROGRAMME/continuation-inputs" \
  --output-selection "$CONTINUED_PROGRAMME/continuation-inputs/inputs/sources.json" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-author \
  --input "$CONTINUED_PROGRAMME/continuation-inputs/inputs/specification.json" \
  --sources "$CONTINUED_PROGRAMME/continuation-inputs/inputs/sources.json" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4 \
  --output-dir "$CONTINUED_PROGRAMME"
```

Continue with the ordinary run/read/recover/export commands against the returned
home. The target requires `retained-training-continuation.json` and an exact
typed source-lineage FILE in C. Readers authenticate the original C and prove
that D, allocations, streams, folds, numerical selections, response mathematics,
exposure and availability are unchanged. Future source provenance and its
derived response and E6-policy bindings change through their ordinary owners.

E1/E2/TRAIN retain their original homes, producers, receipts and native contacts.
The runner derives the TRAIN adoption selection from those original publications;
the operator does not assemble a task roster or predecessor census. E3 authenticates
every original winning receipt, native contact and bank publication through
`RECEIPT_BOUND_BANK_RECONSTRUCTION`, without repeating independent array mathematics.
This does not claim a new full numerical replay. The ordinary scientific reader
retains that separate scope. E3 publishes its new future source manifest after
authenticating the original pre-TRAIN commitments; it never backdates a seal.
E4 explicitly joins those retained TRAIN inputs to the continued C.

Stock metadata reads share immutable facts only inside a bounded live context.
Complete byte and access checks run before each consumer and on exit; custom
reader policies retain their own verification scopes. E3 may reuse its verified
prepared graph after the mandatory cold reopen and current binding checks.
Source transition and metadata reuse grant no issue, execution, reveal, freshness
or scientific qualification authority.

## Continue after E3 prefixes and model freeze

Use `matrix.programme.retained-e3-continuation` after a retained-TRAIN programme
has entered E3 and stopped with a `BLOCKED` or `FAILED` terminal. Every original
prefix, numerical check, causal projection, physical forecast, fit and model
freeze must have successful custody. Completed features and CAL forecasts may
also be retained. No future response may have entered, and no later phase may
have been authored. The original controller must be stopped.

Copy [the entered-E3 selection](retained-e3-continuation.example.json) and its
[empty selector](retained-e3-continuation.sources.example.json). Replace the
unwritten predecessor with the actual retained-TRAIN programme publication.
Select a disjoint new programme home, a new E3 run ID and the actual original
E3 reveal authority ID. Keep the original environment, worker count, operations
and scientific selections. The repaired source must retain the dependency lock
and the numerical owners checked by the continuation contract.

```sh
uv run --no-sync empirical-lawhood config prepare \
  --consumer matrix-programme-retained-e3-continuation \
  --config "$COPIED_CONTINUATION" --output-file "$CONTINUATION"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$CONTINUATION" --sources "$CONTINUATION_SOURCES" \
  --metadata-directory "$CONTINUED_PROGRAMME/continuation-inputs" \
  --output-selection "$CONTINUED_PROGRAMME/continuation-inputs/inputs/sources.json" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers "$WORKERS"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-author \
  --input "$CONTINUED_PROGRAMME/continuation-inputs/inputs/specification.json" \
  --sources "$CONTINUED_PROGRAMME/continuation-inputs/inputs/sources.json" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers "$WORKERS" \
  --output-dir "$CONTINUED_PROGRAMME"
```

The public deriver authenticates the original partial terminal, complete task
and receipt census, resource history, native prefix completions and absence of
future response contact. It derives the complete continuation graph from those
records. Each completed task becomes an explicit pure adoption of its original
bytes; the remaining response tasks bind the current source and original prefix
source separately. The original execution lock stays held while those facts are
used, with fresh access checks at consumption. The failed attempt remains in
its original home.

The same command can continue a stopped entered-E3 continuation after an input-contract repair.
Select that programme publication and its actual reveal authority.
This transition requires a `BLOCKED` terminal, every completed adoption, all causal features, and no future native contact.
Pending attempts must be known input-computability refusals with no output or uncertain resource work.
The owner retains the original plan, terminal, receipts and resource history unchanged.
It derives a separate issued plan containing only unfinished tasks.
Completed outputs become exact receipt-bound external inputs, with their original producers and access labels.
The full scientific design remains available for validation but grants no execution of completed tasks.
No additional adoption, refit or prefix acquisition occurs.
The installed source must be selected before derivation and issue.
Product exports retain the original model and freeze producers beside the new calibration producers.
Downstream readers authenticate both runs through the unfinished continuation and the completed new plan.

Use the returned paths with the ordinary run/read/recover/export commands and
the selected continued E3 run ID. Current source, issue, execution, resource and
reveal prerequisites still apply. The continuation refits no model, reacquires
no prefix and changes no allocation, stream, endpoint or denominator. Full
scientific reads authenticate adopted bytes and continued native completions,
and report the original fitted models and freeze explicitly. E4–E6 source
recipes retain the original TRAIN producer and the exact E3 adoption lineage.

## Apply the prospective curve/mechanism amendment before TRAIN

The separately versioned `matrix-programme-curve-amendment` consumer implements
the fixed 2026-10-25.1 change in the
[matched forecast specification](../../records/matrix-matched-forecast.md).
It selects the original programme publication, the exact amendment rule, a
disjoint target directory, and both exposed E2 analyses. Each analysis selects
its original completion, manifest, report and specification by absolute path,
SHA-256 and byte count. List every superseded source continuation in
`withdrawn_derivations`, ordered by record ID. These are exact published
continuation handles; an authored superseded TRAIN packet must remain unentered.

Use `config prepare --consumer matrix-programme-curve-amendment` for the copied
selection. Its empty `ExperimentFileInputSelection` uses protocol
`matrix.programme.curve-mechanism-amendment`. Call the ordinary
`campaign experiment-derive-inputs` with metadata directory
`$AMENDED_PROGRAMME/amendment-inputs` and output selection
`$AMENDED_PROGRAMME/amendment-inputs/inputs/sources.json`. Select the frozen new
source and the original worker count and environment. Author the resulting
`inputs/specification.json` and `inputs/sources.json` through the ordinary
`campaign experiment-author` command at `$AMENDED_PROGRAMME`.

The deriver authenticates original E1/E2 execution, all declared future
nonentry, and the exact 96-root E2 protocol roster in both analyses. It preserves
the historical text bytes in development-visible snapshots. Those analyses
remain post-outcome explanatory evidence. Their referenced derived arrays are
bound by their original manifests; derivation does not rerun those analyses.
The allocation census remains unchanged, and a separate amendment census records
the exposed E1/E2 stage identities and original future reservations.

Only the declared curve endpoint, shared feature rules, diagnostic construction
and corresponding source bindings may change. The new programme requires its
`curve-mechanism-amendment.json` publication for every reopening and exports
that lineage with the evidence references. Original E1/E2 and superseded TRAIN
packets remain immutable. The ordinary issue, source, execution and reveal
boundaries continue to apply. Source-only continuation still refuses changes
to the original scientific design.
E1/E2 retain their original programme, producing source, child directories and
run bindings. Remaining work is authored under the selected new source and
still needs genuine current source, resource, issue and reveal admission.
Reports include the source handoff and each phase's `producing_programme`.
A source continuation creates no freshness, sampling or scientific qualification
claim; exposed E1/E2 remain the original evidence.

## Close entered E3 calibration before confirmation

Use `matrix.programme.e3-cal-closeout` after an unfinished E3 execution stops
with every original CAL root entered and all CONF responses unentered.
The original dispatcher must have stopped. Current original reveal
authority and a compatible installed source remain required.

Copy [the closeout selection](e3-cal-closeout.example.json) and its
[empty selector](e3-cal-closeout.sources.example.json). Select the actual
predecessor programme publication, original reveal ID and a separate programme
directory. Select a new E3 run ID. Preserve the original worker count,
numerical environment, scientific inputs and resource limits.

```sh
uv run --no-sync empirical-lawhood config prepare \
  --consumer matrix-programme-e3-cal-closeout --config "$COPIED_CLOSEOUT" --output-file "$CLOSEOUT"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$CLOSEOUT" --sources "$CLOSEOUT_SOURCES" \
  --metadata-directory "$CONTINUED_PROGRAMME/continuation-inputs" \
  --output-selection "$CONTINUED_PROGRAMME/continuation-inputs/inputs/sources.json" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4
```

The owner authenticates the complete original allocation, contacts, native
returns, receipts, models and resource history. It retains completed scores
only with their actual completed native custody. An unknown contact produces
explicit missingness under the new assessment source and original visibility.
It creates no native completion, replacement observation or successful
receipt for the original call. An existing blocked terminal remains unchanged.
An absent terminal remains absent. The closeout binds the exact original
recovery index, control census and unresolved resource journal in either case.
Changed custody, revoked access, later native entry and unreceipted parent
outputs refuse this transition.

Author the returned specification and sources through `experiment-author`.
Use the returned paths and ordinary programme run, read, recovery and export
commands. The new plan publishes missing-outcome scores, calibrates the complete
original CAL population and freezes that calibration before CONF forecasts.
Every entered CAL native task and completed predecessor task is excluded.
Interrupted PURE publication uses ordinary recovery in the new execution.
Never use the original no-contact continuation to repeat an uncertain call.

Missing scores remain infinite calibration scores. An infinite calibrated
radius preserves CONF eligibility and its full original denominator.
The original assays, forecasts, admission decisions and scientific criterion
remain required. Original source, resource, issue, execution and reveal checks
still apply. Closeout and software checks establish no scientific qualification.

## Continue after completed E3 under a repaired installation

The public `campaign matrix-continue` command prepares a source continuation,
authors a separate programme, and executes eligible new tasks within one
invocation. Select the repaired source installation, the original operator
profile, original worker count and an explicit disjoint output directory:

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" \
  campaign matrix-continue --authoring-dir "$PREDECESSOR_PROGRAMME" \
  --output-dir "$CONTINUED_PROGRAMME" --workers 8 --yes \
  --attempt-dir "$CONTINUATION_ATTEMPT" --progress-file "$CONTINUATION_PROGRESS"
```

All source capture, canonical request preparation, derivation, authoring and
execution admission occur after this request starts. No prepared E4 child or
cache warming is required. Actual native entry is recorded by the ordinary
native execution owner; a RUNNING report or authored child is not native entry.
Measure entry latency from invocation start through the first authenticated native call entry.
Authoring and execution share one programme context.
The execution owner authenticates each newly authored child before dispatch.

Retrospective reconstruction and exhaustive reporting are
[off by default](../../../../../docs/using/configuration.md#optional-retrospective-scientific-reconstruction).
The default authenticates original receipts and consumed product bytes without
recomputing completed E3 numerical results. New E4–E6 scientific computations,
revision decisions and nomination conditions retain their ordinary owners.
Required decision reports identify their consumed census separately from deferred retrospective reconstruction.
They preserve complete denominators, negative outcomes and conditional nonentry rules.
Select `--scientific-reconstruction full` explicitly for the full integrated
scientific read. Original adverse and unevaluable findings remain unchanged.

A stopped E4 development child with only partial input preparation can be
retained through this continuation. The owner authenticates its original
binding, packet, execution plan and exact partial-input census while holding
its ordinary execution lock. Partial inputs can include the ordinary producing provenance.
Its published bytes and original producing source remain required.
Any contact, receipt, recovery record or other
execution namespace refuses this handoff. The old child and inputs remain
unchanged; the new source gets a separate child and run namespace. This path
cannot continue an entered or uncertain native task.

The lower-level derivation and authoring commands remain available:

The same `matrix.programme.source-continuation` specification and
`experiment-derive-inputs` command support the completed E3 boundary. Select the
actual published predecessor plan and a disjoint new programme directory as in
[the source-continuation procedure](#continue-after-a-source-change-before-train).
Use the repaired installation, the existing operator profile, worker count,
environment and unchanged numerical owners. The selected profile is required
for the original issued E3 scientific read.
When the host admits a larger controller working set, select the global
`--metadata-rss-limit-bytes` option with a retained `--attempt-dir` for each invocation.
This [operational allowance](../../../../../docs/using/configuration.md#explicit-metadata-rss-allowance)
preserves the original programme records and native task budgets.

The deriver authenticates complete E1/E2/TRAIN/E3 execution and original E3
product custody under current access. Full retrospective reconstruction requires
the explicit opt-in. It refuses entered or uncertain E4–E6 successors; the
stopped input-only E4 development handoff above is the sole authored exception. This boundary accepts an already continued
programme; its original continuation and amendment records remain required.
An adverse E3 scientific result is retained and does not prevent eligible E4.
An unfinished E3 does not meet this handoff's prerequisites.

E4 input access authenticates each original E3 product under its actual producer.
After CAL closeout, the model and freeze can belong to an earlier partial run.
Their receipt closure requires the completed continuation and its exact imported products.
The original terminal remains unchanged, including its absence.
Current reveal checks apply to every producer.

A failed E4 handoff can leave a complete original bank metadata publication.
The completed-E3 continuation accepts only its six exact bank and programme members, with their original publication controls.
It authenticates those bytes against the original C, E3 products and TRAIN custody.
The original metadata remains unchanged.
Missing members, foreign paths and changed access refuse the handoff. Successor
children, bindings or runs require the exact stopped input-only exception above.

The returned `source-continuation.json` records each actual phase binding and
terminal, including a supported additive repair terminal when present. Original
receipts, model bytes, freeze, allocations, resource history and producing
programmes remain in their original custody. The new programme inherits those
phases and cannot rederive, reauthor or reacquire them. Source-adjusted future
inputs preserve the original scientific design and reservations.
The input source proof keeps the exact original E3 commitment and any retained
TRAIN lineage under their actual producers. E4–E6 use that original commitment
for predecessor joins and the new source for future acquisition. This proof
does not authorize another completed-E3 source handoff.

Author the returned specification and sources with `experiment-author`, then
use ordinary `experiment-run`, `experiment-read` and product export against the
returned programme. Select genuine later child authorities as they become
required. Retain the original instruction and repair evidence alongside the
final scientific report; neither a source handoff nor software checks establish
scientific qualification.

## Continue after completed E4 development under a repaired installation

Use `campaign matrix-continue` with the completed E4 development programme as `--authoring-dir`.
Select a disjoint new programme directory, the original operator profile, worker count and environment.
The command above also supports this boundary. Keep the original programme and every acquisition in place.

The owner authenticates complete E1/E2/TRAIN/E3 custody, E4 development acquisition and its required PURE structural child.
E4 may have a successful [output-allowance repair](#repair-a-pure-development-output-allowance)
or [controller repair](#resume-interrupted-development-with-a-repaired-controller) terminal.
Its original terminal, refused attempts, successful receipts, worker source and repair controls remain required.
An unfinished acquisition, incomplete structural child or authored later phase refuses this handoff.
This boundary does not permit adoption of an entered but unfinished E4 run.

Before later phases are authored, select a larger PURE response-score output allowance when required:

```sh
"$REPAIRED_CLI" --project-root "$REPAIRED_SOURCE" --operator-profile "$PROFILE" \
  campaign matrix-continue --authoring-dir "$COMPLETED_E4_PROGRAMME" \
  --output-dir "$CONTINUED_PROGRAMME" --workers 8 --yes \
  --pure-output-bytes 268435456 \
  --attempt-dir "$CONTINUATION_ATTEMPT" --progress-file "$CONTINUATION_PROGRESS"
```

This explicit selection changes only the response-score output allowances for later E4, E5 and E6 phases.
The complete original E4 development and structural terminals remain required.
Any authored later phase refuses the transition.
The selected allowance must increase an original value, never lower one, and fit each original memory ceiling.
The registered in-memory ceiling remains 256 MiB.
Original memory, source, native-task and authority ceilings continue to apply.
The separate continuation request and record bind the exact operational change.
Original operations, completed task inputs and receipts remain in their original custody.
Without `--pure-output-bytes`, the continuation preserves every original operational value.

The new `source-continuation.json` binds both original E4 terminal identities and all five completed phase bindings.
The continued programme delegates E4 input and child lookup to the actual original producer.
It cannot rederive, reauthor or reacquire completed E4 development.
Only later unentered phases use the new admitted source.
Original scientific rules, allocations, current access and numerical source continuity remain mandatory.
The revision owner consumes actual retained E4 results before it determines later eligibility.
Operational completion and this source handoff do not establish scientific qualification.

## Repair a failed PURE retained-E3 adoption

Use the installed public recovery command when a software defect has exhausted
one PURE retained-model adoption. Select a separately built controller, the
original frozen worker installation, the existing operator profile and a new
catalog projection. Keep the original worker count and one numerical thread per
worker. Existing execution and reveal authority must remain valid.

```sh
"$REPAIRED_CLI" \
  --project-root "$REPAIRED_SOURCE" --operator-profile "$PROFILE" \
  --catalog-relative-path "$REPAIR_CATALOG" \
  --approval-checker-trust "$CHECKER_TRUST" \
  campaign experiment-recover --authoring-dir "$E3_CHILD" --run "$E3_RUN" \
  --reveal-authority-id "$E3_REVEAL" --workers 8 --yes \
  --repair-retained-e3 --repair-instruction "$OWNER_INSTRUCTION" \
  --worker-interpreter "$FROZEN_WORKER_PYTHON" \
  --worker-source-root "$FROZEN_WORKER_SOURCE" \
  --attempt-dir "$REPAIR_ATTEMPT" --progress-file "$REPAIR_PROGRESS"
```

`OWNER_INSTRUCTION` contains the retained owner instruction for this selective
repair. The API derives the repair identity and complete task selection from the
actual frozen plan, terminal, receipts and resource journal. No task roster or
replacement scientific records are supplied by the operator. Use the original
instruction bytes when continuing an existing repair.

The controller authenticates both installations and checks unchanged numerical
owners and dependencies. Parent preparation uses the repaired controller; workers
run in the original isolated interpreter and retain their actual producing
provenance. Existing inputs are authenticated and compared byte for byte, with
their original validation stamps and current access checks.

Each additional wave retains the exact successful receipts under their producing
source. Only the known failed PURE adoption can receive a new attempt; blocked
dependencies keep first-execution status. A separate resource journal retains the
entire preceding history and frozen limits. Committed model outputs must match
the original retained model exactly. Native contact, uncertain pending work,
changed bytes, refitting and prefix reacquisition are refused.

If a repair itself fails, select a separately installed corrected controller and
a new catalog through this same command. Its additive continuation preserves the
previous failed terminal, output publications and resource history. Repeating
the command with the same controller resumes its existing wave; it cannot grant
another attempt. Historical controller-admission records remain readable, but
new recovery does not introduce a record type for each software defect.
The continuation binds the latest completed receipt census, including work
completed by an earlier repair. It can retry one failed retained fit, model-freeze
or forecast adoption while all future native responses remain unentered. The
original record revision remains readable with its original bytes.

Use the compatible repaired installation for `experiment-read` and status so the
reader follows the authenticated additional wave. Original failed terminals
remain accessible in their original custody. Retain direct evidence of the new
adoption receipt and newly completed dependencies. Passing checks or publishing
a repair transition does not establish scientific progress. Continue eligible
later phases, then perform the full scientific read and export.

## Repair a PURE development output allowance

Use this recovery when a completed development wave has resource-refused PURE calculations.
Every original native task must already have its successful receipt.
Select a separately built controller and the unchanged original worker installation.
Keep the original operator profile, worker count and current input-access selections.

```sh
"$REPAIRED_CLI" \
  --project-root "$REPAIRED_SOURCE" --operator-profile "$PROFILE" \
  --catalog-relative-path "$REPAIR_CATALOG" \
  campaign experiment-recover --authoring-dir "$E4_CHILD" --run "$E4_RUN" \
  --workers 8 --yes --repair-development-output-bytes 16777216 \
  --repair-instruction "$OWNER_INSTRUCTION" \
  --worker-interpreter "$FROZEN_WORKER_PYTHON" \
  --worker-source-root "$FROZEN_WORKER_SOURCE" \
  --read-access "$CURRENT_INPUT_ACCESS" \
  --attempt-dir "$REPAIR_ATTEMPT" --progress-file "$REPAIR_PROGRESS"
```

The selected bytes bound the combined output from each repaired calculation.
The value must exceed its original allowance and remain within the registered capability ceiling.
The in-memory ceiling is 256 MiB.
This example selects 16 MiB.
Input-edge limits, memory, wall time, source bytes and native budgets remain unchanged.

The owner derives the complete task census from the original `BLOCKED` terminal and its receipts.
Only exhausted, single-attempt PURE calculations with a recorded resource refusal can receive another attempt.
Dependency-blocked PURE tasks receive their first execution.
Prior contact, uncertain attempts, other failures and unreceipted outputs refuse this repair.
The exclusive original run lock prevents overlap with active execution.

The repair retains the original plan, task configurations, inputs, receipts, failed events and terminal.
A separate recovery index binds the output allowance, owner instruction and both source installations.
All original adapter and kernel bytes and the dependency lock must match.
Workers execute in the original interpreter with the original producing provenance.
Current input access remains mandatory before protected reads.

Repeat the exact selection to resume this repair without another attempt.
Use the repaired installation for result reads so it authenticates the additional terminal.
Readouts identify the original terminal and the operational allowance separately.
Completion of this repair supplies no new native authority or scientific qualification.

## Resume interrupted development with a repaired controller

Use this explicit recovery when development has both completed work and a recorded PURE output refusal,
and an operational controller repair is needed before the original graph finishes.
Validate the replacement installation before interrupting the original controller.
Send `SIGINT` only to that controller process, let active workers drain, and verify that it has exited.
Do not terminate its workers or start a concurrent controller.
The recovery takes the original exclusive run lock and authenticates the complete retained census.

```sh
"$REPAIRED_CLI" \
  --project-root "$REPAIRED_SOURCE" --operator-profile "$PROFILE" \
  --catalog-relative-path "$REPAIR_CATALOG" \
  campaign experiment-recover --authoring-dir "$E4_CHILD" --run "$E4_RUN" \
  --workers 8 --yes --repair-development-controller \
  --repair-development-output-bytes 268435456 \
  --repair-instruction "$OWNER_INSTRUCTION" \
  --worker-interpreter "$FROZEN_WORKER_PYTHON" \
  --worker-source-root "$FROZEN_WORKER_SOURCE" \
  --read-access "$CURRENT_INPUT_ACCESS" \
  --attempt-dir "$REPAIR_ATTEMPT" --progress-file "$REPAIR_PROGRESS"
```

This example selects the 256 MiB combined in-memory output ceiling.
The selection must fit the original registered capability ceiling and available resources.
It covers unfinished PURE calculations of the resource-refused capability, including those not yet attempted.
Native task budgets, scientific input edges and every frozen task configuration stay exact.
Select the original worker count and profile; eight workers are shown here.

The repair preserves every original receipt, event and any existing terminal.
An interrupted run may have no terminal; the repair records its absence without fabricating one.
Ordinary reconciliation can finish missing success events from already durable receipts.
Only original native tasks with no prior contact may enter under their existing execution and access prerequisites.
A native contact without a successful receipt, any native failure, other failure classes,
unreceipted outputs or changed original controls refuse this transition.
The separate index gives each unfinished task one repair candidate and retains original successful candidates.
Repeating the exact selection resumes that index without granting another attempt.

The original worker installation and dependency lock remain frozen.
The controller must preserve the capability registry, numerical owners, kernel and adapter sources;
only the two programme continuation metadata modules may differ among adapter sources.
Current input permission is refreshed throughout reads and immediately before native entry.
The repair record and result readout disclose both sources, the original control census and task categories.
Operational recovery does not establish scientific completion or qualification.
After complete E4 development and its structural child, use the
[completed-E4 continuation](#continue-after-completed-e4-development-under-a-repaired-installation).

## Prepare a separate incomplete-native continuation proposal

Use this preparation when ordinary recovery refuses incomplete original native contacts.
First verify that the original controller and workers have stopped.
Select the original development child, run, frozen worker installation and current input access.
Select a disjoint proposal directory beneath the same guarded artifact root.
Retain the exact instruction that requests preparation.

```sh
"$REPAIRED_CLI" \
  --project-root "$REPAIRED_SOURCE" --operator-profile "$PROFILE" \
  campaign experiment-prepare-native-continuation \
  --authoring-dir "$E4_CHILD" --run "$E4_RUN" \
  --output-dir "$CONTINUATION_PROPOSAL" \
  --worker-interpreter "$FROZEN_WORKER_PYTHON" \
  --worker-source-root "$FROZEN_WORKER_SOURCE" \
  --preparation-instruction "$PREPARATION_INSTRUCTION" \
  --pure-output-bytes 268435456 \
  --read-access "$CURRENT_INPUT_ACCESS" \
  --attempt-dir "$PROPOSAL_ATTEMPT" --progress-file "$PROPOSAL_PROGRESS"
```

The command returns `PREPARED_REVIEW_REQUIRED` and the canonical `proposal.json` path.
It derives candidates from the complete original task, receipt, contact and nested-work census.
It retains original `BEGUN` and `UNKNOWN_COMPLETION` states, exact prepared inputs, source bindings and missing-control observations.
It excludes completed acquisitions and refuses candidates with retained native returns, products or incomplete dependency custody.
The original exclusive run lock, current access and final byte checks remain required.

The proposal grants no execution and adds no independent observations.
Preparation changes no original task, attempt, output allowance or scientific denominator.
The proposed output allowance concerns later PURE calculations only.
The command cannot recover, dispatch or retry tasks, and accepts no `--yes` option.
Original uncertainty remains part of the scientific account even if separately authorized work later completes.
Review the exact candidates and their retained obstructions before selecting any separate execution.
The separate command below consumes this proposal only with an explicit execution selection.
Ordinary no-reacquisition recovery still refuses these contacts.

## Select a separate native continuation

This route supports incomplete E4 development response and continuation tasks from the preceding proposal.
It requires retained completed work and the recorded PURE output refusal.
Keep the original profile, worker count, frozen worker installation and current input access.
Select the accepted replacement controller and retain a separate execution instruction.

First validate the exact proposal without execution:

```sh
"$REPAIRED_CLI" \
  --project-root "$REPAIRED_SOURCE" --operator-profile "$PROFILE" \
  campaign experiment-continue-native --authoring-dir "$E4_CHILD" --run "$E4_RUN" \
  --proposal "$CONTINUATION_PROPOSAL/proposal.json" \
  --execution-instruction "$EXECUTION_INSTRUCTION" --workers 8 \
  --read-access "$CURRENT_INPUT_ACCESS" \
  --attempt-dir "$VALIDATION_ATTEMPT" --progress-file "$VALIDATION_PROGRESS"
```

The default returns `EXECUTION_SELECTION_REQUIRED` and starts no task.
It publishes no continuation record or recovery index.
Examine the exact original incomplete attempts, retained successes, proposed separate attempts and PURE output allowance.
After an explicit execution selection, repeat the command with `--yes` and new attempt and progress destinations.

The confirmed command preserves the original run, task configurations, scientific inputs, numerical sources and independent-unit denominator.
It gives each proposed incomplete case one separate attempt with disjoint native contact, invocation, nested-work and receipt custody.
The original `BEGUN` or `UNKNOWN_COMPLETION` state remains unchanged and appears beside the later result.
Completion of a separate attempt does not prove that an uncertain original call never occurred.
Completed original tasks retain their original candidates and receipts.
Other uncontacted native tasks remain subject to their original execution and input-access requirements.

The PURE output selection covers unfinished calculations of the recorded resource-refused capability.
It changes no native budget, input edge, memory reservation, scientific threshold or future programme phase.
Current source, exact proposal bytes, original custody and the exclusive run lock remain required.
Changed original controls, retained native returns, unreceipted outputs or another selected repair refuse activation.

Repeat the exact confirmed selection to resume the same additional index.
This grants no second attempt after another uncertain contact.
Use the compatible reader to retain both original uncertainty and the continuation result.
Software acceptance and successful execution establish no scientific qualification.

## Repair a failed PURE development structural child

Use this route when E4 development acquisition completed but every structural measurement failed with a known value error.
The original structural terminal must retain those failures and their unstarted dependants.
Successful structural outputs, uncertain attempts, native contacts and other failure classes refuse this route.

Select a separately installed corrected source and the original operator profile.
The source guard preserves the kernel, numerical implementations and dependency lock.
It permits the structural access-label correction and documented programme metadata changes.
The corrected diagnostic record retains sealed ancestry with development visibility.
Current original-input permission remains mandatory.

```sh
"$REPAIRED_CLI" --project-root "$REPAIRED_SOURCE" \
  --operator-profile "$OPERATOR_PROFILE" \
  campaign experiment-repair-structure \
  --authoring-dir "$E4_DEVELOPMENT" \
  --repair-instruction "$OWNER_INSTRUCTION" \
  --workers 8 --yes \
  --attempt-dir "$ATTEMPT_DIR" \
  --progress-file "$PROGRESS_FILE"
```

The owner derives a separate structural directory from the original custody, corrected source and retained instruction.
It reuses the exact original preparation, scientific graph, configurations and input bytes.
The ordinary compiler derives the new run and its complete task census.
No native acquisition repeats, and the repair adds no independent observations.
The original failed child, source, terminal and attempt events remain unchanged.

Retain the returned `structural_authoring_dir` and `structural_repair` record.
Repeat the same instruction and source to resume that child through its existing attempt budget.
The ordinary E4 readers authenticate both the failed predecessor and selected replacement.
After successful structural completion, use the [completed-E4 handoff](#continue-after-completed-e4-development-under-a-repaired-installation).
An operational failure does not establish scientific nonentry or qualification.

## Deliver the retained scientific products

Copy [the product export selection](product-export.example.json), replace its
unwritten programme identity with the exact `programme` identity returned by
the completed operation or `experiment-read`, and choose a new delivery directory outside the original
programme. The default operational read supplies this identity without retrospective reconstruction.
This operational selection changes no scientific protocol, result
or independent unit. Prepare it with consumer `matrix-programme-product-export`:

```sh
uv run --no-sync empirical-lawhood config prepare \
  --consumer matrix-programme-product-export --config "$COPIED_EXPORT_SELECTION" \
  --output-file "$EXPORT_SELECTION"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" \
  --catalog-relative-path "$PROGRAMME_CATALOG" \
  --scientific-reconstruction full campaign experiment-export-products \
  --authoring-dir "$PROGRAMME_AUTHORED" --selection "$EXPORT_SELECTION" \
  --programme-request "$PROGRAMME_REQUEST"
```

`PROGRAMME_CATALOG` is the actual retained catalog path relative to the selected profile's scientific scratch.
Retain the programme's catalog selection for reads and export; do not guess a new path from an example.
For an installed reader, `PROJECT_ROOT` is its matching source distribution.
The catalog default is the legacy repository catalog, which requires a Git worktree.

Omit `--programme-request` only when original retained authority selections
suffice for the actual entered phases. This command produces the full scientific report and its delivery in one authenticated reconstruction.
When both outputs are required, run this command directly without a preceding full `experiment-read`.
Export applies the ordinary scientific readers and current protected access checks.
It does not derive inputs, author, recover,
issue, reveal or acquire. An unavailable result stays unavailable.

The delivery contains one `products.json` with the original programme report
and its phase reports once, retaining their exact encoded sizes and SHA-256.
The command returns its `path` and a `programme_readout` locator with the report digest, size, state and reconstruction scope.
Read the report at `/value/programme_readout/report` in that file.
Require `scientific_reconstruction=full`, `read_scope=FULL` and `state=COMPLETE` for a complete integrated scientific report.
An export with reconstruction disabled does not establish that scientific completion.
Its complete phase census retains conditional
nonentry, missing observations, adverse results and original denominators.
Scientific products retain their original producing run, task and receipt,
logical identity, physical materialization and publication custody. Operational
products and provenance metadata remain separate. A metadata reference alone
does not certify payload validation or scientific completion.
Product entries point to the complete manifests in `evidence_references`.
The programme report carries the design and input commitments; those bodies
are retained once.

Full export saves each completed phase report under `checkpoints/` in the selected delivery directory.
It saves the completed programme report before it assembles the delivery census.
The aggregate checkpoint references exact saved phase reports instead of duplicating their bodies.
Execution censuses retain exact encoded-size and digest bindings.
The final delivered report still contains the complete phase reports.
These operational checkpoints retain original access classes and exact source, input, execution and byte bindings.
`STAGE_COMPLETE` describes one saved stage. Its `export_status` remains `IN_PROGRESS`.
A checkpoint does not establish a complete export or portable copy.

After an interruption, repeat the same command, selection and installed source to reuse those stages.
The reader authenticates current execution records, protected access, original publications and every saved input digest before reuse.
When all bound initial phases and the matched E4 revision have checkpoints, delivery uses recorded lineage.
It restores those reports and consumes the original receipted fit and freeze without reopening full predecessor or DEV reconstruction.
Incomplete and other phase frontiers retain their ordinary readers.
Changed source, inputs, grants or checkpoint bytes refuse reuse.
One format migration accepts the exact first-version checkpoint writer.
It also permits one exact local-report exclusion update, identified by both source digests.
Every other package member, the lock, runtime and operation bindings must remain exact.
Relocated numerical libraries must retain identical bytes and all other runtime fields.
Their original and current files are rechecked before final delivery.
The migrated aggregate retains the original checkpoint source identities.
This exception permits no scientific-calculation or numerical implementation change.
Its byte-pinned transport repairs also share the live grant scope and already
authenticated file census. They preserve current access before protected reads
and the complete final byte check. Reloading another saved phase does not require
rehashing the same immutable inputs again within that read.
The command returns reused stage names in `reused_export_stages`.
Predecessor authentication remains mandatory and can still repeat its required scientific reconstruction.
No completed or uncertain native contact repeats.

The selection above creates a reference package. Native arrays stay in their original custody.
Reopening references
requires the recorded original artifact root and applicable current protected
access. Preserve those products, receipts, sidecars and publication commits with
the delivery. Export checks exact scientific-product and receipt bytes,
original metadata and current grants before and after atomic publication.
It creates no freshness or qualification claim. A late source or grant refusal
can leave published bytes; inspect that custody before retrying.

For a portable copy, use [the portable export selection](portable-product-export.example.json)
with the same `experiment-export-products` command. Prepare it with consumer
`matrix-programme-portable-product-export`. Select the actual programme, reference
directory, guarded replica root, receipt path, and positive byte and file limits.
The example contains unwritten identities and storage selections.

Create the empty replica directory on your selected mounted storage first.
Keep it outside the original artifact root, with the original logical
`storage_root_id`. Select a new receipt path outside both custody roots.
The storage owner checks the mount, free space, containment and complete copy bounds.
On first entry, it refuses existing target files.
Before copying, it saves an exact operational plan beside the selected receipt, with suffix `.progress.json`.
Repeat the same command to resume that plan after an interruption.
The owner verifies existing complete files and copies only the missing files.
It restarts its own unpublished partial files and refuses changed complete files or unexpected paths.
It never overwrites original evidence.
The selected bounds still apply to the complete copy. Free-space admission uses the remaining bytes.

With `--scientific-reconstruction full`, the export performs the full scientific read under current access.
It copies actual receipted outputs, including native NPZ arrays, their producing
receipts, complete atomic publication batches, and the programme reference report.
Every copied file retains its original bytes, relative path and storage namespace.
The separate replica receipt records the actual destination and complete checksum census.
Only `portable_replica.status=COMPLETE` establishes that this byte copy finished.

Metadata-only references remain references; the copy does not grant access to
their bodies or create a self-authorizing execution environment. Current grants
are checked during copying. A changed source, revoked grant or copy failure
leaves visible partial files without a COMPLETE replica receipt. Preserve that
failed attempt and its complete copied files. Resume only the unchanged copy plan under current access.
If exact reuse is refused, resolve the diagnosis before selecting a separate destination.
Portable custody creates no new scientific qualification, freshness or permission.

The direct TRAIN directory still supports its ordinary bank-export selection
for bank consumers. The outer programme export uses the programme selection
above and includes every entered phase.

The original E6 model and radius are never refitted or recalibrated. Both
reserved regimes retain the complete acquisition denominator, fixed
comparators, native functional errors, simultaneous coverage, admission,
delivered service, joint service and unresolved false-admission risk. See the
[selected E5/E6 guide](../matrix-selected-revision/declarative-guide.md),
[initialization](../matrix-selected-revision/initialization-guide.md),
[configured E3](../matrix-response-experiment/configured-protected-v2-guide.md),
[selected E4](../matrix-selected-e4-protected/guide.md) and
[prepared-source assembly](../matrix-response-experiment/prepared-source-assembly.md)
for the scientific contracts and genuine prerequisites.

The amended family retains eight primary slots at `1/160` each.
E1 retains eight PRIMARY-Y cells with noncoverage `1/1280` each and each tail `1/2560`.
Under amendment 2026-10-25.1, E4 tests the fixed SR/BR whole-group continuous-curve
loss comparison within its single slot. K-loss remains a secondary readout.
Calibration alpha `0.05` is separate. Unavailable slots receive no redistributed
allocation. The [scientific specification](../../records/matrix-programme.md#exact-grid-allocations-and-primary-family)
lists every question and its exact criterion. Structural diagnostics add no
primary allocation or scientific authority.
