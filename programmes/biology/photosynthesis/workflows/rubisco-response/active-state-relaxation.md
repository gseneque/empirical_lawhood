# Complete active-state preparation and matched relaxation

SPDX-License-Identifier: CC-BY-4.0

This workflow prepares every catalytic site of the four M1/V1 WT/I95M models
and retains the complete declared chemical alternatives. It can then relax each
starting geometry with the selected full periodic reference potential through
the existing recursive execution and native-subwork lifecycle. A prepared
geometry or stationary endpoint does not establish an equilibrium population,
chemical accuracy, force accuracy, a physical rate or a mutation response.

Use the original assessed full Amber construction, its complete molecular
representation and coordinate bytes, and the
[periodic force selection](periodic-force-probe.md). Authenticate their original
publication and native receipts before supplying them to this workflow. The
original topologies, waters, ions, atom order and complete molecular environment
remain the scientific operands. The eight sites are nested views of one source
assembly, not eight independent biological replicates.

For GPU relaxation, select `AcceleratedPeriodicNumericEngine` in each matched prototype and `accelerated_compute: true` in the invocation.
Follow the [accelerated-compute guide](../../../../../docs/using/accelerated-compute.md) for environment and resource selection.
The authoring function derives a separate GPU configuration for the complete or conditional state selection.
The endpoint reader requires original GPU apparatus and complete force-cost observations before it accepts a GPU endpoint.
No GPU selection changes the four-material, 384-state preparation denominator.

## Prepare and independently read every site

The public owner is
`empirical_lawhood.api.domain_composition.rubisco_response.active_models`.
`prepare_active_model` accepts the complete `representation`, `prototype`,
`coordinate_bytes`, an `ActivePreparationProtocol`, an `artifact_writer` and a
fresh `output_relative_path`. It returns the typed preparation, its published
path and artifact manifest. An optional observer receives each independently
checked site partition.

Build the protocol with `read_catalytic_core_graphs` from an authenticated
`SourceMember` containing the complete selected graph census. The current
protocol requires nine explicit catalytic graphs. Each conserves 118 physical
core atoms and seven boundary hydrogens, net core charge −2 and 476 core
electrons. Those accounting checks and the initial graph's exact native bond
correspondence do not validate the proposed chemical states.

The preparer derives all eight catalytic partitions from their own coordinates.
The selected core includes complete side chains of LSU positions 184, 186,
210, 212, 213, 302 and 342, with explicit CB–CA boundaries, complete RuBP and
the corresponding magnesium. It includes every complete water whose oxygen
is within 3.5 Å of a core nitrogen/oxygen or within 3.0 Å of magnesium, using
the original periodic cell. It checks that every actual first-shell nitrogen
or oxygen within that magnesium cutoff belongs to the QM partition. No
first-site water roster is copied to another site.

Each site retains twelve starting geometries:

- Keto, initial enolate and enediol graphs, each with HIE and HID alternatives.
- Three reactive proton allocations, each with occupied and unoccupied
  magnesium-water alternatives.

The original physical atom population is conserved in every alternative.
Transferred protons receive declared geometric starting positions. An occupied
water hypothesis moves one existing complete water, using a proper rigid
rotation and a deterministic geometric clearance search. Its selected oxygen
distance is 2.15 Å. The unoccupied hypothesis requires all selected water
oxygens to remain outside 3.5 Å. These are starting hypotheses; no energy,
occupancy probability or preference is inferred from their construction.

Each `CatalyticStateSeed` retains sparse coordinate changes, the full original
coordinate digest and the digest of its expanded complete successor array.
`expand_state_coordinates` requires the exact complete original bytes and
rechecks the complete successor. Unchanged coordinates are preserved exactly.
This avoids copying a full solvent array for every hypothesis while keeping
every atom an explicit, recoverable operand.

`read_active_model` accepts the original representation, prototype and coordinate
bytes, plus the publication's relative path and artifact writer. It authenticates
the publication and independently checks every water roster, source bond,
physical atom, proton placement, moved-water geometry and new close contact.
It never invokes the constructor or a native engine. Adverse construction
findings remain in the complete 96-state preparation; they are not dropped.

