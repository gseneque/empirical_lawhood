# Physical rate supplier for the paired Gp WT/I95M reference

SPDX-License-Identifier: CC-BY-4.0

## Selection and scope

**Selected scientific design: GP-WT-I95M-REF1, 28 October 2026.** Use matched
full-assembly QM/MM free-energy calculations, unbiased dynamical rate checks,
and explicit gas-encounter and oxygen electron-transfer calculations. Derive
the paired kinetic response from those calculations. The
[kinetic specification](scientific-specification.md)
owns the endpoints and decision; this document owns their molecular suppliers.

This selects a research model and the calculations needed to test it. It does
not declare the model physically validated, provide calculated Gp rates, or
constitute a prepared native execution. The present evidence contains no
admitted Gp WT/I95M rate contrasts. Molecular preparation, implementation of the
selected reference, measured cost and the enzyme resource allocation remain
separate execution requirements. A refused or unaffordable calculation leaves
its operand missing; it does not license a cheaper unassessed rate substitute.

The first deliverable is a conditional joint reference answer for turnover and
specificity. It does not require identifying all eight microscopic rates if
the four effective contrasts below suffice. Absolute endpoints and affinity
constants require their additional rate or compatible anchoring evidence.
Matrix approximation and speedup experiments follow the reference; they do not
select its physical answer.

## Evidence that determines this choice

