# Configuration

This guide explains copied inputs and their consumer contracts.
It separates editable selections from immutable scientific evidence.
Use the selected consumer to validate and prepare a copied input.

Configuration validation reads one bounded input through its declared parser or typed constructor.
It runs no simulator, source acquisition, external census inspection or provider construction.
It opens no catalog and grants no authority.

The [workflow index](../reference/workflows.md) identifies the relevant guide and
input role. The closed [configuration inventory](../../src/empirical_lawhood/resources/config_schemas/index.json)
lists the supplied inputs supported by the configuration commands, their root
schema IDs, the operator storage and FAIR-MAST source configs, and the human
provenance YAML template. Workflow declarations also identify protocol-specific
selectors and helper files consumed through their documented owning commands.
These are consumer-specific contracts; an object with a `schema` field is not
automatically an editable experiment input.

Experiment explain reports and generated configuration schemas include registered
`configuration_capabilities` where an implemented method fixes part of a selection.
For configured Matrix paired15 measurement, the primary description, primary
horizon and target discrepancy tolerance are selectable. The registered capability
fixes q=2, matrix dimension 4, the complete fifteen-endpoint geometry, numerical
views, timesteps, actions, cadence and measurement rule. Schemas mark these fields
as fixed capability facts and retain them as required canonical fields. Changing
an unsupported fact refuses in the typed owner before acquisition; a future
capability must implement and validate any additional scientific scope.

For recursive development authoring, `author_recursive_wave` accepts either the
existing `contribution_dir` or an explicit nonempty `contribution_dirs` tuple.
The selected directories must authenticate exactly the draft's sorted parent
manifest tuple. Multiple parents require complete `RecursiveInputOrigins`, with
each contribution operand bound to its own parent, product, producing receipt,
digest and permitted role. Independent source operands retain their source role;
parent-produced outputs cannot be supplied as sources. The consumer's registered
scientific contracts still decide whether each original scope is admissible.

Installed experiment protocols use `load_experiment_specification` and
`load_experiment_inputs` with the shared
[`ExperimentProgrammeService`](../../src/empirical_lawhood/api/experiment_programme.py).
When selected inputs inherit protected outcomes, construct the selected artifact
plane before loading them and pass the same current read-access selection through
preparation, derivation, authoring and export. The installed protocol authenticates
its original locators and refreshes current access before protected record reads,
FILE hashing and publication. Plain public inputs retain their ordinary loader.
The [Matrix E1–E6 programme](../../programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md) is a finite
selection of installed component protocols, exact original input bindings and
receipt locators. Its current execution context remains in the existing service.
It stores no scheduler state, completion flags or scientific permission.
The Matrix scientific inputs keep three different stages explicit:

- `matrix-programme-scientific-design` records the complete selected mathematics,
  populations, recipes, comparisons and decision rules before allocation.
- `matrix-programme-allocation-request` selects the actual exposure census,
  distinct source/future stream materials, original FILE operands and metadata
  resources. A new seed label does not establish freshness.
- `matrix-programme-input-commitments` binds actual prospective publications for
  every phase, including E5 DEV/CONF, concrete whole-group revision folds and the
  original E6 policy. Fitted models and later nomination results are separate
  products and cannot replace those original inputs.

Use `config validate` or `config prepare` with those consumer names for copied
inputs. Canonical validation checks the declared values; ordinary derivation
and entry authenticate the referenced publications and complete source joins.
Compact [native/source selections](../../programmes/foundations/emergent-structure/workflows/matrix-response-experiment/input-assembly.md)
bind large immutable original records once through ordinary canonical roles;
request-only examples report the missing originals explicitly.

Canonical-only sources retain their original `ExperimentInputSelection` format.
For original data files, use
[`ExperimentFileInputSelection`](../../src/empirical_lawhood/planning/experiment_inputs.py)
with canonical record bindings and file bindings in one exact selection. Each
file declares its original `ArtifactIdentity`, codec revision, relative path and
byte bound. Every member must lie beneath the selection's real parent directory;
symlinks and parent traversal refuse. Choose a common source directory when
binding files from several subdirectories.

The protocol declares its permitted record types and installed storage codecs.
The loader hashes files in bounded chunks without converting their original
bytes. Domain preparation derives the complete external census and establishes
scientific compatibility; authoring reauthenticates the selected paths through
existing custody. A file handle creates no outcome-access or source authority.
The [Matrix input assembly guide](../../programmes/foundations/emergent-structure/workflows/matrix-programme/input-assembly.md)
uses this route for current D, exposure census, NPZ inputs and the exact
normalization source before publishing C.

