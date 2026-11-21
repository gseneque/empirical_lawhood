# Reuse a scientific component

SPDX-License-Identifier: CC-BY-4.0

This guide locates calculations that work independently of a campaign or native adapter.
Domain contracts preserve their units, applicability, complete populations and assumptions.
Select the component whose input contract matches your scientific question.

## Scientific owners

| Calculation or representation | Current scientific owner | External boundary |
| --- | --- | --- |
| Scientific quantities, time, evidence, identities and experiment records | `science` | No acquisition or application construction |
| Shared inference, selective response, estimation and assessment algorithms | `methods` | Explicit applicability and supplied scientific operands |
| Retained Gaussian elimination, nonlinear retained perturbations and memory controls | `methods.retained_gaussian_response` | Positive-definite quadratic reference, explicit finite retained potential and integration assumptions |
| Joint-port spectral response, residuals, Schur tails, exact moment witnesses and mean/variance bridges | `methods.joint_response` | Supplied operators and ports, verified gaps or inverse bounds, finite updates, and stated arithmetic premises |
| RC nodal operators, trajectories, hidden-state/history challenges and scale comparisons | `domains.circuits`, `domains.history` | Instruments, source-format readers and protected campaign custody remain separate |
| Six-matrix dynamics, geometry, history, preparation, response-law definitions and scientific authoring | `domains.matrix` | Native source acquisition and authenticated input loading remain in adapters |
| Battery control, reduced/segmented/refined inquiry, recursive construction and thermal-service assessment | `domains.battery` | PyBaMM state/solver access and checkpoint capture remain in adapters |
| Quantum response, finite grammar, marked records and trajectory preparation/qualification | `domains.quantum` | Supplied finite-dimensional models and declared observation protocols |
| Cell-response scientific summaries, predictions, protocols and neuron response contracts | `domains.biology` | HDF5/AnnData access, native simulation and output writes remain in adapters |
| Chemical-reactor and reaction–diffusion preparation, scientific records and response assessment | `domains.chemistry` | Cantera/FiPy construction, native integration and version contact remain in adapters |
| Grid, inverter and thermodynamic response contracts and scientific projections | `domains.energy` | Grid2Op and other native simulator contact remain in adapters |
| Fusion denominator, TORAX/GymTORAX/FreeGSNKE, MAST transport and physical-record scientific components | `domains.fusion` | Solver engines, archive access and native state conversion remain in adapters |
| Reactor causal, prefix, regime, feed, replay, frontier and selected-action scientific components | `domains.reactor` | Native reactor execution, source recording and publication remain separate |
| Optical-mirror reductions, prediction/assessment and Glenn physical-system/exploration authoring | `domains.optics` | Instrument/source archive access and format conversion remain in adapters |
| Electron-gas response, superconductivity definitions, material inquiry and supplied-data numerical analysis | `domains.materials` | External source access and solver contact remain in adapters |
| Conditional Rubisco assay, kinetic reductions, geometry, preparation and molecular scientific contracts | `domains.rubisco` | OpenMM/PySCF/other engine bindings and native files remain in adapters |
| Charged-background Ewald correction | `methods.electrostatics` | Declared charge, Ewald parameter and volume; shared by CPU and GPU bindings |
| Checked DIIS eigenvalue, coefficient and block-accumulation mathematics | `methods.electronic_structure` | Supplied finite arrays; native electronic-structure solver contact stays in its adapter |
| Reference-world representations, exploration and scientific authoring | `domains.reference_worlds` | Shared execution and application services own effects and persistent lifecycle |

These scientific owners are reused directly by the [new R01–R22 experiments](joint-description-experiments.md).
The [classical matrix series](classical-matrix-series.md) also composes native
six-matrix dynamics with the [joint-response calculations](../development/joint-response-calculus.md)
and the retained-Gaussian controls through one recursive experiment.
The [family census](../release/preprint-recursive-migration.md) identifies the
implemented recipes and the remaining execution/review obligations. Historical
result reproduction is outside that new scope. Applicability still follows the
source, domain and method contracts; a directory name supplies no scientific proof.

Individual locations are recorded in the [initial migration map](../development/v1-module-migration.json) and the completed extraction maps below. These describe source ownership; they do not replace a component's input contract.

| Boundary | Extraction and preservation record |
| --- | --- |
| Scientific authoring and shared execution constructors | [Composition](../development/v1-completion-composition-map.json) |
| Fusion and reactor science | [Fusion/reactor](../development/v1-completion-fusion-map.json) |
| Battery, matrix, quantum, cell, molecular, optical and other substrates | [Substrate extraction](../development/v1-completion-substrates-map.json) |
| Optical and inverter experiment declarations | [Glenn](../development/v1-completion-glenn-map.json), [NREL archive](../development/v1-completion-nrel-map.json) |
| Reaction–diffusion balance, assessment and complete failure census | [FiPy supplied-operand boundary](../development/v1-completion-fipy-map.json) |
| VirtualCell normalization, reduction and prediction preparation | [Response reduction](../development/v1-completion-virtual-cell-reduction.json), [prediction preparation](../development/v1-completion-virtual-cell-prediction-map.json) |
| Molecular numerical diagnostics and DIIS | [Geometry diagnostics](../development/v1-completion-geometry-diagnostics-map.json), [DIIS mathematics](../development/v1-completion-diis.json) |
| Electron-gas candidate, authoring and protocol construction | [Uniform electron gas](../development/v1-completion-ueg-map.json) |
| Source identity records and actual source access | [Source manifest boundary](../development/v1-completion-source-manifest.json) |

