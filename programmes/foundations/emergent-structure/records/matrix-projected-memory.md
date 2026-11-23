# Matrix memory and the blind two-pulse forecast

SPDX-License-Identifier: CC-BY-4.0

**One previous position sample greatly improved the forecast over using present positions and drive. None of the 14 field models delivered the complete trajectory within the declared tolerances.** On 128 independent preparations, the selected one-lag model met the signed-response margin on the blind two-pulse composition. A constant-by-drive forecast met that margin on both pulse recipes. The best field models for the signed difference, absolute levels and joint trajectory therefore differed. A minimum sufficient history for this nonlinear receiver remains undetermined. [All candidate intervals and original receipts](matrix-projected-memory.json)

## What was issued

The six-matrix source recorded two position ports of the first Y matrix and their past at a common phase in the prescribed drive. All field candidates received their declared observations before continuing. Only the momentum model used directly measured port momenta as forecasting features. A separate oracle had the full native state and 16 independently shot future tapes. The baseline used training-population means for each drive. Four independent native tapes per held-out root supplied the reference, coupled across pulse signs and clocks within that root.

Training saw PLUS, MINUS and HOLD for a single eight-tick pulse. At the evaluation cutoff the application issued both single-pulse and composed-pulse trajectories, including the composition with a second, opposite pulse on ticks 32–39 and its mirror. It supplied **zero** intervening observations. The primary signed receiver was the even position at tick 64, in units of the direct inertial displacement 0.00048. The level forecasts and joint score used both ports at ticks 32, 64 and 128. The primary joint comparison used the positive-starting branch within each recipe. [Scientific definition and workflow](../workflows/matrix-projected-memory/guide.md)

## Frozen controls and native generalization

The harmonic control had the same static stiffness, 2, at both hidden frequencies. Its memory at time one was +0.54030 and −0.41615. The reduced convolution, including the hidden initial force, reproduced direct full acceleration to 1.34 × 10⁻¹⁵. On the 192-coordinate frozen matrix, the full finite recursion reproduced direct propagation to 6.89 × 10⁻¹⁵, a switched-operator check to 5.56 × 10⁻¹⁶, and the one-step affine, force and OU-noise injection to 8.89 × 10⁻¹⁶. The Hessian directional check differed from the independent gradient difference by 7.99 × 10⁻¹¹.

The hidden block of the fitted transition had spectral radius 1.00519. Its first and last tested feedback norms were 0.00001316 and 0.00001411. An infinite converged memory sum is unjustified for this frozen transition. For the signed forcing input and two position outputs, finite Hankel numerical ranks at block horizons 4, 8, 16, 32 and 64 were 4, 5, 6, 6 and 6. The singular spectra and tolerance are retained. This is a finite, forcing-specific diagnostic of a linearized map. These ranks cannot determine the minimal nonlinear stochastic state. [Original training operator and harmonic checks](matrix-projected-memory-diagnostics.json)

## Prediction at the receivers

The 16 separate selection roots chose the one-lag model. Four lags and measured momentum were close on the selection score (0.003323, 0.003347 and 0.003359 respectively). Sixteen additional roots calibrated the joint bands after selection. Across the blind evaluation, the native mean signed response was 0.478286 scaled or 0.00022958 native position unit. On the single pulse it was 0.934608 scaled or 0.00044861 native. All 14 field models got the primary direction right on all 128 roots. Their errors in magnitude differed substantially.

