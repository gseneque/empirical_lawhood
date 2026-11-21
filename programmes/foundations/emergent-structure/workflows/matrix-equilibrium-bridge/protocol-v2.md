# SCI02-D: estimate a finite paired equilibrium contribution (v2)

SPDX-License-Identifier: CC-BY-4.0

This protocol selects a paired equilibrium experiment for the Rubisco bridge.
It tests whether a reduced response decreases the cost of a precise ensemble difference.
Use the [run guide](guide.md) to prepare, execute and independently read its finite stages.

## Operational revision

This revision corrects the complete output allowance for new executions.
The shared native-subwork boundary charges native files and ordinary parent copies against the same invocation allowance.
The original [protocol v1](protocol-v1.md) remains the immutable specification of the November 2026 retained experiment.
Its reference acquisition completed before parent publication exceeded the original 192 MiB allowance.
The existing completed-native recovery route retains those original outputs and attempts.
This revision selects 384 MiB before new work; it changes no scientific equation, sampling horizon, fitting rule or cohort size.
A newly prepared allocation still receives its own protocol digest, source binding and committed streams.
It does not inherit scientific qualification from the original study.

## Status and scientific scope

The protocol identifier is `matrix.paired-equilibrium-bridge.sci02d`.
Its exact bytes enter the immutable design before scientific acquisition.
SCI02-D is a new, nonpromotable numerical study.
It does not replace E4 or SCI01–C, their denominators, or their scientific decisions.
All previously observed results remain development evidence.
The new allocation contains 16 development bundles, 64 confirmation bundles and eight independent reference bundles.
No source-qualification, issue or reveal authority is fabricated for this development lifecycle.

The molecular consumer is the [restrained formation integral](../../../../biology/photosynthesis/workflows/rubisco-response/restrained-formation-v1.md).
The native reference remains the complete Hamiltonian in each arm.
The experiment changes the estimator of its average.
It does not substitute an approximate ensemble or infer a finite mutation from an infinitesimal derivative.

## Questions and falsifiers

1. Does the control preserve the selected canonical mean under its mathematical premises?
2. Does the structural control improve the signed paired estimator beyond the coordinate-only control?
3. Are uncertainty, preparation, numerical and quadrature findings consistent with the requested precision?
4. Does improvement repay construction, sampling and assessment costs within the stated finite use?
5. Which actual molecular suppliers remain necessary before the corresponding M1 pilot?

An incorrect zero-mean identity falsifies the estimator construction.
An adverse sampling, numerical or cost result does not become a software exception.
A small corrected variance does not establish equilibrium or hidden-state coverage.
Failed and unevaluable bundles remain in the original denominator.
No all-development-success gate prevents assessment of heterogeneous outcomes.

## Canonical target and units

For arm a and center s, let `U_a,s=V_a+k*(xi-s)^2/2`.
The target distribution is proportional to `exp(-U_a,s/T)` in the original Cartesian Hilbert–Schmidt measure.
The Matrix temperature T has energy units.
It replaces RT in the molecular formula, without assigning molecular units to Matrix parameters.

```text
G_a,s(q) = k*(s-xi(q))
Q_h = sum_i omega_i*(E_M,i[G_M,i]-E_W,i[G_W,i])
```

The ordered center grid uses composite trapezoidal weights.
The high-coupling arm is M and the low-coupling arm is W.
The names identify the finite parameter contrast only.
They are not chemical WT or mutant materials.
`Q_h` is the discrete restrained integral.
Its continuous-center counterpart has a separate quadrature discrepancy.
Neither quantity is automatically an activation barrier.

The Matrix absolute error request is 0.01 in native energy units.
The numerical, quadrature and preparation allowances are each 0.002.
The remaining 0.004 is the selected sampling half-width budget.
Unresolved initialization or hidden-state support prevents an equilibrium-accuracy claim even when these diagnostics pass.
An interval containing zero is still a useful estimate if its uncertainty is adequate.
Direction resolution is reported separately.

## Complete native physics