The installed [battery obstruction programme](../../programmes/energy/battery-charging/workflows/battery-obstruction-reassessment/guide.md)
uses canonical source, portable parent manifest and original-custody selections.
Its registered binder receives authenticated record locations and derives the
parent directory, explicit SOURCE/MODEL origins and immutable instance. Shared
authoring authenticates the existing portable parent; domain custody validation
joins typed manifests to original sidecar bytes and rechecks the original
UNKNOWN state. Preparation does not read the large supplier payload.

## Operational artifact verification

The public workflow defaults to `artifact_verification: reduced`.
This operational setting changes repeated artifact checks within one invocation.
It changes no scientific record, storage identity, source requirement or authority.

Copy [the operational example](../../configs/operational.example.yaml) to an explicitly selected working directory.
Select `reduced` or `strict` in its `value.artifact_verification` field.
Validate the copy with consumer `operational-configuration`.
Put the optional global selection before the command group:

```text
empirical-lawhood --operator-profile /absolute/work/operator-profile.json --operational-config /absolute/work/operational.yaml campaign experiment-read --authoring-dir /absolute/programme
empirical-lawhood --operator-profile /absolute/work/operator-profile.json --artifact-verification strict campaign experiment-read --authoring-dir /absolute/programme
```

The flag overrides the copied configuration.
Without either selection, the mode is `reduced`.
The invocation report records the selected mode separately from scientific results.
The API accepts the same selection through `create_api(artifact_verification="strict")`.

Reduced mode authenticates first-use bodies, sidecars and complete atomic publications.
It reuses registered format proofs within the current invocation.
The bounded proof cache retains identities and small header facts, without scientific payloads or access decisions.
Cache eviction restores the ordinary checks.
Repeated read checkpoints inspect guarded paths, file metadata and current access.
Publication, worker delivery and the final read boundary retain full byte checks.
The final read boundary covers the complete observed census, including consumer refusal.
Worker inputs retain their fresh sealed copies.

Same-size changes with preserved timestamps can escape an intermediate reduced checkpoint.
Persistent byte changes still refuse at the final boundary.
Reduced mode does not provide continuous byte authentication.
Strict mode retains full hashing at intermediate checkpoints.
Custom custody policies retain their existing eager checks.
Kernel validation, scientific operands, complete denominators and resource controls apply in both modes.

## Optional retrospective scientific reconstruction

Retrospective reconstruction defaults to `scientific_reconstruction: 'off'`.
This choice is independent of `artifact_verification`. Matrix continuation,
authoring, execution, recovery and status read actual execution records and the
retained products required by the next task. They do not reconstruct completed
predecessor computations or produce exhaustive scientific reports by default.
Original outputs, complete task receipts, current access checks and new task
computations remain required. Operational completion does not establish a
scientific result or qualification.

Select `scientific_reconstruction: full` in the copied operational configuration,
or place `--scientific-reconstruction full` before the command group:

```text
empirical-lawhood --project-root /absolute/reader-source --operator-profile /absolute/work/operator-profile.json --catalog-relative-path retained-programme/catalog.sqlite3 --scientific-reconstruction full campaign experiment-read --authoring-dir /absolute/programme
```

The CLI flag overrides the configuration. The invocation records both choices.
An operational configuration at record version `1.0.0` is read with reconstruction
off; its original bytes remain unchanged. New configurations use version `2.0.0`.
Full reconstruction performs the original scientific read and exhaustive report
under current access. It can be substantially more expensive than operational
status. Use it explicitly for an integrated scientific report.

## Output reservations and actual storage

Output reservations are advisory for storage admission.
A task ceiling limits its actual output. It does not predict its final size or scratch requirement.
Execution does not require free space for the complete reservation or the largest task allowance.
Retained invocations report the task count, declared output allowance and zero additional reservation-based storage floor.

The operator profile still selects a free-space floor.
The actual mount, write access and storage checks remain active at guarded I/O boundaries.
Actual storage exhaustion can stop a write and leaves its original recovery records intact.
Frozen plans, task ceilings, source requirements and input access remain unchanged.

The global `--allow-output-reservation-overcommit` flag remains accepted for command compatibility.
It does not change storage admission or require a retained invocation.

## Explicit metadata RSS allowance

The global `--metadata-rss-limit-bytes` option selects a positive byte allowance for Matrix controller RSS checks.
Select a retained invocation destination and choose an allowance suitable for the actual host and concurrent work.
The invocation records the selected allowance, each original limit and the effective limit.
Without the option, each original metadata RSS limit applies.

