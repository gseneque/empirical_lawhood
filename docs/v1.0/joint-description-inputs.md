# Physical and native inputs for the new joint-description experiments

Start with [experiment authoring](joint-description-experiments.md) for the
researcher workflow and execution commands.

R13–R19 and R22 are new experiments modeled on the preprint's scientific
questions. They do not read an original result, reuse an accepted fitted law,
reconstruct the old case roster, or promise the old numerical conclusion. Their
finite comparison asks whether a cheaper description remains useful for the
authored preparation, intervention, receiver and horizon family, and whether an
omitted dependence returns as explicit interface coordinates, retained history,
or prediction/control error.

The scientific definitions live in
`domains/joint_description_native.py`. Its `presets()` supplies editable
questions, action/horizon menus, receiver policies and four description
candidates. `prepare_predictors()` constructs the pre-outcome table. `produce()`
acquires the requested response table through the selected physical adapter or
the execution runner's typed native port. These are scientific contributions to
the recursive protocol, not a second standalone campaign runner.

## Researcher choices and interpretation

Author calibration and evaluation **independent-unit IDs** before execution.
Cells, optical blocks and discharges are independent units; action options,
horizons, time samples, numerical models and receiver channels remain nested
within those units. A physical unit cannot be present in both splits. Select
the full intended action menu even when an archive records only some options:
unlogged options become explicit unsupported rows and are never invented.

Preparation checks the archive schema, pre-action coordinates and independent-unit
assignment for both splits. For R22 it also validates every selected native
profile against its recorded core temperature and density. Receiver reduction
takes place in the acquisition phase. A valid roster can include unavailable
or failed episodes.

Review every receiver's target, normalization scale, absolute-error promise,
safety bounds and weight. The included numbers are editable experimental design
choices. They are not a clinical, instrument, battery or plasma safety
certification. Receiver scales preserve physical units when the common method
constructs a dimensionless utility. Economic prices and reuse assumptions are
likewise authored inputs; a finite winning candidate does not establish a
globally smallest description.

The description menu tests a one-coordinate instantaneous model, an additive
preparation/history model, an interface-augmented model and a joint product
model. All fits use calibration units. Multiplicative features are declared
algebraic coordinates, not features trained on evaluation outcomes. A history
coordinate is charged as one retained sample of one dimension. R17's supplied
preparation has no measured history coordinate and is charged no memory.

The common recursive sequence must freeze predictions and action choices before
evaluation acquisition. Preparing evaluation predictors performs no native
engine call and invokes no physical receiver reducer. Evaluation acquisition
uses the identical feature constructor; execution rejects feature substitution.
The simulator obtains a potential-action panel for a held-out action-selection
audit. This establishes neither an online feedback controller nor a physical
intervention result.

## Family contracts

| Family | Preparation/history fields | Action | Actual receiver calculation | Evidence scope |
| --- | --- | --- | --- | --- |
| R13 | `baseline_hz`, `history_hz`, `resistance_mohm` | Injected-current option, pA | Spikes in `[0,T)` divided by `T` | Logged cell options only |
| R14 | `baseline_angle_rad`, `history_angle_rad`, `resonance_hz` | Constant signed mirror drive, V | Signed endpoint displacement, rad | Recorded optical blocks; sign is retained |
| R15 | `history_current_a`, `initial_soc`, `initial_temperature_k` | Constant discharge-positive current, A | Endpoint voltage and integrated current in A.h | Recorded cells; source measurement uncertainties retained separately |
| R16 | `baseline_density_1e19_m3`, `baseline_gas_rate`, `history_receiver` | Requested modulation frequency, Hz | Complex receiver/gas-rate phasor at that frequency | Recorded discharges, with windows/samples nested |
| R17 | `bootstrap_multiplier`, `density_nbar`, `inner_transport_scale`, `temperature_scale` | Fractional change of declared NBI power | Native Gym–TORAX `Q_fusion` | Fresh simulator preparations |
| R18 | `history_current_a`, `initial_soc`, `initial_temperature_k` | Constant current after a history prefix, A | Native SPMe voltage, capacity and peak temperature | Fresh PyBaMM simulations |
| R19 | Same battery preparation/history fields | Same current continuation in two models, A | Absolute DFN–SPMe voltage and peak-temperature defects | Reduced-model adequacy; not an exact-state restart claim |
| R22 | `core_temperature_ev`, `density_1e19_m3`, `heating_power_w`, `history_temperature_ev` | Fractional change from declared heating power | Separate recorded and native TORAX core-temperature changes, eV | Archive scope and conditional simulator scope remain distinct |