Reuse the six-matrix potential and the real Hilbert–Schmidt coordinate convention in the [Matrix programme](../../records/matrix-programme.md).
There are six Hermitian 4-by-4 matrices and 96 real position coordinates.
All trace components remain present.
Kinetic mass is one.
Potential masses are both 0.5.
The fixed scaled couplings retain these exact Decimal values:

```text
alpha_tilde_X = 0.6666666666666666666666666667
alpha_tilde_Y = 7.333333333333333333333333334
cross-coupling c = 0.5 or 2
bath temperature T = 1
friction gamma = 1
PRIMARY timestep = 0.001
FINE timestep = 0.0005
```

Use the physical Hamiltonian at these final parameters throughout each restrained trace.
The two starting histories are all-zero positions and the nominal product background.
Both have Maxwell momenta at T=1.
They target the same canonical distribution.
Their subsequent disagreement is a preparation diagnostic, not a second estimand.
No history or basin receives an empirically chosen favorable weight.
The prespecified estimator averages the two history estimates equally while retaining their separate results.
That averaging supplies no missing equilibrium-population evidence.

The scalar coordinate is

```text
r0 = alpha_tilde_Y^2/36
xi = sum_a Tr(Y_a^2)/(12*r0)
chi = sum_a Tr(X_a^2)/12
k = 32
centers = (0.8, 0.9, 1.0, 1.1, 1.2)
```

The normalization is calculated from the stated noiseless product background.
It is not fitted to new outcomes.
The reference bundles use all nine centers from 0.8 through 1.2 in increments of 0.05.
Their even nodes give the original five-center integral.
The odd nodes assess center-grid refinement within the same reference bundle.

## Three fixed estimators

For a differentiable field v, define

```text
C_v = T*div(v) - v dot grad(U_a,s)
E_pi[C_v] = 0
G_corrected = G - beta dot C
```

The identity follows by integrating `div(v*exp(-U/T))`.
The positive quartic native terms confine this Cartesian Matrix system.
The selected polynomial fields therefore have vanishing surface terms.
The complete native gradient includes the restraint.
Replacing it with an approximate gradient would change the identity.

The final field selection respects simultaneous matrix rotations:

```text
v0 = grad(xi)
v1 = (xi-s)*grad(xi)
v2 = chi*grad(xi)
v3 = (xi-s)*grad(chi)
```

NATIVE uses no correction.
COORDINATE uses v0.
STRUCTURE uses all four fields.
The last two fields represent environmental coupling in the projected equilibrium response.
This is the finite Galerkin response construction selected for execution.
It replaces the proposal's illustrative global inverse-curvature matrix with an invariant field basis before outcome contact.
No molecular Hessian or additional force evaluation is required at a sampled frame.
The divergence is analytic:

```text
div(grad(xi)) = 8/r0
norm(grad(xi))^2 = xi/(3*r0)
div(grad(chi)) = 8
C0 = T*8/r0 - grad(xi) dot grad(U)
C1 = (xi-s)*C0 + T*xi/(3*r0)
C2 = chi*C0
C3 = (xi-s)*(T*8 - grad(chi) dot grad(U))
```

Each arm is corrected before the signed quadrature difference.
Fit one coefficient vector for the complete paired integral.
Use PRIMARY development blocks, with both preparation histories retained.
Center the five block observables within each development root and preparation.
Use the complete covariance matrix for G and the four controls.
COORDINATE uses its scalar covariance ratio.
STRUCTURE solves the four-variable system with a ridge of 0.01 times the largest control variance.
Keep negative coefficients and signed covariances.
No intercept or signed residual regression is fitted.
The coefficients freeze before confirmation and independent reference acquisition.

Select each correction's operational sampling fraction from `(0.25,0.5,1)`.
Choose the smallest fraction no smaller than its development variance ratio to NATIVE.
Use 1 when no smaller fraction qualifies or the ratio is unresolved.
This is a measured allocation heuristic, not an error bound.
Its accuracy is assessed on the complete confirmation cohort.
No coefficient, field or allocation changes after confirmation contact.