## Freeze a matched relaxation design

The public owner is
`empirical_lawhood.api.domain_composition.rubisco_response.active_relaxation`.
Call `prepare_matched_active_relaxation(models=..., settings=...)`, with four
tuples of `(material, preparation, prototype)` and explicit
`ActiveRelaxationSettings`. The returned `MatchedActiveRelaxationPlan` binds all
four materials, the identical site/state census, chemical preparation protocol,
electronic and molecular settings, numerical engine and endpoint thresholds.
It requires the exact all-eight-SSU I95M intervention within each M1/V1 pair.
Authoring additionally joins each supplied material to its complete molecular
representation. Model names cannot substitute for sequence correspondence.

For each selected member, call `author_active_relaxation` with the plan,
`model_name`, prepared record, original prototype and complete representation,
original raw Amber topology and coordinate bytes, project root, artifact writer,
fresh authoring destination and native work directory. The returned handoff
uses ordinary `run_recursive_wave` and its existing recovery route. The public
author constructs the complete task and native roster; do not hand-build them.

The registered operation is `rubisco-response.matched-active-relaxation`.
One operation retains all 96 starts of one model. Its 104 direct inputs are
the configuration, seven complete shared scientific records, and 96 separately
authenticated seed records. Its original topology is retained once in the
working root. Every state has a distinct native definition, entry, actual-call
observation, return, raw archive, complete file census and completion receipt.
The frozen matched plan retains the four-model denominator even when only one
member has run. Four member readouts are required for the matched assessment.

Before the first native entry, the worker joins all original inputs and
independently rechecks every prepared partition and seed. A rejected seed
refuses the operation before entry. That seed remains in its preparation and
must be addressed explicitly; it is never silently removed from the roster.
The worker authenticates the selected numerical environment using the same
thread and source rules as the periodic force probe.

The operation retains the selected eight CPU equivalents, 8 GiB RAM and 4 GiB
native-output allowance, with no experiment time ceiling. Thread counts must
match the selected engine. Neither an authored plan nor these allocation
values establish that a full enzyme calculation fits memory. Resolve a failed
force evaluation and validate the reference operator before launching an
expensive relaxation tranche.

## Retain and assess the actual endpoints

### Select a conditional pilot before execution

Use `prepare_conditional_active_relaxation` when the next scientific question requires an explicitly limited preparation scenario.
Supply the complete matched `plan`, an ordered `state_census`, and explicit chemical `assumptions`.
Each census row contains the original site identifier, state label and water-occupancy label.
The same rows must exist in all four materials.
Empty, repeated, unknown and unmatched rows refuse.

Pass the returned record as `conditional_selection` to `author_active_relaxation` for each material.
The registered operation is `rubisco-response.conditional-active-relaxation`.
It uses the existing native execution, minimizer, force operator, resource lock and original-result reader.
The selection receives its own direct input and native-source identity.
All original preparation records and 96 direct seed inputs remain authenticated.
The native roster contains exactly the selected starts.
The original complete operation and its record formats remain available unchanged.

Freeze this selection and its assumptions before observing candidate effects from its new calculations.
Use measured force cost to select feasible pilot counts and controls.
A prior preparation geometry does not supply a state population or physical rate.
Do not select a favorable state after inspecting its mutation effect.

Read each original result with `read_active_relaxation`.
Pass the same `conditional_selection` to `assess_matched_active_relaxation` with all four original readouts.
The assessment retains every selected success, failure and unevaluable endpoint.
It separately counts each unselected start as unmeasured within the complete 384-state preparation census.
Unselected alternatives have no inferred energy, population, success or failure.
Matched endpoints remain conditional on the declared scenario.
Equilibrium populations, chemical applicability, turnover and specificity require their own evidence.

### Retain complete original returns

