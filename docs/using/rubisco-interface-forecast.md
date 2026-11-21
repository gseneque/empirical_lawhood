# Reconstruct a paired SSU forecast

For a selected Val1 electronic return, `read-crossed-fields` takes the same
`--native-root` and independently retained `--manifest-sha256` as
`read-crossing-orbitals`. Select four numerical threads for the original
CPU field calculation. The reader reconstructs the signed charge replacement
on both fixed hosts, every carbon and oxygen state, both hydration choices
and the original wet I95M recovery. It reports spectral bounds and work at
the original frozen density in hartree, the observed self-consistent shift,
and the signed four-state contrast in kcal/mol. The first missing reference
and its subsequent recovery have distinct records. [Field reconstruction](../../src/empirical_lawhood/api/domain_composition/rubisco_response/crossed_fields.py) · [Field energy bounds](../../src/empirical_lawhood/methods/electronic_structure/field_energy.py)

The command-line and Python routes share the same scientific operations. Call
`measure_interface_transfer` for the geometry, forecast, blind score or recursive
fit. Call `read_forecast_returns(native_root, evidence)` to compare the four
original conditioned materials, including failed trials, force checks, structural
components and process costs. The workbench's preparation and oxygen methods
identify their implementing operations. [Transfer API](../../src/empirical_lawhood/api/domain_composition/rubisco_response/interface_forecast.py) · [Return reader](../../src/empirical_lawhood/api/domain_composition/rubisco_response/forecast_returns.py)

The selected case compares matched small-subunit variants on held-out large-subunit backgrounds. It forecasts log mutant/parent ratios for activated-site carboxylation turnover and conventional CO₂/O₂ specificity. The conventional null has both ratios equal to one. An operationally successful reconstruction verifies numerical reproducibility. Independent enzyme outcomes govern scientific transfer.

Use the [construction environment](rubisco-construction-environment.md) for OpenMM, Amber and the structural profiles. For the fit use the [locked Rubisco prediction profile](environments.md). The selected evidence directory supplies the design commitment, structure assemblies, engineered sequence recipes and native primary tables. The separate input archive supplies the Wilson panel, potato source and complete target sequences. Each command writes its own fresh output.

```bash
uv run --no-sync python scripts/measure_gp_transfer.py geometry --evidence "$evidence" --reference "$dry_reference_zip" --output "$evidence/geometry.json"
uv run --no-sync python scripts/measure_gp_transfer.py predict --evidence "$evidence" --archive "$source_archive" --output "$evidence/forecast.json"
(cd "$evidence" && sha256sum forecast.json transfer-design.json geometry.json hybrid-recipes.json > frozen-inputs.sha256)
uv run --no-sync python scripts/measure_gp_transfer.py score --evidence "$evidence" --archive "$source_archive" --output "$evidence/evaluation.json"
uv run --no-sync python scripts/measure_gp_transfer.py recursive --evidence "$evidence" --project-root "$PWD" --workspace "$fresh_workspace" --output "$evidence/recursive-reconstruction.json"
```

Freeze numeric predictions before opening held-out labels. The retrospective recursive reconstruction imports only the original design's feature rows, training responses and outcome-free queries. It fits one through-origin two-output ridge, reads the saved result and compares the full roster against the frozen forecast. Supplies with different designs, observations or biological units require their own versioned selection. Missing assays and per-mass rates have explicit dispositions in the scoring return.

For a selected observed-core material, the caller supplies the authenticated Amber and numerical engine, six parameter sources, starting 1BWV pH 8 PDB, Met1 donor 1IWA mmCIF and keto-RuBP component. The cut LSU uses charged Amber termini. The charged-cut model and initial 75 fs of dynamics describe one structural starting assumption. Source paths in a selection may be absolute or relative to the selection file. Use a fresh directory for each build, conditioning attempt and full-coordinate validation.

```bash
uv run --no-sync python scripts/prepare_gp_forecast.py build --selection "$selection" --case M1-WT --output "$build"
taskset -c "$physical_cpus" uv run --no-sync python scripts/prepare_gp_forecast.py condition --build "$build" --protocol "$protocol" --output "$condition"
uv run --no-sync python scripts/prepare_gp_forecast.py read --build "$build" --condition "$condition"
taskset -c "$physical_cpus" uv run --no-sync python scripts/prepare_gp_forecast.py force --build "$build" --condition "$condition" --threads 8
uv run --no-sync python scripts/prepare_gp_forecast.py validate --build "$build" --condition "$condition" --output "$geometry_review" --runtime-prefix "$molprobity_root" --runtime-receipt-sha256 "$receipt_digest"
```

