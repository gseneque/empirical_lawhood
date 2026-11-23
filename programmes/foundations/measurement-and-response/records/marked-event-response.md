# What an early site mark changes about a later count

SPDX-License-Identifier: CC-BY-4.0

**The clock alone and the last site mark each discard consequential information.** In a four-site, two-particle monitored chain, an early event at a given site can change the expected late site-0 count differently on histories that look identical to either observer. The independent lower confidence bounds on their RMS losses were 0.03585 and 0.01448 count per active event. Both exceed the declared 0.01-count margin. The remaining three compressed histories gave inconclusive bounds. Complete history replay reproduced the conditional consequence at the primary nodes to within 4.0 × 10⁻¹⁵ count. [Original measurements, models and receipts](marked-event-response.json) · [Clock refinement and full replay](marked-event-response-diagnostics.json)

## The estimand and the evidence

The established HOLD Hamiltonian and occupation-projector monitoring ran on the six-dimensional fixed-number sector with both couplings and the baseline rate equal to one. The initial occupations were sites 0 and 1. At each early clock node in [1,2), the reference compares inserting a specified site event with continuing from the same pre-event state. The receiver is the site-0 count in [3,4). Every active site contributes in proportion to its instantaneous intensity. The total intensity is exactly two. Dividing by it expresses the squared loss in counts squared per active event. The complete physical prefix includes every event time and site since preparation.

| Information supplied at the clock node | Estimated ideal squared loss | Independent lower confidence endpoint | Achieved fitted upper confidence endpoint | Held-out activity absent from training | Decision at 0.0001 squared |
|---|---:|---:|---:|---:|---|
| Clock | 0.0031910 | 0.0012850 | 0.0032975 | 0% | Exceeds margin |
| Last site | 0.0014804 | 0.0002097 | 0.0015986 | 0% | Exceeds margin |
| Last site and binned age | 0.0010737 | 0.0000343 | 0.0012049 | 0.024% | Unresolved |
| Last two marks and binned gaps | 0.0003670 | 0.00000115 | 0.0006831 | 2.31% | Unresolved |
| Last four marks and binned gaps | 0.0000839 | 0.00000008 | 0.0016069 | 31.48% | Unresolved |
| Complete marked prefix | 0 by deterministic reconstruction | 0 | Maximum observed absolute discrepancy 4.0 × 10⁻¹⁵ | All 4,096 reconstructed | Exact for this model and receiver |

The independent lower bound pairs separate histories in the same observed cell. The upper bound uses the predictor fit on TRAIN and chosen on calibration. The endpoints allow for the five compressed observers. The empirical ideal uses separate weighted moments for each clock, site and cell. For four marks, up to 1,640 observed cells occurred at a single node. Sparse cells made the empirical fit look good while the frozen predictor generalized poorly. Even a small empirical within-cell variance can leave the accuracy of an affordable forecast unresolved. The 16- and 32-node reanalyses of the original histories retained both positive lower-bound decisions. The maximum replay discrepancy over all refinements was 1.39 × 10⁻¹⁴, including zero discrepancy on the 79 event-free prefixes. [All grid estimates and occupied support](marked-event-response-diagnostics.json)

## Response to a physical change of rate

Weighting the *signed* event consequences by physical activity predicted **−0.001080** count per unit change in early log rate, with a 95% interval of [−0.001832, −0.000328]. Independent piecewise density integration gave **−0.000630** at the finest perturbation. The difference was −0.000450 [−0.001202, 0.000301], inside the ±0.01 margin after adding the quadrature allowance. The direct derivatives at perturbations of 0.10, 0.05 and 0.025 were −0.000597, −0.000623 and −0.000630. The independent trajectory-score estimate was −0.01489 [−0.06666, 0.03688]. It provided a less precise check. The signed contributions largely cancel in the aggregate even though particular early marks carry material consequences.

The all-sites late-count receiver has constant conditional expectation two, so every event-insertion consequence is zero. Its largest measured departure from zero was 5.8 × 10⁻¹⁵. The conditional count agreed with a separate direct density ODE within 2.8 × 10⁻¹⁵ at the development check. Independently shot futures gave a mean sampled-minus-deterministic consequence of 0.00788 [−0.04658, 0.06234]. [Development checks and held-out derivative](marked-event-response.json)

## Custody and cost

The original run `recursive.19da237db13825752696cdb7` completed 144 recursive operations. Every one of 256 development, 1,024 training, 512 calibration and 4,096 evaluation histories was evaluable. The evaluation assignment spans 552613022 through 552617117 inclusive. Every evaluation batch has a frozen-model parent, native prefix, released observation and an issued prediction preceding its reference. Development, evaluation-prefix and evaluation-future work sampled 33,850, 16,199 and 16,248 physical events. The workers recorded 134.27 CPU seconds across the operations and 25.58 MiB of binary companions. The largest recorded worker high-water mark was 417.24 MiB. These costs include joint production of all candidates and checks. The original producing checkout was clean at `967781c2d`. The retained authority is source-bound numerical development with disjoint evaluation. [Scientific definition and reproduction](../workflows/marked-event-response/guide.md) · [Original identities and per-stage costs](marked-event-response.json)
