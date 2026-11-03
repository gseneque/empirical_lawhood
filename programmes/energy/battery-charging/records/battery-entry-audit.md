# Bounded battery entry audit

SPDX-License-Identifier: CC-BY-4.0

The 11 October 2026 D0/D1 audit stops at an incomplete consequential charging contract.
The inspected sources support lumped electrothermal simulation and history-dependent prediction.
They establish no exact unresolved charging-service inadequacy, selected supplier or later decision.
This is an entry stop, not a result that every thermal, model, uncertainty or preparation inquiry fails.
No native contacts, new scientific units, environment synchronization or setup repairs occurred.

The [machine-readable audit](battery-entry-audit.json) binds 41 source/document members by SHA-256,
records precise gate outcomes and preserves missing operands.
It is an audit record, not a frozen scientific protocol or qualification receipt.
The target is `recchain` at `9a4c29cb017cae6338dcf7c422f202062bc2a8cd`.
The donor checkout is `codex/safest-honest-metatheory-route-v1` at
`70ad6708799f0e8070526ef15c1da4870e080238`.
Pre-existing untracked plans/handoff and donor changes remain intact.
Their inspected file hashes matter; HEAD alone does not identify those inputs.

## Supported source and receiver meanings

The installed metadata identifies PyBaMM `26.6.2.0`, CasADi `3.7.2`,
PyBaMM solvers `0.8.2` and a CPython `3.11.14` environment.
No native import/build was used to inspect these facts.
The [electrothermal owner](../../../../src/empirical_lawhood/adapters/simulators/pybamm_electrothermal_hierarchy.py)
retains SPMe/DFN × isothermal/lumped × CasADi/IDAKLU denominators with Chen2020 and pouch geometry.
The [public input owner](../../../../src/empirical_lawhood/adapters/simulators/pybamm_development_input.py)
permits only SPMe/isothermal/CasADi; the
[recursive source contract](../../../../src/empirical_lawhood/adapters/methods/battery_recursive_construction/contracts.py)
also fixes isothermal SPMe. Neither shipped input establishes thermal controller science.

Installed `Chen2020.py` has SHA-256
`7c360a546a76492585e147231caee2f8f4fe29222b893cb12091dc4d158f62f0`,
matching the existing recursive contract's parameter-source hash.
It supplies total heat transfer `10 W m⁻² K⁻¹`, cooling area `0.00531 m²`,
cell volume `2.42e-5 m³`, nominal capacity `5 A·h` and native voltage events at `2.5/4.2 V`.
The default effective heat capacity uses layer-thickness-weighted electrode,
separator and current-collector density × specific heat.
The optional lumped heat-capacity override is disabled.
The existing thermal-action menu includes ambient `+0.5 K` words;
historical preparation strata span initial `291.15–297.15 K` and SOC `0.25–0.80`.
These are simulated preparation choices, not a measured manufacturing or thermal-contact distribution.

The source's default `surface temperature = ambient` is consequential:
`Surface temperature [K]` is the ambient boundary, not independent measured cell-surface telemetry.
The retained lumped model has one cell-temperature state broadcast through the cell.
A correctly declared modeled volume-mean thermometer port remains possible for a limited simulated inquiry.
A distinct hidden-core versus measured-cell-surface explanation is unsupported by this denominator.
That rejection does not reject model/qualification/preparation distinctions.
The optional two-temperature surface model requires `Casing heat capacity [J.K-1]`
and `Environment thermal resistance [K.W-1]`, absent from inspected Chen2020 and ORegan2022 sets.
The x-full tier remains excluded for its missing current-collector surface heat-transfer operand.
No invented parameters, extra sensor or model tier was introduced.

## Retained findings and their decision limits

| Evidence | Retained result | Charging consequence established here |
|---|---|---|
| V8B, 24 preparations, eight denominators, 3,840 complete receipts | Adjusted order equivalent in 23/24 coordinate-denominator rows; coarse DFN/lumped exception `0.0159889 K` did not recur in refined view. All same-end repetition rows equivalent. Exact restart conditional; reduced chart inadequate. | No frozen delivered-charge/deadline/risk decision; P4/P5 not entered. |
| V8C, six evaluation preparations, 240 continuations | 240/240 lossless R3 target-direct continuations. | Reconstruction resolution only. |
| V8D, 12 preparations, 480 supported complete predictions | 479/480 adequate; one SPMe/lumped/coarse thermal defect `0.005929472639763844 K` at 420 s; voltage error `0.00015881707199438821 V`. | No useful charging decision or safety/service boundary established. |
| V8D natural order pairs, 96 nested rows | Close/diverged 96/96; future differences up to `0.5 K` and `0.05437 V`. Retained history cannot be dropped from this chart. | Prediction relevance, not exact-coordinate equivalence or demonstrated action-choice reversal. |
| Public recursive A/B, two exposed preparations | Exact-state procedure supplied to C1; observable-only C2 refused; voltage history and proportionality defects retained. | Known isothermal development construction, not universal observable-only impossibility or thermal charging service. |