### R15 uncertainty and R19 reduction

For R15, set `parameters.current_tracking_tolerance_a` before evaluating
recorded cells. It is the maximum absolute difference, in amperes, between
the nominal command and the measured current through each receiver horizon.
Recipes that omit the field use the historical value of 0.000001 A. Document
the source protocol and pre-action evidence for a wider tolerance. Wider
bands must preserve the sign of each nonzero command and be disjoint across
the menu. An excursion fails the affected horizons. Capacity always integrates
the measured discharge-positive current on the recorded clock.

R15 preserves source voltage and capacity uncertainties in evaluator-only
diagnostics. These are measurement uncertainties, not a newly calibrated
predictive confidence interval. The common response-law assessment tests its
authored absolute-error promises. Do not label that assessment a statistical
coverage guarantee without an additional declared interval-calibration method
and independent calibration/evaluation protocol.

R19 builds a DFN and an SPMe model with the same authored initial SOC,
temperature, history-current duration, continuation current and thermal model.
Each evolves its own model state. Their comparison tests supported reduced-model
continuations. It does not assert identical hidden states across models,
simulate an exact state transplant, or recite the old preprint count of passed
continuation checks. Every action/horizon/receiver defect remains in the result,
including failures.

## Strict raw physical JSON

R13, R14, R15, R16 and R22 require caller-supplied raw JSON. Select it through
the recursive workflow's typed input materialization route so the run binds the
exact bytes. Production passes the retained JSON directly to the adapter;
no unguarded temporary path is created. An explicit path is also available to
standalone adapter clients, mutually exclusive with the pinned JSON transport.
The physical adapter reads at most 64 MiB and retains its SHA-256.
Unknown fields, duplicate JSON keys, nonfinite numbers, changed units, duplicate
independent units and duplicate action options are rejected.

Top-level fields are exactly:

```json
{
  "schema": "el.joint-description.raw-physical.v1",
  "family_id": "R13",
  "source_id": "researcher-declared-source-identity",
  "exposure": "recorded-archive",
  "action_unit": "pA",
  "receiver_unit": "Hz",
  "units": []
}
```

This snippet is a structural illustration, not an executable empty cohort or
scientific evidence. Supply a nonempty complete selected roster. Required unit
strings are:

| Family | `action_unit` | `receiver_unit` | Additional top-level field |
| --- | --- | --- | --- |
| R13 | `pA` | `Hz` | None |
| R14 | `V` | `rad` | None |
| R15 | `A` | `V;A.h` | None |
| R16 | `Hz` | `W.m^-2` | `forcing_unit: "Pa.m^3.s^-1"` |
| R22 | `fraction` | `eV` | None |

Each unit has exactly `unit_id`, `split`, `preparation_time_s`, `preparation` and
`episodes`. R22 additionally requires `native_preparation` and
`mapping_assumptions`, described below. `split` is `calibration` or `evaluation`.
`preparation_time_s` must be strictly negative relative to the action at zero;
the preparer attests that all supplied preparation/history values precede this
cutoff. `preparation` contains exactly the named fields in the family table,
with finite numerical values in the indicated units. SOC lies in `(0,1)` and
absolute temperatures, resistances and positive density/power coordinates must
be positive.

Each episode has exactly these fields:

```json
{
  "action": 40.0,
  "status": "complete",
  "reason": "",
  "data": {
    "duration_s": 1.0,
    "spike_times_s": [0.12, 0.31, 0.74]
  }
}
```