This operational selection changes only current-process RSS admission at Matrix metadata checkpoints.
It preserves canonical resource records, native task budgets, payload byte bounds, current access and final custody checks.
The controller still measures RSS and refuses a value above the selected allowance after reclaiming unused pages.
The allowance is not a peak-memory guarantee or scientific authority.
It expires with the invocation.

## Retained storage access selections

For protected experiment inputs, repeat `--read-access` with the original locator
files described in the owning [input guide](../../programmes/foundations/emergent-structure/workflows/matrix-response-experiment/input-assembly.md).
The installed protocol requires its complete locator roster and checks actual
stored grants at each read boundary. This selection carries current access for
the operation; it grants no authority and changes no scientific identity.

The optional global --artifact-root-contract input is a typed ExternalRootContract
for **current operational access** to retained evidence. Its logical storage ID
comes from the selected original publication namespace. It does not rewrite or
assert the original historical physical contract, migrate data, install trust,
or grant execution or outcome access.

Validate a copied selection with consumer operator-artifact-root-access.
The actual storage owner compares every physical field with the operator profile:
canonical artifact path, required mount, free-space floor, device and volume
constraints, filesystem types and profile schema must agree exactly. Only logical
name and storage ID may differ. Mount, containment and original publication and
receipt checks still apply. An absent selection keeps the profile-derived ID.

Select the actual retained root or a verified replica and its explicit current access contract when recovering read-only original evidence.
Choose writable external destinations for new receipts, operational controls, catalogs and reports. Programme run/read/recover use the same root and installed
storage codecs. Fresh legacy authoring-directory compositions refuse this
optional override; use their original profile-derived route or the experiment
programme route.

## Validate and prepare a copied input

For the portable [RC ladder](../../programmes/foundations/measurement-and-response/workflows/rc-ladder-response/guide.md), use a
fresh working directory outside the checkout.
Select an existing external work directory with write access and sufficient space.
Replace `/absolute/external/work` below with that directory.
Run from the selected checkout and locked main environment described in [environments](environments.md).

```bash
WORK=$(mktemp -d /absolute/external/work/config.XXXXXX)
cp programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json "$WORK/model.editable.json"
# Edit the copy; whitespace and property order may change.
uv run --no-sync empirical-lawhood config validate \
  --config "$WORK/model.editable.json" --consumer rc-ladder-model --format json
uv run --no-sync empirical-lawhood config prepare \
  --config "$WORK/model.editable.json" --consumer rc-ladder-model \
  --output-file "$WORK/model.canonical.json" --format json
uv run --no-sync empirical-lawhood campaign rc-ladder-native-check \
  --config "$WORK/model.canonical.json"
```

`validate` reports the input's SHA256, selected consumer, disposition, typed
validity, canonical SHA256/size when applicable, and consumer byte readiness.
Valid values can require preparation because an exact-byte consumer rejects
formatting changes. A consumer using the authoring codec can already read a
pretty document, provided it fits that consumer's own byte ceiling.

`prepare` writes only an explicitly selected **new file** under an existing real
directory. It refuses overwrite, in-place conversion, symlinks in input or output
paths, and parent-directory traversal. It preserves the input file and reports
the original and prepared byte hashes. It does not update source hashes,
approvals, assignments, seed labels or exposure claims. An edited scientific
value changes the relevant configuration identity.

Unchanged pretty RC and Brian2 JSON copies prepare to the exact supplied
canonical bytes. Brian2 execution still requires its separate environment;
validation/preparation use the main environment without Brian2 execution.
Do not add `$schema` to an input envelope or convert tagged Decimal values to
binary numbers. These are closed records:

```json
{"decimal": "0.001"}
```

The exact Decimal string carries the value. In canonical records, duplicate keys,
bare fractional JSON numbers, nonfinite values, extra fields, wrong nested
schemas/revisions, and semantic constructor violations refuse. JSON Schema
does not replace these lexical and semantic checks.

Successful reports go to stdout. Validation/preparation refusals exit 2 and
write the chosen text or JSON error to stderr, leaving stdout empty. Click
option/usage errors also exit 2 with their ordinary stderr diagnostic.

## Consumer limits and dispositions

The `--consumer` selector names a closed input role. It must match the declared
schema; it is required whenever a schema has more than one registered role.
Schema text never selects a Python import or a native factory. Shared schema
IDs can serve multiple consumers with different limits or preparation rules.
Unknown roots, issued/authority records and opaque
plan/design files have no fallback parser in this interface.