| Candidate | Single-pulse signed MSE | Blind signed MSE | Blind excess energy score against shooting | Blind simultaneous coverage |
|---|---:|---:|---:|---:|
| Known drive, population mean | 2.15966e-05 | 1.71887e-05 | 1.64907 | 100.0% |
| Present positions and drive | 0.750875 | 0.227904 | 0.14915 | 94.1% |
| One previous sample | 0.000313135 | 1.72293e-05 | 0.04788 | 98.4% |
| Four previous samples | 0.000611064 | 0.000460323 | 0.04479 | 98.8% |
| Eight previous samples | 0.00694654 | 0.00314457 | 0.04375 | 99.2% |
| Sixteen previous samples | 0.0494856 | 0.0237858 | 0.04074 | 99.4% |
| Measured momentum | 0.000553861 | 0.00049032 | 0.04559 | 98.6% |
| Static elimination | 0.000703364 | 0.000560825 | 0.20013 | 94.7% |
| One kernel coefficient | 0.827406 | 0.228763 | 0.17429 | 93.0% |
| Four kernel coefficients | 0.738927 | 0.228674 | 0.17612 | 93.0% |
| Eight kernel coefficients | 0.628779 | 0.228416 | 0.17855 | 93.0% |
| Sixteen kernel coefficients | 0.435578 | 0.227439 | 0.18337 | 92.8% |
| Full 128-tick kernel | 0.00175995 | 0.00140584 | 0.21885 | 93.4% |
| Full kernel, unconditional hidden mean | 0.00175995 | 0.00140584 | 0.17093 | 94.1% |
| Priced full-state shooting | 9.14873e-10 | 6.07789e-10 | 0.00000 | Reference |

Signed mean-square error uses independent reference panels to remove the positive floor from squaring a noisy target. The signed RMS tolerance was **0.01**, or **0.0001 squared**, including the coarse/fine allowance. For the selected model the single-pulse MSE was 0.0003131 [0.0002750, 0.0003517] and the blind MSE was 0.00001723 [0.0000101, 0.0000265]. Its blind paired gain over present plus drive was **0.22789** [0.22685, 0.22890] squared units. The drive-only baseline attained 0.0000216 on the single pulse and 0.0000172 on the blind pulse. Both passed the signed margin. This comparison leaves little evidence that history is necessary for the *signed intervention* at this operating point. Shuffling the past while keeping each root's present and phase fixed worsened the selected model's standardized development **level** error by 0.03286 [0.00966, 0.05606]. [Primary decisions](matrix-projected-memory.json) · [History and physical-unit diagnostics](matrix-projected-memory-diagnostics.json)

The one-lag model's blind joint energy score was 0.09312 against 0.04524 for native shooting. Its excess was **0.04788 [0.03671, 0.06021]**, crossing the 0.05 noninferiority margin. Its nominal 90% simultaneous bands covered **98.44% [95.70%, 100%]** of held-out trajectories, clearing the 80% lower-bound requirement. The mean full H64 widths were 0.11407 and 0.11459 native position units. Its issued within-trajectory even-port covariance between ticks 32 and 128 was 0.000329, compared with 0.0000867 from the independent reference tapes. Coverage and a coherent fitted trajectory distribution each provide information that the signed contrast omits.

Every field candidate missed at least one absolute-level or joint requirement. The selected model's blind H64 even-port squared level error was 1,223 [758, 1,793] in squared displacement units, against a level tolerance of 0.0025. Even the finite 16-tape state-informed reference left its **absolute conditional-mean** level tolerance unresolved at this measurement budget. The full frozen kernel and the unconditional-hidden-mean version made identical signed predictions, as expected when additive initial-state terms cancel in a linear contrast. Their joint excess scores differed. No least-cost full-delivery model can be selected from this experiment. [All six level intervals, band widths and joint scores](matrix-projected-memory.json)

## Custody and cost

Run `recursive.c181b2d126b9e0f8b9ad6cd5` completed 80 operations from clean `967781c2d`. All 16 development, 64 training, 16 selection, 16 calibration and 128 evaluation roots were evaluable. The evaluation roots were 532611342 through 532611469 inclusive. The study used 4,653,056 native updates, including 1,376,256 during development, 2,293,760 at evaluation-prefix acquisition including privileged shooting, and 983,040 for independent evaluation futures. The sixteen-tape full-state comparator alone required 10,240 native updates per evaluation root across five recipes. All field predictions together required zero future native steps and 14.18 worker CPU seconds for the prediction stages. The complete study used 3,287.76 worker CPU seconds, 17.79 MiB of binary companions and a maximum recorded batch-worker RSS of 403.75 MiB. The original source-bound numerical result has disjoint evaluation and retains its development evidence ceiling. [Original costs and identities](matrix-projected-memory.json) · [Reproduction guide](../workflows/matrix-projected-memory/guide.md)