Choose eight different package/core pairs for the matched protocol and set secondary numerical thread pools to one. The retained final snapshot contains every particle coordinate, velocity, force and periodic vector. Chemical states, full-length transfer, steady-state equilibration and reactive discrimination require separate observations. [Independent CCTBX component scopes](rubisco-molprobity.md) · [KCX backbone supplement](rubisco-kcx-backbone.md)

The complete four-material assessor rejoins each native topology, trajectory endpoint, seven component results and the KCX supplement. It preserves superseded attempts and their available resource measurements.

```bash
uv run --no-sync python scripts/read_gp_forecast_returns.py --native-root "$native_root" --evidence "$evidence" --output "$review"
```


## Read the original gas-free SANDER study

Select the original cost ledger and its independent SHA-256. Select its native job directory and the reference input directory named by the material selections. Use the versioned SANDER installation manifest and its reviewed digest.

```sh
uv run --no-sync python scripts/prepare_gp_forecast.py read-sander \
    --ledger "$ledger" --ledger-sha256 "$ledger_sha256" \
    --native-root "$native_root" --reference-root "$reference_root" \
    --installation "$installed_sander" --installation-manifest "$installation_manifest" \
    --installation-manifest-sha256 "$installation_manifest_sha256" > "$new_report"
```

The Python entry point is `read_sander_release_archive(SanderArchiveSelection(...))` in `empirical_lawhood.api.domain_composition.rubisco_response.sander_archive`. It verifies all issued jobs, original sources and returned members through the numerical read. The result includes failed jobs, measured resources, original force checks and every observed trajectory prefix. Continuations use the original material, Hamiltonian, cell, restart and seed. Frame counts and cutoff decisions describe the selected finite gas-free paths. The historical engine manifest and the restored executable closure have separate identities. [Native installation](rubisco-construction-environment.md)

To compare conditional precursor occupancy, add `--precursor-panel panel.json`
to `read-sander`. Repeat the option to read several panels from the same ledger
in one verification. Each panel names one original material, its assigned seeds,
and one issued release per seed from each prepared origin. For example, the
nominal clear-HIP archive contains these assignments.

```json
{
  "panel_id": "clear-hip.v1-wt",
  "material": "V1-WT",
  "seeds": [11031, 22063],
  "coupled_jobs": ["V1-WT/coupled/released-direct-11031", "V1-WT/coupled/released-direct-22063"],
  "outer_jobs": ["V1-WT/outer/released-direct-11031", "V1-WT/outer/released-direct-22063"]
}
```

The same Python operation accepts a tuple of `SanderPrecursorPanel` selections
through `precursor_panels`. The reported bounds count occupied post-entry frames
and every assigned frame still unresolved at native failure. A continuation
contributes its authenticated prefix once. Each material remains one independent
assembly. Complete paths on matching grids supply the original 2.7 Å joint
test, first passages, water-shell transitions and late-quarter comparisons.
The finite-path exchange screen requires reciprocal shell transitions, overlap
of the two water-distance histograms and all four late-quarter ranges, and
three sustained round trips in each origin. A passing screen yields a model
fraction across the two prepared origins. The biological natural weight retains
its full interval from zero to one.

To continue a gas-free release, select its original parent directory relative
to the native root, its issued receipt digest, its restart digest and the
number of additional integration steps. `prepare-sander-continuation` takes
the same seven archive arguments as `read-sander`, plus `--parent-directory`,
`--parent-receipt-sha256`, `--parent-restart-sha256` and `--steps`. It verifies
the original chain and reports the child input digest before native entry.
The parent determines the material, quantum atoms, occupation, Hamiltonian,
sampling interval and cumulative clock. The thermostat seed follows the
original continuation rule.

`run-sander-continuation` accepts those arguments and requires `--output`
and `--timeout-seconds`. Give it a fresh directory under an existing parent.
The operation verifies the sources through the native return and records
the expected and observed frame counts, native exit, elapsed time and file
digests in `return.json`. The Python operations take `SanderArchiveSelection`
and `SanderContinuation` from the same module. Each execution has its own
attempt record and retains the original preparation's conditional scope.

## Inspect the periodic observed core

Select the original Val1 return with its independent `SHA256SUMS` digest and
the installed construction environment. Supply the real interpreter path and
its site-packages directory. The reader binds the topology, 20 ps hydrated
coordinates, selected seed, source-mapped atoms, water, cell and all seven
QM/MM cuts for the chosen material. Its output identifies the engine and
host coordinates and reports one independent assembly.