Prospective authoring selects the smallest installed profile that admits the
measured scientific selection and retained members.
Scientific payload capacities remain 16, 32 or 64 MiB.
The separate `draft128` profile admits a 128 MiB draft with a 64 MiB scientific payload.
It retains the template and other member bounds of the 64 MiB profile.
Both profiles admit the existing 256 MiB v4 operational carrier.
These operational byte allocations do not limit scientific populations.
Existing retained packets keep their original decoder and carrier contracts.
A larger advertised file size cannot upgrade them.

New prospective authoring checks both `preissue-run-plan.json` and
`preissue-execution-plan.json` against the selected artifact custody allowances
before publishing the final packet. Operational plan reads use those allowances
and a stable descriptor; their canonical decoder uses the actual byte count.
The default `None` allowance adds no arbitrary size ceiling.

The separate selected-source manifest and source observation use the same
selected control-record and in-memory payload allowances. Source capture checks
both rendered members before compilation or publication when a writer is
selected. Their publisher checks the complete pair before writing either
member. Readers authenticate publication custody and the exact declared size
before reading companion payloads, then decode the authenticated original bytes.
An explicitly selected smaller allowance refuses before payload allocation;
file growth, truncation, replacement and digest changes still refuse.

These operational selections do not change historical canonical records or
their versioned scientific decoder allocations. The large historical
retained-member decoder keeps its 512 MiB physical allowance. Authoring,
candidate and campaign-package capacities, schema checks and nesting/node
bounds keep their separate contracts. Custody allowances are defined in
[artifact contracts](../../src/empirical_lawhood/runtime/artifacts.py), with producer
checks in [prospective authoring](../../src/empirical_lawhood/api/recursive_prospective_authoring.py).

Operational attempts write the complete JSON report after rendering it,
including its final newline, with an allocation equal to the encoded byte count.
Input, package, receipt and scientific array contracts retain their separate
limits. Actual I/O failures are retained as `EXPORT_FAILED`; inspect custody
before further execution.
The [results guide](results-and-failures.md) distinguishes export failure from incomplete scientific work.

Canonical output must fit the existing consumer's limit. Editable input has a
separate ceiling of four times that limit, capped at the existing authoring
codec's 128 MiB maximum; retained imports still fit their original byte ceiling.
With an explicit consumer, the file is bounded at that role's authoring ceiling
before parsing. Automatic root discovery has a 128 MiB read ceiling and then
enforces the selected role's tighter ceiling. Existing nesting/node bounds also
apply. Decimal fixed-point expansion and total canonical output are bounded
before serialization. Extra whitespace does not relax the eventual consumer
limit.

| Consumer | Owning input/command | Consumer maximum | Disposition |
|---|---|---:|---|
| `recursive-inquiry` | `campaign recursive-author`; partial draft explanation | 8 MiB | Editable typed programme; selected path closure and evidence roles remain explicit |
| `recursive-prospective` | `campaign recursive-author`; prospective specification explanation | 16 MiB | Editable typed prospective specification; exact source, assignment, parent roles and separate issue/execution/reveal gates remain required |
| `rc-ladder-model` | `campaign rc-ladder-native-check` | 64 KiB | Editable; exact JSON consumer |
| `rc-ladder-study` | `campaign circuit-author` study | 128 KiB | Editable; exact JSON consumer |
| `brian2-current` | `campaign brian2-native-check` | 16 KiB | Editable; exact JSON consumer |
| `electron-gas-reference` | `campaign electron-gas-reference-check` | 32 KiB | Editable; exact JSON consumer |
| `lattice-method-authoring` | `campaign synthetic-material-author` | 128 KiB | Editable; exact JSON consumer |
| `reactor-fresh-profile` | `campaign reactor-author` profile | 64 MiB | Editable; exact JSON consumer |
| `reactor-assigned-profile` | Assigned exposed profile, same authoring owner | 64 MiB | Retained exact bytes; preparation forbidden |
| `matrix-response-authoring` | `campaign matrix-response-author`, route in input | 1 MiB | Editable authoring record |
| `reaction-development` | `campaign reaction-response-native-check`, backend in input | 32 KiB | Editable authoring record |
| `tokamak-heat` | `campaign torax-native-check` | 32 KiB | Editable authoring record |
| `material-control-input` | `campaign material-workflow-input-check` | 32 KiB | Editable authoring record |
| `battery-development`, `grid-development`, `tokamak-control` | Their native-check guides | 16 KiB | Editable authoring records |
| `propulsion-reference`, `scale-morphism-reference`, `glenn-import-selection` | Their reference/import-check guides | 16 KiB | Editable authoring selections; external inputs uninspected |
| `reactor-batch-input`, `reactor-prepared-input` | Reactor input-check commands | 16 KiB | Editable development selectors |
| `prepared-canary`, `prepared-dependent-input` | Prepared native/dependent input checks | 16 KiB | Editable development selectors; parent/custody uninspected |
| `finite-canary`, `finite-calibration-input`, `finite-stage-input` | Finite native/input/stage checks | 16 KiB | Editable development selectors; stage/parent checks remain with owner |
| `response-composition-input` | `campaign response-composition-input-check` | 16 KiB | Editable analysis selector; operands uninspected |
| `operator-storage` | Operator profile, used by doctor/guarded commands | 128 MiB | Editable deployment record; no mount access or authority |
| `fair-mast-selection` | `source acquire --source-config` and source preview | 64 KiB | Editable selection; exact JSON consumer; no acquisition |
| `prepared-prior-census` | `matrix-response-author --prior-inspection` | 64 MiB | Retained import; owning `_prior_census` parser only |
| `finite-prior-census` | Finite input check `--prior-exposure` | 128 MiB | Retained flat import; owning `_census` parser only |
| `exposed-inventory` | Supplied example documentary inventory | New 64 KiB shape-check ceiling | Helper shape only; member hashes/custody not authenticated |
| `evidence-provenance-template` | `configs/templates/evidence-provenance.yaml` | No consuming limit | Human template; runner validation/preparation unsupported |

