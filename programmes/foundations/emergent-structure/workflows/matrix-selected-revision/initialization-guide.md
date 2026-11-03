# Declared Matrix initial conditions

This guide publishes declared Matrix initial conditions.
The deterministic initializer creates state operands without trajectory acquisition or RNG use.
Select the actual source closure and copied request before derivation.

The `matrix.preparation-initialization.inputs` protocol publishes V2 initial-state operands through ordinary input derivation.
It calls the original deterministic Q2 initializer and independently checks its literal Pauli/tensor entries. It initializes the two numerical views separately and
requires byte-identical common positions and momenta. The NPZ shape `(2,3,4,4)`
contains the X/Y matrix sectors; numerical views are not an extra array axis.

This constructs a declared initial condition. It advances no trajectory,
consumes no RNG stream and records zero native contacts. In particular, the
actual `00` initialization rule has zero positions and momenta; those values
come from the declared original rule, not an exposed TEST array. The decreasing
`11` initialization has the original nonzero background at `decreasing_start`.
The V2 record carries the exact original source, root, stream roster, clock,
physical zero cutoff and actual producing numerical provenance. It has no
`original_history` or `original_assessment` fields. Historical V1 states and
retained results retain their exact meanings and bytes.

Copy [the specification](initialization.example.json) and
[source selector](initialization.sources.example.json). Their request identity
is an explicitly missing placeholder. Supply one canonical `request` binding
to `MatrixPreparationInitializationRequest`. Its scientific inputs are:

- The phase and exact original reservation, selection, compact source
  descriptors, provenance roster and exposure audit/publications, in
  `MatrixPreparationInitializationSources`.
- The actual `MatrixPreparedOriginalCommitments` with native TRAIN locator and
  exact published whole C with its selected positive complete-source byte bound,
  and exact current census FILE or publication support.
- For E5 CONF only, the actual complete separate E5 DEV product locator. This
  supplies exclusion facts; a label or a nomination summary cannot replace it.

The source closure deliberately precedes initial-state construction. Construct
it from actual original source records; it does not need a fake history:

```python
sources = MatrixPreparationInitializationSources(
    record_id=selected_sources_id,
    reservation=actual_reservation,
    specification=actual_scheduled_specification,
    provenances=actual_provenances,
    descriptors=actual_compact_descriptors,
    audit=actual_audit,
    audit_publication=actual_audit_publication,
)
```

The existing canonical configuration consumers are
`matrix-preparation-initialization-request` and
`matrix-preparation-initialization-inputs`. Select the actual locked environment,
current source snapshot, guarded EL output root and four-worker operator profile.
Use four distinct physical cores and one numerical thread per worker for new project runs.
Run `campaign experiment-prepare`, then:

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-derive-inputs --input "$WORK/initialization.json" --sources "$WORK/initialization-inputs.json" --metadata-directory "$ARTIFACT_ROOT/initialization-current" --output-selection "$ARTIFACT_ROOT/initialization-current/sources.json" --environment-id "$ENVIRONMENT" --source-snapshot "$SOURCE"
```

Derivation authenticates the actual complete native TRAIN and all three original C E4
allocations and response selections before publication. The whole-C read lifetime
remains guarded through the last dependent publication. Its assigned E5/E6
roots, streams, numerical policies and producing provenance must match C; an
additive current audit does not authorize a different assignment. E5 refuses their groups/streams, prior DEV for
CONF, and complete reserved E6 physical keys; its current audit must contain
the authenticated exclusion union. E6 retains the exact original pre-TRAIN
reservation, source descriptors, all reserved root streams and original audit.
Initialization neither observes nor spends those streams.

The generated `initial-states.json` bank and NPZ FILE bindings reopen through
the normal public loader. `bank.prepared_closure(record_id=..., numerical_scope=...)`
returns the existing protected source closure with the new initial-state
edition. DEV may derive its existing preparation source bank from the same
actual originals and selected recipes. This metadata-only protocol has no
executable experiment draft; its zero native count is intentional. Select the
resulting source bank and original files in the existing declarative E5/E6 route.
Genuine prepared-source qualification still needs the actual later E5 DEV
independent controls and all ordinary authority.

Recipe compatibility remains exact. Historical V1 `HOLD` means a constant
coupling: it starts at restored `(2/3,22/3)` in the retained example and cannot
silently consume the actual original deanneal tick-zero `(8,8)` state.

For a baseline with no added intervention, declare the distinct
`MatrixOriginalScheduleRecipe` using the existing coordinate:

```python
baseline = original_schedule_recipe(
    actual_coordinate,
    actual_prefix_policy.cutoff_tick,
    recipe_id=selected_recipe_id,
    effort_unit=actual_functional_criterion.effort_unit,
)
```

Its kind is `ORIGINAL_SCHEDULE_BASELINE`, with a separate canonical schema.
Every half tick must equal the actual `coordinate.couplings(i, refinement=2)`;
matching endpoints alone cannot admit it. Both the actual prepared source and
its seedless selected point design check the complete schedule. The supported
cutoff ends within the original ramp so original preparation-stream ownership
is preserved. The actual coupling total variation remains its effort; this
baseline does not have zero effort merely because it adds no intervention.
Select it explicitly as the baseline arm in DEV, CONF and both E6 regimes;
the old arm field name `hold_arm_id` remains readable and selects either exact
baseline edition. Every source retains its own original clock, root, bath,
coordinate and pre-TRAIN reservation. A shared schedule identity grants no
cross-regime sampling or transport warrant.

The supplied-noise controls compare every retained primary/fine state,
innovation, tick and coupling byte against the original paired native path for
all four declared initial rules. They are implementation controls, not fresh
acquired results. Original E6 physics requires those controls to pass and all
ordinary native, exposure and authority checks. Initializer publication alone
does not establish E6 execution readiness or downstream uncertainty.
