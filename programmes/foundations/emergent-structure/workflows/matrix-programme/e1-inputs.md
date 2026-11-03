# E1 inputs from the whole programme

The `matrix.programme.e1-input-assembly` operation derives ordinary compact E1
inputs from the original whole-programme commitment C. It produces canonical
metadata and performs no native acquisition. The existing compact E1 lifecycle
owns subsequent preparation, authoring, execution, assessment and recovery.

Before freezing D, use `matrix.programme.e1-allocation` to bind the mathematical
criterion to its actual prospective allocation. Copy the four
`e1-allocation.*.example.json` files from this directory to your selected external input
directory. These are exposed software examples with 96 roots per family;
select the actual scientific counts, current complete exposure census, four
coordinates, namespace, disclosed stream material and finite metadata budget
in the copied request before canonical preparation. This step requires no D,
old issued package or placeholder allocation fingerprint.

Set `$PROJECT_ROOT` to your selected checkout or matching installed source distribution.
Use the same explicit operator profile, source and storage selections throughout the commands below.

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$E1_ALLOCATION" --sources "$E1_ALLOCATION_SOURCES" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4 \
  --metadata-directory "$E1_ALLOCATION_METADATA" \
  --output-selection "$E1_ALLOCATION_METADATA/inputs/sources.json"
```

The output contains the actual allocation and bound compact criterion. Put that
criterion into D, then compile C with the same census, namespace, root stream
material and coordinates. The whole-programme compiler checks the exact
allocation fingerprint; it cannot substitute another allocation or weaken the
criterion. Allocation metadata creates no acquisition or scientific authority.

Use the version 2 occurrence criterion: time-zero risk, both views and sectors,
all three survival diagnostics, and exact E1 alpha 1/160. The eight primary
PRIMARY-Y occurrence/joint-survival intervals use noncoverage 1/1280 each.
Family choices contain assigned root counts; they contain no minimum-admission
or probability-above-one-half gate. The programme selects occurrence through
tick 1024 and first-origin follow-up of 128 ticks, requiring all 1152 history
ticks. The [E1 specification](../../records/matrix-e1-occurrence.md)
defines initial presence, unknown eligibility and the complete-population
interval envelope.

Supply one `selection` binding in an `ExperimentInputSelection` or
`ExperimentFileInputSelection`. The current consumers are:

| Consumer | Record |
| --- | --- |
| `matrix-programme-e1-context` | Scientific question, alternatives, system, claims, assignment, measurements, controls, precision goals, obligations and observation operator |
| `matrix-programme-e1-assembly-selection` | Version 2 selection with scientific context, current campaign, six phase budgets, workers/resources, progress contract and explicit entry/formal selections; no C handle |
| `matrix-programme-e1-assembly` | Version 2 specification selecting the actual C publication and binding that exact assembly selection |

For standalone assembly, select C once in the assembly specification. The
whole-programme runner supplies this specification from its original C selection;
no C handle is copied into the E1 operational selection.

The context supplies mathematical declarations directly. An earlier StudyDraft,
issued package, READY status or metadata receipt is not an input prerequisite.
The current system's authority policy must cover the programme namespace, and
the campaign must select that exact policy. This policy is a declaration; real
issue, execution and reveal acts remain separate requirements.

Select the locked main environment, an operator profile with at least four
physical cores, and explicit input/output paths on the storage declared by that profile. After canonical preparation through
[configuration](../../../../../docs/using/configuration.md), use the public derivation:

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-explain \
  --input "$E1_ASSEMBLY" --sources "$E1_ASSEMBLY_SOURCES" --workers 4
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$E1_ASSEMBLY" --sources "$E1_ASSEMBLY_SOURCES" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4 \
  --metadata-directory "$E1_METADATA" --output-selection "$E1_METADATA/sources.json"
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-explain \
  --input "$E1_METADATA/specification.json" --sources "$E1_METADATA/sources.json" --workers 4
```

Assembly authenticates all twelve original C roles and binds the E1 reservation,
criterion, exact four coordinates, producing provenance and scalar publication.
It derives the complete assigned root census, causal cutoffs and reveal barrier
and publishes the ordinary compact selection and source selector. Metadata
access receipts are regenerated from the actual published operands. They
establish exact access and decoding, not sampling or source qualification.

The returned requirements and scientific root retain missing capacity, entry,
formal and authority prerequisites. Assembly clears inherited evidence and capacity states;
it cannot carry an old READY decision into the new experiment. Establish current
admission through the [public experiment lifecycle](../../../../../docs/using/designing-and-running-an-experiment.md)
before authoring or acquisition. Retain all failed and incomplete attempts.

Before freezing an outer programme, derive the E1 review inputs with its entry
and formal selections absent. Use the final E1 metadata directory
`<programme>/derived/e1/produced`, but select a separate review output:

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT_ROOT" --operator-profile "$OPERATOR_PROFILE" campaign experiment-derive-inputs \
  --input "$E1_ASSEMBLY" --sources "$E1_ASSEMBLY_SOURCES" \
  --source-snapshot "$SOURCE_SNAPSHOT" --environment-id "$ENVIRONMENT_ID" --workers 4 \
  --metadata-directory "$E1_METADATA" --output-selection "$E1_METADATA/entry-review/sources.json"
```

The review directory contains `selection.json`, `specification.json`,
`sources.json` and `requirements.json`. Its selection retains the exact current
scientific root and missing prerequisites. Bind the reviewed entry package,
formal methods and source inventory to that root in the copied E1 assembly
selection, then update the assembly specification's selection identity and the
copied source binding. Put that same completed selection into the outer
programme's `operations.e1` before freezing the outer specification.

Final derivation uses `$E1_METADATA/sources.json`. The public programme runner
performs this same derivation. Shared scientific operands stay at their original
locations, so adding entry and formal records preserves the exact root they
identify. Review files remain unchanged. If the scientific context, resources,
C or producing implementation changes, select a new metadata directory and
review its new root. A review output must be a canonical `sources.json` inside
the selected metadata directory. These metadata operations establish no entry
approval, execution permission or scientific qualification by themselves.
