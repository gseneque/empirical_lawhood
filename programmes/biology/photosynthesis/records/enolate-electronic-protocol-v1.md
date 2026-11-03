# Enolate electronic-method pilot v1

SPDX-License-Identifier: CC-BY-4.0

**Frozen before the first SCF calculation, 10 October 2026.** This is a finite,
exposed preparation and electronic-method assessment following the
[reactive-state supplier assessment](reactive-state-supplier-assessment.md).
It asks whether an available open solver and a declared population diagnostic
recover the carbon-site ordering change between two authentic reduced enolates.
It supplies or rejects a narrow method prerequisite for later paired chemistry;
it supplies no enzyme-edit response, kinetic forecast, independent biological
sample, recursive task receipt, EL advantage or nomination.

The primary source uses a frontier-orbital approximation and Hirshfeld-I
partitioning. This pilot uses the same frontier-orbital premise with explicitly
different symmetric Lowdin and Mulliken partitions. It does not reproduce the
source's atom-condensed Fukui values. Neither a complete microscopic kinetic
map nor new wet-lab validation is a prerequisite for this provisional assessment.

## Exact originals and complete roster

Use the authentic `SI_input_files.zip` from
[Douglas-Gallardo et al., 2022](https://doi.org/10.1021/acscatal.2c01677),
[Zenodo record 6791151](https://zenodo.org/records/6791151): **10,139,036 bytes**,
SHA-256 `48e76a27e3cea2c49ab6a9685551ba311a898f357416f4f91b35fc28c4dcce8b`.
The acquired archive, its inventory and semantic projections belong to the
closed `followup-reactive-inputs-v1` source packet. Its original register has
SHA-256 `14344362981f2a85a38754d71ad7b6d9950e2419d8faca1cdb0335ea1513ca66`;
do not append members or alter source bytes after its closure.

All four Cartesian members below are required. Paths are relative to
`C-Conceptual_DFT_calculations/` inside the archive. Pair each geometry with
its source-labelled functional and basis; do not cross methods or optimize
coordinates during this pilot.

| Case | Original member | Bytes | SHA-256 |
|---|---|---:|---|
| B2 | `B3LYP  6-31G(d)/Enolate 2/react_small._opt.xyz` | 989 | `edaaa4cb244159798707119e1b9903cb1463b3e9a1342cdf515f23985b2af3b1` |
| B3 | `B3LYP  6-31G(d)/Enolate 3/react_small._opt.xyz` | 989 | `d9097c378dcfc2659e81c9935496f027fb4f8b93813132b2afd652eba87ed9f9` |
| W2 | `WB97X  DEF2-SVP/Enolate 2/react_small._opt.xyz` | 989 | `73efbb6a45b582acf673d4cd281c68b225a44d6e509595950015020276c4e4c1` |
| W3 | `WB97X  DEF2-SVP/Enolate 3/react_small._opt.xyz` | 986 | `40a68f5e75852aad8bbc4bb5a438375c28da46a41e2f454274f53ddc7e19fb82` |

Retain the native ACS SI `cs2c01677_si_001.pdf`: **3,949,091 bytes**, SHA-256
`bd5030f66d3233b3518f3b1936d6f72f0b342bfdbbec1924a4f96a8df622d267`.
Its physical page 9 contains Tables S1/S2 at B3LYP/6-31G(d). Independently
retain the
[author accepted manuscript](https://research-information.bris.ac.uk/ws/files/339252396/Rubisco_carboxylation_reference.pdf):
**9,395,316 bytes**, SHA-256
`b374b8c4967bbb0afeb84e57a3f3946b5bc5725b80082ec355c2fdb10f0f7703`.
Its methods specify frontier-orbital Hirshfeld-I condensation using Chemtools;
Table 1 on physical page 17 supplies the omega-B97X/def2-SVP reference.
Bind this additional original in the selected pilot custody, separately from
the already closed archive packet. University `/files/` retrieval returned
HTTP 403; the `/ws/files/` endpoint delivered the admitted PDF. Original bytes,
source versions and table roles remain separate.

Each geometry has the same **14 atoms, C4H7O3**. Original XYZ atom positions
are one-based: C2 is atom **2**, C3 atom **3**, O2 atom **5**, O3 atom **6**.
The transferred proton is atom **8**. Atom order, C-O adjacency and proton
distances jointly support these semantic roles. In B2/W2, H8 is bonded to O3
(0.988/0.978 A); in B3/W3 it is bonded to O2 (0.998/0.984 A).
The original bond-length pattern changes with that placement. Retain the full
fourteen-atom correspondence and exact coordinates rather than identifying
states by the folder label alone.

These reduced substrates have no phosphate-bearing full RuBP construction,
Mg, protein, small subunit, point charges, solvent or gas. Their proton
arrangement is an authentic reduced-molecule operand, not a simulation of
His294/KCX201 proton exchange or a measured enzyme microstate population.

## Source reference and its evidence role

Only native **vacuum** point values enter the reference. Exclude the distinct
300 K enzyme Boltzmann averages, their standard deviations and the fifty
configurations from this assessment. They do not create biological replication
or a sampling ensemble for the four selected geometries.

| Source functional and enolate | C2 | O2 | C3 | O3 |
|---|---:|---:|---:|---:|
| SI B3LYP/6-31G(d), 2 | 0.12 | 0.24 | 0.32 | 0.18 |
| SI B3LYP/6-31G(d), 3 | 0.27 | 0.14 | 0.14 | 0.31 |
| Manuscript omega-B97X/def2-SVP, 2 | 0.12 | 0.24 | 0.33 | 0.17 |
| Manuscript omega-B97X/def2-SVP, 3 | 0.29 | 0.15 | 0.15 | 0.28 |

The native f-minus descriptor addresses electrophilic attack. The source
approximates it using the **one-electron HOMO density**, neglecting orbital
relaxation, and assigns that density with Hirshfeld-I. Its separate discussion
of Mulliken atomic charges is not the Fukui partition definition. A relaxed
neutral-minus-anion charge difference would be another observable.

Both native functional pairs show **C3 > C2 in enolate 2** and **C2 > C3 in
enolate 3**. From 2 to 3, all four displayed sites change in the same directions:
C2 increases, O2 decreases, C3 decreases and O3 increases. Retain every site,
both functional pairs and all failed/unevaluable calculations. Native values
were already exposed when this question was selected.

## Frozen electronic realization

Use the independently selected locked `rubisco-electronic` profile with
**CPython 3.11.14 and PySCF 2.14.0**, and `uv run --no-sync` after that profile
is selected. Do not import a solver from a sibling checkout in the maintained
route. Observe actual NumPy/SciPy/h5py, libxc, native-library, BLAS/OpenMP,
interpreter, producing-code and platform identities in the run custody.

Set **two numerical threads before importing scientific libraries**, and
verify the realized thread configuration. Use PySCF/libxc **`B3LYPG` (402)**
with spherical `6-31g*` for B2/B3, and **`WB97X`** with spherical `def2-svp`
for W2/W3. Observe the resolved functional identifiers and coefficients.
`B3LYPG` fixes the selected implementation convention; absent source job cards
do not establish equivalence with every original ORCA setting. Do not silently
select another VWN variant, omega-B97X-D, dispersion correction or density
fitting. Expected contracted basis sizes are **112** and **133** AOs.

At each fixed geometry calculate exactly these two states, yielding a complete
**eight-job roster**:

| Electronic role | Charge | PySCF spin, N-alpha minus N-beta | Electrons | Solver |
|---|---:|---:|---:|---|
| Reduced enolate | -1 | 0 | 56; 28 alpha/28 beta | Restricted KS |
| Vertical neutral ionization diagnostic | 0 | 1 | 55; 28 alpha/27 beta | Unrestricted KS |

The chemistry and nuclear-charge arithmetic motivate these charge/spin
assignments. The XYZ headers are not authentic electronic job cards; retain
the assignments as explicit successor hypotheses. No electron-added third
state, electron affinity, spin crossing or kinetic rate is requested.

Use atomic/minimal initial guesses, PySCF numerical **grid level 4**,
energy convergence tolerance **1e-10 Hartree**, and at most **120 SCF cycles**
per job. Record the realized grid, initial guess, numerical defaults and
convergence observations. No geometry optimization, Newton retry, state
switching, basis augmentation or post-result change of functional is allowed
inside this protocol. A nonconverged or resource-limited case remains in the
complete assigned denominator, without a rescued value.

## Primary observable and separate diagnostics

For each converged anion obtain the occupied HOMO coefficient vector `c`,
overlap matrix `S` and AO-to-atom census. For this closed-shell spatial orbital,
the **one-electron** frontier density matrix is `c c^T`, with
`c^T S c = 1`; do not multiply by its two-electron occupied-state factor.
Retain enough numeric operands and their identities to reproduce the analysis.

The primary symmetric Lowdin HOMO weight on atom A is the sum, over its AOs,
of squared entries of `S^(1/2) c`. The secondary Mulliken HOMO weight is the
sum of `c_i (S c)_i` over those AOs. Use the symmetric positive overlap square
root; refuse a nonpositive or numerically singular overlap rather than
silently clipping it. Both weight vectors must be finite and sum to one
within **1e-8**. Retain every atom and any negative Mulliken contribution;
do not normalize just the four displayed sites or replace a population method
after inspecting the result. Report the adjacent occupied-orbital gap and any
frontier near-degeneracy as a sensitivity limitation.

For each native table/site report both population diagnostics, raw differences
from the matching source point values and the complete direction/order census.
Those numerical differences are descriptive **cross-partition differences**,
not numerical reproduction errors, calibrated intervals or enzyme predictions.
The native Hirshfeld-I pipeline is not installed or reimplemented for this
pilot. A later quantitative reproduction needs that separately specified
partition and its reference assessment.

The neutral calculation supplies only a fixed-geometry vertical ionization
energy **E(neutral doublet) minus E(enolate singlet), in Hartree**. Retain both
energies, convergence, S-squared diagnostics and molecular electron counts.
Report the deviation of the neutral S-squared value from **0.75**, any
nonpositive vertical ionization result and unbound/frontier warnings without
turning them into absolute rates or redox potentials. A failed neutral job
makes its ionization diagnostic unevaluable; it does not manufacture an
anion HOMO value or erase the independent anion result.

## Assessment, resource limits and stop

The **primary entry criterion** requires all four anion cases to be evaluable
and their primary Lowdin carbon ordering to recover C3 > C2 for B2/W2 and
C2 > C3 for B3/W3. An exact tie fails this ordering criterion. Retain the
separate primary outcome for each source functional pair and the secondary
Mulliken outcomes. Report all eight enolate-2-to-3 site directions across
both functional pairs, including oxygen-site disagreement. Do not select a
single successful functional, site subset or population method as a replacement
for a failed complete primary assessment.

Passing admits only that this declared open-engine diagnostic recovers the
source's carbon-site ordering in these exposed reduced substrates. Population
or functional dependence remains explicit. Failure rejects this selected
realization at this scope; it does not reject chemical modelling generally.
Neither outcome identifies a protein mutation, predicts intrinsic turnover or
specificity, supplies an SSU response, or establishes useful joined delivery
against conventional methods.

Cap the **whole eight-job realization** at **900 CPU seconds, 900 wall seconds,
2 GiB peak RSS and 128 MiB retained outputs**. Keep scratch within the same
128 MiB bound; place it only in the selected run directory and account for
peak scratch separately from final retained bytes. The final retained-output
bound includes the selected source/producing/protocol packet and results.
Account for native initialization, preparation, successful and failed jobs,
analysis and all storage; report acquisition/resource costs separately where
they precede the measured native realization. Resource limits are ceilings,
not predicted performance. Terminate at the ceiling, preserving complete
assigned roster and partial logs without reporting unfinished energies as
converged observables.

Authenticate original inputs, this frozen protocol, selected interpreter/lock,
launcher, producing code and full roster before the first SCF. Retain all eight
job statuses, source mappings, electronic states, numerical operands,
wavefunction/checkpoint identities where written, raw logs, metric operands
and assessment, including failures. This direct native pilot has **zero
recursive task receipts and zero established independent biological units**.
Any source, electronic-state, numerical, roster or criterion change requires
a successor protocol before execution; retain this result unchanged.