YAML is accepted only for the editable roles whose consuming command already
uses the restricted authoring codec. Exact JSON consumers and retained imports
stay JSON-only. The existing safe YAML grammar refuses anchors, aliases,
explicit tags and duplicate mappings; quote Decimal text. Preparation returns
canonical JSON and leaves the YAML input unchanged.

The prepared census example shares the larger inspection record's schema ID but
contains only the fields consumed by the historical import reader. It is **not**
decoded as that larger canonical inspection record. The flat finite census has
its own import envelope. Import schemas retain the owner's extensible metadata
fields, and the tool never sorts, rewrites or normalizes imported evidence.
Successful import validation only establishes the owning census parser's
acceptance; it does not establish complete history, authentic custody or fresh
units. Held, assigned, issued and authority inputs cannot be repaired through
general preparation.

## Offline editor schemas

Export the installed resource for your copied RC input:

```bash
uv run --no-sync empirical-lawhood config schema \
  --schema-id empirical-lawhood/adapters/simulators/rc-ladder-response/resistor-capacitor-ladder-model-config \
  > "$WORK/rc-ladder-model.schema.json"
```

For a root shared by several registered consumers, supply `--consumer` to export
that role's exact record revision. The recursive inquiry request root is shared
by `recursive-inquiry-decision`, `recursive-inquiry-decision-v2`, and
`recursive-inquiry-decision-v3`; each exports its corresponding historical or
current structural contract. An omitted, unknown, or mismatched consumer refuses
an ambiguous export. This selection grants no current admission or authority.

Associate the schema outside the scientific payload. For example, VS Code
workspace settings can associate the copied filename with the local export:

```json
{
  "json.schemas": [
    {"fileMatch": ["model.editable.json"], "url": "./rc-ladder-model.schema.json"}
  ]
}
```

Every projection declares Draft 2020-12 and uses local `$defs` references. No
network resolver is needed. Projections include required fields, nested exact
envelopes/revisions, enums, nullable values, integer/boolean distinction, tuple
shapes, closed tagged Decimal objects and explicit unit metadata for declared
unit suffixes. Constructor defaults do not make serialized fields optional.
Schema structural acceptance does not imply canonical byte spelling, duplicate
key safety, valid dimensions/clocks, scientific qualification or authority.
JSON Schema can accept an integer-valued numeric token such as `4.0`; the
runtime's canonical JSON parser still rejects that lexical spelling.

Library users can read/export resources without a checkout:

```python
import json
from empirical_lawhood.api.configuration_schemas import configuration_schema

schema = configuration_schema(
    "empirical-lawhood/adapters/simulators/rc-ladder-response/resistor-capacitor-ladder-model-config"
)
print(json.dumps(schema, indent=2))
```

