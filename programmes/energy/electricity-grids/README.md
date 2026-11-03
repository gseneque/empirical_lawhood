# Electricity grids

SPDX-License-Identifier: CC-BY-4.0

This overview identifies the programme's question, evidence and available operations.
It keeps scientific findings separate from software availability.
Choose a study below before selecting a run guide.

## Scientific question

Which network changes achieve the required operating outcome when demand or network conditions change?

## Findings and unresolved questions

The retained grid comparison separates a successful topology change from
adequate overload relief. Both tested interventions changed the intended
connection, while neither met the thermal criterion in the shared episodes.

The current Grid2Op workflow checks a selected held chronic. It does not
reproduce that historical comparison or supply a fresh qualified grid cohort.
The inverter assessment records a separate missing physical action journal.

## Studies and evidence

A study design, also called a protocol, specifies the observations, analysis and outcome rules.
Read its date and revision before selecting inputs.
The [scientific record index](records/README.md) provides the retained document census.

| Study | Design | Result | Supported operation | Evidence availability |
|---|---|---|---|---|
| Grid interventions and operating outcomes | [Study design](records/grid2op-qualification.md) | [Findings](https://empiricallawhood.org/how-the-method-developed/#evidence-grids) | [Run guide](workflows/grid-response-inputs/guide.md) | Historical results have external custody; the public guide supports a bounded development check. |
| Physical inverter source | [Study design](records/nrel-inverter-qualification.md) | [Findings](records/nrel-inverter-qualification.md) | No public study runner | The prospective physical-inverter route is outside this release. |

## Available workflows

- [Grid2Op held-chronic native development check](workflows/grid-response-inputs/guide.md).

Use the [researcher procedure](../../../docs/using/designing-and-running-an-experiment.md#researcher-procedure)
and the selected guide's environment, input and storage requirements.
Static discovery supplies no missing source, execution permission or scientific qualification.

[All programmes](../../README.md) · [Workflow catalogue](../../../docs/reference/workflows.md) · [Results and failures](../../../docs/using/results-and-failures.md)
