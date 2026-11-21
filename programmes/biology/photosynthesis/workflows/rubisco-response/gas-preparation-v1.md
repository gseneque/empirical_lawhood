# Prepare source-bound carbon and oxygen inputs

SPDX-License-Identifier: CC-BY-4.0

This protocol binds original gas geometries and parameter stock for the
[initial conditional model](initial-model-v1.md). It supplies source and
coordinate preparation components. It does not supply an equilibrated gas
encounter, an electronic state, an addition rate or a commitment probability.

## Original sources and direction

Use protocol `GP-GAS-PREPARATION1` with the existing complete Gp preparation
and its selected focal enolate state. Preserve all four materials and the
original starting-hypothesis denominator. A common initial local geometry
across WT and mutant does not establish mutation invariance after relaxation.

Use the public Python composition
[`gas_preparation`](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/gas_preparation.py).
Select original source bytes explicitly. The source and coordinate functions
do not download files, build a provider or start a native task.
Publish their returned canonical records through the existing guarded
artifact writer and retain the original source bindings.

`prepare_oxygen_source_projection` accepts the exact 2019 oxygen SI PDF and
a separately retained text extraction. It checks all 24 original geometry
projections, containing 5,994 atoms, against the maintained token digests.
This is a new extraction; it does not reconstruct an earlier inspection
JSON or its custody. The first unprotonated syn state supplies the selected
oxygen encounter coordinates. Its original one-based gas indices are
162 and 168. The source fragment's charge and spin do not become Gp job cards.