## Sampling and independent units

Each ordinary bundle has 8,192 warmup and 16,384 production PRIMARY steps.
Retain one production frame every 64 PRIMARY steps: 256 frames per chain.
Each independent reference bundle has four times both horizons and 1,024 retained frames per chain.
Both numerical views share physical sample times.
Every bundle includes both couplings, both starting histories and its complete center grid.

Use PCG64DXSM streams derived from one newly committed 256-bit source seed.
The selected source derives separate momentum, coarse-noise and fine-bridge streams for every bank and ordinal.
The two coupling arms share innovations within each center/history.
Different centers and histories receive separate Gaussian entries.
FINE half-step innovations use the existing OU bridge equation.
The same coupling of noise is assessed, rather than assumed to improve every paired variance.

The independent unit is a complete bundle.
Frames, blocks, centers, starts, arms and numerical views are nested observations.
The 64 confirmation bundles estimate repeated performance for one selected physical target.
They are not 64 distinct mutation targets or an automatic finite-reuse justification.
Reference bundles have separate streams and cannot enter fitting.

The default block length is 32 retained samples, or 2.048 physical time units.
Report the doubled-block comparison and unresolved correlation tails.
For each full series and operational prefix, estimate statistical inefficiency from the initial positive adjacent-lag autocorrelation sums up to half the retained length.
Mark its tail diagnostic unresolved unless a nonpositive pair is reached and at least 20 estimated correlation times are retained.
This finite diagnostic supplies no mixing or hidden-state guarantee.
The native recorder retains every selected position, full gradient and five observables.
It also retains kinetic temperature, warmup radius and exact generator states before and after acquisition.
The original standard-noise sequence has a retained SHA-256 digest.
One prescribed PRIMARY transition every 1,024 steps retains both phase states, both gradients and its innovation.
The reader checks those witnesses independently.
It does not claim to reconstruct every unretained integration step.

The batch force is compared with the existing scalar termwise gradient at every retained frame.
Independent coordinate stencils check the divergence and selected potential derivatives.
No new random stream or native trajectory is acquired during readback.

## Solvable controls

First assess a harmonic restrained target with an analytic mean and exact control cancellation.
Then use the two-coordinate potential

```text
V_c(x,y) = 2*(x^2-1)^2 + (1+c*x^2)*y^2/2
xi=x; T=1; k=4; c in (0.5,2)
```

Integrate out y analytically.
Compute the remaining one-dimensional partition and mean with independent adaptive quadrature.
Compare a separate two-dimensional quadrature calculation of the zero-mean controls.
Retain numerical integration errors and refinement residuals.
Use centers from -1 to 0.
Compute the unrestrained PMF endpoint contrast independently from
`A_c(x)=2*(x^2-1)^2+log(1+c*x^2)/2+constant`.
Report the finite-restraint and quadrature differences explicitly.
These controls establish mathematical and software behavior only.
They supply no Matrix equilibrium or molecular qualification.

## Confirmation, uncertainty and costs

Acquire all 64 confirmation bundles even when development predicts no saving.
Assess all three methods at full length and at their frozen operational fractions.
Keep PRIMARY/FINE, both starts, both chronological halves and complete node contributions.
Compare reference five-node and nine-node integrals.
The independent reference has estimated uncertainty; it is not exact simulator truth.
Retain the complete arm/node block covariance matrices before their signed quadrature contraction.

Report signed bias, RMSE, interval coverage counts, point errors, variance ratios and preparation discrepancies.
Use whole-bundle Student intervals for population means.
Per-bundle block intervals remain approximate diagnostics.
Their observed coverage is assessed against the independent reference and its uncertainty.
Report the complete 64 denominator and binomial uncertainty.
No 95/95 reliability claim follows automatically.

Mean preservation, reduced variance, useful precision and lower complete cost are separate findings.
Require at least 20% lower total cost at equal stated precision for a positive practical result.
Charge preparation, fitting, numerical verification, reference assessment, failed work and orchestration.
Report reference-force counts separately from CPU and elapsed time.
Do not add child CPU twice to its parent total.
Historical unmeasured overhead remains unknown.

