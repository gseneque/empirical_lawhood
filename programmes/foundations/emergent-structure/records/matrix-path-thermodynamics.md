# Six-matrix dissipation and physical reversal

SPDX-License-Identifier: CC-BY-4.0

The native BAOAB recorder reproduced the hot and equal-temperature preparation rates to the declared tolerance. The driven cycle did **not establish positive dissipation** for an orientation-response experiment. On its fine clock the mean heat to the bath was **−1.634** energy units per cycle. The frozen observed-path test gave a lower confidence bound of **−0.464 nats** on the matched cycle. All 128 assigned evaluation families and all 4,096 additional preparation roots were evaluable. [Cycle measurements and receipt identities](matrix-path-cycle.json) · [Independent preparation measurements](matrix-path-preparation.json)

## Preparation instrument

The six Hermitian positions and momenta at $q=2$ each have 96 real Hilbert–Schmidt coordinates. The transient used the two-orientation position mixture with Gaussian jitter 0.03, unit friction and a unit-temperature bath. The two momentum temperatures shared standardized draws within each root. Four sign-reflected arms and both numerical refinements remained nested. The observable was heat to the bath plus the change in negative log initial density. The known initial density makes its instantaneous derivative the system entropy slope. The finite-window cross entropy includes a positive relative-entropy term, which makes window extrapolation especially important.

| Initial preparation | Analytic bath / system / total rate | Measured bath rate | Measured system rate | Measured total rate and widened interval |
|---|---|---:|---:|---:|
| Equal temperature | 0 / 0 / 0 | −0.111 | +0.212 | **0.102 [0.033, 0.170]** |
| Twice bath temperature | +96 / −48 / +48 | +96.017 | −47.621 | **48.395 [47.256, 49.535]** |

The first panel of 128 gave 48.415 [41.313, 55.516] for the hot total. It resolved the opposite signs of the two terms and lacked the precision for the ±2.4 equivalence margin. The 4,096-root preparation panel used the original three windows (0.001, 0.002 and 0.004 model time) at 4, 8 and 16 steps each. The physically measured heat and boundary-density terms used the same native step. Both total-rate intervals fit the margin. The equal-temperature estimate has a small reproducible positive intercept, and its interval excludes exactly zero. Treat the instrument as accurate to the reported tolerance. The intervals include root-level sampling error, paired time-step and short-window discrepancies. Those numerical allowances are empirical checks on the extrapolation. [All nine cells per term, allowances and original root ranges](matrix-path-preparation.json)

The OU forward/reverse Gaussian log-density ratio agreed with heat divided by temperature to a maximum absolute difference of 1.70 × 10⁻¹³ over the full cycle families. The largest endpoint momentum reconstruction error was 4.96 × 10⁻¹³. The parameter-work difference against the full native potential at the checked jumps stayed below (8.16\times10^{-14}). EL retained seven complex frames per step for the preselected first development and first evaluation roots in both physical directions and at both resolutions. The independent reread of the evaluation frames recovered all stored position ports exactly, with zero interstep discontinuities. Correctly identifying the drift midpoint makes the whole discrete path invertible on the known protocol. [Frame and per-family ledger checks](matrix-path-cycle.json)

## The driven population

The symmetric native potential used mass coefficients 0.5 and cross coupling 1. The X coupling rose by one over 128 primary ticks and returned over 384. Y stayed fixed. The period was 0.512 at primary step 0.001, with a 0.0005 matched view. Roots alternated between starting position jitters 0.03 and 0.12 and had a fair global orientation. Four burn-in cycles preceded the measured fifth cycle. An independent forward terminal bank supplied parity-reversed starting states for independently driven reverse paths. The mirrored schedule changed the coupling at its mirrored physical boundary. Forward, bank, reverse, fixed control, numerical views and phase samples are nested in one family.

| Fine-clock measurement per cycle | Forward mean [95% interval] | Physical reverse mean [95% interval] | Fixed-coupling mean [95% interval] |
|---|---:|---:|---:|
| Heat to bath | −1.634 [−3.106, −0.162] | −1.549 [−3.068, −0.029] | −1.047 [−2.386, 0.292] |
| Protocol work | 0.0855 [0.0227, 0.1483] | −0.0636 [−0.1351, 0.0079] | 0 [0, 0] |
| Shadow work | −0.000110 [−0.000250, 0.000031] | 0.000099 [−0.000051, 0.000250] | −0.0000023 [−0.0000079, 0.0000033] |

