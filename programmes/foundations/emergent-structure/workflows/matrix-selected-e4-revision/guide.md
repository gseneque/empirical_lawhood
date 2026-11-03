# Selected E4 revision from original DEV acquisition

SPDX-License-Identifier: CC-BY-4.0

Programme: [Emergent structure — stochastic matrices](../../README.md).

This guide derives an E4 revision from actual DEV acquisition.
It preserves original custody and the declared revision procedure.
Authenticate the retained DEV receipts and required structural closeout first.

The owner derives bounded observations, programme and source bank through the original custody reader.
It then authors the existing two-operation revision component.
Researchers do not construct observation JSON, graph nodes, fitted coefficients or receipt pins.

The amended matched declaration selects `E4MatchedRelationTarget` and
`E4MatchedRelationSelection`. It fits SR/BR from DEV16 with two assigned
whole-group folds and at most five paired58 fit bundles per fitted arm.
Its trigger is null and its legacy candidate/tie menus are empty. Actual
pre-future mechanical forecasts and causal features are authenticated from
their original arrays before fitting. The shared rules in the
[dense-response specification](../../records/matrix-dense-response.md)
govern common eligible groups, transforms, losses and missingness.
`FIT_AVAILABLE` freezes both required models; `FIT_UNAVAILABLE` retains the
failed fit and prevents dependent CAL/CONF and E5/E6 entry. CONF does not choose
this account. S0/B0 remain unchanged references.

The wrapper protocol is `matrix.selected-e4.revision-from-acquisition`; its
[specification](specification.json) embeds the exact editable revision declaration.
The generated nested declaration selects the original programme and response
criterion, the dense paired58 target, sixteen groups, two whole-group folds,
penalties 1/10 and the five-bundle fit budget. It selects the matched relation
with the published nominal physical values and a null trigger.
Replace its example programme/criterion references and group IDs with the actual
original DEV declarations; the zero fingerprints are unresolved example selectors.
The folds must retain the original assigned family support; example labels do
not establish eligible development observations.

Configuration validation grants no original source custody or scientific eligibility.

Copy inputs beneath a selected directory on the default EL disk, following
[environment reuse](../../../../../docs/development/maintainer-environment.md). Keep the producing
checkout and selected locked environment stable throughout dependent execution.
Select worker concurrency from the operator profile, or pass its exact selected
value explicitly. Neither the programme nor the CLI supplies a scientific resource
estimate. The [resource example](resources.json) explicitly requests1GiB per PURE
task and unlimited wall time; select measured operational reservations appropriate
to the actual workload before authoring. Ordinary DEV retains its existing
resource semantics and does not acquire an issued NonTime aggregate envelope.

The closed `--sources` selection has four canonical bindings:

| Key | Selected original input |
| --- | --- |
| `allocation` | Byte-preserving copy of the actual native DEV packet's `experiment-allocation.json` |
| `campaign` | Actual selected campaign configuration used for this project |
| `source` | Copied [acquisition directory selector](acquisition-source.json), edited to the guarded original authored DEV directory relative to the selected storage root |
| `resources` | Copied [explicit PURE phase reservations](resources.json) for `revision-fit` and `revision-freeze` |

Use the existing [input selection contract](../../../../../docs/using/configuration.md) and exact
published/config-preparation identities. Keep all four member paths beneath the
selection's real parent directory; copied bytes retain their original identity.
The acquisition selector contains no caller-asserted successful receipt, native
result or authority. `allow_partial=false` requires the original complete read;
an explicitly selected partial read keeps all assigned missing/adverse groups
and may yield an unevaluable trigger.
Complete source derivation uses one fresh authenticated custody read for its locator
and bounded observations. Later fitting and freezing still authenticate original
source custody afresh; an exported companion grants no execution authority.

Validate copied declarations first:

```sh
uv run --no-sync empirical-lawhood config validate \
  --config "$WORK/specification.json" \
  --consumer experiment.matrix-selected-e4-revision-from-acquisition --format json
uv run --no-sync empirical-lawhood config validate \
  --config "$WORK/acquisition-source.json" \
  --consumer matrix-selected-e4-revision-acquisition --format json
uv run --no-sync empirical-lawhood config validate \
  --config "$WORK/resources.json" \
  --consumer matrix-selected-e4-revision-resources --format json
```

