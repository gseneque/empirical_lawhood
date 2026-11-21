# Retained physical first passages

SPDX-License-Identifier: CC-BY-4.0

This guide gives instructions for first-passage observations from original unbiased trajectories.
It preserves physical clocks, event definitions, censored paths and exact probability weights.
Use it after the [reference trajectory route](reference-trajectory.md) returns the selected attempts.

## Select original paths and physical events

Use the selected [locked environment](../../../../../docs/using/environments.md) with `uv run --no-sync`.
Select an external artifact root and a fresh output directory.
Supply every original configuration, representation, phase payload, result and native-subwork reader.
Use `None` for a result that is not supplied.
This absence does not prove that the original task was never entered.

Use the records in `adapters.methods.rubisco_response.physical_first_passage_records`.
Freeze the selection before outcomes when the analysis requires a prospective design.
A retrospective selection remains retrospective.

| Record | Required selection |
| --- | --- |
| `PassageRegion` | One finite, half-open interval per declared coordinate |
| `PassageEvent` | Physical definition, region, productive/reverse/other role and contiguous residence steps |
| `PassageEnsemble` | Exact reference operator, coordinate/image convention, entry distribution and complete event census |
| `FirstPassagePath` | Original trajectory configuration, run, preparation, site, entry-history label and exact weight |
| `FirstPassageSelection` | Complete ensemble/path census, dependence source, assumptions and projection allocation |

The entry region and event regions must not overlap.
Distances use angstrom and signed torsions use radians.
The coordinate definition reuses `UmbrellaWindow` and `ReferenceBiasConvention`.
No restraint, Metropolis sampler or bias from that historical record is executed.
The original trajectory remains unbiased natural-mass dynamics.

Select `NVE` for the existing trajectory operation.
For a stochastic dynamical model, select `DECLARED_UNBIASED_LANGEVIN` with explicit temperature and friction.
That selection reuses the existing BAOAB acquisition and original-noise assessment.
It requires no bias, zero discarded steps and a sample interval of one step.
The passage reader observes every physical frame, including the initial frame.
It reproduces each complete frame's original noise from the selected PCG64DXSM seed and checks both generator states.
Unframed noise from a failed final step remains in original custody without an invented complete-frame assessment.
Bath transport and friction dependence remain explicit unevaluable requirements until their separate assessment.

This selection does not convert arbitrary thermostatted sampling into an admitted physical rate.
Biased windows, altered bath operands and omitted initial time refuse the passage read.
The original records, clocks, noise and evidence scope remain unchanged.

One ensemble retains one reference operator, integration step and selected horizon.
Different operators or step refinements require separate ensembles.
Every run's path weights must sum exactly to one.
`PathWeight` uses reduced integer fractions, including exact thirds and other nonterminating decimal fractions.
Identical deterministic phase histories cannot become separate run labels.

Preparation, site and history labels retain the declared nesting.
They do not establish independent biological observations.
An optional free dissolved gas concentration requires its source and uses uM.
Pressure or total added gas cannot substitute for this operand.
One supplied concentration establishes no dilute concentration scaling.

## Read or export

Use `api.domain_composition.rubisco_response.physical_first_passage`.
Construct one `RetainedFirstPassagePath` carrier for each selected path, in the same order.
Keep original source and outcome-access checks active throughout the read.

```python
report, arrays = read_first_passages(
    selection=selection,
    sources=original_path_carriers,
    assessor_source=assessor_source,
)
exported = export_first_passages(
    selection=selection,
    sources=original_path_carriers,
    project_root=project_root,
    artifact_writer=artifact_writer,
    output_relative_path="selected/first-passages",
)
```

Use either read or export for the required action.
Export performs the original read itself.
It returns paths for `selection.json`, `evidence.json`, `readout.json`, `arrays.npz` and `report.txt`.
The closed package retains original receipt ancestry, numerical provenance, every path and each original cost.

Call `read_first_passage_export` with the returned relative directory, original carriers and artifact writer.
It authenticates all package members and reconstructs the original path analysis.
It performs no force evaluation or native retry.
Original-byte changes during reduction refuse the return.

