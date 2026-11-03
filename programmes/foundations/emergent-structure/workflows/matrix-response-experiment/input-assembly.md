# Copied native TRAIN and finite-dt source inputs

The installed `matrix.response-error.native-training-input-assembly` route derives
TRAIN metadata from the complete original programme input commitment, **C**.
Its specification and request have one current authoring version, `3.0.0`;
the derived acquisition request remains version `3.0.0`. Assembly allocates no new
groups or streams and retains the original pre-TRAIN availability and E6 policy.

The [specification](native-training-assembly.example.json),
[request](native-training-request.example.json) and
[source selector](native-training-sources.example.json) illustrate the current
copied input shape. The specification's `replace-with-original`
commitment/publication fields are explicitly **unwritten descriptors**. They
validate the input shape but cannot authenticate, author or execute a programme.
Replace that complete handle with the actual published C and bind the
specification to C's exact candidate.
The [scientific protocol](native-training-scientific-protocol.example.json),
[assay](native-training-assay.example.json) and
[exposure census](exposure-census.example.json) remain disclosed scientific
input examples. Their streams and arrays cannot become fresh evidence by
renaming them.

The assembly specification selects C once. The whole-programme runner
supplies that specification from its original C selection; the operational
request contains no C handle. The source selector binds only `request`, a
`NativeTrainingAssemblyRequest`:

| Field | Required input |
| --- | --- |
| `record_id` | The selected request identity |
| `resources` | Explicit native operation budgets and worker count |
| `campaign` | The selected ordinary campaign; it grants no issue, execution or reveal authority |

C binds the immutable scientific design D, complete exposure census and audit,
actual producing provenance, scalar definitions and normalization source FILE,
and all twelve original input roles: E1, E2, TRAIN, E3 CAL/CONF, E4 DEV/CAL/CONF,
E5 DEV/CONF and both E6 reserves. It also binds the complete DEV revision folds,
actual preparation availability and original E6 transport policy. Fitted models,
calibration products and E5 nomination remain later results. The original
policy includes the four pre-TRAIN E3/E6 response selectors; it cannot be added
after fitting to repair an uncommitted transport design.

D contains the exact mathematical protocols, full physical coordinates,
numerical designs, scalar definitions, causal prefix policies, response assay,
E4 factorial/revision/nomination/structural choices, E5 recipes and complete
E5/E6 decision criteria. The assay includes the mechanical model, actions,
horizons, receiver count, template NPZ member contracts, numeric tolerances and
origin rule. Identical source/assay operands retain the per-root canonical
response bytes. Actual original custody, source eligibility, freshness and
sampling are checked separately.

The census must include the independently enforced mandatory exclusions and
every known acquired, exposed, reserved or uncertain effective stream, whole
group and physical regime. The mandatory floor alone is not a complete audit.
Historical audit bytes remain factual external evidence without requiring an
old executable implementation. A renamed group or refined timestep does not
create independent evidence or an unused physical regime.

Validate copied inputs with consumers `matrix-native-training-input-assembly`
and `matrix-native-training-assembly-request`. D, the allocation request and C
have separate consumers `matrix-programme-scientific-design`,
`matrix-programme-allocation-request` and `matrix-programme-input-commitments`.
The independent protocol, assay and census consumers remain
`matrix-native-training-scientific-protocol`,
`matrix-native-training-response-assay` and `matrix-factor-exposure-census`.
Use `config prepare` with the same consumer to canonicalize an edited copy
before binding its exact identity. Configuration validation checks the shape;
assembly reopens C's actual guarded publications and independently joins the
whole original design before producing TRAIN metadata.

Use ordinary `experiment-prepare`/`experiment-explain` with `--sources`.
A complete request reports `native-assembly.derive`; static preparation does
not open C, infer native counts or confer authority. Select the actual current
source snapshot, environment, guarded EL output, worker count and numerical
thread limits before derivation:

Set `$PROJECT_ROOT` to your selected checkout or matching installed source distribution.
Use the same explicit operator profile, source and storage selections throughout the commands below.

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$NATIVE_SPECIFICATION" --sources "$NATIVE_SOURCES" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4 \
  --metadata-directory "$NATIVE_METADATA" --output-selection "$NATIVE_METADATA/inputs/sources.json"