A mixed native module remains an effect owner; its extracted scientific implementation has the recorded new owner.
Stored schema strings remain unchanged when their implementation moves.
An adapter uses these components rather than maintaining a second scientific implementation.

## Example: conditional Rubisco assay

Run this calculation in the base environment:

```python
from empirical_lawhood.domains.rubisco.assay.core import Kinetics, GasQuery, execute_assay

kinetics = Kinetics(kcat_c=3.0, kc=10.0, kcat_o=1.0, ko=100.0)
products = execute_assay(kinetics, GasQuery(co2_um=10.0, o2_um=100.0, duration_s=1.0))
print(products.pga_per_site, products.pgly_per_site)
```

The stationary occupancy has three equal weights for these supplied inputs.
The expected products are `7/3` and `1/3`, subject to floating-point tolerance.
Concentrations are dissolved micromolar and time is seconds.
The model assumes activated sites, saturating RuBP and clamped gases.
It does not predict the kinetics of a new protein.

## Compare fixed proton positions

`domains.rubisco.rubisco_response.active_state_geometry.fixed_proton_references` accepts an unwrapped Cartesian array in ångströms, its element order, and the indices of the donor oxygen, acceptor oxygen, moving hydrogen, spectator hydrogen and spectator oxygen. For the dry KCX–RuBP diagnostic the donor–acceptor distance must lie in the inclusive interval 2.20–3.50 Å and the spectator O–H distance must be at most 1.30 Å.

The result gives the original distances and three positions for the selected nucleus, in order from donor to midpoint to acceptor. Each endpoint lies 1.00 Å from its respective oxygen. An out-of-support geometry retains its measured distances and refusal. Energies at these fixed coordinates describe a conditional electronic comparison. Proton populations and free-energy barriers require additional sampling.

## Reuse through an investigation

A helper calculation does not need an independent registry entry.
To expose a reusable operation, follow the [method declaration guide](add-method.md).
Declare its complete input/output contract, applicability and numerical requirements once.
An investigation protocol selects compatible operations and owns the scientific composition judgment.

For engine or instrument contact, follow the [domain integration guide](add-domain.md).
Keep actual effects, source access and native conversion in the adapter.
Use shared execution, custody and recovery services through their existing contracts.
Do not add a second scheduler or infer a permission from a successful calculation.

## Inspection and numerical reconstruction

Retained Rubisco analysis exports contain the original report, arrays, receipts and provenance.
Their normal reader authenticates those objects without repeating numerical analysis.
The `scientific_reconstruction: full` operational selection requests the additional independent comparison.
The reader reports that selection and refuses disagreement without replacing the original result.
Both modes retain current access checks, complete outcome censuses and closing mutation checks.

## Verification

Use [conformance and numerical purposes](../development/testing.md#verification-purpose-and-execution-profile) separately.
Contract tests exercise invalid inputs, preserved identities, complete populations and native-effect boundaries.
Numerical tests name an independent analytic, mathematical or differential reference.
Neither group grants scientific qualification or fresh experimental evidence.

## Model-free matrix suppliers

The [M0–M7 programme](model-free-matrix-programme.md) owns native matrix
acquisition in `domains.matrix.model_free`. Reusable calculations are independent
of this substrate:

| Calculation | Owner | Scope |
| --- | --- | --- |
| Observation clock, streaming finite histories, CK, conditional memory and paired segment changes | `methods.model_free.observation`, `methods.model_free.memory` | Declared chart, root population, complete within-segment denominators and finite conditioning support |
| Root-valid uncertainty and record ladder | `methods.model_free.uncertainty` | Finite bounded probabilities; bootstrap explicitly approximate |
| Random-audit residual correction and direct-SRS comparison | `methods.model_free.finite_population` | Frozen finite frame and sample; paired design covariance; revealed-frame exact moments versus actual sparse omissions |
| Finite-horizon events and paired history contrasts | `methods.model_free.events` | Complete assigned root/replica weights, shared-future contrasts, unresolved entry/path mass and failure/censor distinction |
| Known controls and optional comparisons | `methods.model_free.controls`, `methods.model_free.comparators` | Explicit observation and fitted/physical assumptions |
| Native receiver certificate, signed errors and equilibrium suppliers | `methods.model_free_response` | Joint/retained derivations, complete-root covariance, normalized importance endpoints and independent-root variance transport; physical measure and finite-sample bias remain explicit |
| Optional parameter-relation benchmark | `methods.parameter_relations` | Explicit TRAIN/CAL/CONF; distinct from the direct core |

The public `api.model_free_matrix` owner prepares new development, authenticated
confirmation and retained phase-only reanalysis through the shared recursive
services. There is no separate scheduler or compatibility dispatch layer.
