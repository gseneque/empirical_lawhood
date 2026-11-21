# Original equilibrium sampling

SPDX-License-Identifier: CC-BY-4.0

This route acquires one selected BAOAB Langevin sampling trace under the complete periodic reference potential.
It retains reference forces, optional umbrella bias and thermal noise separately through the shared native lifecycle.
A complete trace does not establish equilibration, effective sample size, free energy or a physical rate.

## Select the original operands

Use the complete representation, original Amber files and operator selection from the [periodic force route](periodic-force-probe.md).
Supply every initial position and velocity in native atom order, with their original source identity and custody.
The sampler preserves every physical mass and applies no constraints, mass repartitioning or velocity rescaling.

For GPU sampling, select `AcceleratedPeriodicNumericEngine` in the prototype and `accelerated_compute: true` in the invocation.
Follow the [accelerated-compute guide](../../../../../docs/using/accelerated-compute.md) for environment and resource selection.
The authoring function derives the separate GPU configuration without inspecting a device.
The reader authenticates per-force GPU costs alongside the stochastic trace.
Missing GPU observations remain explicit in `gpu_assessment_error`; complete sampling mechanics alone cannot discharge that error.

Select `ReferenceEquilibriumSettings` with explicit temperature, friction, seed, generator, integration step and sampling schedule.
The temperature must match the represented material.
The reactive integration step cannot exceed 0.5 fs.
The selected step count is a sampling horizon, not an experiment deadline.
Discarding an initial prefix does not demonstrate equilibration.
Thermostatted sampling time is not an unbiased dynamical rate clock.