```

The result returns the actual `NativeTrainingAcquisitionSpecification` and
source selector for public author/run/read/recover. Its request seals exactly
seven original evidence pins: C, the four future selectors, preparation
availability and E6 policy. Derivation reuses C's original reservations,
streams, arrays and publication handles, starts no native task and creates no
scientific issue, human act or reveal grant. Exact retries retain those same
original inputs and availability.

A complete TRAIN64 result retains all 64 assigned roots and negative or
unavailable outcomes. Copy the [export selection](native-training-export.example.json)
and use `experiment-export-products` to publish authenticated feature/outcome
banks. The version-`2.0.0` export selection contains its record ID, bank ID and
relative output path. Select the actual authored directory with `--authoring-dir`;
the exporter returns its exact `native_training_locator` for downstream source
bindings. Export and exact repeated export acquire no additional data.

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-export-products \
  --authoring-dir "$NATIVE_AUTHORED" --selection "$NATIVE_EXPORT_SELECTION"
```

## Current access to completed original products

An original product's scientific identity and producing receipts stay frozen
when its reveal grant expires or is revoked. To select a valid replacement
grant for the same original, copy its existing locator and change only the
`reveal_authority` identity to the exact current grant supplied by the authority
owner. Do not edit the original publication, request, source selector or scope,
and do not change the original run, package, issue, execution, plan or product.
The copied locator creates no grant or scientific qualification.

Configured E3 product export writes `models.locator.json`,
`model-freeze.locator.json`, `calibration.locator.json` and
`calibrated-freeze.locator.json`; its report supplies their actual paths.
Copy all four into an explicitly selected EL directory. Each file retains the
existing `MatrixSelectedOriginalProduct` schema and revision. Edit the copies
with a JSON/YAML editor, using the actual current grant identity rather than
inventing a digest. The closed CLI codec reads these copies directly; no Python
construction or new permission record is required.

For a supported E3-derived development input, repeat `--read-access` once for
each of those four copied locators:

```sh
uv run --no-sync empirical-lawhood --project-root "$SELECTED_SOURCE" \
  --operator-profile "$OPERATOR_PROFILE" campaign experiment-prepare \
  --input "$DEV_SPECIFICATION" --sources "$DEV_SOURCES" \
  --read-access "$CURRENT_ACCESS/models.locator.json" \
  --read-access "$CURRENT_ACCESS/model-freeze.locator.json" \
  --read-access "$CURRENT_ACCESS/calibration.locator.json" \
  --read-access "$CURRENT_ACCESS/calibrated-freeze.locator.json" \
  --output "$PREPARATION_REPORT"
```

The same repeatable option is available on `experiment-explain`,
`experiment-derive-inputs`, `experiment-author`, `experiment-run`,
`experiment-read`, `experiment-recover` and `experiment-export-products`.
The selected specification or exact retained packet selects its code-owned
protocol before any copied locator is decoded. This distinguishes supported
protocols that use the same locator schema. Protected E4 structural reads use
the complete original `SelectedE4WaveLocator` roster instead of E3 product
locators. Mixed types, unsupported protocols or revisions, and incomplete or
foreign origin rosters refuse.

For a supported prepared protected owner, `--read-access` selects current access
to its original products alongside the new campaign's independent `--plan` or
`--run`, confirmation and `--reveal-authority-id` options. Original-product
locators do not supply that campaign's own issue, execution or reveal authority.
Composite requests and custody-only recovery cannot consume this option.

Input loading selects the actual artifact plane before opening copied records
or FILE bodies. Authoring, Ready, native contact and final scientific reads
retain their own current-access checks; a preparation report or earlier valid
read is not reusable permission. A completed `experiment-read` needs the
installed reader, its data, an explicit operator profile and any required
current access, with no producing checkout or source reconstruction. A current
`--artifact-root-contract` may select the original storage namespace while
retaining the profile's exact physical policy. Authoring, run, export and
recovery still select and authenticate their current implementation. Expiry of
the campaign's execution grant forbids a new Ready/native entry; exact retained
controls remain readable subject to the actual original-product and reveal read
grants. Each protected read and final verification checks those grants again.

