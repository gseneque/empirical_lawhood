# Bind the paired C3–H3/KCX formation operand

SPDX-License-Identifier: CC-BY-4.0

This protocol binds a restrained mean-force estimator and one possible
receiver-specific omission rule for the [initial conditional model](initial-model-v1.md).
It distinguishes the measured restrained integral, its physical corrections
and a formation-rate contrast. None is supplied by force conformance alone.

## States, coordinate and measure

The protocol identifier is `GP-WT-I95M-FORMATION1`. Use the initial model's
matched full-assembly keto/HIE and initial-enolate/KCXH/HIE selections at
`site.gp.lsu.01`. Retain all eight substitutions and other-site assignments.
Use exact returned preparation/relaxation identities, complete atom tables,
natural masses and unchanged native constraints. Unrelaxed constructions are
starting hypotheses, not equilibrium ensembles.

Resolve the actual substrate C3, transferred H3 and accepting KCX oxygen
through retained atom-role assignments. The coordinate is
`xi = d(C3,H3) - d(H3,O_KCX)` in angstrom. Keep the same ordered physical
roles in both arms through the complete finite atomic transformation;
equal native indices do not establish correspondence. Retain common, changed,
added and removed atoms, parameter changes and complete bond differences.

Select the existing full periodic QM/MM operator, fixed cell, temperature,
unconstrained Cartesian coordinates and natural masses. Each distance uses
the documented orthorhombic minimum image. The existing bias reader refuses
unresolved image boundaries and coincident coordinate directions. A later
holonomic constraint or altered mass scheme needs its own measure correction
and cannot enter this estimator as the same ensemble.

For one fixed stiffness `k`, the biased energy is
`U_s(q) = U(q) + k*(xi(q)-s)^2/2`. With a center-independent integration domain
and Cartesian measure:

```text
A_k(s) = -R*T*log integral exp[-U_s(q)/(R*T)] dq
dA_k(s)/ds = <dU_s/ds> = k*(s - <xi>_s)
```

`k` is in kJ/mol/angstrom² in the existing umbrella record. The retained
receiver uses J/mol/angstrom and multiplies by exactly 1000 at that unit
connection. This is a restraint-center derivative. A projection of the
Cartesian reference force onto the coordinate is not substituted for it.

Select all centers, fixed stiffness, original acquisition configurations,
discarded prefixes, complete sample horizons, grouping and block lengths
before acquisition. The supported estimator uses strictly increasing centers
and composite trapezoidal weights. For each arm, all centers share the exact
reference potential, coordinate definition, cell and temperature. Every
selected trace belongs to exactly one node and arm. Do not choose a barrier
maximum retrospectively from a favorable subset of noisy nodes.

## Estimator, uncertainty and free-energy connection

The public
[`restrained_formation`](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/restrained_formation.py)
composition reuses the existing independent equilibrium reader and its
complete native receipts, phase arrays, mass checks, bias checks and sample
projection. It performs no new force calculation. Its closed export retains
the original sampling and MBAR diagnostics, raw coordinate projections,
node means, signed paired integral, coupled block draws, failures and costs.
It also retains the paired integral from each chronological half of every
trace. Select its disagreement tolerance in J/mol before acquisition.
The basin/MBAR contrast diagnostics cannot replace this receiver-specific check.

Use `RestrainedFormationSelection` with an exact `AtomicTransformation` and
the complete `EquilibriumReweightingSelection`. Call
`validate_restrained_formation_inputs` before entry,
`export_restrained_formation` for the retained calculation and
`read_restrained_formation_export` for authenticated reconstruction. Missing
or failed traces retain their prefixes but do not become complete node
estimates. Shared noise/dependence groups retain common block draws. A short
series or unresolved correlation cannot establish equilibrium or guaranteed
confidence coverage.

When only the numerical engine changes, use the public
[`active_model_rebinding`](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/active_model_rebinding.py)
composition. It authenticates the original preparation and preserves every
physical selection, seed and assessment. Its independent reader compares both
publications through their final source checks. Changed coordinates, chemical
settings, force settings or cell parameters require a different preparation.
Engine rebinding supplies no new relaxed state or numerical-conformance evidence.

