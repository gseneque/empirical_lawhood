# Battery state supply and subsequent voltage inquiry, revision 1

SPDX-License-Identifier: CC-BY-4.0

This protocol fixes a two-wave numerical development construction before native contact. It uses PyBaMM 26.6.2.0, its installed Chen2020 parameters, the isothermal single-particle model with electrolyte (SPMe), and CasADi 3.7.2. The existing exact-state rebuild machinery is known. Assessing its finite contract in Wave A and reusing it in Wave B is a pedagogical development construction, with no scientific-literature novelty, physical battery validation, population estimate or fresh qualification claim.

## Scientific questions and starting stock

Wave A asks whether binary-exact internal state and the source-input ledger supply a faithful numerical continuation, and whether SOC/capacity/temperature alone supply an adequate voltage continuation in the tested histories. Existing native restart code, the Chen2020 parameterization and charge conservation are available starting knowledge. The exercise explicitly withholds an assessed portable procedure contribution until this wave produces it; it does not present that pedagogical boundary as a newly discovered scientific gap.

Wave B asks what changed current words reveal about voltage history dependence and departure from current-proportional response on a new numerical history. It uses the Wave A procedure as a design/procedural contribution, performs a new checkpoint acquisition and new continuation effects, and assesses their instance supply before reporting the further product. Capacity integration is a conservation control, not the nonlinear scientific finding. A history effect in this nonlinear model does not identify a unique electrochemical mechanism or prove that history dependence itself is nonlinear.

## Frozen preparations, actions and clocks

All temperatures are 293.15 K. Positive current denotes discharge. Wave A has one preparation, initial SOC 0.60, with two nested numerical prefixes: early current is 1 A on [0,150) s and zero on [150,300) s; late current is zero on [0,150) s and 1 A on [150,300) s. Both prefixes deliver 150/3600 A·h. They have separate branch/history identities and are not simultaneous interventions on a physical cell.

At 300 s, retain the exact native state, state-layout and model identities, source parameters/options, original SOC/temperature, source-input ledger and checkpoint capacity. The future in Wave A is a zero-current hold through 600 s. Compare three routes: independently acquired same-object native continuation; rebuilt full-state plus source-input continuation; and equilibrium reconstruction from initial SOC minus checkpoint capacity divided by the installed nominal 5 A·h capacity, with the same temperature. Align the reduced reconstruction's capacity bookkeeping to the checkpoint value. Its voltage assessment must not succeed or fail merely because capacity was reset to zero.

Wave B has one different preparation, initial SOC 0.70, with the early prefix above. Its new checkpoint is acquired once as the shared supplier. Reference continuations may independently reexecute the declared prefix as nested numerical control effects; those effects are counted and never represented as recovery of the shared acquisition. Importing Wave A evidence does not reacquire it.

The four predeclared Wave B future words are:

| Word | Current from 300 to 420 s | 420 to 540 s | 540 to 600 s |
|---|---:|---:|---:|
| Hold | 0 A | 0 A | 0 A |
| Early 1 A | 1 A | 0 A | 0 A |
| Late 1 A | 0 A | 1 A | 0 A |
| Early 3 A | 3 A | 0 A | 0 A |

Output clocks are every 10 s and include every phase boundary. Wave A restart assessments use 310,320,…,600 s; 300 s remains recorded but is excluded from that error assessment because it is the source-to-future input boundary. Wave B also retains its complete continuation clocks and the 410 s receiver used below. Model time belongs to its own preparation/history; the two waves' actual execution ancestry must be chronological.

## Numerical contract and contribution

The coarse view has 20 points in each of x_n, x_s, x_p, r_n and r_p, CasADi-safe relative tolerance 10⁻⁵ and absolute tolerance 10⁻⁶. The tighter Wave B forward solve uses the same 20-point state layout and the same supplied checkpoint, with tolerances 10⁻⁷ and 10⁻⁸. It assesses forward integration agreement, not unmeasured physical uncertainty or mesh convergence. Use finite CasADi integrator step limits and preserve any termination or numerical failure.