This interface does not establish that every E1–E6 owner supports replacement
access, that an unentered structural stage has run, or that exposed data are
fresh. Inspect the complete retained result and each actual prerequisite.

## Current finite-dt source assembly

The separate `matrix.source.finite-dt-input-assembly` route derives protected
E4 CAL or CONF source inputs from the original whole-programme commitment C
and actual completed E3/native-TRAIN products.

The [finite-dt source specification](finite-dt-source-assembly.example.json),
[request](finite-dt-source-request.example.json) and
[source selector](finite-dt-source-sources.example.json) are disclosed,
unexecuted software input shapes. The specification and request have one current
version, `2.0.0`. The selector binds only `request`, a
`MatrixFiniteDtSourceAssemblyRequest`. It carries actual publication handles for
C, the configured E3 public package, its original preparation and response assay,
plus four original E3 producer locators: models, model freeze, calibration and
calibrated freeze. It also retains the exact native TRAIN locator, scientific
cutoff, computability evidence, metadata-only dataset envelope, key policy,
CAL/CONF phase and operational resources. Replace every unwritten example
publication or producer descriptor with its actual original custody.
Validate with consumers `matrix-finite-dt-source-input-assembly` and
`matrix-finite-dt-source-assembly-request`. A complete request reports
`finite-dt-assembly.derive`; static preparation does not open C, infer its group
census or authenticate the referenced original products.

Source derivation authenticates C and the complete original E3/native-TRAIN
products and producing receipts, then uses C's already committed E4 population
and scientific choices. It creates no new reservation or effective stream.
The example's `allow_metadata_key_creation` is false; the actual metadata key
must exist at its explicit guarded path, outside the publication directory.
Requester and approver must differ. Dataset metadata authorization uses the
existing issuer and policy. It does not perform scientific issue, human acts,
reveal or native acquisition.

Use `experiment-derive-inputs` with the source specification and selector,
current implementation/environment/four-worker choices, and select
`<SOURCE_METADATA>/sources.json` as output. The result reports its exact source
qualification specification and input paths for ordinary author/run/read/recover.
Exact retries reuse original committed controls and publications. Missing or
changed original receipts, incomplete TRAIN denominators, changed exposures or
missing metadata keys retain the owning refusal. Independent numerical controls
and the actual prospective source lifecycle still determine scientific standing.

The [E1–E6 programme](../matrix-programme/guide.md) composes these same transitions.
The [prepared-source route](prepared-source-assembly.md) supplies the separate
E5/E6 source premise; the E4 TRAIN certificate does not replace it. No example,
seed label, passing configuration or development receipt establishes freshness,
sampling, transport, qualification or outcome-access authority.

The E4 source route requires exact equality between the TRAIN certificate and
future-bank producing provenance. A changed candidate must satisfy its own
current TRAIN, certificate and target-bank checks. An archived source comparison
cannot transfer qualification to that candidate. Scientific issue, execution,
reveal and outcome access retain their separate authority requirements.

## Freeze the separate E3 secondary response target

The configured primary protocol and its numerical discrepancy gate remain the
primary selection. The current version-`3.0.0`
`ConfiguredProtectedE3PreparationSelection` can additionally bind a separate
response-adequacy target. Without that binding the secondary readout is
`NOT_SUPPLIED`; there is no inferred tolerance. The optional primary-family
amendment and secondary target can coexist in this same preparation record.

Copy the [direct target example](secondary-response-target.example.json) and edit
its declared JSON values. `MatrixE3SecondaryTarget` has schema
`empirical-lawhood/matrix-response-experiment/secondary-response-target`, version
`1.0.0`, with exactly `record_id`, the complete `mathematical_protocol`, and
`normalized_adequacy_tolerance`. The mathematical protocol must equal the current
E3 selection. The tolerance is an explicit positive finite Decimal; for example,
`{"decimal": "0.01"}` is a disclosed example choice, not a default or a
scientifically selected threshold for a new programme. Keep the primary
criterion and fitting parameters unchanged.

