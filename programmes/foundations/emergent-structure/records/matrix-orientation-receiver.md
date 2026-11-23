# Does the discarded orientation matter to the signed pulse receiver?

SPDX-License-Identifier: CC-BY-4.0

**At tick 64, discarding the orientation cost 0.00327 pulse-displacement units RMS, below the 0.01 practical margin.** The paired, grid-widened interval was [0.00228, 0.00424]. The two physical lifts did have different conditional responses. For this odd laboratory receiver, at this horizon, returning zero on both lifts met the required accuracy. The low-capacity forecast that also received the physical orientation bit had higher error. All 24 assigned evaluation families contributed. [Original measurements, root IDs, predictions and receipts](matrix-orientation-receiver.json)

## Symmetry, intervention and controls

The scalar-driven, six-matrix preparation has two equally weighted global orientations. Conjugating every position, momentum and innovation by the same unitary maps one lift into the other. The canonical observation folds the entire native prefix once. For a forward and physically reversed source law sharing this symmetry, the forward/reverse likelihood ratio is constant on each orbit. Its magnitude on the matched driven population remains unresolved. The earlier 128-family matrix-cycle experiment supplied a negative measured lower confidence bound on path KL. The researcher selected a receiver-only pilot. [Earlier cycle result](matrix-path-thermodynamics.md) · [Pulse definition and reproduction](../workflows/matrix-orientation-response/guide.md)

At the cutoff, a finite eight-tick rectangular pulse acted along an even direction of the first Y matrix. Every root supplied PLUS, HOLD and MINUS on two physical lifts, four shared future tapes and both time grids. The odd receiver changes sign across lifts while a co-rotated apparatus agrees. The twin-prefix, co-rotated and even-port maximum discrepancies were all zero. The even port's mean signed H64 response was 0.93403 in direct inertial-displacement units. On development, the zero-amplitude contrast was zero and the largest full-minus-rescaled-half-pulse discrepancy was 1.39 × 10⁻¹² in native coordinates. No evaluation prefix was a symmetry stabilizer.

For the first lift, the mean H64 odd position was about −0.045865 even on HOLD. At H64, the PLUS and MINUS increments from HOLD on this lift were about −0.000068 and +0.000068 in pulse-displacement units, and the second lift gave the opposite signs. Averaging this signed increment over roots conceals differences among individual conditional responses. The squared ambiguity instead uses the product of independent two-tape panels within each root. [Native PLUS, HOLD, MINUS readings for each lift, horizon and receiver](matrix-orientation-receiver.json)

## Size of the lost distinction and value of returning the bit

| Horizon | Coarse estimate of squared ambiguity | Root interval on squared scale | RMS estimate |
|---|---:|---:|---:|
| 32 ticks | 0.000000552 | [0.000000270, 0.000000931] | 0.000743 |
| **64 ticks, primary** | **0.000010668** | **[0.000005188, 0.000018014]**, including grid allowance | **0.003266** |
| 128 ticks | 0.000163361 | [0.000080197, 0.000273292] | 0.012781 |

One unit at H64 is 0.00048 native position unit. The primary RMS cost is therefore about 1.57 × 10⁻⁶ native position unit. The secondary H128 point estimate exceeds the corresponding 0.01-unit margin, but its interval crosses the threshold. This pilot settles the primary horizon. It leaves the practical effect at the later horizon open.

| H64 predictor | Root-averaged squared conditional-mean error | Root interval |
|---|---:|---:|
| Folded zero, also the optimal constant for this drive | 0.000010668 | [0.000005203, 0.000017998] |
| Canonical-prefix ridge plus actual orientation bit | 0.000019964 | [0.000009713, 0.000032337] |
| Shuffled-bit diagnostic | 0.000019597 | [0.000010185, 0.000031198] |
| Full state with separately sampled native futures | 5.24 × 10⁻¹¹ | [−2.53 × 10⁻¹⁰, 3.36 × 10⁻¹⁰] |

The estimated reduction in loss from returning the bit to the affordable model was **−0.00000930** [−0.00001838, −0.00000202]. Its grid-adjusted upper error was still inside the absolute tolerance. Its extra information did not earn an accuracy improvement over zero. Native shooting could use the full state to resolve the conditional response, at the cost of independent continuations. The shuffled-bit comparison permutes the available bit on the held-out panel and serves as a diagnostic. Negative cross-panel error endpoints are retained. [Original conditional errors and bit comparison](matrix-orientation-receiver.json)

## Custody and cost

Run `recursive.3632f08c9f1b2abf0e8ea933` completed all 54 operations on clean source `967781c2d`. The 16 development, 64 training, 32 calibration and 24 evaluation families were all evaluable. The disjoint evaluation roots were 522611342 through 522611365 inclusive. Paired twins, future tapes and numerical refinements remained nested within their assigned root. The reference futures descended from the particular native prefix and its already-issued forecast.

The 2,629,632 native updates comprised 2,113,536 in development, 294,912 at evaluation-prefix acquisition including privileged shooting, and 221,184 on the held-out references. Four independent shooting tapes for each sign and clock cost 3,072 additional native updates per evaluation family. The folded and bit-informed predictors required zero future native updates. Across all roles the workers logged 1,873.55 CPU seconds and 733.09 MiB of binary companions. Peak recorded batch-worker RSS was 420.68 MiB. The raw prefixes and original application custody remain external. This is source-bound numerical development with disjoint evaluation. [Per-stage cost and custody](matrix-orientation-receiver.json) · [Public reproduction guide](../workflows/matrix-orientation-response/guide.md)
