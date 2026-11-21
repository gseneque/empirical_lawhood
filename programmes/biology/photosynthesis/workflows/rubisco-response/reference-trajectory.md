# Original reference trajectories

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for diagnostic trajectories under the complete periodic reference potential.
It supports original force capture and independent trace assessment.
Use it to bind a selected initial phase space before native execution.

## Prerequisites

Supply the complete representation, original Amber files and operator selection from the [periodic force route](periodic-force-probe.md).
Supply every initial coordinate and velocity in the original physical atom order.
Retain their source identity and original custody.
The diagnostic selection does not qualify an equilibrium or dividing ensemble.
Do not infer ensemble validity from a temperature label or supplied velocities.

For GPU trajectories, select `AcceleratedPeriodicNumericEngine` in the prototype and `accelerated_compute: true` in the invocation.
Follow the [accelerated-compute guide](../../../../../docs/using/accelerated-compute.md) for environment and resource selection.
The authoring function derives the separate GPU configuration without inspecting a device.
The reader reports authenticated per-force costs and any `gpu_assessment_error` separately from physical trace checks.
Neither observation supplies a qualified starting ensemble or molecular rate.

Select `ReferenceDynamicsSettings` with an exact physical step and positive step count.
The reactive step cannot exceed 0.5 fs.
The step count specifies a physical observation horizon, not an execution deadline.
Select `ReferenceTrajectoryCriteria` before examining the new trace when acceptance criteria are required.
Absent criteria leave trace acceptance unevaluable.

The artifact writer must include the installed operation storage codecs.
Use the existing integration validator or `api.recursive_operations.operation_storage_codecs()` when constructing its validator registry.
The trajectory uses the shared `ArrayDatasetManifest` for its two binary64 arrays.
Its raw payload contains coordinates in angstrom followed by velocities in nm/ps, each in complete native atom order.
These bytes use the registered raw-source codec, not a JSON encoding of numerical payloads.

## Prepare and author

Use the functions in
`empirical_lawhood.api.domain_composition.rubisco_response.periodic_trajectory`:

```python
selection, phase_bytes = prepare_reference_trajectory(
    prototype=prototype,
    representation=representation,
    phase_source=original_phase_source,
    initial_angstrom=original_coordinates,
    initial_velocity_nm_per_ps=original_velocities,
    settings=settings,
    criteria=criteria,
    density_guess_policy="COLD",
)
authored = author_reference_trajectory(
    selection=selection,
    prototype=prototype,
    representation=representation,
    raw_topology=original_topology_bytes,
    raw_coordinates=original_amber_coordinate_bytes,
    phase_bytes=phase_bytes,
    project_root=project_root,
    work_directory=work_directory,
    artifact_writer=artifact_writer,
    output_dir=output_dir,
)
```

Use fresh selected work and authoring directories.
Authoring returns the ordinary recursive handoff and seven direct-input paths.
Execute that handoff through the existing shared lifecycle.
The single operation uses the common periodic-force resource lock and one original attempt.
The current allocation remains eight CPU equivalents and 8 GiB, without an experiment deadline.

`COLD` selects an independent electronic guess at each geometry.
`PREVIOUS_SUCCESSFUL_RKS` permits the preceding successful density within one fixed restricted operator.
The unrestricted operator requires `COLD` in this trajectory route.
Neither policy changes the selected energy or orbital convergence criteria.
The first evaluation always starts independently.

## Original outputs and failures

The producer checks every actual native mass against the original full atom table.
It adds no constraints, thermostat, bias, mass repartitioning or velocity scaling.
Positions remain unwrapped and velocities correspond to complete integration steps.
One complete force starts the trajectory, followed by one complete force per selected step.

Every attempted evaluation retains its input coordinates.
Returned energy and gradient arrays are saved before trajectory validation.
A complete frame marker follows its saved velocity and exact physical time.
A failed marker write retains its partial file without completing that frame.
The original complete-directory archive includes unsuccessful attempts and all diagnostic files.

A native failure retains the valid trajectory prefix.
Completed recovery reads the original receipt and files without another native call.
An uncertain original contact cannot be repeated automatically.
The existing native contact reader distinguishes uncertain work from work that was never entered.
Missing frames alone cannot establish either contact state.

## Independent assessment

Call `read_reference_trajectory` with the original configuration, representation, phase bytes, result, native-subwork reader and assessor source.
The reader authenticates the original definition, completion, receipt and every archived byte.
It continues archive authentication after an early trace-assessment error.
The trace calculation keeps only a bounded number of complete frames in memory.

The reader checks original phase space, physical masses, clock and force census.
It independently checks the position and momentum equations and measures energy drift.
Finite violations of selected criteria remain negative findings.
An incomplete horizon retains its actual duration and remains unevaluable unless an observed criterion is already falsified.
The report separates native errors, assessment errors and trace findings.
It makes no new force evaluation.

These checks do not establish numerical step convergence, force accuracy, chemical applicability, initial-ensemble validity or physical rates.
The selected sampling tranche still requires complete coupled controls and feasible enzyme cost.
Paired trajectories require their actual matched preparation, state, weighting and uncertainty selections.
This diagnostic operation supplies no implicit carbon, oxygen, processing or commitment operand.
The [first-passage analysis](physical-first-passages.md) adds declared events, residence, recrossings and complete censored-path accounting.
Its closed export retains original clocks, weights and receipts without another force call.
Physical rate and state-reduction admission remain separate requirements.

## References and research

The [physical supplier](physical-rate-supplier-v1.md#physical-clock-prefactors-and-standard-states) specifies the physical clock and required rate evidence.
The [periodic numerical controls](periodic-numerical-controls.md) assess selected force directions and numerical refinements.
The [trajectory mechanics](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/periodic_dynamics.py)
implements the synchronized velocity-Verlet equations cited in the supplier.
