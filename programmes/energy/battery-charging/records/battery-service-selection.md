# Battery charging-service selection proposal

SPDX-License-Identifier: CC-BY-4.0

Select a **15-minute standard-charge-equivalent top-up** on the exact Chen2020 LG M50
surrogate: from initial SOC `0.30`, deliver at least `0.36375 A·h` by `900 s`,
with correctly named modeled temperature and voltage constraints.
Compare initial/ambient preparations of `23 °C` and `27 °C` in one parameter family.
These inputs are selected before native model outputs.
The [exact selection record](battery-service-selection.json) binds operands, source identities,
limits, comparisons, proposed resource allowance and remaining entry gates.
This supersedes the previous audit's missing-selection disposition; it supplies no native result.

The deadline is an explicit researcher service choice, using the existing bounded 900-second
horizon. The charge target is exactly `1.455 × 900 / 3600`, equivalent to 7.275% of the modeled
5 A·h capacity. It is a useful partial charge, not a full-charge promise or an OEM deadline.
If competent ordinary control meets it under both preparations, close the question as
solved or non-discriminating. Do not tighten the target or add conditions to create a gap.

## Exact cell and source envelope

The manufacturer-authored historical M50 specification describes standard CC/CV charging
at `1.455 A`, voltage regulation at `4.2 V`, and termination at `50 mA`.
Its current tiers are `1.455 A` at `0–25 °C` and `3.395 A` at `25–50 °C`;
handling instructions restrict charging to `0–45 °C`. Select that intersection and the lower
current at the ambiguous `25 °C` boundary. The standard test is `25 ± 2 °C`, and shipping
SOC is nominally 30%. The source is a tentative 23 August 2016 LG Chem document on a
third-party mirror, not current OEM approval. It supplies no numeric deadline.
See [M50 specification](https://www.lithiumelements.com/wp-content/uploads/2023/07/m50.pdf),
pages 4, 6, 10 and 11.

Use absolute currents; the document's 0.3C convention implies 4.85 A·h, whereas installed
Chen2020 specifies nominal 5 A·h. Do not convert the selected current using a substituted
capacity. M50LT and other named cell variants are not aliases.
The independently read PDF is 576,273 bytes with SHA-256
`a8d895143a55e0beae273f2c94eb4f3038857f19cc190ea2048f825e77a76f6a`;
its bytes were read in memory and not retained as a scientific payload.

The [Chen validation-data record](https://zenodo.org/records/4032561) identifies three LG M50
cells with CC/CV charge, current/voltage and cell-surface/chamber temperature records.
Its physical surface measurement is distinct from a simulator's latent mean temperature.
CSV values were not acquired or used for selection; a requested file returned HTTP 429.
The publisher DOI fetch was denied. Exact listed member MD5s remain in the JSON for later
authenticated acquisition if needed; this selection opens no new data-acquisition campaign.

## Geometry, receiver and finite actions

Select PyBaMM `26.6.2.0`, Chen2020, SPMe, `thermal=lumped`, `cell geometry=arbitrary`,
zero-dimensional current collectors, default ambient surface model and no contact resistance.
Keep all installed source parameters except explicit initial temperature, ambient input and
current input. Initialize the two numerical preparations at SOC 0.30, with temperatures and
constant ambient boundaries `296.15 K` and `300.15 K` respectively.

This geometry choice matters. The historical battery denominator requires `pouch`; that option
computes cooling area and volume from single-layer unrolled electrode dimensions.
It does **not** use Chen2020's actual-cell cooling area `0.00531 m²` and volume `2.42e-5 m³`.
The corresponding historical values are `0.2060606320 m²` and `2.062216e-5 m³`.
Its area/volume ratio is approximately 45.54 times the actual-cell ratio.
This is a source/model difference, not evidence of a charging failure.
The [official pinned thermal documentation](https://docs.pybamm.org/en/v26.6.2.0/source/examples/notebooks/models/thermal-models.html)
and installed `parameters/geometric_parameters.py` independently describe this distinction.
Original V8B/V8C/V8D findings retain their pouch scope; they do not qualify the new denominator.
The earlier audit's parameter list remains authentic, but those A/V fields were not active in its
historical pouch simulations. All 41 prior source digests remain unchanged in their original record.

Ordinary policies receive the same modeled voltage, current and **volume-mean cell temperature**
history, nominal model/parameters, preparation metadata and clocks. Native
`Surface temperature [K]` means the ambient boundary and is not used as cell-surface telemetry.
No hidden-core ambiguity, physical thermometer adequacy or physical safety claim is selected.
The evaluator may inspect additional native state; deployable selectors may not.

The selected charging word requests `-1.455 A` on `[0,900)`; positive current discharges.
It uses the existing interval boundaries `0,150,300,450,600,900 s`, with the same current
in every interval and zero ambient delta. The receiver at 900 s measures the preceding charge;
it does not authenticate an additional zero-current delivery.
The finite menu also identifies a zero-current native HOLD, which supplies zero charge and
fails the useful-delivery requirement. No HOLD native contact is allocated in this premise proposal.
Its existence as a word is not measured native-HOLD qualification.

Assess realized net charge by the independent current integral and checkpoint-relative capacity.
Require modeled voltage within `2.5–4.2 V`, modeled volume-mean temperature within
`273.15–318.15 K`, and current within the conservative source envelope throughout the service.
The positive voltage tolerance in the OEM specification is not extra control headroom.
Require zero certified deterministic violations, retaining every termination, refusal and
unevaluable outcome. There is no population risk-confidence claim.

## Comparator and decision rule

The first common policy is ordinary manufacturer-standard CC/CV control with live voltage,
temperature and current protections. If the CC phase reaches 4.2 V early, a competent comparator
can continue in CV to the 50 mA termination criterion; an early-stopping CC implementation alone
does not establish conventional failure. PyBaMM supplies Experiment/voltage-control interfaces
for that source-native operation, although the selected EL public route still lacks its binding.

An opened inquiry uses temperature-aware direct-model CC/CV with the same observations,
current tiers, model-change and qualification opportunities. Correcting the known geometry is
initial knowledge available to every arm; it is not an EL-exclusive supplier discovery.
The ordinary no-supplier procedure can also supply the meaningful direct-control alternative,
provided its separate total-cost and attribution estimands remain assessable.

The candidate distinction is a consequential model/qualification inadequacy versus no service
inadequacy after the known source correction. Its practical consequence is still unmeasured.
If both preparations pass under a competent common policy, no additional supplier is needed
for this chosen service: retain the solved/non-discriminating closeout.
If a service failure survives competent direct control, freeze its live explanation pair and the
minimum independently assessed model, preparation or qualification supplier. Preserve failures
without treating numerical issues or an omitted CV tail as scientific evidence of such a gap.
No extra supplier/reuse sequence is commissioned by this proposal.

## Native entry is pending a narrow typed route

The current command is `campaign battery-native-check` with schema
`empirical-lawhood/simulators/py-ba-mm-development-input`, version `1.0.0`.
Its [input owner](../../../../src/empirical_lawhood/adapters/simulators/pybamm_development_input.py)
allows only SPMe/isothermal/CasADi and excludes the 300.15 K preparation.
The [recursive source contract](../../../../src/empirical_lawhood/adapters/methods/battery_recursive_construction/contracts.py)
fixes isothermal 293.15 K and its old finite words.
The retained [electrothermal factory](../../../../src/empirical_lawhood/adapters/simulators/pybamm_electrothermal_hierarchy.py)
supports lumped SPMe/DFN, but its strict denominator and `_source_options` require pouch geometry.
There is **no current strict public EL input/factory combination supporting this exact selection**.
Official PyBaMM support does not make an ad hoc validation-bypassing script an accepted EL route.

The coordinator can freeze this pre-output selection and add only a separately identified bounded
thermal-service input/model binding through the existing battery adapter/provider owners.
Keep historical fixed contracts intact. Bind arbitrary geometry, exact preparation/current words,
realized receivers and independent service assessment; retain existing source, authority, custody
and resource guards. This is a narrow interface prerequisite, not a scientific stopping result.
RA5-C remains required for an opened controlled route through the existing author/compiler/runtime
with ACT, independently supported native HOLD, NONATTEMPT and stale/wrong delivery checks.

Proposed separate native allowance: one worker, one attempt, at most 300 CPU seconds,
600 wall seconds, 1 GiB memory, 64 MiB outputs, zero setup repairs and at most three solves.
These are the two primary 23/27 °C standard-charge preparations and, if needed, one nested
tighter 23 °C numerical view. They supply zero physical units and one simulated parameter family;
the two preparations and all clocks/refinements are nested.
Use CasADi-safe with 20 points per spatial coordinate, primary `rtol=1e-5/atol=1e-6`
and 10 s outputs; the optional tighter same-mesh view uses `1e-7/1e-8` and 1 s outputs.
That comparison assesses integration agreement, not mesh convergence or physical uncertainty.
Do not borrow V8D's 5 mK materiality. Whole-time envelope assessment needs supported events
or justified bounds; sampled extrema alone do not certify it.
Do not launch until resource/source, exact typed-route, authority/custody and output-path gates pass.

This follow-up performed zero native contacts, synchronization or setup repairs.
Only these two selection reports were added. Inspection CPU, aggregate wall, memory and
researcher expense were not metered and remain unknown; historical costs were not reset.
The selection is concrete and pending coordinator freeze, not entry acceptance or evidence
that the common policy succeeds. No comparative advantage is claimed.
