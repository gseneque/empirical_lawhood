# Specify paired Rubisco kinetics and their scientific limits

SPDX-License-Identifier: CC-BY-4.0

This specification defines paired Rubisco predictions and their acceptance requirements.
It separates conditional mathematics from biological prediction and measured computational benefit.
Use it to bind materials, chemistry, rate evidence, uncertainty and the complete case census before execution.

## Scientific question and combined milestone

The target question concerns Galdieria partita WT and the sequence-defined SSU I95M candidate.
The candidate must improve carboxylation turnover while preserving specificity in a matched assay context.
A successful scientific delivery also requires validated prediction and Matrix-informed computational benefit.
A conditional reference forecast does not close either missing requirement.

The [study record](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/study.py) asks which conclusions follow from supplied joint parameter support.
It reports the requirements that remain between that conditional result and the combined milestone.
Its biological predictive calibration is always `NOT_ESTABLISHED`.
The existing [supplied-kinetics example](../rubisco-kinetic-join/guide.md) retains its original, separate evidence meaning.

The narrower [initial joint-root protocol](initial-root-v1.md) retains the original unresolved M1/V1 conjunction and twelve physical requirements.
The [paired preparation-response specification](preparation-response-v1.md) defines a separate local investigation of a formation-relevant force response.
Its checkpoint, response, assessment and inquiry extensions are implemented through the existing recursive services.
Its [retained acceptance](preparation-response-v1.md#implementation-and-retained-acceptance) establishes component behavior at named source scopes, with complete installed/deployment acceptance still pending.
The later remediation snapshot has artifact and harness inspection acceptance only; the scientific selection and acquisition counts remain under owner review.
Retained continuation and finite read reuse preserve the original design and exposed evidence. They do not add independent units, acquire missing observations or endorse a revised roster.
The actual molecular questions remain unanswered.
That local investigation supplies neither the broader combined milestone nor a kinetic contrast without the required physical connections.

## Materials, processing and exposure

The [retained nomination reader](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/nomination_reuse.py) checks the original dossier and producer receipt.
It derives complete parent and mutant sequences from the dossier's authenticated source members.
The Gp candidate changes I95 to M in all eight SSUs and retains identical LSU sequences.
M1 and V1 are distinct complete processing views; neither changes linear residue numbering.
The source mapping also retains structural author I112.

The initial nomination selection retains five paired cases:

| Case | Parent and child | Role |
| --- | --- | --- |
| Gp M1 | Full WT and all-eight-SSU I95M | Candidate processing view |
| Gp V1 | Full WT and all-eight-SSU I95M | Candidate processing view |
| Gp M1 no change | The same full WT material in both arms | Mathematical identity control |
| Gp V1 no change | The same full WT material in both arms | Mathematical identity control |
| Matched Te donor | Te-P415A with WT SSU, then the same LSU background with SSU V98M | Exposed donor contrast |

The donor effect is not an I95M effect estimate.
A conditional favorable witness is not a nominated effect magnitude.
The [nomination record](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/acceptance.py) therefore stores direction separately from an optional sourced magnitude interval.
An absent magnitude stays absent.
The readout compares a nominated prediction separately from the candidate decision.

A sequence selection does not admit physical assembly, expression, processing or catalytic activity.
Logical chain names are not structural author chains or atom mappings.
Source groups retain their original exposure.
Processing views, alternative parameters, active sites and repeated numerical evaluations are nested views, not new biological units.
Current conditional studies contain zero independent biological observations.

## Assay and all-site chemical selections

The [context records](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/contexts.py) require all eight active-site assignments.
Each assignment identifies its LSU chain, catalytic lysine, carbamylation, magnesium, ligand, protonation, tautomer and metal-coordination selections.
The complete protocol also identifies solvent, ions and the treatment of other-site coupling.
The same selected protocol must map to the paired full sequences.
Its existence does not establish physical admission.

An active assay context refuses CABP-inhibited or partly unactivated site selections.
Changing one CABP-bound site while retaining seven inhibited sites does not meet that context.
A mixed preparation needs its own explicit state and applicability assessment.

Bind temperature, pH treatment, saturating RuBP, dissolved bulk gas concentrations and product handling.
Turnover means carboxylation events per active site per second.
Two 3-PGA molecules per event do not double event turnover.
The physical clock is seconds; capture coefficients use micromolar dissolved bulk gas.

The historical 298 K preparation does not identify the 298.15 K assay context.
Choose a new temperature selection or supply a separate temperature-conversion assessment.
Changed temperature changes the exact context identity.
The source-bound rate ledger must refer to that same context.

The [molecular representation](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/molecular_atoms.py)
retains the full native atom order, all chain/residue mappings, native masses
and exact charge values with their conversion scale. Coordinate arrays retain
their complete shape and hash. Finite sequence changes and chemical-state
transformations have separate [change records](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/molecular_transform.py).
Every common, removed or added atom and changed parameter or bond remains in
the denominator. Atom indices alone do not establish physical correspondence.

The [independent preparation reducer](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/molecular_assessment.py)
uses exact retained topology, coordinate, heavy-atom and origin files.
All-site ligand graphs and complete native force returns have separate joins.
Selected numerical contact/force limits, original operational failures,
partial returns and unknown costs remain explicit. A satisfied numerical check
does not satisfy physical ensemble, chemical accuracy, source-origin admission
or kinetic validity. Native execution still requires the selected supplier and
its actual source, environment, access, execution and resource prerequisites.

The [preparation census](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/molecular_preparation.py)
derives both endpoints across every selected case, chemistry and parameter model.
Case sequences retain their distinct processing views.
Missing, failed and uncertain members remain in the full denominator.
The reducer independently rechecks each available finite atom transformation.
Complete bookkeeping and numerical success leave physical and chemical admission open.

## Provisional kinetic relation

The [four-state model](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_prediction/kinetic_model.py) is a conditional development closure:

```text
E0 -> E*             a
E* -> E0             b
E* + CO2 -> EC       c [CO2]
EC -> E* + CO2       d_C
EC -> E0 + products  r_C
E* + O2 -> EO        o [O2]
EO -> E* + O2        d_O
EO -> E0 + products  r_O
```

All rates except capture coefficients have units of inverse seconds.
The capture coefficients have units of inverse micromolar per second.
Formation, capture and product-return rates must be positive.
Reverse rates may be exactly zero; zero remains distinct from uncertain positive support.
The concentration standard state is one micromolar.

The solver normalizes the stationary balance equations and returns event fluxes.
It retains exact rational intrinsic constants and derivatives with respect to every rate.
The [independent assessor](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_prediction/kinetic_model_assessment.py) checks balance, normalization, fluxes, constants and sensitivities.
It does not invoke the producer or a molecular backend.

With chi_C = r_C / (r_C + d_C) and chi_O = r_O / (r_O + d_O), the closure gives:

```text
kcat_C = a r_C / (a + r_C)
K_C    = (a + b)(d_C + r_C) / [c(a + r_C)]
S_C/O  = c chi_C / (o chi_O)
```

The intrinsic K_C comes from the zero-oxygen carbon-dioxide response.
At fixed dissolved oxygen, apparent K_C equals intrinsic K_C times (1 + [O2] / K_O).
These are distinct output meanings.
Common gating through a and b cancels from specificity.
If mutation-invariant discrimination and commitment are imposed, unchanged specificity is a conditional identity, not independent evidence of preservation.

## Rate evidence and joint propagation

The [parameter ledger](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/rate_contracts.py) retains all eight rates.
Each entry binds transition meaning, units, supplier route, evidence kind, dependence, applicability limits, bounds and unresolved requirements.
The ledger distinguishes measurements, computations, derivations, nuisance support, imposed assumptions and unidentified rates.
Unassessed evidence retains an admission requirement.
An unidentified rate has no fabricated bounds or point estimate.

Suppliers may use physical transitions, free energy with dynamics, or source-conditioned support.
The [Gp WT/I95M physical-supplier design](physical-rate-supplier-v1.md)
selects matched full-assembly free energies and dynamics, explicit gas access,
finite reverse commitments and an electron-transfer oxygen model. It specifies
the paired calculations and acceptance conditions; actual preparation and
rate evidence remain required.
A free-energy difference alone does not identify a rate.
A physical rate supplier must retain standard states, physical clocks, prefactors, transmission assumptions and supported reverse commitments.
The [activation-rate connection](activation-rate-connection.md)
converts supplied paired activation free energies under those explicit choices;
its arithmetic assessment leaves physical-rate admission unresolved.
Unknown oxygenation chemistry remains consequential when it can change the joint decision.

A paired realization contains complete WT and mutant rate vectors.
Marginal bounds do not define a joint distribution or authorize independent sampling.
The implemented producer maps finite joint points to finite joint endpoint support.
It does not claim that a finite grid encloses every point in a continuous rate box.

Raw WT and mutant endpoints remain in every result.
An optional WT anchor applies the same paired effect to the observed WT reference.
Its joint reference uncertainty and correlations must remain explicit.
An anchor is not a second independent validation of the mutant.
Unknown covariance stays unknown.

The [reference assessor](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/reference_supply.py)
preserves this finite joint support and every original scenario outcome.
It checks local derivative rank for the selected endpoint and rate coordinates.
Two target endpoints leave six unconstrained differential directions in the
eight-rate control. This finding supplies no unique microscopic parameter vector.
Boundary directions and global identification remain distinct questions.

The independent concentration diagnostic checks the complete selected query
census and retains undefined zero-gas specificity ratios.
The state-aggregation diagnostic compares exact outgoing rates between blocks.
A small nonzero mismatch remains a counterexample to exact Markov aggregation.
Neither diagnostic admits physical state meanings or biological accuracy.

[Supplier semantics](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/rate_suppliers.py)
bind clocks, temperature, source standard states, bulk access, paired prefactors,
transmission assumptions, reverse commitments and effective-state assessment.
Each missing premise remains a named requirement beside the original rate support.
Retained work costs keep every actual attempt and its original receipt.
Unknown expenses remain unknown. Analysis-task costs do not identify an expensive
molecular supplier or establish computational benefit.

## Joint support and candidate decisions

Each model scenario retains its original available, failed or unknown state.
Scenarios are alternative explanations for the same candidate.
They are not independent cases that can be combined with an any-member-fails rule.
The [joint assessor](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_prediction/paired_assessment.py) uses the nonempty union of their supported regions.

The decision binds its exact paired case and assay context.
Select a minimum turnover ratio, a minimum specificity ratio, optional absolute floors and the next action.
Strict specificity preservation requires a ratio of at least one.
A permitted loss must be labeled exploratory.
Select strict turnover increase when equality is insufficient.

| Complete supported union | Conditional action |
| --- | --- |
| Nonempty and wholly acceptable | ADVANCE |
| Nonempty and wholly outside the acceptable region | DEPRIORITIZE |
| Crosses the decision boundary, with a permitted finite action | REFINE |
| Crosses the boundary without that action | HOLD |
| Empty, unknown, failed without adequate completion, or missing a prerequisite | HOLD |

Finite supports and continuous convex enclosures have different meanings.
A convex enclosure can intersect the acceptable region even when every listed vertex fails a different criterion.
The exact assessor accounts for that intersection.
A finite complexity stop returns HOLD.

A failed scenario may receive a separately assessed conservative completion.
Its failed history, original sources and every other unresolved requirement remain visible.
A completion cannot silently clear unrelated prerequisites.
Declared probabilistic coverage carries its source; it never becomes a model weight or a claimed biological probability of success.

## Accuracy, validation and benefit selections

The [acceptance contract](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/acceptance.py) requires both absolute log-endpoint tolerances and paired log-effect tolerances.
It also binds uncertainty interpretation, useful service, false admission, reference, conventional baseline, cost units and planned reuse.
Specify a finite refinement menu, acquisition ceiling, checkpoint rule, stopping conditions and any reference fallback.
These selections need independent admission for their actual purpose.
The software does not invent missing scientific margins.

The disclosed short-sequence example uses explicit arbitrary criteria to exercise these interfaces.
It selects a zero native-acquisition ceiling.
Its values cannot establish appropriate Gp tolerances, physical rate support, biological coverage or measured computational benefit.

Experimental validation must retain independent units, pairing, calibration and validation roles, and actual held-out axes.
Already exposed nomination or donor evidence cannot become fresh by relabeling.
Predictive validation and Gp applicability remain separate requirements.
Prospective service and cost assessment must retain failures, fallback, unresolved work and offline costs on the full assigned denominator.

## Retained biological evidence and applicability

The [biological source reader](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/biological_sources.py)
retains the original closed source denominator and nomination receipt. All 32
candidate recipes remain available, including absent mutant measurements and
adverse controls. The full nineteen-row Wilson panel retains native means,
standard errors, significance suffixes and column-level replication ranges.
These ranges are not per-enzyme joint sample counts. Turnover and specificity
remain measurements from different reported preparation/assay procedures.
The matched donor changes SSU V98M on the same Te-P415A LSU background.
Its mean ratios are not a Gp I95M effect estimate or a joint confidence region.

The [independent support assessment](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/biological_support.py)
checks every selected case, processing view, target context and declared anchor
use against those retained records. Source sequence equality establishes a
recipe join only. Actual expression, processing, homogeneous assembly, active
chemistry, normalization, paired dependence and mutation-dependent discrepancy
retain separate gaps. Numeric temperature and pH mismatches remain explicit.
A compatible temperature alone does not admit an assay or a physical ensemble.

The original Gp WT catalogue values have unknown uncertainty and unresolved
matched-preparation joins. Reusing them as WT anchors supplies no independent
validation of the mutant. Source and value contradictions remain visible in
anchor assessments. Gp M1/V1 views and new simulation seeds are nested numerical
views or repeated computation, not additional biological labels. The unentered
paired-assay proposal has zero actual assays and remains a proposal.

Each exact predictive requirement in the frozen acceptance and the distinct
Gp-applicability requirement receives an explicit finding. Current exposed
sources leave these requirements UNEVALUABLE. A descriptive adverse mean does
not by itself statistically falsify the joint prediction, and a favorable donor
mean cannot satisfy it. Conditional arithmetic may still recommend an early
candidate action at its stated scope. It cannot close biological validation
or the combined milestone. Future eligible evidence needs separately assessed
source membership, independent-unit allocation, cutoffs and outcome access.

## Scientific requirements and completion

The [requirement graph](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/requirements.py) is built backward from the combined milestone.
It retains biological prediction, Gp applicability, all rate suppliers, physical-state admission, independent validation and computational benefit.
The Matrix handoff remains a named requirement until an eligible programme report supports it.
Adverse and unresolved transfer propositions are valid handoff content.

Scientific prerequisite cycles are rejected separately from executable task cycles.
Each selected connection has procedure, instance, admission and joined-use assessments.
An exact conditional transform can satisfy its scoped mathematical connection.
That finding does not discharge its biological or computational-benefit ancestors.
Completed reads and independent assessment consume retained results without repeating acquisition.

## Scientific finding and report interfaces

The [reference finding report](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/finding_report.py)
reassesses retained outputs independently and keeps the original nominated
prediction distinct from the candidate acceptance region. Direction, magnitude,
conditional action and biological action remain separate fields. A robust
adverse candidate finding can coexist with valid conditional arithmetic.
A failed numerical output cannot inherit an accepted candidate decision.

The combined milestone retains eight components: joint kinetic prediction;
numerical and chemical validity; predictive validity and applicability;
approximation fidelity; prospective recognition and useful service;
computational benefit; reusable implementation; and scientific delivery.
Every component binds the exact frozen acceptance, its criterion, direct evidence
and remaining requirements. Completion requires all eight to be satisfied.
The early-reference interface leaves absent comparative, biological, chemical
and native evidence explicit. Software checks do not satisfy those components.

Complete endpoint and parameter projections include all expected cases,
scenarios and points. Failed or unknown alternatives retain rows without invented
values. Original raw predictions remain in the canonical report even when their
assessment fails. Extra retained case identities are reported separately.
WT anchors, finite joint dependence, original exposure, source revisions and
unavailable uncertainty remain visible. Log bounds describe arithmetic rounding,
not a new uncertainty model.

When original work is supplied, the report binds the exact inquiry specification
and complete work-bound state. Every attempt, recovery witness, cost event and
unknown expense remains in that state. Its scientific target must match the
selected study. Original producing receipts and product locators remain primary
custody. The [export owner](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/report.py)
uses the shared guarded artifact plane, inherits access metadata, rechecks
current original custody and publishes all report members atomically.
Readable text and exact CSV projections accompany the complete canonical record.

## Finite joint indicator, sequential procedure and policy

The indicator stacks WT and mutant log turnover/specificity and their paired
log differences. Paired Jacobian rows are exactly mutant minus WT rows on the
same parameter columns. A finite joint convex hull preserves dependence;
its linear support function is the extrema over the complete declared vertices.
For each output, the largest absolute linear error plus the nonnegative selected
nonlinear allowance is divided by its frozen tolerance. The threshold is one.
A small value establishes only this conditional arithmetic. Error-set coverage,
nonlinear validity and physical applicability require independent evidence.

A finite sequential procedure declares strictly ordered pre-action checkpoints
and all six endpoint error allocations. Their exact sum cannot exceed the
family error probability. Valid endpoint bounds conditional on permitted past
information make the union bound applicable to any stopping checkpoint in that
finite menu, without an independence assumption. Allocations alone establish
no such conditional validity. Calibrated predictors cannot use a zero-risk
allocation as if they were rigorous bounds. Development heuristics cannot admit
reduced work. The selected study retains its original finite-support meaning;
this policy contract does not turn its rate points into a probabilistic region.

The policy extends the full combined-target requirement graph. Complete
four-phase findings are required for active chemistry, exact context and clock,
native acquisition allowance, justified supplier selection and the relevant
indicator, sequential or reference gate. All transitive prerequisites remain in
the action's eligibility denominator. Missing native contact expense or allowance
is not zero. The reference has one declared attempt; a failed return does not
reset it. An actual completed reference can be read only through authenticated
reuse with independent current-use admission. Unknown reference validity blocks
that reuse. The shared service owns actual work, source custody, finite resource
allowances, uncertain-contact recovery and authority.

The complete frozen outcome map retains positive, negative, unevaluable,
missing, failed-execution and uncertain-contact possibilities. Missing authored
successors are explicit HOLD alternatives. Automatic ordering uses the declared
finite policy order, not an invented probability of scientific progress.
No target-closure action is supplied by the exposed policy adapter. Original
candidate decisions and combined-milestone requirements retain their meanings.

Policy validation must retain every assigned case and its original exposure
group. A group receives useful reduced-service credit only when all its nested
selected cases were admitted and their joint errors satisfy the allocation.
An adverse admitted view remains a false admission for the group. Unknown
references remain unresolved, and the reference audit includes refused cases.
Report both complete-assignment and admitted-group false-admission denominators;
freeze which one owns the criterion. Persistent abstention fails useful service.
The service assessor's known/possible bounds describe the retained finite census.
They provide no population confidence, causal authentication or new biological
units. Actual prospective comparison must independently supply those premises.


## Reduction target, signed error and mathematical controls

The target assessment retains the full case/scenario/rate-supplier census.
A local derivative can identify sensitivity at the retained points. A locally
zero derivative cannot exclude importance elsewhere. Conditional reference
analysis supplies neither actual molecular expense nor physical applicability.
Without adequate target justification, only target-independent contracts and
exposed controls are supported. The eligible Matrix handoff remains required.

The signed error convention is log reference minus log approximation.
Its full intermediate sequence is reference, projection, omitted return,
frozen dynamics, finite mutation and final approximation. Adjacent positive
endpoint ratios multiply exactly to the outer ratio on all six output axes.
This identity preserves signed cancellation. The account never replaces it
with a sum of absolute errors. Directed logarithm enclosures cover arithmetic
rounding, and normalization uses the six selected positive log tolerances.
Unknown or failed stages retain their original outcomes and unknown terms.
They are not zero-error contributions. The conventional method has a separate
reference-relative error account under the same selected parity contract.

Raw paired endpoints and optional shared WT anchors retain their original
values and covariance sources. Within-stage covariance does not identify
cross-stage dependence. Shared chemical-model discrepancy lies outside this
comparison. Neither cancellation nor small same-model error establishes
biological validation or independent physical parity.

The exposed controls use the discrete equations `x[n+1] = A[n] x[n] + B[n] u[n]`
and `y[n] = C[n] x[n] + D[n] u[n]`. Their exact finite memory account retains
omitted initial state, omitted driving and returned retained-state history.
A receiver confined to retained coordinates can still depend on that history.
Changing matrices retain their original checkpoint-specific values.
The first-order response includes derivatives of all four matrices, inputs
and initial preparation. The independently checked finite perturbation retains
the residual beyond that first-order response.

These systems have at most eight states, four inputs and thirty-two steps.
Their two receivers, indexed clocks and dimensionless values are mathematical
controls. They select no molecular backend and establish no computational benefit.
The retained assessor checks original local equations and complete arrays.
It does not call the trajectory producer or replace failed arrays with zeros.


## Complete comparison preparation and entry boundaries

The comparison design preserves the original study bytes and the separate
editable experiment specification. Each finite policy binds the exact selected
study, acceptance, checkpoint procedure and case. Shared comparison operands
retain the selected context, reference and conventional method. Criterion edits
require corresponding new policy selections. They do not alter source evidence
or its development exposure.

The code derives three comparison arms for every selected scenario and point.
Failed or unknown scenarios without points retain explicit unresolved members.
All original controls and processing views remain in their exposure groups.
The complete reference audit includes refused cases. No sample of successful
returns can replace that denominator.

Preparation supplies no native authority. Its returned prerequisites distinguish
actual source access and admission, physical state and reference validity,
supplier justification, parity, indicator validity, Matrix transfer, specialist
preflight, resource capacity, storage checks and installed-source acceptance.
Issue, execution and outcome access retain their existing owners. A complete
selection or retained preparation census cannot mark these acts as passed.
The conditional preparer remains available at its original evidence ceiling.


## Retained comparison assessment

The [comparison assessor](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/comparison_assessment.py)
binds the complete frozen design, three original arm reports and full ordered
case decision histories. Original prediction bytes, producing receipts,
completed attempts and scientific work must join the selected method and
study operands. An adopted assessment wrapper alone cannot establish the
original producer's method. Every declared scenario and point remains in the
assignment census, even when its source or output is unknown.

A usable exposed reference requires available original output, a successful
producer-method join and independently satisfied kinetic arithmetic. Each
approximation retains raw values even when its own equation check fails, so
that disagreement against usable truth remains visible. Raw or anchored
comparison is fixed by the design. Absent anchors, stages, parity operands or
truth remain unknown. The signed six-output account retains missing intermediate
terms while independently evaluating a total when its endpoints are available.
Physical parity and biological reference validity remain separate requirements.

Original decision packets retain their shared specification, state, sources,
menu, policy, campaign, right, implementation and optional ACT intent. The
embedded finite selection and all earlier checkpoint identities must match.
Actual HOLD stays HOLD even when an alternative names a supplier. Original
reference already present in pre-action information falsifies causal ordering;
a later read cutoff cannot establish when acquisition happened. Current exposed
records therefore cannot establish prospective qualification.

Useful service, false admission, fallback and reference coverage retain every
assigned exposure group, including refused groups. A known admitted error
exceeding any frozen tolerance takes precedence over missing error at another
point. Unknown truth is never counted as correct. Both false-admission
denominators are retained. The results describe this finite exposed census;
they do not assert population coverage or joint sequential calibration.

The [cost assessor](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/comparison_cost.py)
deduplicates original physical events, preserves conflicting-custody refusals,
and retains all failed or uncertain attempts. Frozen exact scientific-work
allocations distinguish setup, use and common audit. Each arm receives the full
common audit charge. Complete-campaign expense, use plus audit, and
`setup + N * (use + audit)` are separate accounts. Exact rational arithmetic
preserves per-use division and strict break-even inequalities. Missing planned
work, unclassified attempts or unmeasured fields prevent a claimed saving.
An explicitly empty attempt census has zero recorded expense but establishes
no comparative performance. GPU time, peak memory, native-call counts and
campaign elapsed time are not inferred from task costs.


## Integrated delivery and native-entry review

The [integrated report](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/integrated_report.py)
adds complete comparison, target and native-entry findings while preserving the
original reference report schema and bytes. The target must belong to that
exact reference. All eight milestone components retain their frozen acceptance
and unresolved premises. Descriptive comparison failures remain visible in the
complete comparison operand and tables; exposed arithmetic success cannot
establish native approximation fidelity, prospective service or scientific
computational benefit.

The report retains nominated direction and magnitude separately from candidate
selection, biological readiness and combined milestone status. Its complete
case/scenario/point/arm tables include unavailable originals; original decision
histories and failed/uncertain work remain complete. Native-entry requirements
are derived from the preparation owner, without granting source access,
scientific admission, specialist preflight, execution or outcome access.
Current-use molecular evidence requires an authenticated reader at its own
boundary; unguarded records cannot be supplied to this export to replace it.

The [integrated export owner](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/integrated_report.py)
revalidates all original report and decision sources before publishing its
closed ten-member package. Each member inherits the original evidence lineage,
visibility and outcome-access restrictions. Full canonical readout and
human/tabular projections preserve the same complete denominators. Export
changes no original result, creates no fresh unit and runs no acquisition.
Delivering this explicit unresolved result does not close the scientific
milestone or authorize a subsequent native campaign.