The reader checks the complete projected size before it opens an original result.
The named-array transport has a 64 MiB expanded bound and at most 256 members.
The selected workspace also accounts for frame metadata and complete physical arrays.
An exceeded allocation refuses the whole analysis.

## Events, residence and recrossings

The existing trajectory reader independently checks original mechanics, masses, phase and clock.
The passage observer receives each frame after that check.
It independently reconstructs coordinates from the complete physical atom array.
It retains the coordinate digest and exact integer physical step.

An event occurs at the first completed contiguous residence in its selected region.
Zero residence steps select the first observed entrance.
One residence step requires two consecutive frames in the region.
An intervening departure resets that residence count.
The event clock is the confirmation clock, including the selected residence delay.

The readout retains entrance and confirmation steps separately.
It also retains every later region visit, departure and residence interval.
These observations expose recrossing of the selected geometric regions.
They are not a reactive-flux transmission coefficient or a validated chemical committor.

Adjacent grid points give the reported time-resolution interval.
No interpolation, continuous-path crossing proof or resolution below the physical step is supplied.
Unobserved motion between frames remains a step-refinement requirement.
Unwrapped molecular coordinates retain the selected periodic-image convention.

## Missing paths and finite-horizon accounting

A mechanically acceptable prefix can retain an observed confirmed event after a later native failure.
That failure and its cost remain visible.
A valid prefix without an event is a computational truncation.
It is not automatically noninformative censoring.

A complete valid horizon without an event is `HORIZON_CENSORED`.
Missing criteria, failed mechanics, an invalid entry or unavailable GPU observations retain distinct unassessed dispositions.
Their assigned weight remains in the unresolved denominator.
No subset is renormalized after failures.

Each run retains cause-specific observed probability and unresolved weight.
The horizon-event bounds include computationally unobserved paths.
Eventual-event bounds also include paths censored at the selected horizon.
All declared exits, including inactive or misprocessing exits, remain separate causes.

The restricted mean first-passage bounds retain the complete selected horizon.
An unobserved tail prevents a complete mean-exit estimate.
These bounds describe unknown values in the weighted empirical paths.
They are not sampling confidence intervals or physical-model error bounds.
Equal-run summaries retain every original run and all joint path results.

The analysis supplies no automatic memoryless rate or reciprocal censored mean.
An absent reverse event does not establish a zero reverse rate.
Productive commitment, effective return, concentration scaling and state reduction require their own assessment.
The [retained rate assessment](physical-rate-assessment.md) supplies conditional hazard checks and complete processing/encounter joins.
The [physical supplier](physical-rate-supplier-v1.md) defines their separate physical requirements.

## Exact weighted-path resampling

`resample_weighted_paths` acts on a complete tuple of `WeightedPathState` records.
`WeightedResamplingSelection` fixes bins, offspring counts, the PCG64DXSM seed and an integer workspace allowance.
Only active paths at the same physical time are resampled within each original run.
Terminal, censored, missing and failed paths retain their original weights.

Each occupied bin uses weight-proportional multinomial parent selection.
Every offspring receives the bin's exact total weight divided by its selected offspring count.
Integer rejection sampling avoids floating-point probability rounding and modulo bias.
Every random word, rejected draw, original parent and offspring remains in `WeightedResamplingEvidence`.

A child inherits its chosen parent's whole history and phase.
Unselected parent histories remain in the original census.
`assess_weighted_resampling` checks categorical intervals, random words, exact weights, ancestry and unchanged clocks.
Resampling adds zero physical steps and zero independent units.
This construction follows the path-resampling interpretation of weighted ensembles.

Deterministic NVE clones have identical futures under identical dynamics.
Resampling does not add stochastic dynamics, change velocities or promise acceleration from those clones.

## Prepare and execute subsequent segments

Use `api.domain_composition.rubisco_response.weighted_paths` for continuation and campaign reconstruction.
`WeightedContinuationRule` fixes the initial path selection, bins, next segment, total physical horizon and boundary tolerances.
It also binds the resampling selection and the stochastic stream-derivation seed.
The boundary tolerances use kJ/mol for energy and kJ/mol/angstrom for gradients.
The total horizon counts physical integration steps; resampling contributes no steps.