The forward ensemble absorbed heat while the protocol did positive work. Its mean energy rose by 1.719 over the final cycle. The coarse mean heat was −1.636. Refinement changed it by +0.00258 [−0.00101, 0.00616]. Successive forward fine-clock heat means were −8.329, −4.679, −2.292, −2.633 and −1.634. None of energy, either port moment, heat or work passed the prespecified stationarity checks across consecutive blocks and dispersed starts. The independent terminal bank supplies a reverse preparation, but supplies no normalized terminal density or bound on the endpoint entropy change. Accordingly the heat measurement cannot establish the sign or magnitude of total entropy production. [Block, start-group, energy and refinement results](matrix-path-cycle.json)

## How much direction was measurable

The bounded path critic used identical position-port features on forward paths and on physically reversed paths aligned to the forward clock. Sixteen disjoint development families fixed its weights, threshold and scaling. On 128 evaluation families its primary sample score was −0.11274 on the coarse clock and −0.11270 on the fine clock. The one-sided lower bounds were −0.46413 and −0.46410 nats with simultaneous 95% coverage across those clocks. Forward and reverse score ranges overlapped almost completely. The development fit scored +0.76006 on its own data. The independently evaluated critic thus provided no positive lower bound beyond KL's mathematical lower bound of zero. The true full-path KL could still be positive.

Endpoint strides 4 and 16 and both label views also yielded nonpositive lower bounds. An instantaneous label commuted with reversal at every checked time. Reversing the already processed trailing-four label disagreed with physically reversing the path before labeling at **85/64,896**, **81/15,744** and **68/3,456** scored evaluations for strides 1, 4 and 16 on the primary clock. Both orders used the same interior window and three true samples of padding at each end. History counts at depths 1, 2, 4 and 8 include absent contexts and unavailable history. These are repeated observations within paths. The test establishes an ordering effect of the causal observer. Comparing the fitted lower bounds cannot establish the amount of information lost under thinning. [All observation bounds and label context censuses](matrix-path-cycle.json)

## Consequence for the orientation experiment

Keep the symmetry argument. Under the specified scalar protocol, simultaneous global conjugation preserves both path laws and commutes with momentum parity. Their likelihood ratio is constant on each two-element orbit, so folding the entire prefix once preserves its KL whenever that ratio exists. The present experiment leaves the magnitude of that KL unresolved. The hot preparation rate applies at a different population and time. A paired pulse pilot can test whether the orientation carries a consequential signed response, provided its claim is limited accordingly. A combined claim of positive dissipation, orientation loss and prospective repair needs independent positive direction evidence on the same prefix plus the paired loss and repair experiments. [Thermal circuit comparison](../../measurement-and-response/records/thermal-rc-dissipation.md)

## Original custody and reproduction

| Panel | Source revision | Original run | Development / evaluation seeds, inclusive | Native updates, development / evaluation |
|---|---|---|---|---:|
| Complete cycle and transient | `3e1c2a9d8` | `recursive.88a7b4aee4dc72c06e5e1141` | 123112300–123112315 / 123112316–123112443 | 400,896 / 3,207,168 |
| Preparation precision | `7c26e4e50` | `recursive.bbc8d17d82eb32792d795411` | 143110000–143110063 / 143110064–143114159 | 30,720 / 1,966,080 |

The preparation precision allocation was fixed from the 16 development families before inspection of the cycle evaluation aggregate. Both studies completed with eight eligible workers and one numerical thread per worker. The tables use independent roots for uncertainty. Coarse/fine views and sign arms share innovations. The machine records identify every acquisition block and parent assessment and give receipt and binary digests, compressed byte counts, and acquisition process and wall times. EL recorded numerical development evidence with disjoint evaluation, scientific authority `NONE` and qualification `NOT_ESTABLISHED`. The original arrays remain in their original operator workspaces. [Public workflow and recipes](../workflows/matrix-path-thermodynamics/guide.md)