These listed spike times illustrate encoding only. Replace them with actual
source measurements. `status` is `complete`, `unavailable` or `failed`.
Noncomplete episodes require a nonempty reason and `data: null`. An empty
episode list is valid: all selected options for that independent unit then
remain unsupported. Each action occurs at most once within a unit. If an
archive has repeated trials, first author a scientifically justified nested
reducer or a genuine independent-unit grouping; do not inflate the number of
independent units by relabeling samples.

The complete episode's `data` fields are closed per family:

| Family | Required `data` fields |
| --- | --- |
| R13 | `duration_s`, `spike_times_s` |
| R14 | `time_s`, `position_rad`, `drive_v` |
| R15 | `time_s`, `current_a`, `voltage_v`, `temperature_k`, `voltage_uncertainty_v`, `capacity_uncertainty_ah` |
| R16 | `time_s`, `gas_rate`, `receiver` |
| R22 | `time_s`, `core_temperature_ev` and either a logged `heating_fraction` or the measured pair `power_time_s`, `power_w` |

All clocks start at zero, increase strictly and cover the requested horizon.
Matching scalar arrays have one value per clock. A horizon between samples uses
declared linear endpoint interpolation; no extrapolation is allowed. R13 spikes
are nonnegative, strictly increasing and no later than acquisition duration;
an event exactly at `T` is excluded from the half-open receiver. R14's measured
drive must match its declared signed constant action. R15's measured constant
current must match its action, and uncertainties must be finite and nonnegative.
R22's logged `heating_fraction` must match the declared option.

For measured neutral-beam power, declare `recorded_power_tracking` in the
R22 recipe. Its `max_fraction_error` is the permitted absolute departure
from the selected fractional change relative to the unit's pre-action
`heating_power_w`. Use disjoint bands that preserve the sign of each
nonzero option. Set `max_power_gap_s` and `max_temperature_gap_s` for the
two measured clocks. Both must cover the full interval from zero to the
selected horizon, including the samples used for endpoint interpolation.
EL retains the maximum fractional departure. A power trace outside the band
leaves that option unsupported at that horizon. An invalid clock records a
failed receiver. The shorter horizon retains its own observation.
This comparison describes delivered power in the recorded discharge.

