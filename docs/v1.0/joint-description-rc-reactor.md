# RC and reactor joint-description experiments

R01, R02, R20 and R21 are new experiments authored around a finite preparation,
intervention, receiver and horizon family. They do not load historical results,
replay old qualifications, or claim that the original paper's findings have
been reproduced. Their common question is whether a less joint information
description remains useful once prediction error, interface information,
retained history, action outcomes and authored costs are counted together.

The code-owned defaults are supplied by
[`circuits.joint_description.presets`](../../src/empirical_lawhood/domains/circuits/joint_description.py)
and
[`reactor.joint_description.presets`](../../src/empirical_lawhood/domains/reactor/joint_description.py).
Use the public [investigation authoring workflow](define-investigation.md) to
freeze a specification, select its operational environment, and execute its
recursive graph. Editing a preparation, observation history, receiver, horizon,
description or economic coefficient creates a different scientific
specification. Changing hardware alone does not authorize changing these
operands.

RC authoring validates the physical parameters against the implemented
forecast features. Changing the cell count, partition or history requires
matching retained-channel counts and a construction-work budget at least as
large as the declared reference estimate for that implementation. An
unimplemented parameter or stale cheaper budget is refused before execution;
the authoring service does not silently revise the scientific specification.

## Start with the research question

| Family | Research question | Independent unit | Default physical operands |
| --- | --- | --- | --- |
| R01 | When does mean-voltage compression lose control-relevant contrast, while independently composable branch laws remain sufficient? | One pair of preparations sharing a present mean | Two uncoupled RC branches, time constants 1 and 4 s; common source levels 0, 0.5 and 1 V; horizons 0.25, 1 and 3 s |
| R02 | Which present, interface or history descriptions of a coupled circuit meet receiver and control requirements? | One independently drawn component set and preparation | Eight cells; capacitances and interior resistances independently drawn between 0.65 and 1.35 F or ohm; two local receiver partitions; the same source and horizon menu as R01 |
| R20 | Which observed reactor description supports a useful response atlas and bounded action choice? | One newly assigned physical scenario and native noise seed | Common preparation to 3600 s; constant preparation feed; candidate feed rates 0, 0.016 and 0.032 kg/s; horizons 30, 120 and 300 s |
| R21 | On paired fresh reactor roots, does interface information or memory preserve policy utility after a changing preparation history? | One newly assigned scenario, shared across candidate policy actions | Common preparation to 9000 s; alternating preparation feed; the same action menu; horizons 120, 300 and 600 s |

Actions, horizons, numerical views, receivers and description alternatives are
nested observations. They do not multiply the number of independent units.
Calibration and evaluation units are disjoint. The seed, unit roster and source
identity determine every new simulator preparation; original result archives
are not inputs.

## R01: hidden contrast and an explicit factorization control

The two branch voltages obey

\[
\dot v_i=(u-v_i)/\tau_i, \qquad
y=(v_1+v_2)/2.
\]

For each pair, the decision-time states are `(0.5+d, 0.5-d)` and
`(0.5-d, 0.5+d)` V, with a newly drawn contrast `d` between 0.05 and 0.45 V.
The earliest preparations are specified so that unforced forward evolution
produces those decision-time states. This establishes a real pre-decision
history; it does not infer that history from a future response.

The joint description observes both present voltages. The reduced description
observes their mean and sets unresolved contrast to the minimum-norm estimate.
The interface description additionally measures the branch-voltage contrast.
The memory description keeps the present mean and three earlier means at
0.1 s spacing. These forecasts use the same known physical branch parameters.

An independent-branches control evaluates the two scalar RC laws separately
and averages their responses. It requires no dynamic cross-branch
communication. Its success is allowed: the experiment must not manufacture
irreducibility by giving every decomposed model an incorrect law.

The two pair members are named receiver outcomes of one independent pair.
The analytical global minimax lower bound is an evaluator diagnostic from the
extracted Decimal RC calculation. It refers to the exact identical-input
premise and a maximum over nonnegative time. It is not a sampled confidence
bound and is not automatically the error at every configured horizon.

## R02: coupled physics and observation history

The circuit is constructed by the existing modified-nodal-analysis component,
`rc_ladder.mna.build_operator`, in SI units. Initial cell voltages lie between
0 and 1 V. The default preparation coasts for five 0.1 s intervals before
the decision; all information arms see the same physical preparation age.

| Description | Retained present information | Additional channel |
| --- | --- | --- |
| Joint | All eight cell voltages | None |
| Partitioned | Two local capacitance-weighted means | None |
| Interface | Those two local means | Voltages on the two sides of the partition boundary |
| Memory | Those two local means | Five previous observations of both means |

History reconstruction solves the forward observability problem at the
earliest preparation and propagates the estimate to the decision. It does not
run noisy observations backwards in time. The retained rank records whether
the declared history identifies the physical state numerically. A low-rank
history is still evaluated; it is not silently dropped from the denominator.

The receivers are the complete circuit's capacitance-weighted mean voltage and
its terminal-cell voltage. The default observations are noiseless simulator
measurements. These experiments establish neither laboratory sensor adequacy
nor robustness to noise that was not declared.

All four information arms still use the full known physical propagation
operator. Their costs describe retained information, interface measurements and
history, not a demonstrated reduction in numerical state-space dimension or
simulation runtime. Operator compression is a separate experiment requiring
its own approximation and computation accounting.

## R20 and R21: causal preparation, then paired native action panels