For a biased window, supply the original `UmbrellaWindow` and its `ReferenceBiasConvention`.
Both identities must match the equilibrium settings, and the window model ID must equal the representation ID.
Every restrained atom must occur in the complete physical atom table.
The [bias convention](physical-rate-supplier-v1.md#implemented-umbrella-bias-arithmetic) defines units, ordered coordinates and periodic images.
The equilibrium settings control this acquisition's schedule and RNG.
The historical window's Metropolis proposal, step counts and seed are retained as original record fields but are not executed by this route.
Use `None` for both window and convention when the settings explicitly select no bias.

Select `ReferenceEquilibriumCriteria` before examining new trace results when mechanics acceptance is required.
Absent criteria leave trace acceptance unevaluable.
Energy and momentum conservation are not imposed on a stochastic bath.

## Prepare and author

Use the functions in `empirical_lawhood.api.domain_composition.rubisco_response.periodic_equilibrium`:

```python
selection, phase_bytes = prepare_reference_equilibrium(
    prototype=prototype,
    representation=representation,
    phase_source=original_phase_source,
    initial_angstrom=original_coordinates,
    initial_velocity_nm_per_ps=original_velocities,
    settings=settings,
    window=window,
    convention=convention,
    criteria=criteria,
    density_guess_policy="COLD",
)
authored = author_reference_equilibrium(
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
Include `api.recursive_operations.operation_storage_codecs()` in the artifact writer's validator registry.
The route reuses the [trajectory phase transport](reference-trajectory.md): two complete binary64 arrays and the original mass/source identities.
Its embedded phase selection has no NVE criteria and does not execute a separate trajectory.

Authoring returns the ordinary recursive handoff and seven direct-input paths.
Execute the handoff through the existing shared lifecycle.
The single operation uses the common periodic-force resource lock and one original attempt.
The current resource selection is eight CPU equivalents and 8 GiB without an experiment deadline.
`COLD` selects an independent electronic guess at each point.
`PREVIOUS_SUCCESSFUL_RKS` permits only the preceding successful restricted density within the fixed operator.
The unrestricted route requires `COLD`; neither policy changes electronic convergence criteria.

## Original returns and partial work

One complete reference force starts the trace, followed by one new reference force per selected step.
Before each later force, the producer captures the original standard-normal array, generator states and NumPy version.
It retains each bias input, returned energy, complete gradient and local coordinate derivatives separately.
Reference energy and gradient returns are captured before sampler validation.
A complete frame marker follows all required arrays and the synchronized velocity.

Reference calls, bias calls, draws and complete frames have distinct counts.
A failed bias or noise capture cannot be counted as an entered subsequent reference call.
A failed reference return or frame capture retains its original files and valid prefix.
No failure is retried automatically.
Completed recovery reads the original receipt and files; uncertain original contact cannot be reentered.

## Independent reading and limits

Call `read_reference_equilibrium` with the original configuration, representation, phase bytes, result, native-subwork reader and assessor source.
The reader authenticates the original definition, completion, receipt and every archived byte.
It finishes custody checks even if an early frame fails assessment.
The calculation retains only a bounded number of complete frames in memory.

The reader checks exact settings, sampling times, sample ordinals and the original force/bias/noise census.
It verifies continuity of recorded generator states and the correspondence of original bias terms, units and gradient decomposition.
It independently evaluates the stochastic position, velocity and heat recurrences using retained forces and realized noise.
It invokes no reference force operator, producing bias evaluator or RNG.
Finite violations of selected trace criteria remain falsified; an intact incomplete horizon remains unevaluable.

Generator-state continuity does not independently regenerate or validate the selected random stream.
Bias correspondence and decomposition alone do not independently verify coordinate geometry or force accuracy.
The [numerical bias controls](../../../../../tests/test_rubisco_periodic_bias.py) and original source/environment custody remain separate evidence.
This reader provides no equilibrium, overlap, correlation, timestep-convergence, chemical-model or rate admission.
Use the [retained free-energy route](reference-free-energy.md) for complete cross-window potentials, correlation, overlap and joint block-resampling estimates.
Its numerical diagnostics do not establish physical-model or equilibrium admission.
Paired physical contrasts require their actual sampling and uncertainty assessments.
Use the [unbiased trajectory route](reference-trajectory.md) for physical flux studies only after their starting ensemble and numerical accuracy are admitted.

### Independent bias geometry

Select `ReferenceBiasGeometryCriteria` from `periodic_bias_assessment` before examining new bias results when numerical acceptance is required.
Bind the exact original `ReferenceBiasConvention` identity.
Select a positive Cartesian derivative step in angstrom.
The independent reader uses this step and half this step.
Supply all numerical limits explicitly:

- One value limit per CV, in its selected angstrom or radian unit.
- One Cartesian derivative limit per CV, in that CV unit per angstrom.
- One derivative-refinement limit per CV, in the same derivative unit.
- An absolute energy limit in kJ/mol, applied to each term and the total.
- Complete-gradient disagreement and refinement limits in kJ/mol/angstrom.

Pass this record as `bias_geometry_criteria` to `read_reference_equilibrium`.
The readout retains its complete canonical selection.
This assessment selection does not alter the original acquisition configuration, native attempt or receipt.
Absent criteria leave independent bias-geometry acceptance unevaluable.
An unbiased acquisition cannot select bias criteria.

The reader reconstructs periodic distances and signed torsions from original coordinates.
Its torsion calculation uses projected vectors instead of the producer's reverse chain rule.
It compares original CV values, restraint displacements, term energies and total energy.
Two numerical derivative stencils check each local CV derivative and the complete bias gradient.
The comparison includes overlapping terms and unrestrained atoms.
Step refinement is a numerical consistency check, not a rigorous error enclosure.

An unresolved bond, collinear plane, image boundary or restraint cusp cannot pass the derivative check.
A smooth signed-angle branch crossing remains assessable.
A finite violation remains falsified even if another stencil is unresolved.
An intact incomplete horizon remains unevaluable unless a retained frame already falsifies the selected criteria.
The result preserves complete frame counts, per-CV unresolved counts, maximum errors and the first affected evaluation.

This reader generates no new reference forces, bias-producer returns or thermal draws.
Original archive authentication still finishes after an early assessment error.
Numerical bias acceptance does not qualify a chemical reaction coordinate, initial ensemble, equilibrium population or physical rate.