The paired integral is
`Q_k = sum_i omega_i*(g_M,i-g_W,i)` in J/mol. It estimates a difference of
restrained endpoint free-energy differences. To obtain the activation
free-energy contrast used by `q_a`, separately supply:

1. Finite-restraint/deconvolution and coordinate-measure corrections for the
   declared unrestrained target. Unconstrained center integration does not
   itself require a holonomic Fixman term; it also does not supply an
   unrestrained PMF or reactant normalization.
2. The reactant basin and activation dividing surface, with their
   normalization and any remaining orthogonal-coordinate contribution.
3. Equilibration, hidden-state/preparation coverage, complete sampling
   uncertainty and quadrature discretization error.
4. The paired transmission/prefactor and effective-state aggregation
   connection. Keep the [activation-rate assumptions](activation-rate-connection.md)
   explicit; an electronic energy difference is not an activation free energy.

The current restrained reader leaves these requirements and `q_a` unavailable.
Evidence for them must enter the initial-model reader through assessed original
contrasts or supported bounds. No automatic equality between `Q_k`, an
activation barrier and a rate ratio is selected.

The separate [retained Gaussian response method and molecular extension contract](retained-gaussian-response.md)
describe deterministic retained-space supply of the same declared restrained targets.
The generic numerical method is implemented. Its molecular source, residual,
measure and destination contracts remain additional work.
Quadrature results need their own supplier records; they cannot replace original
trajectories inside this reader or acquire activation-rate meaning automatically.

## Molecular bridge and complete costs

The complete native QM/MM calculation is the reference. Bind a conventional
frozen response and any selected one-update candidate to the actual finite
mutation and paired preparations. Include the direct receiver change, changed
initial state, omitted-state feedback and nonlinear remainder. Matrix FULL
and FULL_REFRESH32 are response approximations, not molecular references.

Use the retained E4 mechanism analysis together with the
[SCI01 comparison](../../../../foundations/emergent-structure/records/matrix-sci01-retained-refresh-v1.md).
Their usable response evidence comes from four independent development groups,
with 36 usable cases and 108 missing origins in the complete 144-case census.
They supply method-design evidence, not a molecular error bound or a fitted
predictor of when a Rubisco approximation will fail.

| Retained mechanism finding | Consequence for this molecular handoff |
| --- | --- |
| E4 distinguishes evolving-operator error from reduction error; their relative sizes change with response time. Persistent factor structure outlasts response adequacy. | Keep both errors separate. A stable relaxed structure does not admit a frozen response over a sampling trajectory. |
| E4 curvature changes dominate some actions, while changing eigendirections dominate complementary actions. Slow-mode contributions are incomplete and signed contributions can cancel. | Construct directions from the selected molecular input and receiver. Assess discarded response and coupling to the environment; neither low frequency nor eigenvalues alone select an adequate representation. |
| SCI01's single refresh improves the assessed absolute response at H64, but supplies no adequate H128 continuation. Its refreshed reduced finite contrasts have adverse diagnostics. | Treat one causal update as a candidate at a prospectively selected molecular checkpoint. Assess the WT–mutant difference directly. Do not transfer Matrix rank, clocks, tolerances or error percentages. |
| E4's revealed-path tangent is an accurate diagnostic on its observed paths. | It requires future native-path information. Count that acquisition when using the diagnostic; it cannot serve as a free prospective operator update. |

For a selected response diagnostic, retain the signed decomposition into
native-minus-path-tangent, path-tangent-minus-frozen-full and
frozen-full-minus-reduced terms, with their cross terms. Use the corresponding
refreshed-full intermediate when assessing an updated reduction. Leave an
unavailable component explicit; do not acquire a full molecular Hessian or
future path merely to fill this diagnostic. The small finite-amplitude
remainder in Matrix does not bound the finite I95M mutation remainder.

Bind molecular force directions to the actual coordinate gradient, masses and
constraints, including the environment's response. A projected-operator update
and a basis change are different operations. A one-update candidate keeps its
selected basis, instrument and own predicted state; it cannot silently rebuild
the basis or reset to an observed response. Require actual evidence for its
retained directions and horizon. Matrix potential-term attributions do not
identify a Rubisco term that may be removed.

