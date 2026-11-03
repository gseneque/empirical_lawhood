# Fusion

SPDX-License-Identifier: CC-BY-4.0

This overview identifies the programme's question, evidence and available operations.
It keeps scientific findings separate from software availability.
Choose a study below before selecting a run guide.

## Scientific question

Which delivered interventions and observations support useful control of a plasma?

## Findings and unresolved questions

The retained prospective simulation study found a positive direction of
response under its selected intervention. Numerical sensitivity leaves the
converged magnitude and physical transfer unresolved.

Current workflows provide bounded tokamak diagnostics and public source
acquisition. Acquiring an archive member does not establish actuator semantics,
source qualification or reproduction of a historical plasma study.

## Studies and evidence

A study design, also called a protocol, specifies the observations, analysis and outcome rules.
Read its date and revision before selecting inputs.
The [scientific record index](records/README.md) provides the retained document census.

| Study | Design | Result | Supported operation | Evidence availability |
|---|---|---|---|---|
| Selected-action efficacy | [Study design](../../../paper/SOURCES.md#paper-studies-and-current-software) | [Findings](../../../paper/revision-and-evidence-notes.md) | [Run guide](workflows/tokamak-control-response/guide.md) | Historical producing records remain external; the current diagnostic is a separate task. |
| Heating response and source semantics | [Study design](records/mastu-voltage-source-assessment.md) | [Findings](records/mastu-voltage-source-assessment.md) | [Run guide](workflows/tokamak-heat-response/guide.md) | Physical delivery semantics and joined-pipeline evidence remain separate requirements. |
| FAIR-MAST source intake | [Study design](workflows/fair-mast-source/guide.md) | [Findings](records/mastu-voltage-source-assessment.md) | [Run guide](workflows/fair-mast-source/guide.md) | Bounded public metadata/data acquisition with its own custody requirements. |

## Available workflows

- [Inspect and acquire a bounded FAIR-MAST source](workflows/fair-mast-source/guide.md).

- [Gym–TORAX native development input](workflows/tokamak-control-response/guide.md).
- [Direct TORAX native heat check](workflows/tokamak-heat-response/guide.md).

Use the [researcher procedure](../../../docs/using/designing-and-running-an-experiment.md#researcher-procedure)
and the selected guide's environment, input and storage requirements.
Static discovery supplies no missing source, execution permission or scientific qualification.

[All programmes](../../README.md) · [Workflow catalogue](../../../docs/reference/workflows.md) · [Results and failures](../../../docs/using/results-and-failures.md)