The installed wheel contains the schema resources and inventory, not the
checkout's experiment inputs. Supply your own copied input. The API entrypoints
are `validate_configuration(Path(...), consumer=...)` and
`prepare_configuration(Path(...), Path(...), consumer=...)` in
[configuration.py](../../src/empirical_lawhood/api/configuration.py).

Maintainers change the closed registry/type owners, regenerate with
`python scripts/generate_config_schemas.py`, and check drift with
`python scripts/generate_config_schemas.py --check`. Unsupported annotations fail
generation; they never become unconstrained schemas. The schema acceptance
tests use an offline Draft 2020-12 validator from the development environment.

The [recursive inquiry examples](recursive-inquiry.md) are
owned by `scripts/generate_recursive_examples.py`. It reconstructs the original
RC protocol and two separately frozen revisions, checks their exact scientific
fingerprints, and projects their explicit operation drafts. It also supplies the
partial materials programme and exposed battery supplier investigation. These
frozen files retain their original finite graph allowances and exact canonical
identities. The generator applies those historical values locally; current draft
builders use unrestricted graph defaults. Run the generator and its `--check`
mode in the selected locked environment. Copy a draft to author a new design;
scientific results and contribution receipts retain their immutable identities.

## Current paper integration inputs

[Current integration guides](paper-study-workflows.md) add explicit purpose/seed/split allocations, source requests and phase selections through the same inventory.
The inventory owns each consumer's exact limit, parser and preparation rule.
Use its consumer identifier when one schema has several roles.
The table above describes the established development selectors rather than every integration consumer.

Scientific protocol, editable selection, environment identity and retained evidence remain separate records.
Array operands carry exact byte identities and bounded member manifests.
Source and stage helpers derive object identities from authenticated selections.
Researchers need not fabricate manifests or grant hashes.
Configuration preparation does not acquire arrays, replace fixed protocols or refresh source bindings.

The [configured matrix guide](../../programmes/foundations/emergent-structure/workflows/matrix-response-experiment/configured-protected-v2-guide.md#receipt-bound-reconstruction-of-retained-train-banks)
defines optional receipt-bound export adoption and a separate historical-input
metadata selection. These explicit inputs preserve the original producer and
future response commitments. They do not authorize changed-source workers.

The [Matrix programme continuation](../../programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md#continue-after-a-source-change-before-train)
has a separate `matrix-programme-source-continuation` consumer. It selects an
actual original programme publication and a disjoint new home. Its public
deriver requires completed E1/E2 and wholly unentered original TRAIN/later
custody, and creates a `matrix-continued-programme` specification with a
mandatory handoff identity. Scientific design and allocations stay unchanged;
remaining workers still require current source and authority admission.

The [prospective curve amendment](../../programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md#apply-the-prospective-curvemechanism-amendment-before-train)
uses `matrix-programme-curve-amendment` and produces a
`matrix-curve-amended-programme` specification. Its exact exposed-analysis
file selections and superseded continuation handles are mandatory parts of
the selected change. The new target requires its amendment publication on
reopening; the original allocation census, native selections and historical
E1/E2 remain unchanged. This explicit scientific change cannot be passed to
the source-only continuation consumer.

Current matrix source configurations bind the exact selected dependency lock and complete package bytes.
Prepare a new configuration when either binding changes.
Native APIs require the explicit selected project root before numerical contact.
Producing provenance is immutable completion evidence, separate from editable allocation or configuration.
Its observed environment and working-source inventory do not create scientific authority.
Changed serialized source and result contracts use explicit record versions; original records remain unchanged.

Before native TRAIN, authenticate its exact allocation, future reservations, E6 policy and all four response selectors.
A changed candidate requires its own current candidate-bound acts through the existing authority owners.
Original candidate approvals do not authorize changed scientific operands.
Current source admission verifies the selected committed bytes and records checkout status separately.
Untracked plan documents do not waive tracked source checks.

A current wrapper around frozen OriginalF or the 48-root nomination preserves its original numerical bytes and provenance.
It does not upgrade their evidence status.
Retained result, current parent, import-publication and fixed-operand records use their owning authentication APIs.
The public [history allocation](../../programmes/foundations/emergent-structure/workflows/matrix-history-analysis/guide.md) and [tangent configuration](../../programmes/foundations/emergent-structure/workflows/matrix-tangent/guide.md) expose actual numeric master inputs.
Changing a namespace leaves those numerical draws unchanged.

Public seed examples remain exposed.
Independent exposure checks use actually consumed numeric operands, including truncated generator seeds where applicable.
A role label, canonical bytes or passing schema establishes no freshness, scientific qualification or operational authority.