The reactor adapter loads the installed pinned upstream plant and parameter
bytes. Each new scenario is sampled within the public uncertainty envelope.
The hidden kinetic multipliers, cooling faults and plant parameters never
enter predictor features. Only delayed/noisy callback temperatures, current
dosed mass, observed delivered actuator settings and pre-decision history are
available to a description.

The recursive stages enforce the following separation:

1. Calibration action panels supply response-law fitting and root-held-out
   model selection.
2. The model is frozen before evaluation preparations begin.
3. A native evaluation preparation stops at its decision callback. Its worker
   closes and joins without reading the hidden grid or delivering any candidate
   response action. The complete predictor table is persisted.
4. The response-law forecast chooses a permitted action from those predictors.
   If every candidate violates a predicted guard or lacks required predictions,
   the result is no entry.
5. Native action branches replay the same deterministic preparation and noise
   seed. Their predictor bytes must match the frozen table. Only after each
   branch closes does the evaluator read the true native grid.
6. Assessment scores the frozen choices and all scheduled outcomes, preserving
   failed native contact, no entry, adverse outcomes and incomplete action
   menus.

The default joint reactor description means the joint **observed**
temperature/dose/actuator context. It is not privileged access to complete
chemical state. The partitioned description uses reactor temperature alone,
with the prospective action and horizon. The interface arm adds jacket and
delivered-actuator observations; the memory arm instead retains past reactor
temperature observations. R20 retains five past samples; R21 retains eleven.

The preparation feed is 0.012 kg/s after the native dosing window opens. R21
alternates between half and one-and-a-half times that rate every 300 s.
The requested jacket temperature is 316 K. Native actuator limits, slew,
measurement delay, noise and the pinned integration protocol remain active.

Receiver meanings are exact:

| Receiver | Definition | Units | Default scoring scale |
| --- | --- | --- | --- |
| Peak reactor temperature | Maximum true temperature on the complete inclusive native decision-to-horizon grid | K | 20 K |
| Conversion | Terminal conversion of reactant B | Dimensionless | 1 |
| Delivered mass | Terminal dosed mass minus mass at the decision | kg | 10 kg |

The thermal upper guard is 356.2 K. The authored target temperature is 340 K;
conversion is targeted at one, while delivered mass contributes an explicitly
weighted resource penalty. These targets and prices are scientific/economic
assumptions to review, not facts inferred from the simulator.

This is a held-out simulator action-panel control audit. Choice is frozen
before response acquisition, and alternative actions share physical roots.
It does not establish a certified controller, a physical deployment result,
or a statistical safety guarantee from point prediction alone.

## Interpreting economics and uncertainty

State dimensions, interface scalars and memory scalar-samples are separate
quantities. `memory_dimension` is the number of coordinates **per past sample**;
the retained history count is `memory_dimension * memory_samples`. These are
numerical information counts, not Shannon bits. The authored economic
coefficients convert them to the declared accounting unit.

Each description declares `forecast_work_units`, `forecast_work_unit` and
`forecast_work_basis`. The common computation cost includes that construction
estimate plus evaluation of the final predictor features. A precomputed
mechanistic forecast is therefore not made artificially cheap by appearing as
a single final feature. RC estimates include dense propagation, reconstruction
and history operators; the independent scalar-branches control has its own
smaller construction estimate. Reactor estimates include only visible-feature
construction, with native acquisition accounted for separately. These are
authored operation proxies with stated formulas, not certified counts or
empirical timing measurements. Revisit them if the implementation or intended
reuse changes.

RC producer work additionally records a dense state-multiply proxy. Reactor
acquisition work counts native integration steps, allocated once over nested
receiver/horizon rows; its separate preparation-only stage incurs additional
recorded prefix work. Native receipts own measured runtime and resource use.
Training and common acquisition are not silently attributed to one information
arm, and no cross-substrate runtime comparison follows from these proxies.

Root-held-out calibration ranking includes forecast error, observed utility of
the action selected from held-out predictors, and description cost. Evaluation
retains all-use and support-conditional results. An incomplete alternative
action panel cannot yield an optimistic oracle regret: it receives the authored
missing-evidence penalty. Realized safety failures remain failures even when
predictions were admissible.

The reported uncertainty is over independent roots. A finite standard error
does not establish simultaneous coverage or guarantee the safety of a future
action. A useful candidate is useful only under the exact declared preparation,
action, receiver, horizon, accuracy and price assumptions. A finite-menu winner
does not prove a universal smallest joint description. Review the Pareto menu
and vary the authored economic assumptions before interpreting dependence as
having moved into interfaces, memory or error.

## Execution and extension boundaries

These four defaults use local CPU numerical implementations. Remote execution
can supply CPU workers; selecting a GPU does not turn the pinned reactor or
closed-form RC calculation into a GPU implementation. Other substrate
families may require their own CPU/GPU environment selection.

Focused numerical controls cover the independent scalar RC solution,
observability, Kirchhoff charge balance, reactor receiver units and the
pre-decision truth barrier. Fake native ports occur only in software tests.
Production reactor acquisition never falls back to a fake simulator.
The [programme results](../../programmes/shared-records/joint-description-results.md) give the original RC and reactor assessments. The [release procedure](../release/release-artifacts.md) defines the software checks.

To add an information channel, implement its pre-decision meaning in the domain
module, declare its feature roster and actual retention/interface costs, and
add a focused independent mathematical or protocol control. Native observation
and delivery effects belong in the adapter. Fitting, safe action choice and
finite-menu assessment remain reusable methods; record meaning remains in
science; graph compilation and worker scheduling remain in execution.