The study acquires complete confirmation paths to compare the frozen shorter prefixes.
Its operational cost is consequently a reconstruction from paid native work.
It does not claim that its already acquired assessment suffixes were avoided.
State asymptotic cost projections separately from finite measured cost and actual future deployment.
Repeated estimates of this same known target cannot create legitimate reuse demand.
The molecular finite workload requires its own selected centers, states and suppliers.

## Molecular entry and remaining connections

The first molecular scope is the selected full-assembly M1 WT versus all-eight-SSU I95M pair at 298.15 K.
Retain exact atom correspondence, natural masses, cell, electronic settings and the C3–H3/KCX coordinate.
M1 evidence does not supply V1 applicability.
The Matrix radius fields do not transfer as molecular vector fields.
Construct an admissible molecular field with the actual coordinate geometry and periodic boundary treatment.
Validate all divergence terms and units independently.
Native forces remain the complete QM/MM forces plus the selected restraint.

Entry needs actual assessed matched preparations, executable sampling configurations, a physical tolerance and a complete resource allocation.
Missing suppliers remain explicit in the final bridge finding.
A successful Matrix result supplies no substitute geometry, unobserved equilibrium population or compute authorization record.
The molecular pilot uses predetermined reactant-side, intermediate and product-side centers.
These nodes assess feasibility and cannot supply the complete integral alone.
The proposed molecular precision is 100 J/mol for the bare integral, subject to an explicit downstream selection.
It is not a selected bound on the full formation-rate ratio.

Finite-restraint and measure corrections, basin/dividing-surface normalization, orthogonal-state coverage, transmission and effective-state aggregation remain separate suppliers.
The `q_r`, `q_D` and `q_chi` work proceeds under the [conditional model](../../../../biology/photosynthesis/workflows/rubisco-response/initial-model-v1.md).
No missing contrast defaults to unity.

## Execution and custody

Use registered operations for solvable controls, native sampling, independent assessment, fit and confirmation reduction.
The source selection derives roots and streams.
The domain lowerer derives tasks, dependencies and output contracts.
Reuse generic experiment preparation, authoring, execution, recovery and result reading.
Native subwork retains original contact markers, outputs and receipts.
Unknown contact cannot be repeated through a renamed task.
Continuation authenticates the completed development result and frozen fit before new inputs are produced.

Select the locked main CPython 3.11.14, NumPy 2.4.6 and SciPy 1.17.1 environment.
Use one numerical thread per worker and four workers.
Select `/home/chevre/empirical-lawhood-sci02-d` for inputs, artifacts, checks, scratch and results.
Keep at least 2 GiB free and inspect the complete output allowance before entry.
Positions, gradients and diagnostics occupy three existing bounded Matrix array artifacts, each at most 64 MiB.
The complete per-task output allowance is 384 MiB, including both retained native files and ordinary parent copies.
The artifact partition changes no selected sampling frame.
The native finite horizons are scientific sampling selections, not wall-clock deadlines.

## References and research

- Roussel and Stoltz, [A perturbative approach to control variates in molecular dynamics](https://doi.org/10.1137/18M1171047), 2019.
  This source motivates approximate physical response functions for variance reduction.
- Si et al., [Scalable Control Variates for Monte Carlo Methods via Stochastic Optimization](https://arxiv.org/abs/2006.07487), version 2, 2021.
  This source describes Stein controls and their computational tradeoffs.
- Fass et al., [Quantifying Configuration-Sampling Error in Langevin Simulations of Complex Molecular Systems](https://pmc.ncbi.nlm.nih.gov/articles/PMC6208357/), 2018.
  This source distinguishes timestep-dependent sampling bias from stable integration.
- The [SCI02-C protocol](../matrix-preparation-shortcut/protocol-c-v1.md) supplies the prior scalar-consumer design and its separate evidence limits.
