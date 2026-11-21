# Assess the initial conditional Gp WT/I95M model

SPDX-License-Identifier: CC-BY-4.0

This protocol defines a conditional M1 and V1 comparison from four effective
mutation contrasts. It identifies the physical quantities still needed and
does not supply missing observations. Use the [workflow guide](guide.md) for
the existing researcher lifecycle and the [restrained formation
protocol](restrained-formation-v1.md) for the selected molecular operand.
The separate [joint-root protocol](initial-root-v1.md) composes this model's
original inputs into a requirement graph, independent conjunction assessment
and retained inquiry decision without changing this protocol's exports.

## Model and original evidence

The protocol identifier is `GP-WT-I95M-INITIAL1`. Select 298.15 K, pH 8,
saturating RuBP, initial-rate product sinks and free dissolved bulk gas
concentrations in micromolar. Retain full Galdieria partita L8S8 assemblies,
all eight SSU I95M substitutions and separate M1 and V1 processing views.
No nested site or starting hypothesis counts as independent biological
replication. The physical clock is seconds; normalization is carboxylation
events per active site.

Reuse the four accepted Amber constructions and their complete atomic and
parameter sources. The matched relaxation plan retains four materials,
32 site partitions and 384 starting hypotheses. Select its returned
`site1-keto-enolate` conditional preparation: focal `site.gp.lsu.01`,
`keto-hie` and `initial-enolate-kcxh-hie`, both `AS_CONSTRUCTED`. Other sites
retain the original carbamylated, Mg-bound RuBP occupancy and HIE, solvent
and counterion context. These are prospective conditional selections, not
measured pH populations or a claim that the other hypotheses are absent.
Retain unselected and failed hypotheses in the original denominator. M1
preparation does not discharge the corresponding V1 work.

Use the [source assessment](../../records/reactive-state-supplier-assessment.md)
and [original carbon archive inspection](../../records/reactive-preparation-result.md)
with their original bindings. The inherited descriptions have distinct roles:

