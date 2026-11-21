# SCI02 preparation shortcut study

SPDX-License-Identifier: CC-BY-4.0

Programme: [Emergent structure — stochastic matrices](../../README.md).
Read the [scientific protocol](protocol-v1.md) before selecting inputs.
This is a separate development experiment using the shared prepare, author,
run, read and recover lifecycle. It supplies no new protected authority.

Select the [locked main environment](../../../../../docs/using/environments.md),
an explicit operator profile and guarded artifact/scratch destinations. Use
`uv run --no-sync` after environment selection. An installed wheel requires its
matching source distribution. Keep the source and dependencies fixed through
entry and independently authenticated readback.

The supported input constructor is
[`create_inputs`](../../../../../src/empirical_lawhood/api/matrix_sci02.py).
Supply original scientific-design and template files, the audited current
exposure census, an existing campaign metadata record, this protocol, the
selected source root and a new explicit input directory. For example, from
the selected interpreter:

```python
from empirical_lawhood.api.matrix_sci02 import create_inputs

paths = create_inputs(
    original_design_path="/absolute/selected/scientific-design.json",
    templates_path="/absolute/selected/templates.original.npz",
    exposure_census_path="/absolute/selected/current-exposure-census.json",
    campaign_path="/absolute/selected/campaign.json",
    protocol_path="/absolute/selected/source/programmes/foundations/emergent-structure/workflows/matrix-preparation-shortcut/protocol-v1.md",
    project_root="/absolute/selected/source",
    output_directory="/absolute/selected/new-sci02-inputs",
    namespace="matrix.sci02.selected-study",
    molecular_requirement="Paired C3-H3/KCX restrained-formation force correction to q_a; preserve conditional ensemble and required weights; assess avoided complete energy/gradient calls.",
)
print(paths)
```

The constructor checks inherited template bytes, retains the exact original
files, observes producing provenance and derives one finite DEV16/held32 stream
reservation. It draws no native trajectory. Its returned paths select the
canonical specification, source bindings and source snapshot. Do not construct
root identities, operation maps or predecessor records yourself. A census hash
cannot establish factual completeness; reconcile actual historical reservations
before this constructor is used for new science.

For an existing Matrix programme, `reconcile_exposure_from_programme` in the
same API accepts its original `MatrixProgrammePublishedInput`, the guarded
artifact reader, a new explicit output directory and a finite
`maximum_source_bytes` allowance. It authenticates the complete original input
publication and unions all reserved roots and response streams, including
unentered phases, with the prior census. Use the returned `exposure_census`
path and retain its audit. This reads reservations without acquiring trajectories
or granting freshness or qualification.

Set `PROJECT`, `PROFILE`, `INPUTS`, `ARTIFACT_ROOT` and `ENVIRONMENT` to your
explicit selections. `INPUTS` is the new directory returned above. Create the
selected report parent before preparation.

```sh
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-prepare \
  --input "$INPUTS/specification.json" --sources "$INPUTS/sources.json" \
  --environment-id "$ENVIRONMENT" --source-snapshot "$INPUTS/source-snapshot.json" \
  --output-root "$ARTIFACT_ROOT" --workers 4 --output "$INPUTS/preparation-report.json"
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-author \
  --input "$INPUTS/specification.json" --sources "$INPUTS/sources.json" \
  --environment-id "$ENVIRONMENT" --source-snapshot "$INPUTS/source-snapshot.json" \
  --workers 4 --output-dir "$ARTIFACT_ROOT/sci02-dev8"
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-run \
  --authoring-dir "$ARTIFACT_ROOT/sci02-dev8" --workers 4
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-read \
  --authoring-dir "$ARTIFACT_ROOT/sci02-dev8"
uv run --no-sync empirical-lawhood --project-root "$PROJECT" --operator-profile "$PROFILE" campaign experiment-recover \
  --authoring-dir "$ARTIFACT_ROOT/sci02-dev8" --workers 4
```

The selected profile must admit the requested four workers. Each operation has
one CPU, 2 GiB memory, a 3600-second wall limit, a 2 GiB source-scan ceiling
and a 128 MiB output ceiling. Use one numerical thread per worker. Storage and
resource admission remain actual entry checks. Preparation derives 224 ordinary
operations, 80 native intervals and 24 response packages for DEV8. The common
prefix is acquired once per root. Successful preparation is not a scientific result.

The reader authenticates original products, causal predecessors, native child
receipts and both child outputs: numerical arrays and generator continuation
metadata. It independently checks scientific equations and complete criteria,
then reports all recipe/method cells and signed finite-pair contrasts.
Partial custody defers scientific completion. Completed recovery reuses the
original receipts; an uncertain native contact cannot be reacquired by retry.

The first installed specification admits DEV8 only. Read its complete findings
and cost before selecting continuation. Later tranches require their accepted
composition, original reservation and frozen policy; do not relabel a fresh
DEV8 run as DEV16 or holdout. A local scientific stop leaves the required
molecular shortcut open. The protocol's finite allocation and held-out rules
remain fixed while those later execution bindings are completed.

`refresh_execution_inputs` in the input API binds an existing exact reservation
to a newly selected implementation after an operational repair. It preserves
the selection, physical design, streams and original input bytes, and retains
the predecessor specification and provenance. Use its returned paths with the
ordinary lifecycle. This does not reset exposure, erase attempts or authorize
reacquiring an uncertain native contact.