The native owner uses the complete periodic energy and physical-atom gradient
in the existing limited-memory geometry minimizer. There are no added
restraints, artificial masses, thermostat or molecular clock. The minimizer has
no total iteration or evaluation ceiling; its numerical line-search and
resolution failures remain explicit nonconvergence. Electronic convergence uses
the separately selected periodic-force settings. The raw derivative unit is
`Eh/PySCF-Bohr-0.52917721092-A`, with the same Coulomb-consistent energy conversion
as the reference operator.

Each seed starts with an independent electronic guess. Within a closed-shell RKS
seed, the next geometry uses the density from the preceding successful complete evaluation.
Every geometry rebuilds its electronic potentials and retains both convergence criteria.
The observation identifies the source evaluation, coordinates and density digest.
A failed evaluation discards the saved guess. Changed operator settings, atom
partition, basis layout, cell or embedding charges refuse reuse before SCF.

Separate seeds and materials share no density. This follows the initial-guess
principle of the [PySCF scanner](https://pyscf.org/pyscf_api_docs/pyscf.scf.html#pyscf.scf.hf.as_scanner),
with fresh periodic potentials at each geometry. It does not establish a unique
electronic minimum or qualify the enzyme model.

Open-shell UKS evaluations retain independent initial guesses. An exposed UKS
control required substantially more SCF iterations with the preceding density.
Small-control cost comparisons do not establish an enzyme speedup.

Every energy/gradient attempt is recorded. The owner makes a fresh full force
call at the final endpoint and retains complete initial and final coordinates,
the complete final gradient, energy, nested electronic observations, selected
protocol and source bindings. It publishes original native files and the
completion receipt before scientific endpoint assessment. Actual failures keep
their partial files and measured cost.

Use `read_active_relaxation` with the original configuration, representation,
prepared record, complete original coordinate bytes, original result,
native-subwork reader, assessor-source identity and new readout ID. The reader
authenticates all 96 definitions, receipts and original archives. It makes no
force call and constructs no coordinates. It checks:

- Every full array, exact native units, evaluation sequence and separately
  retained final force, including the selected maximum gradient.
- Proton-host distances and nearest heavy-atom assignments; selected water
  occupancy using all original water oxygens; gross catalytic heavy-bond loss
  and complete-environment heavy-atom contacts.
- Original protein CA and ILE/THR stereocentres, all RuBP C4 stereocentres,
  and keto-state C3 stereocentres. Enolate/enediol focal C3 is not treated as
  a retained tetrahedral stereocentre.

Default endpoint selections are a maximum gradient of 1 kJ mol⁻¹ nm⁻¹,
maximum proton-host distance 1.3 Å, occupied-water distance at most 2.8 Å,
unoccupied-water distance at least 3.3 Å, minimum nonbonded heavy contact 1.0 Å,
and minimum absolute stereocentre determinant 0.01 Å³. A catalytic heavy bond
longer than 2.2 Å is a gross-break diagnostic. An endpoint energy increase above
twice the selected electronic energy tolerance is rejected. These explicit geometry checks do not infer
electronic bond orders or chemical-state admission from distances.

Native failure, missing endpoint operands, failed force convergence and departure
from a selected geometry remain different outcomes. An optimizer success flag
cannot replace the independently read final gradient. A state that relaxes
away from its starting proton/water hypothesis remains in the result with its
findings; no basin is relabeled or assigned a population. The reader hashes
every archived file even on failures. Selected endpoint operands above its
256 MiB in-memory envelope remain authenticated and retained, with an explicit
unevaluable assessment instead of a truncated read or repeated calculation.

`assess_matched_active_relaxation(plan=..., readouts=...)` requires the four
original member readouts and their exact plan/source joins. It reports all 384
selected starts, including rejected endpoints, missing assessments and native
failures. Stationary geometry counts are not equilibrium weights. Populations,
chemical-state admission, reference-force accuracy and turnover/specificity
contrasts remain unevaluable until their separate physical evidence is supplied.

A known completed attempt is recovered from its original receipt and bytes.
A contacted attempt with unknown completion cannot be repeated automatically.
Use the shared native-subwork inspection and recovery interfaces for incomplete
work. Preserve the original roster and every entered attempt.