Use disjoint `WeightedBinMap` regions and an explicit outside bin for each ensemble.
Start a `WeightedPathCampaign` with that rule and an empty continuation tuple.
Read it with `read_weighted_path_campaign` and the complete original carrier census.
The returned `paths` and `histories` supply the resampling inputs.
Do not construct endpoint phases, histories or active-path statuses by hand.

```python
current = read_weighted_path_campaign(
    selection=campaign, sources=original_path_carriers, assessor_source=assessor_source,
)
sampled = resample_weighted_paths(selection=resampling_selection, paths=current["paths"])
active_histories = tuple(
    history for state, history in zip(current["paths"], current["histories"], strict=True)
    if state.disposition == "ACTIVE"
)
next_segment = prepare_weighted_continuation(
    rule=continuation_rule, resampling=sampled,
    histories=active_histories, assessor_source=assessor_source,
)
authored = author_weighted_continuation(
    prepared=next_segment["prepared"], histories=active_histories,
    raw_sources=original_raw_source_records, project_root=project_root,
    work_directory=selected_native_directory, artifact_writer=artifact_writer,
    output_dir=selected_authoring_directory,
)
```

Preparation reads every active parent, including parents with zero offspring.
It authenticates every original segment and the complete endpoint coordinates and velocities.
It refuses an unknown, failed, invalid or absorbed predecessor.
The full phase, original result identity and accumulated physical clock become each child's exact input.
Stochastic children receive derived, distinct seeds with a check against retained parent streams.
They keep the same bath, integration step and original run label.

Authoring returns `preparation_path` and the existing recursive handoff paths under `children`.
Use those child handoffs with the ordinary [execution procedure](../../../../../docs/using/designing-and-running-an-experiment.md#researcher-procedure).
Authoring performs no native entry.
It binds preparation and original receipt ancestry to every child input.
`read_weighted_continuation_preparation` authenticates the retained preparation and derives it again from original histories.

Keep every original attempt, including a child with no supplied result.
Append the returned preparation to the campaign's ordered continuation tuple.
Supply all original root and child carriers, sorted by path ID, for the next campaign read.
Use a distinct prospective resampling seed for each wave.
Later rules retain the original ensembles, bins, integration step, total horizon and boundary criteria.

The campaign reader reconstructs every population and derives every preparation again.
It removes the duplicated boundary frame from the accumulated clock.
Residence confirmation can cross a segment boundary without a reset.
It compares the new initial energy and gradient with the preceding final return.
For NVE paths, it also checks the whole accumulated position/velocity recurrence, energy drift and selected momentum criterion.
Segment-wise acceptance cannot replace these cumulative checks.

An unfinished scheduled continuation remains unresolved at the total horizon.
A missing or failed child retains its weight and known prefix.
An absorbed path retains its event and receives no further native segment.
Native recovery uses the original operation's retained completion and unknown-contact refusal.
An incomplete authoring retains its files; select a fresh authoring destination for the same prepared inputs.

Use `export_weighted_path_campaign` and `read_weighted_path_export` for a closed package and independent reconstruction.
They return the same five member names as the initial first-passage export.
The package retains every population, original history, boundary finding and unique original cost.
Parents with zero offspring remain in this cost census.
When local result labels collide, the array manifest uses separate canonical source references.
Each reference binds the unchanged original configuration, result and receipt; the readout includes that binding.
Descendants remain nested within their original runs.
Campaign acceptance establishes no entry-distribution validity, bath transport, physical rate or biological prediction.

## References and research

Zhang, Jasnow and Zuckerman (2010), [*The weighted ensemble path sampling method is statistically exact for a broad class of stochastic processes and binning procedures*](https://arxiv.org/abs/0810.1963).
The path-resampling derivation supports weighted parent selection and inherited complete histories.
It does not qualify the selected molecular dynamics, entry ensemble or physical event definitions.

The [original trajectory guide](reference-trajectory.md) owns force capture, physical time and independent mechanics checks.
The [physical supplier](physical-rate-supplier-v1.md#unbiased-first-passage-sampling) specifies the separate gas, processing and rate requirements.
