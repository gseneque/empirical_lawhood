# Convert paired activation free energies to conditional rates

SPDX-License-Identifier: CC-BY-4.0

This connection converts supplied WT/mutant activation free energies into rates
for the [paired kinetic workflow](guide.md).
It retains the physical clock, concentration convention and paired assumptions.
It supplies no molecular calculation or biological rate qualification.
The [physical supplier specification](physical-rate-supplier-v1.md) selects
the Gp WT/I95M calculations that must produce and assess these operands.

## Required evidence

[PairedActivationRateInput](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/transition_state_rates.py)
binds the exact paired case, assay context and temperature. It requires ordered
WT/mutant activation free energies in J/mol, transmission coefficients and
dimensionless prefactor multipliers. State definitions, barrier evidence,
prefactor and transmission models remain identified sources. The same dependence
group accompanies both outputs; the converter never resamples either arm.

An activation free energy includes the selected thermodynamic ensemble and
standard-state treatment. An electronic energy difference, a geometry, or a
force check does not supply that quantity. A missing free-energy assessment
remains an explicit requirement. Every result also retains physical-rate,
state-lumping and paired-prefactor/transmission applicability requirements.

Gas-addition inputs select their source concentration standard state and whether
the supplied barrier already includes bulk access. A local barrier must provide
its paired bulk partition factors. A bulk barrier refuses an additional partition
factor. Unimolecular transitions refuse concentration or gas-access corrections.
Oxygen addition, its reverse transition and oxygen-product progression require
an identified oxygenation model. That reference identifies the selected spin,
electronic or kinetic assumption; it does not establish its adequacy.

## Physical clock and units

For each arm, the selected Eyring model is

```text
k = kappa * p * (k_B * T / h) * exp(-DeltaG_dagger / (R * T))
R = k_B * N_A
```

Here `kappa` is the selected transmission coefficient and `p` is the selected
dimensionless prefactor multiplier. The converter uses the exact SI definitions
of `k_B`, `h` and `N_A`. Its physical clock is seconds, independent of simulator
step indices or the wall time spent computing the barrier. See the
[BIPM defining constants](https://www.bipm.org/en/measurement-units/si-defining-constants)
and the [IUPAC transition-state-theory definition](https://goldbook.iupac.org/terms/view/T06470).

For parameters `c` and `o`, divide this first-order expression by the supplied
standard concentration in micromolar. A 1 M standard state is therefore
`1000000 uM`; the resulting coefficient has units `uM^-1 s^-1`. Apply a local
bulk partition factor only when explicitly selected. The other six parameters
have units `s^-1`. The independent standard-state control changes the free-energy
reference and concentration together and requires the physical coefficient to
remain unchanged.

Reverse barriers belong to their actual reverse states and physical assumptions.
A positive conversion cannot establish that a reverse reaction is negligible.
An irreversible approximation must remain a separate declared kinetic scenario
with its own support. Overflow or underflow refuses conversion; a lost numerical
value never becomes a physical zero rate.

## Composition and independent arithmetic assessment

Use `calculate_transition_state_rate(selected, case, context, result_id=...)`
with the typed input and its actual case/context records. The returned
`PairedTransitionStateRate` retains the input identity, rate units, ordered pair,
dependence group and unresolved requirements. This supported Python composition
uses 60-digit Decimal arithmetic with a fixed rounding context. It performs no
native execution and grants no source or outcome access.

The separate
[assessor](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/transition_state_rate_assessment.py)
uses inverse logarithmic equations at 80-digit precision. It never invokes the
rate producer. It checks exact input/result schemas and revisions, pairing,
units, source joins and unresolved requirements. Its fixed logarithmic tolerance
is `1e-50`; comparison preserves the exact residual without ambient rounding.
A SATISFIED result establishes arithmetic agreement. Physical admission remains
UNEVALUABLE.

The rates can populate the existing four-state consumer only as part of an
explicit complete paired rate realization. Two endpoints cannot identify all
eight microscopic rates. Marginal intervals do not authorize independent draws,
and a finite set of joint realizations does not prove enclosure of a continuous
parameter region. Preserve missing rates and consequential oxygenation or reverse
assumptions through the [scientific specification](scientific-specification.md).

[Focused controls](../../../../../tests/test_rubisco_transition_state_rates.py) cover the
SI clock, concentration conversion, partition accounting, forward/reverse
consistency, paired assumptions, context stability, retained-record tampering,
exact revisions, underflow and the existing kinetic consumer. These use disclosed
algebra operands. They contain no Gp activation barriers or I95M rate evidence.

## Retain an unidentified WT waiting-time split

The endpoint-only composition
[bound_paired_endpoints](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/paired_endpoint_bounds.py)
accepts four supplied, jointly identified mutant/WT ratios: formation `q_a`,
postaddition processing `q_r`, gas discrimination `q_D = (c/o)_M / (c/o)_W`,
and branch commitment `q_chi = (chi_C/chi_O)_M / (chi_C/chi_O)_W`.
Every ratio needs its source. Neither oxygen discrimination nor commitment
defaults to one. This is an additional mathematical composition, without a
new molecular producer or registered experiment command.

For the stated four-state closure, let `w` be the fraction of WT turnover time
spent in effective reactive-state formation:

```text
w = (1/a_W) / (1/a_W + 1/r_C,W)
kcat_C,M / kcat_C,W = 1 / (w/q_a + (1-w)/q_r)
S_M / S_W = q_D * q_chi
```

An unidentified split uses the complete closed enclosure `0 <= w <= 1`.
The turnover-ratio bounds are exactly `min(q_a, q_r)` and `max(q_a, q_r)`.
They include limiting values; the endpoints do not assert zero waiting time
or an infinite physical rate. A narrower interval requires separate source
evidence. Monotonicity gives its exact extrema without a grid or a fitted WT
rate vector. This removes a need to identify the WT split when both effective
rate contrasts already support the same decision. Opposite effects can still
leave the turnover decision unresolved.

The result is conditional on one fixed **joint** realization of the four
ratios and the declared waiting interval. It is not an enclosure of arbitrary
uncertain rate marginals, a confidence interval or a biological forecast.
Preserve separate joint realizations and chemical/processing scenarios, along
with their shared evidence and any dependence of the waiting interval on them.
The composition supplies neither absolute rates nor the other assay constants.
WT anchoring still requires a compatible measurement and a separately stated
transfer assumption; it cannot validate this model.

The separate
[enclosure assessor](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/paired_endpoint_bounds_assessment.py)
checks exact extremal balance equations, specificity, case/context joins and
remaining requirements without invoking the producer. Its arithmetic finding
does not establish physical admission.
[Controls](../../../../../tests/test_rubisco_paired_endpoint_bounds.py) compare against
the complete reversible kinetic solver, preserve opposite waiting-rate effects,
and detect narrowed or altered retained bounds. These are disclosed algebra
operands, with no Gp rate observations.