```sh
PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python scripts/prepare_gp_forecast.py inspect-periodic-core \
    --native-root "$original_return" --manifest-sha256 "$original_manifest_sha256" \
    --material V1-WT --site-packages "$site_packages" --interpreter "$real_interpreter"
```

For one conditional force calculation, use `evaluate_observed_core` in
`empirical_lawhood.api.domain_composition.rubisco_response.observed_core`.
Pass the `ObservedCoreSources` selection, the installed periodic engine record
from `select_periodic_numeric_engine`, spin multiplicity, periodic force settings
and an event observer. A gas-bearing selection also needs the pinned gas
parameter files and every gas atom's coordinates in angstrom. The return
contains the complete energy and gradient at that geometry. The gas-free
source contains one assembly per material. The [programme decision](../../programmes/biology/photosynthesis/records/gp-precursor-release.md)
covers the pending gas acquisition. [Periodic CPU environment](environments.md#complete-periodic-pyscf-forces-on-linux-x86-64)

## Read tagged-gas product observations

Use the original oxygen-path supplement and its pinned text extraction. The reader
checks the source bytes, derives the native oxygen and substrate atom identities
and applies the same bond and stereochemical criteria to all 24 structures.
Four of the published structures contain the bound 2-phosphoglycolate and
3-phosphoglycerate pair under the singlet structural criterion. A rate or a
probability of product release requires separate observations.

```sh
uv run --no-sync python scripts/prepare_gp_forecast.py read-oxygen-products \
    --original-pdf "$oxygen_pdf" --extracted-text "$oxygen_text"
```

For tagged-gas crossing observations, call `assess_tagged_flux_panel` in
`empirical_lawhood.api.domain_composition.rubisco_response.tagged_products`.
Select the assigned draw IDs, a mapping with one entry per ID, and a
`TaggedGasFluxMeasure` with temperature in kelvin and the crossing radius,
solute clearance and bath radius in angstrom. The historical Val1 selection
uses 298.15 K, 4 Å, 8 Å and 48 Å respectively.

For an observed Val1 trajectory, select its `ObservedCoreSources`, gas
parameter stock, numeric engine and `ReferenceDynamicsSettings`. Supply
the original frames in native atom order, starting at physical step zero.
Use `TaggedPathFrame` from
`empirical_lawhood.domains.rubisco.rubisco_response.tagged_path_observations`.
Each frame records its step, Cartesian coordinates in angstrom and active
singlet or triplet surface (`"S"` or `"T"`). At a possible bulk endpoint,
attach a `TaggedReservoirCharacter` from the selected electronic observation.
It binds the observation's source SHA-256, the SHA-256 of the full C-order
little-endian float64 Cartesian array, the gas atom indices in original
order, the reservoir surface and the gas charge and spin in electron units.
Read the frames and electronic observations from their verified original
files and keep those files with the result. This operation consumes the
supplied measurements and authenticates the selected host and gas sources.

```python
from empirical_lawhood.api.domain_composition.rubisco_response.observed_core import read_observed_tagged_path
from empirical_lawhood.domains.rubisco.rubisco_response.val1_flux import paired_path_transmission

options = dict(engine=engine, dynamics=dynamics, measure=measure,
               reservoir_source_sha256=reservoir_source_sha256)
back = read_observed_tagged_path(selection, frames=back_frames, side="back", **options)
forward = read_observed_tagged_path(selection, frames=forward_frames, side="forward", **options)
transmission = paired_path_transmission(back, forward)
```

The reader derives atom roles and the periodic cell from the selected
original host. It reports the first endpoint and its physical time. The
default product residence is four elapsed steps spanning five consecutive
bound-product frames. Another water entering the Mg shell or missing
reservoir character leaves the corresponding fate unresolved. An early
end to the frame stream retains the observed prefix. Recording a paired
transmission for the draw also requires its original insertion weights.

To prepare draws from one gas-free host, call `sample_tagged_flux_host` in
`empirical_lawhood.domains.rubisco.rubisco_response.val1_flux`. Supply the
original positions in angstrom, one natural mass in daltons per atom, the
selected measure and the complete fixed-cell reference force's `evaluate`
callback. Pass a `ReferenceDynamicsSettings` with the step in seconds and
the number of velocity-Verlet steps per proposal. Select a PCG64 seed,
`burn_in`, `draws` and `relaxation_evaluations`. Setting the relaxation
limit to zero starts the chain at the supplied geometry. A positive limit
starts it at the lowest energy actually evaluated during relaxation.

Use `capture(record, positions_angstrom)` to retain each proposal in order.
The record identifies burn-in, acceptance, the trial energy, the change in
Hamiltonian and the retained energy. Rejected proposals repeat the current
position. Force and capture errors stop the chain with the delivered prefix.
These correlated draws describe one host, selected operator and temperature.
Independent host preparations and evidence for their weights are needed to
interpret a population rate.

Each measured draw supplies bulk and surface log insertion weights,
the free-volume fraction, mean positive thermal speed in nm/ps and one
transmission disposition (`PRODUCT`, `ZERO` or `UNRESOLVED`). Use `None`
for an assigned draw which never entered. The report gives the complete
transmission census and lower and upper natural-log rates in L mol⁻¹ s⁻¹.
An unresolved trajectory widens the interval. A missing insertion weight
leaves the upper bound unbounded. These bounds concern the selected draws
within their host preparation, bath and Hamiltonian.

## Compare original electronic states across the oxygen path

Select the funded Val1 native return and the independent SHA-256 of its
`SHA256SUMS`. The historical orbital comparison used four numerical threads.
Run it with the PySCF environment and an allocation of at least four CPUs.

```sh
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
    uv run --no-sync python scripts/prepare_gp_forecast.py read-crossing-orbitals \
    --native-root "$original_return" --manifest-sha256 "$original_manifest_sha256"
```

The reader reconstructs occupied electron spaces from each saved converged
density and its def2-SVP atomic-orbital metric. For each pair of neighboring
geometries it computes the squared singular values of the occupied overlap
using the cross-geometry integral. A value near zero identifies an occupied
direction largely absent at the other point. The report retains both global
spin-label comparisons for the two zero-spin-projection starts, missing
comparisons, and each original path's energy bracket. It also reconstructs
the tagged oxygen Mulliken charge and spin and the total spin squared. Of
84 state slots across 28 geometries, 76 supplied converged determinants,
six returned unconverged and two never entered. These observations
describe electronic continuity on the sampled configurations. Evidence for
spin-transition probabilities or an enzyme rate requires additional inputs.

To locate a crossing on a selected trajectory segment, supply both measured or calculated
endpoint gaps and a callback that evaluates the same states at each requested fraction of the
segment. The Val1 proposal selected a singlet-minus-triplet residual of at most 10⁻⁵ hartree
and a limit of nine probes. `locate_bracketed_energy_gap` returns the accepted fraction,
residual and actual electronic state from that probe. [Energy-gap bisection](../../src/empirical_lawhood/methods/electronic_structure/surface_crossing.py)

At each probe, `opposite_spin_frontier_densities` constructs the two starting densities for a
separate broken-symmetry calculation from the triplet alpha orbitals, their AO overlap and
the singlet occupation per spin. Supply the three independently evaluated energies to
`oxygen_singlet_triplet_gap`. The Val1 proposal used a lower-root tolerance of 10⁻⁴ hartree
and a competition window of 0.01 hartree. A competing lower root leaves the crossing unresolved.
[Orbital preparation](../../src/empirical_lawhood/methods/electronic_structure/occupied_space.py) ·
[Oxygen surface selection](../../src/empirical_lawhood/domains/rubisco/rubisco_response/electronic_coupling_science.py)

For a resolved crossing, `oxygen_crossing_decision` takes the donor-averaged
squared coupling and its error bound from `singlet_triplet_spin_orbit`, the
incoming surface (`S` or `T`), the absolute gap speed in hartree/fs, the
selected speed resolution, ℏ in hartree·fs, and the original uniform draw.
The model assumes an isotropic triplet with one bright combination. The
result gives lower and upper probabilities and a decision to attempt the hop,
stay on the donor, or retain an unresolved draw. [Spin coupling and decision](../../src/empirical_lawhood/domains/rubisco/rubisco_response/electronic_coupling_science.py)

For an attempted hop, `rescale_crossing_velocity` takes the original
Cartesian velocities in nm/ps, physical masses in dalton, gap gradient and
destination-minus-donor energy in kJ/mol. It returns the velocities and
whether the directional kinetic energy permits the hop. The Val1 path
proposal used a minimum resolved gap speed of 10⁻¹² hartree/fs. Its paired
reactive trajectories were held at preparation, so the available orbital
returns supply no measured transition frequency. [Energy-conserving impulse](../../src/empirical_lawhood/methods/electronic_structure/surface_crossing.py)