Validate the edited target and prepare a new canonical file through the public
configuration commands. No Python constructor or old preparation/template carrier
is required:

```sh
uv run --no-sync empirical-lawhood config validate \
  --config "$EDITED_TARGET" --consumer matrix-configured-secondary-target --format json
uv run --no-sync empirical-lawhood config prepare \
  --config "$EDITED_TARGET" --consumer matrix-configured-secondary-target \
  --output-file "$CANONICAL_TARGET" --format json
```

For the same configured E3 specification, copy the current source selector,
retain its exact original `files`, and bind these two ordinary canonical roles
beneath its source directory. Pin the prepared target's actual identity, relative
path and byte bound:

| Role | Exact record |
| --- | --- |
| `protected-selection` | Actual current `ConfiguredProtectedE3PreparationSelection`, version `3.0.0` |
| `secondary-target` | Prepared direct `MatrixE3SecondaryTarget`, version `1.0.0` |

Run ordinary `experiment-derive-inputs` with that specification/selector and
explicit guarded EL metadata/output paths before unopened CAL/CONF authoring.
Keep the output selector alongside the copied source selector, with a distinct
filename; select its metadata directory under guarded custody outside the source
tree.

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$CONFIGURED_SPECIFICATION" --sources "$SECONDARY_SOURCES" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4 \
  --metadata-directory "$SECONDARY_METADATA" --output-selection "$SECONDARY_OUTPUT_SELECTION"
```

The result binds only `protected-selection` and retains the unchanged original
FILE census. Its `secondary_readout` is a `MatrixE3SecondaryReadoutSelection`
containing exact mathematical-protocol and target identities, the actual immutable
publication handle and its fixed lineage scope. The published canonical target
stays `DEVELOPMENT_VISIBLE`/`DEVELOPMENT_ONLY`; blind companions hold references.
Authoring, cold entry and full scientific read authenticate those bytes before
using the target. A frozen binding cannot be replaced. Partial reads defer
secondary science.

This freezes the explicitly selected mathematical target before CAL/CONF. It
supplies no proof that native TRAIN consumed that target. The readout retains
this limitation and keeps primary continuous-error arithmetic,
complete assigned-root denominators, negative outcomes and point nonuse intact.
The target and its metadata publications create no source qualification, issue,
execution or outcome-access authority.


## Amend only the primary testing family after native TRAIN

A stricter primary testing allowance does not change native measurements or
relabel the original TRAIN candidate. For an explicitly expanded primary family,
`MatrixE3PrimaryFamilyAmendment` retains the actual original candidate and native
request/specification pins, and selects a replacement assessment. It permits
only the exact alpha numerator/denominator and complete comparison roster to
change. The original claims remain present, and the exact rational family budget
must remain equal. Calibration alpha, methods, target geometry, numerical screen,
physical populations, margins and all other candidate fields stay exact.

Bind this canonical record as `primary-amendment` beside the current request and
`scientific-protocol`. The single `ConfiguredProtectedE3AssemblyRequest` pins that amendment and keeps
the original native locator/pre-TRAIN input directory. Use the ordinary public
input derivation route. The original native request, candidate and reservation
must still authenticate exactly; the current route then constructs the separate
amended target. It retains original bank publications and actual entry-seal
receipt/plan custody. The current version-`3.0.0` configured selection carries exact
references for authoring, cold entry and full scientific read. Missing original
receipts, a changed bank/seal/reservation, or a non-alpha edit refuses.
This primary amendment and a direct secondary target remain separate optional
bindings in the same current preparation selection.

For the fresh 14-claim programme, the declared roster is the original twelve
E3–E6 IDs plus `e1.recurrence-survival` and `e2.utility`; the outside-E4 primary
allowance is exactly `1/280`. Select the same full family explicitly in later
E5/E6 functional criteria. Their endpoint thresholds remain independently chosen
scientific operands. Calibration coverage alpha `0.05` is separate from the
primary hypothesis-testing allowance. The E4 declared-family Holm owner retains
its own exact step-down arithmetic. Historical twelve-claim inputs and the
original native TRAIN contacts keep their original identities and meanings.
