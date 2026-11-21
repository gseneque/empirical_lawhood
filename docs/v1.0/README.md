# Use and extend Empirical Lawhood

SPDX-License-Identifier: CC-BY-4.0

This guide selects the public interface for your scientific task.
The recursive workflow supplies preparation, execution, custody, assessment and reuse.
Begin with [the scientific-question checklist](from-question-to-investigation.md).
It connects your specification to preparation, execution, assessment and recursive reuse.
Then choose one of the three jobs below.

| Your job | Start here | What you supply |
| --- | --- | --- |
| Define or modify an investigation | [Investigation guide](define-investigation.md) | The question, scientific choices, selected methods, evidence, assumptions and consequential constraints |
| Add a reusable scientific method | [Method guide](add-method.md) | A calculation, strict scientific input/output contracts and explicit applicability |
| Add a domain or substrate | [Domain guide](add-domain.md) | Representations, transformations and any actual native observations or actions |

The [public interface reference](public-api.md) identifies supported imports and application operations.
The [composition guide](compose-investigation.md) runs two connected investigations
and explains how to declare a new scientific procedure.
The [architecture guide](architecture.md) assigns owners and enforces dependency direction.
[Framework maintenance](framework-maintenance.md) is a separate job.
The [CPU and GPU guide](cpu-and-gpu.md) describes configuration and numerical-engine boundaries.
The [scientific component guide](scientific-components.md) locates independently callable calculations.
The [new R01–R22 experiments](joint-description-experiments.md) apply these layers
to finite joint-description, interface, memory and error comparisons. They have
editable recipes and a shared causal lifecycle. The [programme record](../../programmes/shared-records/joint-description-results.md) reports the verified results and remaining measurement and GPU requirements.

The [consolidated classical matrix series](classical-matrix-series.md) covers
the capstones and E1–E6. Its development run completed 290 operations, and
81 retained reanalysis operations reproduced the population results. The
guide shows how to inspect the original or prepare a separate investigation.

The [model-free matrix programme](model-free-matrix-programme.md) describes
the 33-root development pilot and the completed M0–M7 successor. The five
receiver studies used 129 fresh roots and 16 exposed memory roots. The
[receiver-specific results](../../programmes/foundations/emergent-structure/records/model-free-receiver-results.md)
report each scientific decision, fallback and cold-read result. The learned
relation benchmark is a separate optional comparison.

For Rubisco, the four-material gas-free study reports the measured precursor
lifetimes and the evidence still needed to estimate turnover and specificity.
The earlier molecular audit describes the construction, force and custody
requirements for the separate M50 comparison. [Precursor release](../../programmes/biology/photosynthesis/records/gp-precursor-release.md) · [Molecular audit](../release/rubisco-molecular-remediation.md)

## The recursive workflow

An investigation states a question and the conditions needed to answer it.
A missing condition can become another question, with its own selected supplier and assessment.
EL records the relationship between these investigations and their retained contributions.

1. Edit the scientific definition and select its original inputs.
2. Prepare it to expose unmet prerequisites and invalid selections.
3. Derive and inspect the execution plan.
4. Execute the selected work through the shared services.
5. Inspect original results, including adverse and unevaluable outcomes.
6. Assess whether the contribution supplies the next investigation's requirement.

Preparation and plan derivation do not invent an assumption or grant permission.
A completed calculation does not establish that its scientific claim is true.
An unresolved requirement remains visible until its owning assessment resolves it.

## Installation and source selection

EL requires CPython 3.11.
Use the release's selected environment and matching source distribution for source-bound operations.
The [environment guide](../using/environments.md) describes optional solver profiles and numerical settings.

For a checkout, select the environment once:

```sh
uv sync --locked --python 3.11.14
uv run --no-sync empirical-lawhood --help
```

Use `uv run --no-sync` for later commands in that selected checkout.
An installed wheel supplies the same Python contracts and CLI.
Run its console command directly from the selected installed environment.
The wheel's documentation metadata identifies the matching source.

| Surface | Available content |
| --- | --- |
| Installed wheel | Public Python contracts, application operations, CLI, workbench backend and shipped read-only assets |
| Matching source distribution or checkout | Guides, editable scientific definitions, examples, contribution tests and build procedures |
| Explicit operational storage | Mutable inputs, authenticated publications, retained attempts and results |
| Preserved programme records | Original evidence and scientific history, under their existing custody contracts |

Choose output directories explicitly.
A contributor needs no maintainer-specific disk name or private signing key for a pure exposed example.
A protected or native workflow retains its actual access and resource requirements.

## Discovery and interpretation

```sh
uv run --no-sync empirical-lawhood workflow list --format json
uv run --no-sync empirical-lawhood workflow show recursive-inquiry --format json
uv run --no-sync empirical-lawhood capability list --limit 5 --format json
```

Discovery reports declarations and their evidence limits.
It does not execute a method or infer that its environment and inputs are ready.
Use the workflow's guide to distinguish runnable examples, retained-result inspection and incomplete integrations.
The [programme index](../../programmes/README.md) groups scientific questions and findings.
The [workflow catalogue](../reference/workflows.md) is the complete generated route inventory.

## Changes from the preceding source layout

V1.0 uses purpose-named packages and one declaration for a routine extension.
Retired Python paths are removed; there are no import aliases or compatibility wrappers.
The migration map identifies each moved owner.
Original evidence bytes, scientific schema identities and accepted outcomes retain their original meaning.
Source and implementation identities change when executable code changes.
Use [results and failures](../using/results-and-failures.md) for retained reading and permitted recovery.
