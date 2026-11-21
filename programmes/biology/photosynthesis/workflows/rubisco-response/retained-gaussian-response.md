# Extend retained finite response to the Rubisco receiver

SPDX-License-Identifier: CC-BY-4.0

This document specifies the molecular extensions needed by the retained Gaussian response method.
It separates the implemented numerical component from an admitted WT/I95M supplier.
Review the selected physical target and supply each required adapter contract before molecular use.

## Prerequisites and first action

Read the [generic method guide](../../../../../docs/development/retained-gaussian-response.md).
Use the [formation protocol](restrained-formation-v1.md) for the receiver, units, measure and atomic correspondence.
Use the [extension interfaces](../../../../../docs/development/extension-interfaces.md) for any registered operation.
Select the current public workflow, locked environment and explicit external custody before any native work.

The generic calculation and its bounded analytical tests are implemented.
They supply no actual WT/I95M reference, retained potential, residual enclosure or molecular result.
This document specifies additional adapter work; it does not advertise an implemented molecular command.
No native acquisition follows from the analytical examples.

First identify the consumer's required target: finite-grid $Q_k$, continuous restrained endpoint contrast, or a downstream activation quantity.
Declare the accuracy in the consumer's physical units.
Retain the full matched chemical alternative and preparation scope.
A missing molecular input remains a specific unresolved requirement.

## Preserve the receiver and physical correspondence

The formation receiver is

$$
\xi=d(C3,H3)-d(H3,O_{\mathrm{KCX}}).
$$

Within a justified image chart, retain

$$
u=r_{C3}-r_{H3},\qquad v=r_{O_{\mathrm{KCX}}}-r_{H3},\qquad
\phi(u,v)=\|u\|-\|v\|. \tag{33}
$$

The coordinate map is linear on that chart; the receiver remains nonlinear.
The shared hydrogen contributes to the full joint covariance.
Do not replace the two vector blocks with independent distance distributions.
The generic tests exercise this geometry with disclosed Cartesian coordinates.
They do not resolve molecular atom roles or periodic images.

The molecular adapter must authenticate C3, transferred H3 and accepting KCX oxygen from retained atom-role assignments.
Use the original [atomic transformation](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/molecular_transform.py).
Retain all changed, added and removed atoms and every selected substitution.
WT and I95M can use different native dimensions and separate reference operators.
Equal array indices or padded atom tables do not establish physical correspondence.

The current protocol uses orthorhombic minimum-image distances.
A fixed linear map is insufficient across an image change.
Supply a valid chart and its coverage or implement the required image/measure integration.
Keep unresolved image boundaries and coincident directions as refusals.
Additional modification coordinates are required wherever the finite native change cannot be represented in the receiver coordinates alone.
Six coordinates describe receiver support; they do not establish a sufficient molecular retained space.

## Reference and native-energy extensions

Use the existing [complete periodic operator](../../../../../src/empirical_lawhood/adapters/rubisco/rubisco_response/periodic_qmmm.py) and its scientific source contracts.
Do not substitute a different Hamiltonian to obtain a convenient quadratic environment.
A positive reference can differ from the native potential if the complete discrepancy remains explicit.

The supplying adapter needs these independently identified operands:

| Operand | Required implementation and evidence |
| --- | --- |
| Native state and source | Exact original preparation, atom roles, coordinates, cell, chemical state, electronic branch and complete Hamiltonian identity. A construction is not a relaxed ensemble. |
| Positive reference | Define $K$, origin, units and physical coordinate convention. Treat translational modes, constraints and any negative curvature explicitly. Record any reference regularization. |
| Inverse actions | Supply $K^{-1}S$ through the existing native-subwork and array contracts. Preserve solver residuals, tolerances, operator provenance and every paid call. A dense molecular Hessian is not required. |
| Retained lift and potential | Authenticate the map and construct $\bar x(z)$. Evaluate native energies at the selected configurations. Retain failures and the exact reusable energy grid. |
| Omitted potential | Bind $R=U-\widetilde U$ to the same state, Hamiltonian, chart and domain. Supply a justified enclosure or retain its absence. Sampled values alone do not certify it. |
| Integration and support | Select rule, finite point allowance, error assessment and any domain/measure extension. Control multiple modes and omitted tails. Gaussian order agreement alone is not a certificate. |

Reuse [native force-return custody](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/molecular_native.py) where its actual contract applies.
An energy-only operation needs its own explicit contract if the current supplier does not provide that operation.
Keep the selected native precision and electronic convergence requirements.
Count full force or energy work according to the actual implementation.

The numerical lift is not a preparation optimizer and does not establish equilibrium.
A chosen origin need not be a native minimum for the algebra to hold.
Its physical residual and integration cost still determine applicability.
Preserve unavailable relaxed endpoints and checkpoint states.

## Units and normalization

Use angstrom for retained relative vectors and the receiver.
If native energies and $K$ use kJ/mol, use $\beta=1000/(RT)$ with $R$ in J/mol/K.
Then $K$ and restraint stiffness use kJ/mol/angstrom².
Keep native Hartree/Bohr and nm/angstrom conversions explicit at their existing boundaries.
Preserve exact configuration values and conversions in canonical records; the method's arrays are numerical evaluations.

Use the default fixed-reference restraint calculation:

$$
J_m(s)=\mathbb E_{p_{G,m}}e^{-\beta[V_m+k(\phi-s)^2/2]},\qquad
\langle\xi\rangle_{m,s}=N_m(s)/J_m(s). \tag{34--35}
$$

