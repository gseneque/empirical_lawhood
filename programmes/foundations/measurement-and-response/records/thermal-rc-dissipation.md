# Thermal RC dissipation and predictive voltage memory

SPDX-License-Identifier: CC-BY-4.0

In this three-branch circuit the accessible voltage record preserves the full forward/reverse likelihood ratio, even though the present summed voltage discards information about its own future. At unequal relaxation rates its measured lag-two conditional covariance was **0.07969 [0.06935, 0.09003]**. At equal rates it was **−0.00344 [−0.00945, 0.00257]**. Both independent-root intervals met the declared equivalence bounds around their respective exact values. [Original path, memory and phase results](thermal-rc-paths.json)

## What the voltages measure

A unit-temperature resistor drives each unit capacitor. The driven branch has unit rate and a sinusoidal source. The two grounded branches have rates 1 and 4, or both 1 in the memory control. The observed channels are the driven voltage $x$ and the grounded sum $s=y_1+y_2$. Each root contains the three branch voltages. For the path test the forward and reverse thermal draws are independent, the reverse process starts at the forward terminal law, and the waveform runs backward in physical time. All three voltages are even under time reversal.

The hidden branches are stationary and reversible under this drive. Their contributions to the log ratio cancel path by path. Hence $x$ alone, and also $(x,s)$, carry the full forward/reverse ratio. In reference units the instantaneous entropy-production rate is $(\cos t+\sin t)^2/4$, and the entropy produced in a full period is $\pi/2$. The grounded sum alone is blind to the drive. This is an exact property of the defined stochastic model.

## What the independently sampled rates resolved

The observable correlation estimate uses signed products of means from disjoint root halves and the observed second moment of the increments. The vanishing-lag estimate uses the five longest of six lags from 1/128 to 1/4 and retains within-root covariance across those lags. At zero rate the upper and lower limits propagate the uncertainty on the squared scale. A signed estimate can be slightly negative. The 95% interval concerns the population rate. The equivalence margin is ±0.025.

| Setting and exact instantaneous rate | Complete panel, 65,536 roots | Correlation precision panel, 1,048,576 new roots | Decision at the precision ceiling |
|---|---:|---:|---|
| Driven at phase 0, 0.250 | 0.23727 [0.15024, 0.32429] | **0.26228 [0.23912, 0.28544]** | Positive, compatible with 0.250. Equivalence unresolved because the upper endpoint exceeds 0.275. |
| Driven at phase $3\pi/4$, 0 | −0.00205 [−0.00372, 0.03264] | **−0.00026 [−0.00085, 0.00217]** | Within margin. |
| Undriven equilibrium, 0 | −0.00193 [−0.00110, 0.03092] | **−0.00009 [−0.00007, 0.00188]** | Within margin. |

All six finite-lag analytic values fell inside their simultaneous lag limits at every phase in both panels. In the precision panel the largest blind-sum upper bound was 0.00285. The precision study used six exact, possibly unequal, OU intervals, preserving the same joint lag law with six updates per triplet. The design and cap were fixed from the original 4,096 development triplets. The second evaluation did not reuse any complete-panel triplet. [All lags, intervals and blind controls](thermal-rc-correlation.json)

## Physical reverse paths

| One-unit physical window | Continuous-time forward KL | Exact KL at 16 intervals | Measured forward KL [95% interval] | Measured reverse KL [95% interval] |
|---|---:|---:|---:|---:|
| Driven from phase 0 | 0.42702 | 0.42678 | 0.42389 [0.41682, 0.43095] | 0.43048 [0.42342, 0.43754] |
| Driven from zero-rate phase | 0.13634 | 0.13606 | 0.13742 [0.13343, 0.14140] | 0.13447 [0.13047, 0.13846] |
| Equilibrium | 0 | 0 | Within numerical roundoff of zero | Within numerical roundoff of zero |

The zero instantaneous rate and positive integrated divergence refer to different durations. An independent dense Gaussian joint likelihood on $(x,s)$ agreed with the full three-voltage transition product to a maximum absolute error of 7.29 × 10⁻¹⁴. The forward and reverse means agreed with independent numerical quadrature to 1.67 × 10⁻¹⁶. Running the waveform forward again in the reverse denominator changed the positive-phase mean log ratio from 0.424 to 0.811. The complete report includes results on four, eight and sixteen physical intervals. [Original forward and reverse grid results](thermal-rc-paths.json)

## Predictive memory

At stride 1/4 the exact conditional covariance between the previous and next sums given the current sum is $(e^{-1/4}-e^{-1})^2/2=0.0844282$ for distinct rates and 0 for equal rates. The equivalence margin was 0.0211070, one quarter of the distinct-rate signal. In the distinct-rate case, one-, two-, four- and eight-sample histories had next-sum mean-squared errors 1.33324, 1.32856, 1.32593 and 1.32546. With equal rates the MSE was 0.77887 at every history length. Dense Gaussian conditioning agreed with a separate two-state recursive filter within 2.23 × 10⁻¹⁵.

For two distinct positive poles with positive weights, the reciprocal spectrum of the summed Gaussian process is not a finite trigonometric polynomial. Its **raw scalar samples have no finite Markov order**. A two-dimensional latent state still gives exact Gaussian filtering. At equal rates the sum reduces to one sampled OU process. The order statement follows from the analytic spectrum. The measured conditional covariance directly tests failure of one-step Markov prediction. The receiver here predicts a future voltage level. This experiment does not measure a signed matrix intervention or a circuit-board response. [Matrix experiment and the orientation decision](../../emergent-structure/records/matrix-path-thermodynamics.md)

## Custody and reproduction

| Panel | Producer revision | Original run | Development / evaluation seeds, inclusive | All thermal interval updates |
|---|---|---|---|---:|
| Complete | `3e1c2a9d8` | `recursive.6bbc06cb884e320b792c6a46` | 423112300–423116395 / 423116396–423181931 | 18,939,904 |
| Correlation precision | `7c26e4e50` | `recursive.84354262b215e9949b15ed93` | 443110000–443114095 / 443114096–444162671 | 6,316,032 |

All assigned triplets were evaluable. The two panels used eight eligible workers, one numerical thread per worker, and original batch records with member digests and exact root IDs. EL classified the sampled results as numerical development with disjoint evaluation, scientific authority `NONE` and qualification `NOT_ESTABLISHED`. The linked machine records contain the retained scientific measurements and original receipt identities. The physical array containers remain in their original operator workspaces. [Public workflow and recipes](../workflows/thermal-rc/guide.md)
