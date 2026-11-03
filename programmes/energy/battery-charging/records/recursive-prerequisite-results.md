# Battery state supply and subsequent voltage results

SPDX-License-Identifier: CC-BY-4.0

This summary preserves the completed two-wave battery construction and voltage findings.
It keeps procedure assessment, new-instance supply and consumer limits separate.
Read the findings with the original two-preparation denominator and numerical scope.

## Battery: assessed procedure, new instance and further inquiry

The [battery protocol](../workflows/recursive-battery/battery-protocol.md)
uses known PyBaMM 26.6.2.0 SPMe/Chen2020 and exact-state restart machinery.
Wave A assesses continuation on two histories within one exposed SOC 0.60
preparation. Wave B imports that exact assessed contribution, acquires a new
SOC 0.70 checkpoint once, and assesses four changed future current words.
The pedagogical withholding of a known capability is explicit.

| Assessment or finding | Retained outcome |
|---|---|
| A full-state hold continuation, both histories | Satisfied; zero recorded voltage, capacity and temperature discrepancy against the reference |
| A SOC/capacity/temperature reconstruction | Inadequate; voltage defects 2.677503 mV early and 13.595554 mV late, with charge and temperature controls passing |
| B full-state continuation, four future words | All four satisfy the fidelity contract; zero recorded full/reference discrepancy |
| B equal-charge history contrast | +3.240629560057 mV coarse; +3.2390432826692 mV tighter |
| B current-proportionality defect | +16.5424535037204 mV coarse; +16.5388272730386 mV tighter |
| B maximum coarse/tighter voltage disagreement | 4.773805895 microvolts, below the frozen 100-microvolt bound |
| C1 / C2 / combined request | Satisfied / refused / refused |

The history contrast is `V_early1(600) - V_late1(600)` under equal delivered
charge and endpoint current. The proportionality defect is
`V_early3(410) - 3*V_early1(410) + 2*V_hold(410)`. Both numerical views exceed
their respective 1.2 and 1.6 mV floors. History dependence alone is not a
nonlinearity proof; these findings identify no unique electrochemical mechanism.

C1 permits the required internal state. C2 permits only observable channels and
refuses that procedure. The failed reconstruction and C2 refusal concern those
specific representations, rather than every possible observable-only supplier.
The tighter view assesses forward integration agreement on the same mesh and
checkpoint. Physical uncertainty, mesh convergence and population confidence
intervals remain unmeasured.

The two waves retain two exposed preparation specifications, three checkpoints,
18 traces and six restart assessments. Histories, future words, numerical views
and repeated development attempts remain nested. Earlier complete public battery
attempts retain 58 native operations and 196 phase calls; four early probes lack
a trustworthy aggregate phase census. Those exposure limits remain visible.


## Provenance and related findings

The [shared provenance record](../../../shared-records/recursive-prerequisite-provenance.md)
retains exact producing identities, execution counts, recovery and original custody.
The distinct [RC results](../../../foundations/measurement-and-response/records/recursive-prerequisite-results.md)
describe measurement, preparation and timely joined use.