| Source | Inherited content | Required adaptation and limitation |
| --- | --- | --- |
| [Amritkar preparation selection](../../records/rubisco-insilico-dynamics-selection.md) | Gp sequence/assembly construction and retained classical parameter stock. | Preserve all sixteen chains, eight substitutions and exact topology, masses and coordinates. An inhibited structure does not establish active chemistry. |
| [Douglas-Gallardo et al., 2022](https://doi.org/10.1021/acscatal.2c01677) | Carbon reaction coordinates and the explicit dependence on KCX/histidine proton placement. | Map the selected proton transfers into the full Gp assembly. The released two-LSU model lacks SSUs. Its absolute barriers and different protonation states do not supply a Gp I95M contrast. |
| [Kannappan, Cummins and Gready, 2019](https://doi.org/10.1021/acs.jpcb.9b00518) | FM23 oxygen-addition/processing pathway families, retained geometries and its internal carbon/oxygen comparison. | Use the source atom-role, charge, spin and direction audit before any Gp electronic-state selection. The small spinach fragments omit the remote mutation environment. Geometry headers alone are not electronic job cards. |
| [Bathellier et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7533879/) | Evidence constraining an electron-transfer oxygen-activation description. | Preserve its organisms, conditions and isotope/metal perturbations. It supplies neither Gp-I95M oxygen kinetics nor a mutation-invariant spin, access or commitment factor. |

Select the published electron-transfer/peroxide oxygen pathway as the initial
mechanistic hypothesis. Before its native use, retain the actual open-shell
reactant, electron-transfer and product states, total charge, multiplicity,
coupling/spin-transition model and source correspondence. Unresolved electronic
assignments remain missing suppliers. A carbon RKS calculation or a small
constrained-state software control cannot admit that oxygen hypothesis.

## Conditional endpoint closure

Use the existing reversible four-state closure and its
[independent endpoint assessment](activation-rate-connection.md#retain-an-unidentified-wt-waiting-time-split).
The closure assumes a common active-enzyme state, effective reactive-state
formation, competing gas-addition branches and productive versus returning
exits from each adduct. Its selected limits are saturating-carbon turnover
and branch specificity. Finite-concentration assays, additional inhibited
states or non-Markov state aggregation require a separately supported
connection.

For each processing view, keep one joint realization of:

```text
q_a   = a_M/a_W
q_r   = r_C,M/r_C,W
q_D   = (c_M/o_M)/(c_W/o_W)
q_chi = (chi_C,M/chi_O,M)/(chi_C,W/chi_O,W)

T = 1/(w/q_a + (1-w)/q_r)
S = q_D*q_chi
```

An unidentified WT waiting fraction retains the complete interval `0 <= w <= 1`.
It gives the closed turnover enclosure `min(q_a,q_r) <= T <= max(q_a,q_r)`.
No absolute WT rate fit is required for that enclosure. Narrowing `w` requires
separate original evidence. Formation reversal `b` cancels from these two
limiting endpoints under this closure; it remains relevant to state aggregation
and other observables. Do not impose this cancellation on the complete-rate
consumer or use it to waive a failed closure assumption.

## Dependency map and next physical suppliers

Each row requires an assessed mutation contrast or a supported joint bound.
No row defaults to unity. Share authentic operands across rows and retain
their dependence instead of acquiring them twice.

| Contrast | Required quantities | Selected supplier route |
| --- | --- | --- |
| `q_a` | Paired activation free-energy difference for reactive-state formation, paired transmission/prefactor contribution and an effective-state aggregation assessment. | Matched keto/enolate preparations; C3–H3/KCX restrained-center integration; finite-restraint, measure, reactant/dividing-surface and sampling corrections; then the supported activation-rate connection. The restrained integral alone supplies none of the missing corrections. |
| `q_r` | A supported relative effective carbon-processing rate or bound. | First assess the inherited processing model and its mutation-dependent terms. An effective model can supply the contrast directly. Use first-passage observations only when the selected model requires them. Include consequential hydration, cleavage/protonation, release and regeneration effects. A carbon-addition barrier alone does not supply this contrast. |
| `q_D` | Relative effective CO2/O2 addition from the same reactive-state ensemble, including bulk access/partition, local chemical and oxygen spin/electron-transfer contributions. | Bind the matched carbon/oxygen comparison now, alongside M1 formation preparation. Use the inherited internal comparison to bind chemistry. Acquire only required Gp mutation effects through the existing electronic, free-energy and flux services. Do not compare unmatched foreign absolute barriers. |
| `q_chi` | A supported relative carbon/oxygen commitment contrast or bound, including return paths. | First assess the inherited return-versus-productive model. Reuse its carbon-processing terms from `q_r`. Acquire only consequential missing mutation terms. If first-passage observations supply the contrast, share `P_C` across both endpoints. A static adduct or forward reaction energy alone does not identify commitment. |

The following first-passage decomposition is optional.
It does not require five separate acquisition campaigns or supersede a supported direct contrast.
Under the explicitly selected competing-exit closure,
`r_C = P_C/tau_C`, `d_C = (1-P_C)/tau_C` and `chi_C = P_C`.
Thus `q_r = (P_C,M/P_C,W)*(tau_C,W/tau_C,M)`.
The mean time is to **either** exit, with all original trajectories retained;
the productive-only conditional waiting time is not `1/r_C`.
The oxygen side needs `P_O` for the initial specificity endpoint. It does not
require an absolute oxygen turnover time solely to fill an unused interface.
This omission is algebraic within the selected closure, not proof that oxygen
processing is negligible.

The minimal contribution join accepts paired ratios directly:

```text
q_PC   = P_C,M/P_C,W
q_tauC = tau_C,M/tau_C,W
q_PO   = P_O,M/P_O,W

q_r   = q_PC/q_tauC
q_chi = q_PC/q_PO
```

Together with `q_a` and `q_D`, these are five dimensionless contributions.
Each can come from an assessed relative calculation or supported bound.
Absolute probabilities and times are not mandatory inputs to this join.
Their actual native observations remain in custody when that supplier route needs them.
Use the same `q_PC` in both expressions, with the same joint realization and source.
Do not repeat its acquisition for specificity.
The direct `q_r` and `q_chi` interface remains available when those contrasts already have adequate support.

When addition is decomposed into bulk partition `K` and local chemical
coefficient `k`, `c/o = (K_C*k_C)/(K_O*k_O)` under the declared concentration
and access model. A barrier already defined from bulk must not receive a
second partition correction. Preserve the oxygen spin/coupling factor and
paired transmission assumptions in the local coefficient.

For each required quantity retain its material, chemical alternative, original
source, units, temperature, standard state, uncertainty, dependence group and
applicability finding. Unresolved preparation populations and chemical
alternatives remain explicit. Stationarity, sufficient sampling, a valid
dividing surface and the competing-exit connection require evidence beyond
the source-conditioned algebra. Broader microscopic-rate and 44-cell pilot
requirements remain with the [comprehensive reference](physical-rate-supplier-v1.md).

## Select the minimum remaining physical work

Oxygen is an immediate model requirement.
Bind its source states and mutation contribution alongside preparation of the selected M1 pair.
Use the [gas-source preparation protocol](gas-preparation-v1.md) for exact
carbon/oxygen coordinates, full-environment contact checks and scoped gas parameter stock.
It does not wait for a favourable formation result or a successful response approximation.
Use the following scope before selection of native jobs.

| Required contrast | Smallest selected target | Existing supplier and required selection |
| --- | --- | --- |
| `q_D` | One paired effective carbon/oxygen addition contrast from the same enolate ensemble. | Reuse equilibrium, electronic-ensemble and reactive-flux services for contributions required by the selected expression. Bind actual gas atoms, charge/spin, encounter or bulk standard state, access, transmission and any consequential spin-transition contribution. |
| `q_r` | One paired effective carbon-processing contrast, with its inherited model and mutation terms. | Reuse an assessed effective processing model first. If its support requires original exits, select `P_C` and `tau_C` together. Include release and regeneration when they affect the selected cycle. |
| `q_chi` | One paired carbon/oxygen commitment contrast or bound. | Reuse the carbon-processing evidence. Assess consequential productive-versus-return effects on the oxygen branch. Select `P_O` observations only if required by this model. An absolute oxygen turnover time is not an additional target. |

The inherited carbon source distinguishes the initial enolate from its reactive proton arrangements.
The selected C3-H/KCX preparation supplies the initial enolate.
Do not relabel it as the source's reactive carbon state.
Bind subsequent proton redistribution through effective-state aggregation or the selected addition model.
The source's fast proton exchange is an assumption, not a measured Gp population.
The original reactive-state seeds have `OCCUPIED` and `UNOCCUPIED` Mg-water
views; they have no `AS_CONSTRUCTED` view. Select the existing
`reactive-enolate-kcxh-hie`, `UNOCCUPIED` seed as the next conditional
gas-addition preparation target. This follows the carbon source's state without
the additional coordinating water. It does not measure its Gp population.
Keep the occupied view in the original denominator and retain any required
water-occupancy contribution when connecting this state to formation.
This prospective selection does not change an active native job.

The oxygen sources do not justify an automatic irreversible branch or mutation-invariant electron-transfer coefficient.
Kannappan's model permits deoxygenation.
Bathellier's isotope evidence supports electron transfer but does not identify the I95M effect on reorganization or coupling.
Preserve those limits when selecting the relative oxygen contribution.
Do not set `q_chi=1` or cancel a missing oxygen factor solely to complete the reader's inputs.

For local transition-state models, the addition target is a double difference:

```text
log(q_D) = log(q_K,C/q_K,O) + log(q_nu_kappa,C/q_nu_kappa,O)
           - (delta_delta_G_C - delta_delta_G_O)/(R*T)
```

Each `q` in the first two terms is a mutant/WT ratio.
The oxygen transmission factor includes the selected electronic/spin connection.
The expression does not require two absolute addition rates.
It also does not justify setting either non-barrier contribution to one.
Use this decomposition only when its chemical and access assumptions apply.
A directly supported effective `q_D` does not require this decomposition.

### Share processing and commitment calculations

The selected next processing model tests a reversible hydration step followed by
cleavage/protonation and product release. This is a conditional reduction of the
[carbon processing mechanism](https://doi.org/10.1021/acs.jpcb.8b12088) and
[oxygen pathway](https://doi.org/10.1021/acs.jpcb.9b00518), not a transfer of their
numerical barriers. The [later carbon coordinate release](https://doi.org/10.1021/acs.jpcb.0c01169)
supplies additional proton-wire geometries. Its different atom and proton counts
must be reconciled with the selected Gp states before use.

For either branch, let `A` be the gas adduct and `B` the hydrated intermediate.
Use `A -> B` at rate `h`, `B -> A` at rate `j`, `B -> P` at rate `s`,
and `A -> R` at gas-loss rate `d`. `P` includes the completed cleavage/protonation
products. Let `t_L` be the mean time from `P` through complete release and
substrate-ready regeneration. The conditional model requires eventual productive
return from `P`, no unrepresented competing exit, and the declared entry state
after each return. It does not equate a bound product with released product.

Starting at `A`, exact first-exit elimination gives:

```text
D   = h*s + d*(j+s)
P_g = h*s/D
tau = (h+j+s+h*s*t_L)/D
r_g = P_g/tau = 1/(1/h + 1/s + j/(h*s) + t_L)
rho_g = (1-P_g)/P_g = d/h + d*j/(h*s)
```

These are probability and mean-time identities. They do not establish an
exponential exit law or the initial endpoint closure's physical applicability.
When that connection is supported, carbon `r_g` supplies `q_r` and the two
branches' `P_g` supply `q_chi`. Oxygen release time drops out of `P_g` only under
the eventual-return assumption. Its probability of failure or trapping cannot
be dropped with its clock.

Write `q_x=x_M/x_W` and `q_L=t_L,W/t_L,M`.
Without estimating absolute WT chemical rates or release times, the complete
positive WT waiting allocation gives the closed enclosure
`min(q_h,q_s,q_h*q_s/q_j,q_L) <= q_r <= max(q_h,q_s,q_h*q_s/q_j,q_L)`.
This is a conservative enclosure; its endpoints need not be attainable by
finite rates. A missing release contrast remains missing.
For each branch, `q_rho=rho_M/rho_W` lies between
`q_d/q_h` and `q_d*q_j/(q_h*q_s)`.
Then `P_M/P_W=(1+rho_W)/(1+q_rho*rho_W)` lies between `1` and `1/q_rho`.
Retain the joint chemical-rate realization and shared carbon terms when
combining these expressions. Marginal statistical intervals do not become
simultaneous support through this algebra.

The targeted mutation calculations are therefore paired hydration and
cleavage/protonation contributions, their shared reverse hydration contribution,
gas loss from the addition/adduct calculation, and carbon release/regeneration.
Forward and reverse hydration use the same original barrier and basin evidence.
Use the same carbon quantities for processing and commitment. No additional
first-passage campaign or absolute oxygen clock is selected by this reduction.
Bind the proton donor, water, charge/spin, ensemble, transition prefactors and
transmission contributions before converting any energy difference to a rate
ratio. If an omitted state, side exit or failed return invalidates this graph,
retain that failure and use the supported direct contrast or extend only the
affected physical model.

Create native state selections only for quantities present in the chosen expression.
The oxygen sources identify an electron-transfer/peroxide hypothesis and distinct subsequent chemistry.
They do not supply Gp-I95M state cards or a mutation-invariant commitment.
Resolve those assignments before their dependent electronic jobs.
Do not commission every available electronic supplier merely because the software supports it.
Do not enumerate every microscopic processing state when an assessed effective contribution suffices.

Retain native reference acquisition for the selected formation bridge.
First bind its centers, physical horizon, tolerance, finite reuse and complete work allocation.
Then compare frozen or updated response costs with that same required native work.
Include preparation, qualification, observations, updates, fallback and failures.
An unpriced sampling requirement cannot support a saving claim.
The four conditional M1 relaxations prepare starting states only.
They supply no oxygen contribution, free-energy trajectory or completed bridge.

## Independent reader and decisions

Use the public Python composition
[`api.domain_composition.rubisco_response.initial_model`](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/initial_model.py).
`prepare_matched_initial_model` derives both M1/V1 cases and all substitutions
from the original matched plan and conditional state selection. It preserves
their explicit assay contexts. `prepare_initial_model` binds other complete cases, dependencies, closure,
chemical-alternative census and original source selection. Supply exact
guarded `InitialModelSource` publications. `empty_initial_evidence` derives
the missing-operand census from that selection without invented contrasts.

`read_initial_model_sources`, `export_initial_model` and
`read_initial_model_export` authenticate sources, retain exact Decimal/rational
values and reconstruct the closed package. A supplied contrast needs its
original applicability review and supporting sources. A joint support review
must bind the simultaneous support and waiting-fraction dependence; separate
marginal confidence limits do not establish a joint region. A finite sample
remains a sample. Reader authentication does not establish the scientific
truth of a review's assertions.

For the minimal join, use `prepare_initial_contribution_realization` with the existing model case and selected chemical alternative.
Supply all five `InitialContribution` rows, including explicit unavailable rows.
Use `initial_contrast_evidence` to prepare the existing four-contrast inputs.
Publish the original contribution record and source records through the same guarded artifact writer.
The initial-model reader independently reconstructs each supplied projection.
It refuses changed case, chemical alternative, dependence, values or missing-operand status.
`read_initial_contributions` reports the separate exact arithmetic and its source requirements.
Neither function creates an applicability review, simultaneous confidence coverage or physical observations.

Assess the owner criteria exactly: turnover `T > 1`, specificity `S >= 1`.
Report supported favourable, adverse or inconclusive findings separately for
M1 and V1. Missing required evidence makes only the affected endpoint
unevaluable; failed or unknown chemical alternatives prevent a complete
all-alternative conclusion. Do not invent absolute rates or measured endpoints.
The six-output indicator, complete-rate consumer and historical reduction
reader keep their original requirements.

## Work allocation, stopping and custody

Use SCI01's retained response findings to select the formation bridge. They
do not qualify a molecular shortcut. Apply the narrowly scoped paired receiver
bound only with pre-omission molecular coverage and a positive complete-work
saving; otherwise retain the native reference and its explicit refusal reason.
The conditional reader can assess supported inputs independently of their
acquisition method. Its arithmetic completion does not establish completion
of a programme that requires a computational shortcut. Such a programme also
requires assessed paired fidelity, prospective consumer admission, useful
delivery and positive complete-work saving for its selected molecular workload.
A refusal closes the tested candidate while the shortcut requirement remains
open. Develop a bounded construction without requiring a general
receiver-admittance theory first. Preserve the original refusal and its scope.

Prepare and independently inspect M1 first. Preserve the selected V1 pair and
its own original evidence requirements. A failed preparation or numerical
control blocks its dependent physical calculation, not the bookkeeping for
other missing quantities. Select actual native inputs, physical horizons and
scientific criteria before each acquisition. Use the existing preparation,
authoring, execution, recovery, assessment and export owners and their returned
paths; do not create a substitute scientific roster or scheduler.

Price complete force calls, preparation, qualification, sampling, updates,
fallback, failures, assessment, idle time, storage and evidence return.
RUB01 supplies measured single-call costs, not a production trajectory or
relaxation-convergence estimate. Record a stage's workload, current provider
configuration/quote, financial cap and financial stopping behavior before
remote entry. An incomplete budget-limited attempt retains its original
uncertainty; it does not count as scientific convergence. Preserve complete
original outputs and verify returned bytes before normal compute retirement.