The V8D thermal defect localized to transient relaxation, falling to approximately
`3.51e-5 K` at the horizon. Base-preparation dependence or nonlinear relaxation
is an interpretation, not an identified mechanism.
Its small error cannot be promoted into a consequential charging gap by selecting a new threshold around it.
The larger cross-history voltage difference also needs actual absolute receiver values,
a justified service envelope and a choice map before it establishes a charging consequence.
SPMe versus DFN and coarse versus refined views remain separate model/numerical contrasts;
the numerical views change several operands and are not independent experimental units.

The controlling donor reports are
`docs/results/pybamm-electrothermal-hierarchy-successor-v8b-closeout-v1.md`,
`pybamm-exact-restart-reconstruction-qualification-successor-v8c-closeout-v1.md` and
`pybamm-reduced-coordinate-sufficiency-successor-v8d-closeout-v1.md`.
The continuing donor supplier proposal remains draft, unfrozen and unexecuted.
All three named `/media/chevre/SEMIOS/icf-yolo/runs/` roots are present.
Directory presence does not authenticate their payload census, authority, digests or replay completeness;
this audit did not reauthenticate those scientific packages.

## Controller seam and open entry gates

RA5-C should use the existing
[author](../../../../src/empirical_lawhood/adapters/control/controller_authoring.py),
[compiler](../../../../src/empirical_lawhood/runtime/controller_compiler.py) and
[runtime](../../../../src/empirical_lawhood/runtime/controller_runtime.py).
`DeliveryControllerAuthor.author` retains finite admission/reachability,
ACT/HOLD synthesis, instance binding and exact implementation identities.
`ControllerCompiler.compile` returns controller, HOLD-only or NONATTEMPT dispositions.
`ControllerRuntime.tick` checks observer identity, live admission, clocks and deadlines.
The runtime is a frozen lookup with live invalidation; adaptive whole-inquiry construction
must occur through the appropriate inquiry/domain owners.

ACT and independently supported measured HOLD both require real delivery observations.
`NativeDeliveryPort.deliver` returns requested/accepted/applied/realized occurrences;
missing, reordered, wrong-clock/value or explicitly failed delivery requires recovery or termination.
NONATTEMPT invokes no native delivery and records `NOT_ATTEMPTED`.
An inquiry HOLD is not measured native HOLD, and a requested current is not successful actuation.
No selected battery observer/live-gate/delivery composition or actual charging finite
law/admission/reachability operands was found.
Open-campaign metadata naming a current controller does not fill that implementation gap.
ACT/HOLD/NONATTEMPT and stale/wrong delivery acceptance remain unperformed for this route.

The source permits a model-inadequacy versus history-local qualification/preparation question,
but no exact consequential pair is presently frozen.
D0 lacks the independently justified charge/deadline and voltage/temperature risk contract,
terminal-to-choice map, finite supplier menu, distinct later use, one reuse test,
competent adaptive conventional inquiry, meaningful alternative and attribution check.
D1 lacks a selected preparation contrast, corrected observable meaning and applicable
controller/custody/runtime assessment. Independent-unit roster, exposure census,
numerical/risk tolerances and scientific/native allowances also remain open.
Neither existing fresh historical units nor the audit's resource cap qualifies new work.

The smallest eligible next oracle would authenticate already retained signed-current arrays
and test absolute voltage, correctly named modeled temperature and realized charge against
an existing independently justified charging-service contract.
It must retain full initial/ambient histories, all nested views, failures and common robust choices.
That contract is absent from the inspected evidence, so this oracle is not entry-ready.
No new data acquisition or manufactured threshold is warranted.
Close this bounded attempt with the missing-contract finding; continued science requires those
concrete source/value gates, not another family, historical rerun or extra repair sequence.

## Cost and verification

The coordinator froze a follow-up audit cap of 300 CPU seconds, 600 wall seconds,
1 GiB memory, 5 MiB output, zero native contacts and zero setup repairs.
Earlier inspection expense was not reset by that allocation.
Actual CPU, aggregate wall, peak memory and researcher/agent expense were not metered;
unknown costs are recorded as unknown. Historical science costs remain in their original reports.
The JSON is approximately 27 KiB; both durable artifacts fit the output cap.
Standard-library checks verified JSON syntax and source SHA-256 entries.
No software conformance test, scientific comparison, model build, native execution or literature
acquisition was performed. Documentation integration and maintained-document checks belong to the coordinator.