`restrained_series` keeps the complete nonlinear distance restraint inside this integral.
It reuses native energies across centers and strengths on the same resolved grid.
The nonlinear receiver cannot use the affine-restraint absorption helper.
Any separate quadratic modification can use `quadratic_update` with its complete normalization factor.

The generic finite-grid result is in the selected energy unit.
Convert kJ/mol to the formation consumer's J/mol with the exact factor 1000.
Convert its mean forces to J/mol/angstrom by the same factor.
Preserve the original centers, ordered weights, signs, stiffness and both arm denominators.
Do not substitute the endpoint logarithm for the finite-grid operand.

## Residual and numerical error extensions

Select each error application according to its target.
For an endpoint contrast, equation 24 uses the sum of the two residual oscillations.
For the finite-grid operand, equation 25 propagates receiver errors through the absolute node weights.
Both applications can be retained together.
Their output fields must identify supplied bounds separately from estimates based on numerical moments.

Bind a residual envelope to the complete integration domain and its physical measure.
Tube bounds require omitted-tail control before full-integral use.
A bounded-domain implementation must also preserve the corresponding elimination measure.
Constrain inverse-action error through a valid operator bound and actual solver residuals.
A minimum Ritz value does not establish a global positive lower bound.

Keep these error contributions separate:

- Inverse-action, operator-action and arithmetic error.
- Retained-potential and omitted-environment discrepancy.
- Retained-space quadrature and tail error.
- Outer center-grid error relative to the continuous restrained target.
- Physical-state, preparation, chemical-model and coordinate-measure uncertainty.
- Activation, normalization and kinetic prefactor requirements for the downstream consumer.

For covariance enclosures, hold the mean, potential and measure fixed across the bounding integrals.
If an approximate inverse changes the lift and retained potential, account for that change separately.
A covariance enclosure alone does not cover it.

## Result, custody and assessment extensions

The [existing formation reader](../../../../../src/empirical_lawhood/domains/rubisco/rubisco_response/restrained_formation.py) consumes original trajectory records and sampling diagnostics.
It is not a generic container for a deterministic quadrature result.
Implement a distinct typed supplier result and destination assessment through the existing shared services.
Do not manufacture traces, bootstrap draws, native receipts or scientific identities from quadrature nodes.
Numerical nodes and centers are not independent biological units.

Bind the following in the new domain records and retained reader:

| Contract | Required contents |
| --- | --- |
| Selection | Physical target, exact units, both original state/source closures, atomic correspondence, retained coordinates, centers and weights, normalization choice and requested error applications. |
| Numerical evidence | Reference and operator identities, actual inverse actions, complete energy/receiver grid, array manifests, log partitions, moments, paired outputs and complete failed evaluations. |
| Error evidence | Original residual, variance, operator and integration enclosures with domain and applicability scope. Preserve absent and inadequate bounds. |
| Independent assessment | Reconstruct selected numerical outputs from original retained inputs. Refuse changed maps, sources, units, support and incompatible targets. Assess sufficiency in downstream units. |
| Cost | Actual operator/energy calls, preparation, grid construction, residual control, assessment, failures and fallback. Separate measurements from counterfactual estimates. |
| Retained access | Existing canonical revisions, complete member publications, current access and final byte checks. Reading original evidence acquires no replacement native energies. |

Use the supported method and experiment declarations if an installed lifecycle is needed.
Regenerate only affected owned projections in their documented order.
The existing scheduler, inquiry service, artifact plane and workbench retain their responsibilities.
Publish the exact implemented input, output, refusal and read contracts when these extensions are delivered.

## History and activation boundaries

The generic harmonic-bath component evaluates memory, initial forcing and dynamic stiffness for its stated model class.
Static compliance does not determine those history operands.
Molecular temporal use needs an admitted dynamical law, mass metric, bath/coupling representation and actual preparation.
The six relative-vector coordinates are not an orthogonal mass-weighted split by themselves.

A successful restrained calculation does not supply an activation free energy or rate ratio.
Retain the [activation connection](activation-rate-connection.md), reactant/dividing-surface normalization and transmission/population requirements.
Use paired cancellation only where the actual physical evidence supports it.

## Verification and delivery

Reuse the [generic analytical controls](../../../../../tests/test_retained_gaussian_response.py).
Add focused domain checks for atom roles, shared-hydrogen covariance, image boundaries, unit conversions and different native arm dimensions.
Verify both normalization choices where their assumptions apply.
Verify endpoint and finite-grid error applications independently.
Exercise absent residual support, failed energy nodes, immutable source/array joins and retained-read refusal boundaries.

A native validation calculation requires its own selected scientific purpose, resources and execution prerequisites.
No complete molecular reference trajectory is required solely to price an unexecuted cost counterfactual.
Charge any local physical comparison needed to resolve an actual applicability uncertainty.
Retain supported, adverse and unresolved outcomes.

The extension is ready for use only when its consumer has an authenticated sufficient value or bound and a complete error account.
Until then, the implementation supplies a numerical method and an explicit molecular integration specification.

## References and research

The [generic method guide](../../../../../docs/development/retained-gaussian-response.md) gives the equations, implementation entry points and numerical limits.
The [formation protocol](restrained-formation-v1.md) owns the molecular restrained target and its separate activation requirements.
The [scientific specification](scientific-specification.md) owns the WT/I95M evidence and applicability requirements.