The FAIR-MAST Level 2 adapter reads selected source bytes on their original
clock. Use `Level2Array.from_metadata` with the expected units and named
dimensions, then call `read_interval(start, stop, fetch_chunk)` for the
half-open index interval. The caller supplies the original compressed chunks
and records their source identities. A profile slice retains every radial
channel at the selected times. The archived clock and the shot's source
indices locate each pre-action profile and temperature response.
[Level 2 reader](../../src/empirical_lawhood/adapters/physical/mast_archive/level2_array.py)
· [UKAEA channel catalogue](https://ukaea.github.io/fair-mast/level2-data.html)

R16 fits a DC term plus cosine and sine on the actual clock. The transfer uses
the cosine-minus-i-sine phasor convention and retains real and imaginary
components. At least two cycles and six samples are required. A maximum sample
gap at or above half the requested period, an unexcited input or a
rank-deficient/ill-conditioned fit is explicitly unevaluable. The implementation
does not substitute a nearby FFT frequency. Receiver residual RMS, input
amplitude and design condition number are retained as diagnostics.

Malformed raw receiver data produce failed rows for the affected
unit/action/horizon, preserving the census. Missing actions produce unsupported
rows. An invalid source schema or absent selected unit is an input prerequisite
failure, not a native experiment outcome.

## R22 observed-state mapping

`native_preparation` contains every field of the reusable
`NativeToraxPreparation` record except `preparation_id` and `assumption_ids`,
which the adapter supplies from the unit identity and the explicit
`mapping_assumptions` list. The required fields are:

```text
radial_coordinates
electron_temperature_ev
ion_temperature_ev
electron_density_m3
plasma_current_a
main_ion
impurity
zeff
major_radius_m
minor_radius_m
toroidal_field_t
elongation_lcfs
source_radial_location
source_width
electron_heat_fraction
absorbed_power_fraction
chi_i_m2_s
chi_e_m2_s
particle_diffusivity_m2_s
particle_convection_m_s
maximum_core_temperature_ev
```

The first four fields are equal-length arrays on a common normalized radial
grid with at least three points covering `[0,1]`. Temperature and density
profiles must be positive. Core electron temperature must equal the recorded
pre-action `core_temperature_ev`; core density must equal
`density_1e19_m3 × 10^19`. Remaining fields carry units in their names.
`main_ion` is `deuterium` or `tritium`; `impurity` is `argon`, `carbon` or `neon`.
The source-location and heat/absorption fractions lie in `[0,1]`.

`mapping_assumptions` is a nonempty, unique list of stable IDs identifying the
researcher's assumptions about geometry, ion temperature, transport, boundary
conditions, composition and heat-source representation. Document their values
and provenance with the input. Native electron/ion heat equations use the
existing direct-TORAX Gaussian heat-proxy adapter, fixed density/current and
declared constant transport. A sampled or assumed profile is not silently
upgraded to a physical measurement.

The physical and simulated core-temperature receivers have different source
provenance and remain separate columns. They are not additional independent
replicates of one physical intervention. A simulated option does not fill a
missing recorded physical option. Joint useful-control conclusions require
complete support under the authored receiver policy; transferring a simulator
law to the physical system requires separately justified mapping assumptions.

## Native environments and execution

The concrete `NativeJointDescriptionPort` is constructed by the typed native
runner, not by a pure calculation or static discovery. It enters each selected
unit/action once. Failures retain their reason and full requested receiver
census. It does not retry an uncertain or completed native action. Recovery and
effect custody belong to the shared execution lifecycle.

| Families | Native denominator | Device |
| --- | --- | --- |
| R17 | GymTORAX 1.1.1, TORAX 1.4.2, JAX/JAXLIB 0.10.2; `IterHybridEnv` | CPU or configured JAX GPU, float64 |
| R18–R19 | PyBaMM 26.6.2.0; Chen2020; lumped thermal model; safe CasADi solver | CPU |
| R22 | TORAX 1.4.2, JAX/JAXLIB 0.10.2; direct native TORAX | CPU or configured JAX GPU, float64 |

Select the existing [environment](../using/environments.md) for the workload.
Version mismatches, missing distributions and a backend different from the
declared device fail explicitly before model construction. There is no
synthetic engine fallback. CPU/GPU selection leaves the scientific family and
action/receiver menu unchanged; PyBaMM's CPU solver cannot be relabeled GPU.
Remote execution uses the same typed native operation through the repository's
remote worker route and the code-owned `JAX_TORAX_BACKEND`. Its explicit hosted
profile validates the locked CUDA12/JAX/TORAX dependency closure and requires
an authenticated offline worker bundle. See [CPU/GPU selection](cpu-and-gpu.md)
and the [JAX worker procedure](../using/accelerated-compute.md#jax-cuda12-torax-worker-profile).
R17 and R22 each require a matched CPU/GPU comparison for backend qualification.

R17 uses integer-second receiver horizons up to 120 s. Its internal timestep
must divide that one-second action clock. Each native step verifies the actual
clock, applied action and solver-error state; clipped/unknown delivery cannot
be credited to the requested action. Completed earlier horizons survive a later
episode failure. R18–R19 bound each continuation at 3600 s and 10,000 retained
output intervals. Native capacity is independently checked against the
integrated delivered current. R22 reuses the existing typed native time-grid
admission and trajectory validity checks.

## Verification and scientific results

`tests/test_joint_description_physical_native.py` contains independent numerical
oracles for spike counts, nonuniform-clock current integration, signed optical
response, exact sinusoidal transfer, uncertainty distances and reduced-model
defects. Other tests check closed schemas, no calibration/evaluation crossover,
complete negative censuses, feature independence from outcomes, no pre-forecast
engine/receiver contact and no retry on a failed action. Injected unit fixtures
are explicitly not native or physical scientific evidence.

The [programme record](../../programmes/shared-records/joint-description-results.md) reports the primary CPU results and identifies the missing physical cohorts and outstanding GPU comparisons. For a new run, select the locked environment and inputs for its recipe before preparing the recursive operations.