Use the same six public commands. Here `WORK`, `ELROOT`, `PROFILE`,
`SOURCE` and `SELECTED_WORKERS` are explicitly selected operational paths/values;
`SOURCE` is the actual implementation binding, and `ELROOT` is the guarded root
from the operator profile. The working source selection binds the four original
input roles above. No extra `--protocol` override or issued plan is selected.

```sh
uv run --no-sync empirical-lawhood campaign experiment-explain \
  --input "$WORK/specification.json" --sources "$WORK/inputs.json" \
  --source-snapshot "$SOURCE" --environment-id main-locked \
  --output-root "$ELROOT" --workers "$SELECTED_WORKERS"
uv run --no-sync empirical-lawhood campaign experiment-prepare \
  --input "$WORK/specification.json" --sources "$WORK/inputs.json" \
  --source-snapshot "$SOURCE" --environment-id main-locked \
  --output-root "$ELROOT" --workers "$SELECTED_WORKERS" \
  --output "$WORK/new-preparation-report.json"
uv run --no-sync empirical-lawhood --project-root "$PROJECT" \
  --operator-profile "$PROFILE" campaign experiment-author \
  --input "$WORK/specification.json" --sources "$WORK/inputs.json" \
  --source-snapshot "$SOURCE" --environment-id main-locked \
  --workers "$SELECTED_WORKERS" --output-dir "$ELROOT/selected-e4/revision"
uv run --no-sync empirical-lawhood --project-root "$PROJECT" \
  --operator-profile "$PROFILE" campaign experiment-run \
  --authoring-dir "$ELROOT/selected-e4/revision" --workers "$SELECTED_WORKERS"
uv run --no-sync empirical-lawhood --project-root "$PROJECT" \
  --operator-profile "$PROFILE" campaign experiment-read \
  --authoring-dir "$ELROOT/selected-e4/revision"
uv run --no-sync empirical-lawhood --project-root "$PROJECT" \
  --operator-profile "$PROFILE" campaign experiment-recover \
  --authoring-dir "$ELROOT/selected-e4/revision" --workers "$SELECTED_WORKERS"
```

Without sources, explanation/preparation lists missing allocation, campaign,
source and resources plus any unselected execution inputs. A complete static
preparation does not inspect the original run. Authoring then authenticates the
actual original DEV acquisition before creating a fitting component; an unavailable,
substituted or unauthenticated original directory refuses. The owned transition
writes a ready `derived-inputs/sources.json`, the `revision-component` closed
packet, an immutable parent/child binding and the generic programme descriptor.
The original packet's physical source bank and observations are derived from
authenticated products, with exact allocation, cutoff, array and source joins.
The fitter repeats original native custody checks before fitting.

Read/recovery authenticate the exact retained parent, original acquisition locator,
child packet/plan/instance/source and frozen operational reservations. Partial
read retains the assigned denominator and defers unavailable scientific products.
A closed paired15 triggered branch cross-validates both declared accounts and jointly freezes
their actual transforms and coefficients; a nontriggered or unevaluable branch
performs zero fits and preserves the unentered freeze.

This DEV route is nonpromotable. Original E3 calibration remains original-scope
only, including an unbounded radius; its raw CAL bank stays parent-only. E4 revision
calibration, independent CAL/CONF populations, genuine entry qualifications and
later downstream applicability require their separate owners. Native software
controls, successful authoring and a completed DEV selection establish none of
those scientific claims. The closed physical-grid model has no declared off-grid
feature rule. The amended relation uses its fixed log-ratio, pair and aggregate
curvature features for a single off-grid case. Its downstream package retains
the original SR/BR transforms, coefficients and separate E4 calibration radii;
this does not establish transport or complete later-phase workflow acceptance.

The [structural follow-up](../matrix-response-experiment/full-factor-followup.md) remains a separate required closeout for each genuinely entered E4 phase. See
[release status](../../../../../docs/release/release-status.md) for actual acceptance and release status.