Before a bridge acquisition, retain a separate executable selection containing
the actual states/atom correspondence, centers/stiffness, tolerance in physical
units, integration horizon and any update checkpoint, finite reuse count,
full work allocation and stopping rule. No universal Matrix rank, tick count
or molecule-independent error tolerance is assigned here. A missing molecular
HVP/JVP supplier or coverage argument leaves the candidate unavailable.

Charge complete native calls and basis/operator construction, observations,
preparation, qualification, transfer, updates, fallback, verification and
failed/uncertain work. A scalar observation still needs the reference dynamics
that produced its ensemble. Computing both native trajectories first may
measure a diagnostic error, but cannot count as avoiding those trajectories.
Keep the native reference when the candidate has no supported net saving.
The first matched-state relaxation is a separate preparation stage. It does
not execute a response approximation, select a production sampling horizon or
qualify a shortcut. A refusal of the receiver-bound omission below closes that
candidate only. The molecular bridge remains a separate fidelity/cost decision;
no automatic approximation campaign or unpriced production sampling follows.

## One paired receiver bound

The shared orthorhombic cell also supplies a distribution-free geometric
bound for the **bare discrete restrained integral**. Let `D` be its diagonal.
Each minimum-image distance lies in `[0,D/2]`, so `xi` lies in `[-D/2,D/2]`.
At a shared center, `|g_M-g_W| <= 1000*k*D`. Positive trapezoidal weights sum
to the center span `L`, hence `|Q_k| <= 1000*k*D*L`.
For a supplied approximation, `|Q_hat-Q_k| <= |Q_hat|+1000*k*D*L`.
This bound covers arbitrary paired preparation distributions within that cell.
It uses no assumption of WT/mutant cancellation and needs no trajectory.

`periodic_receiver_omission_coefficient` computes the coefficient with outward
rational rounding. Its independent assessor checks exact squared inequalities.
Actual cell and coordinate correspondence must be authenticated separately.
This geometric enclosure supplies no activation-barrier correction bound.
A bound on all corrections is still required before omitting work used by `q_a`.

The narrowly scoped task is whether to omit a specified future native
formation quadrature or operator update. For each selected node retain signed
force-receiver errors and explicit paired correction coordinates:

```text
delta_Q = sum_i omega_i*(e_M,i-e_W,i)
          + delta_coordinate_and_restraint
          + delta_hidden_state_feedback
          + delta_nonlinear_and_direct_mutation
          + delta_preparation + delta_quadrature + delta_sampling
```

Let the complete joint error vector lie in a **justified enclosing** convex
hull with vertices `v_j`. With
`l = (-omega, +omega, 1, 1, 1, 1, 1, 1)`, linearity gives
`min_j l*v_j <= delta_Q <= max_j l*v_j` and
`|delta_Q| <= max_j |l*v_j|`. These are exact support-function identities.
Signed cancellation is retained; adding independent marginal maxima is not
silently substituted for the supplied joint support.

[`bound_paired_receiver`](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/paired_receiver_bound.py)
implements the paired sum; `assess_paired_receiver_bound` independently
reconstructs the dual projection. It checks the complete correction census,
the selected physical tolerance, source availability before the decision and
complete conservative costs. A candidate requires four reviewed premises:
coverage of the actual molecular error, completeness of the decomposition,
the exact selected estimator/ensemble and evidence available before omitted
work. The reader checks the declared records; it does not prove their
scientific assertions by checking a label.

For a supported omission the avoided-cost lower bound must strictly exceed
the sum of all added-cost upper bounds in the same explicitly supported unit.
Unknown development, qualification, observation, update, transfer, fallback,
preparation, verification or failed-work cost is not zero. Missing support,
future/foreign-clock evidence, required outputs of the work being omitted,
an exceeded tolerance or nonpositive saving returns `RETAIN_NATIVE_REFERENCE`.
A heuristic or finite calibration without admitted simultaneous stopping
coverage cannot justify omission. This contract supplies no sequential
risk-spending procedure and no physical-rate admission.

The derivation can therefore end with a documented unresolved or adverse
stop. Such a finding completes the bounded investigation only at its stated
scope; it does not complete molecular preparation, the native bridge or the
forecast. Preserve its evidence and proceed with the selected reference work.