| Retained evidence | Consequence for the selected supplier |
| --- | --- |
| Authenticated Gp nomination and full sequence/source census | Preserve both M1/V1 views, identical LSU sequences and I95M in all eight SSUs. The source contains eight inhibitors and 168 missing LSU residues; it is not an active assay model. |
| [Ethane and molecular preparation requirements](guide.md#prepare-molecular-correspondence-for-a-selected-supplier) | The retained 97-point force diagnostic is a numerical control. It supplies no enzyme chemical accuracy, reaction barrier or mutation response. |
| [Electronic pilot](../../records/enolate-electronic-result-v2.md) | Carbon-site populations and ionization changes can move together. Neither a HOMO weight nor a vertical ionization energy is a kinetic coefficient. |
| [Branch sensitivity](../../records/branch-sensitivity-result-v3.md) | Both specificity gain and loss occur under the exposed illustrative oxygen hypotheses. Their driving-energy grid, reorganization energies and unchanged prefactors are not Gp bounds. |
| [Productive-cycle and source assessment](../../records/scientific-supplier-search.md) | Productive processing, enolization and product release must be distinguished. Inhibitor dissociation supplies none of their rates. |
| [Reaction-source preparation](../../records/reactive-preparation-result.md) | Carbon and oxygen structures supply chemical hypotheses and atom-mapping controls. Different species, protonation states, fragments and electronic methods cannot be spliced into a paired Gp barrier difference. |

The carbon reference study supports testing proton transfer and reversible
free energies, rather than assigning its spinach result to Gp. The oxygen
study supports an electron-transfer hypothesis and identifies assumptions that
must be recalculated in the paired enzyme. Neither supplies an I95M rate.
[Carbon reference](https://doi.org/10.1021/acscatal.2c01677),
[oxygen reference](https://doi.org/10.1073/pnas.2008824117).

## Fixed materials, context and reference potential

Run two separate paired cases: M1 WT/I95M and V1 WT/I95M. Retain all eight LSUs
and eight SSUs, all missing sequence segments, explicit solvent and ions, and
the finite substitutions with their complete atom correspondence. M1 changes
the source SSU V1 to M in both arms. Source author I112 maps to candidate
sequence I95. Sites, frames and the two processing cases are not independent
biological replicates. Preserve the original no-change controls and exposed
matched donor as their own roles; donor effects do not fill Gp inputs.

Select **298.15 K, pH 8.0, fully carbamylated Mg-bound enzyme, saturating RuBP,
initial-rate product sinks**, and concentrations of free dissolved CO2 and O2.
The pH specifies a proton reservoir and a chemical-state assessment, not a
constant-pH simulation implied by a label. Retain actual salt, free-magnesium
and buffer activities in the prepared context; absent activity inputs prevent
an assay-specific absolute forecast. Do not reinterpret historical 298 K
calculations as this context.

All eight sites start with active RuBP rather than CABP. The initial E0 graph
uses keto RuBP(4-) and deprotonated carbamylated lysine. Resolve C3 proton
abstraction, transfer to substrate O2, and O3 deprotonation as separate linked
steps. The first enolate is not automatically the reactive E* ensemble.
Preserve every transferred atom and the charge of the complete subsystem.
RuBP(4-) is the selected initial phosphate state,
consistent with the [ChEBI tetraanion definition](https://www.ebi.ac.uk/chebi/CHEBI:57870),
not proof of its protein-pocket population. The retained neutral RUB dictionary
and spinach/Ca coordinates are chemical and geometric sources, not the Gp/Mg
state. Construct and assess the new graphs explicitly.

Use a fixed chemical sensitivity set: reactive enolate with protonated KCX
and neutral histidine (both neutral tautomers), and reactive enolate with
deprotonated KCX and protonated histidine. Cross these three proton-allocation
states with occupied/unoccupied sixth Mg water coordination. Include their
interconversion in the formation/reversal calculation; do not assume equal
populations, rapid exchange or an intrinsically inactive competing state.
These are Gp hypotheses motivated by the carbon study's proton-relay model,
not a transfer of its state probabilities or barrier values.
Map residues through the actual full sequences and native atoms; do not copy
spinach or R. rubrum residue numbers. Keep these alternatives separate until
their populations or a decision valid across all alternatives are supported.
A newly implicated protonation or misprocessing state triggers an explicit
revision; it is not silently averaged into a favorable existing state.

The selected **conditional reference potential** is electrostatically embedded
QM/MM: omega-B97X/def2-SVPD for the reactive subsystem, ff14SB/TIP3P for the
surrounding protein/water, and explicit assessed parameters for nonstandard
residues, ligands and ions. Use the same functional, basis and MM conventions
in both arms. This is a new design choice, not a claimed reproduction of the
spinach calculation or a qualification inherited from the reduced electronic
pilot. Use def2-TZVPD paired corrections as the declared basis-sensitivity check;
do not choose the basis from the resulting I95M sign.

At each focal site include the complete reacting ligand/gas, Mg, KCX, its
first-shell ligands, the mapped catalytic proton-relay residues and participating
waters in the QM region. Define its exact atom set, caps, electron count and
charge from the prepared chemical graph before energy calls. Keep that region
fixed over a path. Preserve the complete enzyme environment; an isolated LSU
fragment cannot be the mutation-sensitive supplier. Evaluate the eight focal
sites as nested views of each assembly, not eight simultaneous QM calculations
or eight independent preparations. The other seven sites remain active
RuBP/Mg/KCX sites under the declared occupancy scenario. Assess other-site
occupancy dependence before interpreting this conditional scenario as turnover
of an asynchronous enzyme.

The coupled energy must contain the QM energy in the MM electrostatic field,
the remaining MM energy, QM/MM van der Waals and boundary terms exactly once.
Its force must differentiate that same energy, including MM embedding and
link-atom forces. Periodic electrostatics and their subtraction/correction must
be consistent with the selected MM model. Bare PySCF point-charge embedding is
not this complete coupled operator: it omits MM and cross van der Waals terms.
[PySCF QM/MM contract](https://pyscf.org/user/qmmm.html).

The existing GFN2-xTB force route may supply disclosed preparation/diagnostic
work. It is not the selected oxygen surface or an automatic substitute for this
reference. Sampling under another potential can contribute only after a
separately assessed, overlapping reweighting to the reference. A static energy
offset cannot promote its trajectories to reference dynamical rates.

## Paired calculations and the parameters they constrain

Use the same preparations, chemical alternatives, state definitions and
reference Hamiltonian across each WT/mutant pair. Preserve their shared
sampling and systematic errors.

| Calculation | States and actual retained observables | Rate/effect supplied |
| --- | --- | --- |
| Formation and reversal | E0 to the reactive enolate E*; coupled C3-H/KCX proton-transfer coordinate, alternative relay coordinates, opening/closing and reactive-state populations. Retain forward and reverse free energies and reactive-flux checks. | `a`, `b`; paired effective formation contrast `q_a` after aggregation assessment. |
| CO2 access and addition | Bulk CO2 to a defined encounter region; entry, escape and orientation statistics; then enolate-C2/CO2-C bond formation with proton/water coordinates. Retain association, local chemical and reverse pathways. | `c`, `d_c`; the carbon part of gas discrimination and carbon commitment. |
| O2 access and activation | Bulk O2 encounter statistics; donor/acceptor diabatic energy gaps, electronic couplings, triplet radical-pair formation, spin conversion, recombination, return and peroxide entry. | `o`, `d_o`; the oxygen part of discrimination and commitment under the selected SET model. |
| Carbon-product processing | Carboxylated intermediate through hydration, C-C cleavage, stereospecific protonation, both PGA releases and return to substrate-ready E0. Retain competing returns and waiting times. | `r_c` and carbon productive probability; paired effective processing contrast `q_r`. |
| Oxygen-product processing | Peroxide/intermediate through cleavage, PGA plus phosphoglycolate release and return to E0, with unproductive exits retained. | `r_o` and oxygen productive probability. |

Use restrained-path umbrella sampling for chemical free energies and unbiased
short trajectories from the dividing ensemble for dynamical checks. Path
coordinates begin with the chemical changes above and must pass committor and
alternative-coordinate tests. A maximum along one guessed distance is not a
qualified transition state. Hydration/cleavage and product release are separate
calculations; do not declare the one with a convenient barrier rate limiting.
Combine overlapping equilibrium windows using MBAR with correlated sampling
and the actual bias potentials retained. Its equilibrium uncertainty estimate
does not establish a dynamical rate or physical-model accuracy.
[Primary MBAR method](https://arxiv.org/abs/0801.1426).

### Implemented umbrella-bias arithmetic

The [bias component](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/periodic_bias.py)
evaluates the three coordinate kinds declared by existing `UmbrellaWindow` records.
It returns bias energy and analytic Cartesian gradients.
Use `evaluate_reference_umbrella_bias` only with an explicit `ReferenceBiasConvention`.
That convention binds the unchanged window identity, units and geometric definitions.
It does not execute the window's historical Metropolis schedule.

| Coordinate kind | Ordered-atom definition | Center unit | Force-constant unit |
| --- | --- | --- | --- |
| `DISTANCE` | Distance between atoms 1 and 2 | `ANGSTROM` | `KJ_PER_MOL_PER_ANGSTROM_SQUARED` |
| `DISTANCE_DIFFERENCE` | Distance 1–2 minus distance 2–3 | `ANGSTROM` | `KJ_PER_MOL_PER_ANGSTROM_SQUARED` |
| `IMPROPER_DIHEDRAL` | Signed torsion along ordered atoms 1–2–3–4 | `RADIAN` | `KJ_PER_MOL_PER_RADIAN_SQUARED` |

Select `DISTANCE_12_MINUS_DISTANCE_23` for the difference convention.
Select `SIGNED_ORDERED_TORSION_SHORTEST_ANGULAR_RESTRAINT` for the torsion convention.
Select `ORTHORHOMBIC_MINIMUM_IMAGE_EACH_CONSECUTIVE_BOND` for periodic images.
The torsion definition infers neither connectivity nor a central-atom permutation.
Torsion centers must lie within `[-pi, pi]`.
The restraint uses the shortest signed angular displacement from its center.

Each term has energy `k * displacement**2 / 2`.
The total gradient includes every physical atom, with zero rows for unrestrained atoms.
Energy uses kJ/mol; Cartesian derivatives use kJ/mol/Angstrom.
Force is the negative derivative.
The return also exposes coordinate values, local derivatives and individual bias energies.
No reference energy or force is included.

Supply the complete physical atom order, actual coordinates and fixed orthorhombic cell.
The acquisition owner must authenticate their correspondence to the selected material.
Undefined bond directions, collinear torsion planes, periodic-image boundaries and angular-restraint cusps cause refusal.
The periodic-image guard includes floating-point resolution at the supplied coordinate magnitude.
Keep the reference and bias arrays separate in original custody.
Do not supply biased forces to the unbiased diagnostic trajectory operation.

[Focused checks](../../../../../tests/test_rubisco_periodic_bias.py) cover independent energy differences, symmetries, units, identities and singularities.
Exposed native comparisons use OpenMM's
[bond expressions](https://docs.openmm.org/latest/api-python/generated/openmm.openmm.CustomCompoundBondForce.html)
and [torsion expressions](https://docs.openmm.org/latest/api-python/generated/openmm.openmm.CustomTorsionForce.html).
These controls establish numerical behavior, not a qualified reaction coordinate or equilibrium ensemble.
Actual thermostatted windows, retained sampling biases, correlation analysis and physical convergence remain required before MBAR admission.

### Implemented equilibrium sampling mechanics

The [equilibrium component](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/periodic_equilibrium.py)
implements BAOAB Langevin steps with separate reference and bias contributions.
Use `ReferenceEquilibriumSettings` to declare temperature, friction, seed, random generator, physical integration step and sample schedule.
The schedule declares a discarded prefix and a sampling interval.
Discarding that prefix does not prove equilibration.
The step count defines the sampling horizon, not an experiment deadline.

`propagate_reference_equilibrium` uses every supplied physical mass and complete initial position and velocity array.
It neither rescales velocities nor adds constraints or mass changes.
The split sequence applies a half kick, half drift, Ornstein–Uhlenbeck update, half drift and final half kick.
The thermal update uses the declared temperature and mass of each atom.
Each integration step requires one new complete reference force after the initial force.
An optional bias must match both selected window and convention identities.
Reference and bias arrays remain separate in each frame.

Retain each standard-normal array before the next reference force call.
Retain its generator states and actual NumPy version.
The component explicitly uses `NUMPY_PCG64DXSM_STANDARD_NORMAL_FLOAT64` and an integer seed.
NumPy's [stream compatibility policy](https://numpy.org/doc/2.4/reference/random/compatibility.html)
requires the same calls, arguments, build, environment and machine for its stated reproduction guarantee.
Source and environment custody remain necessary.
Neither a failed force nor a failed capture is retried.

The [independent mechanics reducer](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/periodic_equilibrium_assessment.py)
checks position, velocity and thermostat heat from adjacent original forces and realized noise.
It calls neither the force operator, bias evaluator nor random generator.
Selected trace limits preserve finite failures and incomplete prefixes.
The reducer does not require energy or momentum conservation from thermostatted sampling.
It does not independently qualify the energies or random-stream provenance.

[Exposed controls](../../../../../tests/test_rubisco_periodic_equilibrium.py) include exact free-particle thermal updates and harmonic invariant covariance.
These controls do not establish enzyme equilibration, reaction-coordinate validity, step convergence, overlap or effective sample size.
This component supplies no unbiased physical-rate clock or free energy.
The [original equilibrium route](reference-equilibrium.md) binds selected phase space, bias and bath settings through the shared native lifecycle.
Its reader authenticates complete original files and independently assesses retained stochastic mechanics.
Optional [bias-geometry criteria](reference-equilibrium.md#independent-bias-geometry) add independent coordinate and two-step numerical derivative checks.
They bind explicit per-coordinate and complete-gradient limits without changing original acquisition records.
Unresolved stencils and finite violations remain visible in the complete frame denominator.
It preserves incomplete attempts and supplies no ensemble, correlation, free-energy or rate admission.

The [retained equilibrium analysis](reference-free-energy.md) supplies complete reference/bias potentials, basin probabilities and signed joint contrasts.
It reuses the MBAR owner and independently checks its estimating equations.
It retains temporal-correlation diagnostics, overlap, all coupled block draws, covariance and conditional simultaneous intervals.
Failed windows and failed resamples remain explicit.
These numerical assessments supply no automatic ensemble, chemical-model, reaction-coordinate or physical-rate admission.
The splitting method follows
[Leimkuhler and Matthews](https://doi.org/10.1093/amrx/abs010).

### Unbiased first-passage sampling

The [retained first-passage route](physical-first-passages.md) supplies physical-grid observations, exact resampling and original-phase continuation.
It retains every trajectory, residence interval, recrossing, censored path, failed weight and parent cost.
Its independent campaign reader checks cumulative clocks, boundary forces and the complete genealogy.
Physical-model admission and rate reduction remain separate requirements.

The [retained rate assessment](physical-rate-assessment.md) supplies conditional competing hazards and whole-run joint uncertainty.
It checks dwell time, entry history, step refinement, bath dependence and sourced gas concentration scaling.
Complete processing networks retain chemical, release and substrate-ready return times.
Encounter reduction is compared with explicit residence and escape at selected concentrations.
These numerical findings do not establish chemical-state, entry-ensemble, transport or biological admission.

Use weighted ensembles of unbiased reference dynamics for gas access and slow
conformational/product-release first passages. Resampling changes weights and
genealogy, not molecular time. Record entry distributions, residence times,
recrossings, product-event flux and censored paths. Bare 6-Angstrom contact
counts, forced pulling time and metadynamics time are not association or release
rates. An enhanced sampler may estimate equilibrium free energy without
supplying a physical clock.
[Primary weighted-ensemble derivation](https://arxiv.org/abs/0810.1963).

For a postaddition basin retain both the probability of productive exit and
the mean time to either productive or reverse exit. Under an assessed
memoryless reduction these give `r = P_product / mean_exit_time` and
`d = P_reverse / mean_exit_time`. Test entry-history dependence and dwell-time
behavior. If the basin has unresolved substates, retain its network and
first-passage products; do not force a single exponential from a mean.
Product and reverse exits must exhaust the basin's outcomes for this two-exit
reduction. Retain any misprocessing or inactive exit explicitly; never
renormalize it out of the denominator. Product release and substrate rebinding
are included in the definition of return to
E0; saturating RuBP is not permission to drop an unmeasured reset delay.

## Physical clock, prefactors and standard states

Use natural atomic masses, without hydrogen-mass repartitioning. The initial
reactive integration step is **0.5 fs = 5e-16 s**, with **0.25 fs** refinement.
Nonreactive MM steps are **2 fs**, with **1 fs** refinement and the declared
hydrogen-bond constraints. No reacting bond is constrained. Store native step
counts and exact transport to `clock.rubisco.physical-seconds`. Wall time and
CPU time are costs, never reaction times.

Thermostatted sampling prepares equilibrium ensembles at 298.15 K. Physical
short-time flux measurements use unbiased natural-mass dynamics from those
ensembles and must demonstrate energy/step convergence. Any stochastic bath
used for long-time rates is a declared dynamical model whose friction and
transport dependence must be assessed. No arbitrary clock rescaling aligns
the mutant with a measured WT turnover.

For an adiabatic unimolecular edge use

```text
k = kappa_recross * p * (k_B T / h) * exp[-DeltaG_dagger / (R T)]
log(k_M/k_W) = -DeltaDeltaG_dagger/(R T)
               + log(p_M/p_W) + log(kappa_M/kappa_W).
```

`DeltaG_dagger` is a basin-normalized activation free energy with the declared
coordinate measure, restraint, symmetry and thermodynamic corrections. Obtain
the positive-flux prefactor from the same dividing ensemble; encode its ratio
to `k_B T/h` in `p` when needed. This prevents a dimensionful PMF density from
being treated as an Eyring free energy. Obtain the recrossing factor from a
reactive-flux plateau, separately in WT and mutant. Do not assume either its
absolute value or paired ratio is one. The
[existing converter](activation-rate-connection.md) uses exact SI constants
and accommodates these explicit paired operands.

The initial dynamical reference is classical-nuclear. Zero-point and tunnelling
effects, particularly proton transfer, remain a separate applicability/error
component. Do not count a quantum correction in both the barrier and `p`.
An absent correction supports only the labelled classical-model result; it
cannot establish a small physical paired error by presumed cancellation.

Select a **1 M molecular standard state**, exactly **1000000 uM**, for
association free energies. The kinetic API uses dissolved concentrations in
uM and coefficients in `uM^-1 s^-1`; its unit convention does not change the
source free-energy standard state. Unimolecular coefficients use `s^-1`.
For bulk-standard activation free energy, divide the Eyring expression by
1000000 uM exactly once. Retain restraint-volume, orientational, symmetry and
gas-reservoir corrections. Do not use gas pressure, total bicarbonate or total
added O2 as free dissolved concentration without the relevant conversion.

The selected access model keeps an explicit encounter intermediate. Measure
`k_on` in `uM^-1 s^-1`, `k_off` and local chemical `k_chem` in `s^-1`.
Only with assessed encounter elimination may one use

```text
c_or_o = k_on * k_chem / (k_off + k_chem).
```

The pre-equilibrium limit is `K_encounter * k_chem`, where
`K_encounter = k_on/k_off` has units `uM^-1`. Its dimensionless standard-state
constant is `1000000 uM * K_encounter`. A bulk-to-product calculation already
contains access and receives no second partition multiplier. If encounter
residence or memory affects turnover/commitment, retain the enlarged network
instead of using this limiting formula. Assess dilute concentration scaling;
high-concentration gas loading is not automatically an intrinsic assay rate.

### Implemented trajectory mechanics

The [reference trajectory component](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/periodic_dynamics.py)
implements fixed-step velocity Verlet with complete physical-atom gradients.
It preserves the supplied masses and uses unwrapped positions.
Each frame retains positions, synchronized velocities, potential energy, the complete gradient and exact physical time.
The component uses one initial force evaluation and one new force evaluation per selected step.
It adds no thermostat, constraints, bias, velocity scaling or automatic retries.
The [original trajectory route](reference-trajectory.md) binds the full phase space, source masses, fixed operator and shared native custody.
It preserves failed force returns and incomplete frames for independent reading.
Its diagnostic selection does not qualify an initial ensemble.

The [independent trajectory reader](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/periodic_dynamics_assessment.py)
checks the exact clock, initial phase space, force census and position and momentum equations.
It measures energy drift and tests explicit trace criteria when supplied.
A valid incomplete prefix retains its observed duration and cannot satisfy the complete selected horizon.
Finite criterion failures remain negative findings.
Absent criteria leave acceptance unevaluable.
The reader makes no new force evaluation.

Analytical controls test Newtonian motion, mass dependence, reversibility, step refinement and changes to retained frames.
These controls do not establish full-enzyme dynamics, initial-ensemble validity, recrossing, commitment or physical rates.
The acquisition binding uses the existing shared execution and recovery contracts.
Complete coupled controls and feasible enzyme cost remain required before selection of an actual sampling tranche.
The physical observation horizon is distinct from an experiment wall-time deadline.

[OpenMM's velocity-Verlet definition](https://docs.openmm.org/latest/api-python/generated/openmm.openmm.CustomIntegrator.html)
gives the velocity and position equations.
[OpenMM's integrator guide](https://docs.openmm.org/latest/userguide/theory/04_integrators.html)
explains the different time alignment of its leap-frog Verlet velocities.

## Reversal, productive commitment and oxygen assumptions

**Use finite, computed reverse channels as the reference.** Formation/reversal
and addition/deaddition must share the same state free energies and chemical
potentials. For a unimolecular reversible pair with a common dividing surface,
check the forward-minus-reverse barrier against the reaction free energy and
check detailed balance of the rate pair. For `E* + gas <-> E_j`, compare
`(c_or_o * 1000000 uM)/d_j` with its dimensionless equilibrium constant, using
the same retained encounter reduction and state definition. Independent reverse
barrier fits cannot violate that cycle silently.

The separate irreversible scenario `d_c=d_o=0` is a labelled approximation.
To use it for a decision, supported reverse-rate bounds must show that the
complete endpoint change lies inside the preselected numerical/decision budget.
No observed reverse event is not an exact zero. The published carbon result
motivates this check; it does not establish Gp I95M irreversibility.

**Select SET oxygen activation as the primary conditional mechanism.** The
reactants are the closed-shell reactive enzyme/substrate plus triplet O2;
electron transfer produces an enzyme-substrate radical/superoxide pair, whose
spin evolution and recombination lead to peroxide. Compute donor and acceptor
states in the same full enzyme/solvent environment in both arms. Use constrained
charge/spin diabatic states and their couplings; a converged unrestricted SCF
calculation alone does not demonstrate the required diabatic state or spin
transition. The selected electronic model and its open-shell stability must be
assessed before interpreting a rate.

For a tested weak-coupling, linear-response regime, use the nonadiabatic Marcus
model, with **per-molecule energies in joules**:

```text
k_ET = (2 pi / hbar) * |H_DA|^2 / sqrt(4 pi lambda k_B T)
       * exp[-(DeltaG_ET + lambda)^2 / (4 lambda k_B T)].
```

Estimate driving free energy and reorganization from both donor and acceptor
energy-gap ensembles; retain coupling-gap dependence rather than multiplying
unrelated marginal estimates. Test the Gaussian/linear-response and
weak-coupling premises and identify the normal/inverted regime. Molar energy
inputs must be divided by the exact Avogadro constant before this expression.
Do not multiply by an additional Eyring attempt frequency. Reject this supplier
if its premises fail; a Marcus fit is not the preselected fallback for an
arbitrary spin-adiabatic barrier.
[Primary nonadiabatic/adiabatic comparison](https://pmc.ncbi.nlm.nih.gov/articles/PMC7815917/).

The resulting ET rate is **not yet `o`**. Retain the radical-pair spin conversion,
back electron transfer, escape and productive peroxide probability in the
oxygen subnetwork. Their supplier is paired spin-state/coupling calculations
and state-resolved dynamical/first-passage assessment in that same embedding.
Keep singlet and triplet states, their energy gaps and spin-orbit coupling
separate from the charge-transfer coupling `H_DA`. The initial weak-coupling
spin-transition model is a golden-rule spin-orbit coupling/energy-gap model;
its applicability and computed coupling are required operands. The existing
closed-shell force diagnostic supplies none of them.

An explicitly labelled fast-recombination scenario may be reported separately.
An unmeasured mutation-invariant spin probability, oxygen prefactor or productive
commitment is an imposed assumption, not supported specificity preservation.
If their paired support is unavailable, report the conditional oxygen response
and the unresolved joint decision. Neither the exposed lambda grid nor a
literature value such as 55 kcal/mol becomes a Gp uncertainty bound.

## Joint reduction, precision and stopping

For each processing/chemical scenario retain the joint realized contrasts

```text
q_a   = a_M/a_W
q_r   = r_c,M/r_c,W
q_D   = (c_M/o_M)/(c_W/o_W)
q_chi = (chi_c,M/chi_o,M)/(chi_c,W/chi_o,W),
chi_j = r_j/(r_j+d_j).
```

These require four joint roles for each of two processing cases, not eight
independent biological observations. Retain whole paired preparation/run
groups, site nesting, shared barriers, prefactors, state populations, gas
corrections and censored/failed paths. No favorable site, processing view or
chemical model may be selected after inspecting the candidate effect.

Use the existing [endpoint enclosure](activation-rate-connection.md#retain-an-unidentified-wt-waiting-time-split)
when the WT waiting split is unidentified. For one joint realization it gives
the exact closed turnover enclosure between `min(q_a,q_r)` and `max(q_a,q_r)`
and specificity ratio `q_D*q_chi`. Preserve separate correlated realizations;
this is not a confidence region for arbitrary marginal boxes. Narrowing the
waiting interval requires independent evidence. If postaddition processing
has several unresolved waiting steps, do not substitute the most favorable
elementary step's ratio for the effective `q_r`.

For a complete rate realization, use the existing reversible kinetic solver
and independent balance/endpoint assessor. Check the effective graph against
the detailed supplier network across the selected concentration queries,
including the zero-oxygen CO2 response and both-gas specificity. A mismatch
invalidates that closure; it does not justify changing the endpoint definition.

Freeze the candidate's actual `g_C`, strict-preservation `r_S=1`, optional
absolute requirements and numerical error allocation before target assessment.
The nomination supplies direction, not an invented magnitude or precision.
Each uncertainty in paired log barrier, prefactor, gas access, commitment and
state reduction must be propagated jointly. Translate a permitted log-rate
error `epsilon` into a barrier budget `R*T*epsilon` only after allocating the
other terms. Agreement of energies to a numerical SCF tolerance is not that
physical error bound. Do not create a nominal confidence level from too few
independent preparation groups or from an unweighted sensitivity grid.

At each finite, predeclared development checkpoint: inspect the complete case
census; test overlap/convergence, step refinement, state history and force
consistency; compute the resulting joint decision support; refine only a
consequential uncertainty within the authorized resource envelope. A decision
supported across the full retained set may stop early. An overlap failure,
unresolved oxygen factor, exhausted budget or contradictory processing case
returns its exact unresolved requirement. None is a zero effect or failed
biological mutation measurement.

## Concrete handoff and current acceptance boundary

The native preparation packet must supply exact four-material atom/topology
records; every site graph; parameter files and electronic settings; coordinates,
charges, spins and boundary maps; source/environment identity; state, window
and trajectory selections; numerical and chemical controls; and explicit
CPU, memory and storage selections. The current owner-selected execution has
no experiment wall-time deadline; retain its CPU and memory controls and actual
storage accounting. Derive native work through the supported
preparation owners, with fresh selected output paths. This document is not a
handwritten native task roster or a substitute for those records.

Execute the next stages in this order:

1. Construct and independently assess active full assemblies and the paired
   reference force/chemical operator. Measure native force/energy cost on the
   actual enzyme. The ethane allocation is not an enzyme budget.
2. Use that cost to freeze a bounded paired development tranche covering
   formation, carbon chemistry, oxygen gap/coupling evidence and processing.
   Do not spend the complete allowance on one favorable branch while leaving
   every specificity operand absent. Window/trajectory counts and their total
   finite budget are mandatory before that tranche starts.
3. Produce the selected free-energy, dynamical, standard-state and commitment
   products with their original receipts; assess each supplier independently.
4. Populate `ParameterEvidenceLedger` and `RateSupplierSemantics` for all eight
   parameters. Use `PairedActivationRateInput` only for its applicable Eyring
   operands. ET/spin and first-passage rates retain their own physical producer
   evidence; do not encode them as fictitious Eyring barriers merely to fit an API.
5. Use the public paired-kinetic author/run/read route for complete rate
   realizations, or the supported endpoint-only composition for its narrower
   inputs. Retain raw/anchored outputs, the independent assessment, all missing
   roles, physical/model limitations and measured costs in the reference report.

The [public guide](guide.md) describes these
existing consumers and preparation seams. There is currently no registered
command that performs this entire molecular supplier. The selected QM/MM,
diabatic/spin and sampling implementation must pass its actual coupled
operator and lifecycle checks before use; the existing kinetic command alone
cannot execute it.

Completion of this document closes **supplier specification**, including which
paired calculations supply which consequences. It does not close RF04 physical
preparation, RF05 rate evidence, the initial forecast, biological prediction or
the Matrix-benefit milestone. Preserve the retained UNEVALUABLE readout and
publish a successor only when new assessed operands justify it.