`prepare_carbon_source_projection` authenticates the exact
[2022 input archive](https://zenodo.org/records/6791151) and its complete
112-member census. It joins 79 physical atoms in each 86-atom QM geometry
to the corresponding original PDB, keeping seven boundary hydrogens separate.
Native R/TS/P describe decarboxylation: P is the separated CO2 source for gas
addition, and R is the carboxylated source. The P file's literal element
token `M1` remains in its original bytes. The successor Mg interpretation
is explicit and binds original PDB atom 7231. `assess_carbon_source_projection`
reconstructs the source join; it does not independently assess chemistry.
Retain the source KCX/HID protonation and its difference from selected Gp HIE.

## Carbon and oxygen coordinate transfer

`prepare_oxygen_encounter` takes the original complete molecular
representation, active preparation, selected enolate seed, original coordinate
bytes and periodic cell. The supported selections are the original
`initial-enolate-kcxh-hie` `AS_CONSTRUCTED` seed and the
`reactive-enolate-kcxh-hie` `UNOCCUPIED` seed selected by the conditional model.
The latter retains the original proton overlay and displaced coordination
water. It does not remove water atoms or establish their population.
Use the matched preparation's returned seed and site objects.
The function matches C2, C3, O2, O3 and Mg by their actual source and target
atom roles. It uses a proper rotation, preserves the complete target
environment and records both added-atom coordinates without modifying a
topology. It observes nearest atom and nearest heavy-atom contacts against
every original physical atom with periodic images.

`assess_oxygen_encounter` checks the original identities and correspondence,
rotation orientation, least-squares lower bound, residuals, gas positions
and complete periodic contact observations without invoking the fitting
producer. Its numerical comparison tolerance is not a physical overlap
or fit-adequacy criterion. Retain short contacts and unresolved geometry.
An unrelaxed coordinate proposal cannot establish a populated encounter basin.

`prepare_carbon_encounter` uses the same complete target and fitting/contact
owners. It selects the original P geometry and its CO2 atoms C57, O63 and
O64. Its source C2/C3/O2/O3/Mg anchors are 53, 54, 59, 60 and 51.
The record retains the native P label and gas order; a source R label cannot
be relabelled as a separated encounter. `assess_carbon_encounter` independently
checks the retained transform and all three gas–environment contact censuses.
Keep source protonation differences, residuals and short contacts explicit.
Neither gas preparation moves the target's original atoms or supplies a
populated encounter, bulk partition coefficient or reaction barrier.

## Gas parameter stock

The [Amritkar source revision](https://github.com/kacarlab/RuBisCO_evolution/tree/e6c621656ca1a8eb7e09381d6405da5d412274a1/data/systems_for_MD/parameters)
contains CO2 and O2 PREP/FRCMOD files. `prepare_gas_amber_stock` authenticates
those exact bytes and assigns gas-specific atom types, after checking the
complete existing host type census for collisions. Existing protein,
substrate and solvent types must not receive global overrides.
`assess_gas_amber_stock` independently compares all original atom, charge
and parameter tokens after reversal of the type aliases.

Keep the original O2 equilibrium bond length of 1.430 Å separate from its
supplied 1.150 Å coordinates. Preserve the CO2 charge-token sum of
−0.000001 e. Do not silently repair either source or promote source reuse
to a bulk-gas force-field assessment. For a reactive QM/MM use, all reactive
gas atoms must enter the selected QM region. Independently check exactly
which original classical bonded, electrostatic and nonbonded terms are
removed or retained in the complete coupled operator.

## Complete topology transformation component

Use the public
[`gas_parameters`](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/gas_parameters.py)
composition to select the existing ParmEd 4.3.1 and numerical environment.
`select_gas_parameter_engine` records the complete selected package files and
interpreter without importing native libraries. `prepare_gas_parameter_source`
binds the complete original host topology and both gas stocks.
`author_gas_parameter_pair` uses the ordinary authoring owner and returns the
authoring directory and direct input paths. Execute that returned directory
through the [existing researcher lifecycle](guide.md).

The native operation retains two nested gas alternatives for one complete
host. Each transformation loads one host topology, constructs one gas and
combines their parameter tables. It evaluates no forces. Its selected local
allocation is one CPU, 8 GiB memory, 512 MiB scratch and 2 GiB output, with no
native wall-time limit. These resource ceilings do not establish chemical
adequacy. Static discovery performs no engine inspection or library contact.

The ordinary native lifecycle retains actual calls, elapsed costs, raw
returns, failures and uncertain completion. It seals each raw return before
independent parameter assessment. `read_gas_parameter_pair` authenticates the
original completion and raw archive, then reassesses without invoking ParmEd.
An uncertain call is not repeated automatically.

`prepare_gas_topology_augmentation` joins an authenticated, assessed parameter
return to its original complete target, selected seed, source encounter,
parameter stock and periodic cell. This coordinate join makes no native call.

The returned candidate contains complete raw topology and binary64 coordinate
bytes. Retain these bytes before independent assessment. Its initial
`parameter_assessment` is `None`: the complete coordinate join still needs
the independent reader below. Preserve its original native parameter-product
identity alongside the new candidate. Parameter acceptance does not admit
the gas placement or electronic state.

`assess_gas_topology_augmentation` checks the retained candidate without ParmEd
or a call to the transformation producer. It compares all host atoms,
charges, masses, exclusions, signed bonded terms and parameter slots.
Unused parameter slots and inactive zero 1–4 scales remain explicit.
It checks every original Lennard-Jones pair and each added gas interaction.
Original printed values remain exact. New coefficients use a declared
relative tolerance of 10⁻⁸ for parameter serialization.
Distinct original chemical type names can share a Lennard-Jones index.
If the native writer separates them, the reader follows every atom's actual
type correspondence and checks all resulting host pairs. Combining types
with unequal original coefficients is refused.

The reader checks every original host coordinate as an exact binary64 prefix.
It checks gas positions against their original source-to-PREP correspondence.
CO2 PREP order is O1/C1/O2, with source indices 63/57/64.
O2 PREP order is O1/O2, with source indices 162/168.
Neither a successful parameter check nor a preserved coordinate prefix
establishes a physical encounter, reactive electronic state or rate.

## Required physical successor

`prepare_gas_reactive_candidate` maps an original-bound augmentation to a
complete `MolecularRepresentation`, `CatalyticPathSelection` and periodic
cell. Select the original prepared site and explicit electronic settings.
The function retains every host atom, residue, boundary and MM index, and
adds every gas atom to the focal QM region. The other seven sites and the
complete SSU environment remain in the input. Native topology edges do not
invent chemical bond orders. Use the original augmentation reader above to
authenticate and assess the parameter and encounter inputs first.

`GasModelConvention` binds the common host preparation and parameter model,
gas stock and coordinate format. Each host's distinct native parameter return
and coordinate augmentation remain in its source ancestry. Corresponding gas
atoms keep the same named focal-site residue across WT and mutant, even when
their native indices differ. The ordinary finite atomic transformation can
therefore retain the gas and identify the actual substitution changes.

The neutral-reactant selection combines the selected singlet host with
neutral singlet CO2 or neutral triplet O2. Total formal charge stays equal
to the host charge; oxygen requires explicit UKS settings. This is a
prospective electronic hypothesis, not an electron-transfer population
constraint, peroxide assignment or spin-transition mechanism. In particular,
do not turn the isolated gas electron counts into projected-population
targets. Oxygen's remaining mechanism requirement stays visible.

The existing periodic entry accepts Amber ASCII coordinates. The preparation
therefore retains the exact binary64 augmentation separately and creates an
explicit F12.7 coordinate successor. `GasCoordinateEncoding` records its
original identity, resulting bytes and array identity, number of changed
binary64 components, largest actual change and largest decimal printing
error. Printing error is bounded by half the last decimal unit,
5 × 10⁻⁸ Å. The periodic cell must survive exactly. This is a serialization
bound, not a molecular accuracy or overlap tolerance.

`assess_gas_reactive_candidate` independently checks the retained full model,
source correspondence, host preservation, all gas QM atoms, charge/spin
arithmetic, exact cell and coordinate conversion. It does not replay the
mapping or serialization producer. Retain the complete representation,
path, cell, convention, encoding and electronic selection together with original raw
inputs. The returned records can enter the existing periodic selection and
raw-source preparation services. No gas force calculation is started by
this mapping or its reader.

Before native gas work, bind the assessed target state, gas-augmented
topology and complete parameter assignment, masses, cell and QM/MM boundary.
Select total charge, multiplicity, proton allocation and any required
electron-transfer/spin-transition model. Retain the source-to-Gp differences.
The oxygen protocol needs an open-shell reactant and its supported connection
to productive chemistry; a carbon RKS calculation cannot supply it.

Then bind the finite physical quantity required by the initial model:
paired effective carbon/oxygen addition, shared carbon productive commitment
and exit time, and oxygen productive commitment. Preserve access,
transmission, return paths, uncertainty and failed or censored outcomes.
The source preparation components establish none of these quantities.
Use the existing native authoring, execution, recovery and independent
assessment services once their actual inputs and scientific selections exist.

## Relax one selected gas starting point

Use the public
[`gas_relaxation`](../../../../../src/empirical_lawhood/api/domain_composition/rubisco_response/gas_relaxation.py)
composition after the complete input assessments above.
This operation minimizes one selected neutral-gas starting point with the
complete periodic QM/MM gradient. It does not modify the original gas-free
preparation or its complete starting-state census.

`prepare_gas_relaxation_selection` binds the complete gas model and periodic
prototype to their original augmentation, coordinate encoding, convention and
neutral electronic selection. Supply the original prepared site, selected seed,
preparation protocol and explicit `ActiveRelaxationSettings`.
The selection preserves every host atom, appended gas atom, boundary, source
and proton/water hypothesis. Oxygen retains its explicit neutral triplet and
UKS selection. This entry supplies no charge-transfer or crossing model.

Select the stage's actual resources and execution authority separately.
`author_gas_relaxation` publishes the complete original inputs under the selected
guarded destination and returns its ordinary authoring directory.
Use that returned directory with the existing
[recursive execution and result procedure](../../../../../docs/using/recursive-inquiry.md#freeze-and-execute-one-selected-wave).
Keep the producing source, selected numerical environment and operator profile.
Authoring and static discovery make no force call or prerequisite inspection.

The registered CPU and accelerated operations use the existing complete-gradient
minimizer. They add no restraint, artificial mass, physical clock or population
weight. The first electronic call is cold. Subsequent RKS calls may reuse their
own converged density; this UKS entry uses cold electronic solutions.
The original numerical resolution stops remain. No iteration, evaluation or
wall-time ceiling replaces the separately selected monetary policy.

The native return preserves all nested calls, initial and final coordinates,
a fresh final energy/gradient, source bindings, coupling diagnostics and failures.
The ordinary lifecycle owns receipts, original archive publication and recovery.
An uncertain contact is not repeated automatically.

`read_gas_relaxation` authenticates the entire original archive before reporting
a result. It reconstructs the force/convergence census and checks original units,
initial coordinates, proton allocation, Mg-water state, contacts and stereocentres.
It reports all internal gas separations, nearest host contacts and gas-to-C2
distances in ångströms. These observations have no invented gas-basin threshold.
Short contacts, escaped host states and incomplete convergence remain findings.
Numerical acceptance establishes neither gas-basin nor electronic-character
admission, force accuracy, equilibrium population, activation free energy or rate.
