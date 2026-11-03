# Working in Empirical Lawhood

This repository implements response-law contracts and supported researcher workflows.
Keep development results, software conformance and scientific qualification distinct.
Start with the public documentation for the task you are doing.

## Researcher workflows

Use the [programme index](programmes/README.md) to select a scientific question.
Use [getting started](docs/getting-started.md) for installation and the first report.
The [workflow catalogue](docs/reference/workflows.md) lists every supported guide. The
[experiment procedure](docs/using/designing-and-running-an-experiment.md#researcher-procedure)
owns the high-level design, preparation, execution and analysis steps.
For the Matrix E1–E6 programme, follow the
[programme guide](programmes/foundations/emergent-structure/workflows/matrix-programme/guide.md) and its public scientific
specification. Use each guide's supported commands and returned paths; do not
construct task rosters, scientific identities or predecessor records by hand.

Select the guide's [locked environment](docs/using/environments.md), your operator
profile and explicit storage destinations. After environment selection, use
`uv run --no-sync`; do not synchronize merely to inspect a file or edit prose.
Brian2 uses its separate locked interpreter and NumPy pin.
[Configuration](docs/using/configuration.md) explains copied inputs and canonical
preparation. [Results and failures](docs/using/results-and-failures.md) explains
scientific readouts, retained attempts, recovery and original-result access.
Keep actual source, input access, resource, issue, execution and reveal
prerequisites at their documented boundaries. Configuration validation and
development receipts create no scientific or outcome-access authority.

Preserve exact canonical bytes, Decimal values, source digests and record revisions.
Keep cutoffs, independent units, nested views, complete denominators and negative
or unevaluable outcomes. Relabeling exposed evidence does not make it fresh.
Write outputs only to explicitly selected paths. Closed scientific packages
retain their member contracts; receipts are primary custody and the local
catalog is a rebuildable projection. Keep original paper assets unchanged.
Do not use synthetic test signers or exposed examples as qualification evidence.

## Engine development

Read [Contributing](CONTRIBUTING.md), [architecture](docs/development/architecture.md),
[testing](docs/development/testing.md) and the [extension recipe](docs/development/extending-the-engine.md).
Imports point inward: kernel ← planning ← runtime ← adapters/infrastructure ← API ← CLI.
The kernel owns scientific records and canonical identities; adapters own native
science, infrastructure owns bounded I/O and custody, API composes services and
CLI owns presentation. Static discovery must not inspect prerequisites, build
providers or run native tasks. Guide/config paths belong to the selected
checkout or source distribution. Reuse typed source, allocation and array
contracts; keep immutable evidence separate from editable selections.

Run affected focused checks and lint, and `python scripts/check_documentation.py`
for maintained documentation. Change generated owners first, then regenerate
the extension aggregate, executable aggregate and CLI reference in that order.
Workflow/config projections have their own generators. Use the named scripts
in the extension guide and inspect the diff. Do not hand-edit generated
scientific identities. The coordinator owns shared interfaces, generated
aggregates, dependency changes and integrated acceptance.

Exclude every Markdown work plan from wheels, source distributions and release
archives while preserving its original bytes in local or external custody.
Public guides and scientific specifications must stand without packaged work
plans. The [coverage map](docs/release/implementation-coverage.md) records the shipped
implementation summary. Maintained paper indexes may change only with their
manifest bindings.