Full restart fidelity requires complete final-time continuation, exact encoded-state round trip and maximum errors no greater than 10⁻⁶ V, 10⁻⁸ A·h and 10⁻⁸ K against the same-object route. A SOC-only voltage defect exceeding 0.001 V is inadequate under that declared criterion. Otherwise retain its actual adequate or nondiscriminating finding; do not force it to fail. Source/model/layout/input substitutions refuse before native contact.

Wave A's procedure contribution references the actual assessed native products, its hold-continuation scope, required internal-state/input channels, parameters and remaining obligations. It is non-promotable and grants no scientific authority. Wave B's changed future requires its own new-instance and continuation assessments; Wave A's hold evidence is not silently upgraded into qualification of those new words.

## Shared consumers and joined claims

Consumer C1 permits full-state numerical continuation in the declared simulator world. Admission authenticates the contribution, model/source/layout and declared checkpoint channels at 300 s. Actual continuation fidelity is assessed later; its result cannot revise admission.

Consumer C2 permits only the observable SOC/capacity/temperature channel. It refuses the same procedure because that procedure requires latent concentration fields outside C2's allowed inputs. C2 receives an explicit observable/metadata projection, not the forbidden internal state. An unavailable terminal-voltage-only reconstruction remains an unselected alternative with its unresolved premises visible.

The C1 path supplies the positive development construction when full restart fidelity and the complete later scientific assessment succeed. The independently assessed C1+C2 joint request retains the refusal/failure caused by C2's missing permitted supplier. These are separate claims. A null or negative voltage contrast can complete the later inquiry; it is not converted into a positive effect or an operational failure.

## Further scientific product and falsifiers

Retain the signed endpoint history contrast V_early1(600) − V_late1(600). These words have equal delivered charge and the same final zero current. Also retain the current-proportionality defect [V_early3(410) − V_hold(410)] − 3[V_early1(410) − V_hold(410)]. Report both quantities in V with their exact inputs and all finite controls.

Every Wave B word has same-object, full-restart and tighter-forward records. Full restart uses the fidelity bounds above. Maximum coarse/tighter voltage disagreement must not exceed 0.0001 V. A materially resolved contrast must exceed 0.001 V plus 0.0001 V times the sum of absolute contrast coefficients: 0.0012 V for the history contrast and 0.0016 V for proportionality. Require agreement of signs and the declared effect class across the views. Otherwise retain a bounded null, nondiscriminating or unevaluable result as appropriate. These are declared numerical criteria, not calibrated probabilistic intervals.

Check discharge capacity against the current integral independently and retain temperature constancy. These controls cannot substitute for the voltage result. Preserve missing outputs, early termination, invalid numerical arrays, failed restart, unsupported input channels and every assigned branch in the census. No threshold, word, state or admissibility rule changes after observing a result.

## Execution and preservation boundaries

Use registered checkpoint, continuation, projection, admission, assessment, contribution and voltage-analysis operations through the shared public workflow. No task runs the complete two-wave construction internally. Freeze the authored topology and producing implementation before effect entry.

Use one worker, at most 32 native operation instances and 96 declared native phase calls; each state has at most 4096 entries and each native product at most 4 MiB. The total packet allowance is 64 MiB. Declare an operational admission profile of 3600 s, distinct from model time, with no automatic repetition after uncertain contact. Retain the actual effect/phase/resource census and integrator ceilings before execution.

The development denominator is two exposed model preparations, one per wave. Prefixes, future words, reconstruction routes and solver views are nested records. They do not create fresh independent preparations or a sampled population. Retained reads and completed-run recovery perform no native acquisition. Export Wave A's exact contribution closure and source bindings for Wave B's clean-root import; the consumer must not need private producer paths or mutable in-memory objects.

The protocol and freeze manifest are retained before scientific execution. Subsequent source/operation bindings receive their own recorded identities. Original RC inputs, evidence and protocols, existing battery charts, and paper assets remain unchanged.

## Sources

The [existing battery guide](../battery-response-and-restart/guide.md) identifies the retained native contracts and their development limits. [PyBaMM's version-pinned parameter documentation](https://docs.pybamm.org/en/v26.6.2.0/source/api/parameters/parameter_sets.html#chen2020) identifies Chen2020 as the LG M50 parameterization. The installed parameter, SPMe and solver source hashes are recorded in the freeze manifest; this source identity does not qualify the numerical study as a physical battery result.
