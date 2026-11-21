# Independent periodic numerical controls

SPDX-License-Identifier: CC-BY-4.0

This route measures prospectively selected energy differences and numerical
refinements of the [complete periodic operator](periodic-force-probe.md).
Every point retains the original assembly, atom order, topology, cell and
catalytic partition. The points are numerical views of one assembly. They
supply no independent biological replicates or physical rate observations.

Use `prepare_periodic_numerical_controls`, `author_periodic_numerical_controls`
and `read_periodic_numerical_controls` from
`empirical_lawhood.api.domain_composition.rubisco_response.periodic_controls`.
Preparation accepts an existing periodic probe selection and its exact original
binary64 coordinate bytes. Select the derivative directions, at least two
distinct decreasing steps in PySCF Bohr when directions are present, numerical
refinements and their sensitivity budgets before observing the new returns.
The mandatory `required_refinement_kinds` argument is an explicitly authored
sorted tuple; a required kind without a selected refinement refuses before
native entry. An empty tuple limits the selection's coverage and does not
establish that omitted numerical questions are irrelevant. Preparation derives
the complete point census.

`PeriodicDerivativeDirection` selects either one physical Cartesian component
or a deterministic vector with a sign for every physical Cartesian component.
The complete sign vector is derived from its declared SHAKE-256 seed and is
unnormalized: each component moves by the selected step. A directional check
does not establish the accuracy of every separate gradient component. Retain
the identities of selected QM, MM and boundary atoms when interpreting coverage.
Repeated physical directions, duplicate or unrepresentable displacements and
changed original coordinate bytes refuse before native entry.

`PeriodicNumericalRefinement` changes one declared resolution question: SCF
tolerances, DFT grid, basis, periodic electronic Ewald parameters, direct
embedding radius, or molecular Ewald tolerance. It preserves the other selected
settings and refuses coarsened choices. Basis refinement currently supports the
declared def2-SVPD to def2-TZVPD comparison. This numerical comparison cannot
establish functional accuracy, protonation, Mg-water occupancy or chemical-model
adequacy.

## Prospective refinement budgets

Each `PeriodicNumericalRefinement` requires a typed `PeriodicRefinementBudget`.
Its required `maximum_gradient_component_change_hartree_per_bohr` is a bound
on the **largest absolute Cartesian component difference** across all physical
atoms, in Hartree/Bohr. A nonempty `justification` states why that sensitivity
allowance is adequate for this receiver and use. Optional
`maximum_rms_gradient_component_change_hartree_per_bohr` applies to the RMS of
all 3N components; it is not a per-atom-vector norm. Optional
`maximum_absolute_energy_change_hartree` bounds the magnitude of the signed
energy difference. All tolerances are positive finite authored values; there
is no universal numerical-accuracy default.

For one fixed receiver vector `r`, the observed sensitivity obeys
`abs(r dot delta_gradient) <= L1(r) * max_abs_component(delta_gradient)`.
The public `prepare_receiver_refinement_budget` helper derives the component
allowance as useful receiver error times its numerical allocation fraction,
divided by the receiver L1 norm. It records the actual receiver identity and
all three operands. Supply the L1 norm of the **frozen physical receiver**;
unit Euclidean normalization does not make that norm equal to one.

For example, the following composes one new grid-sensitivity question from an
existing authored design, its fixed primary receiver and a matching probe.
`design`, `frame`, `prototype` and `coordinate_bytes` are already authenticated
scientific inputs. This example checks one projected-force difference; it does
not select the full M50 numerical-control portfolio.

```python
from dataclasses import replace
from decimal import Decimal, ROUND_CEILING, localcontext

from empirical_lawhood.api.domain_composition.rubisco_response.periodic_controls import (
    prepare_receiver_refinement_budget,
    prepare_periodic_numerical_controls,
)
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import (
    PeriodicNumericalRefinement,
)

# Round the positive norm upward so its finite decimal representation cannot
# allocate a larger component allowance than the exact coefficient sum.
with localcontext() as context:
    context.prec = 80
    context.rounding = ROUND_CEILING
    receiver_l1 = sum(
        (coefficient.copy_abs() for _, _, coefficient in frame.primary.components),
        Decimal(0),
    )

budget = prepare_receiver_refinement_budget(
    budget_id="budget.grid.fixed-receiver",
    receiver=frame.primary.identity,
    useful_error_hartree_per_bohr=design.useful_error_hartree_per_bohr,
    numerical_allowance_fraction=design.numerical_allowance_fraction,
    receiver_l1_norm=receiver_l1,
    justification="Authored allocation for one same-geometry receiver-force refinement.",
)
refinement = PeriodicNumericalRefinement(
    "refinement.grid", "GRID",
    replace(prototype.electronic, grid_level=prototype.electronic.grid_level + 1),
    prototype.molecular, budget,
)
protocol, points = prepare_periodic_numerical_controls(
    prototype=prototype,
    coordinate_bytes=coordinate_bytes,
    refinements=(refinement,),
    required_refinement_kinds=("GRID",),
)
```

Check that the selected backend supports the tighter grid. An unsupported
choice refuses selection or execution; it does not trigger a different method.
For a Hessian action or finite-response residual, propagate the uncertainty of
every participating force through the displacement denominators and challenge
amplitude before assigning the allowance. The helper above does not do that
multi-operand calculation. An observed refinement difference is empirical
sensitivity, not a bound on unknown exact-force error. See the
[Rubisco remediation and standards audit](../../../../../docs/release/rubisco-molecular-remediation.md)
for the derivation, norm distinctions and pending physical acceptance.

New refinement, numerical-control, force-action protocol and readout contracts
use their revised canonical versions. Old unbudgeted refinement payloads are
rejected; no compatibility conversion supplies criteria after observing a
result. The original twenty WT control returns had no prospective refinement budget.
Their reported grid/direct-embedding differences remain observations under their original
selection. Author fresh controls and budgets on the remediated construction. [Molecular diagnostic report and refinement criteria](../../../../../docs/release/rubisco-molecular-remediation.md#6-new-prospective-numerical-refinement-admission)

Authoring authenticates the complete original Amber sources and rederives every
point. Supply a fresh work directory, artifact writer and authoring destination.
It returns the ordinary recursive handoff and direct-input paths. Execute that
handoff through the existing shared lifecycle. The graph contains one ordinary
task per point, each with the same resource lock and one attempt. Shared large
inputs are streamed once. CPU tasks use the existing eight-CPU, 8-GiB allocation.
Accelerated tasks use the selected engine's host-memory allocation and one GPU.
Neither route adds an experiment deadline. The execution plan retains every selected point;
dropping one from the selected graph refuses compilation.

Each native call retains its complete numerical inputs, actual coordinate
array, diagnostics, raw energy and gradient before interpretation. Known failures
remain failures. Completed recovery returns original evidence without a new
call. An uncertain contact cannot be replayed automatically.

For a successful raw return with interrupted publication, use `recover_periodic_control_publication` from the same public API.
Supply its original configuration, definition and guarded native-subwork store after the worker has stopped.
The recovery authenticates the full received archive, every member and both original control records.
It reconstructs missing publication metadata from these bytes and publishes the original native receipt without another calculation.
The original publication failure remains retained.
Call-wide time and peak memory remain unknown when publication failed before those observations were saved.
After this repair, use `api.recursive_execution.finalize_returned_recursive_tasks`
with the original authored directory, custody writer, frozen worker interpreter
and source root, plus the current controller checkout. It publishes the ordinary
parent receipt without entering any unfinished point. Then use the independent
reader and resume remaining acquisition through the original admitted lifecycle.

The CUDA-MM accelerated baseline also retains complete CUDA and Reference MM energies
and forces at the selected geometry. The Reference comparison uses the original
binary64 parameters and the actual CUDA PME allocation. This comparison includes
parameter-storage and platform-arithmetic differences. It does not isolate
parameter rounding or establish chemical-model adequacy. The CPU control repeats
no electronic SCF. Its separate timing remains in the original archive, and the
baseline task cost includes this control. The GPU complete-force timing retains
its original, narrower interval.

Use `read_periodic_molecular_precision` from the same public API to authenticate
and compare these original operands. It reports energy, maximum force-component
and RMS force-component differences without an invented acceptance threshold.
Its `COMPARED` status is not a platform-accuracy pass. Author the platform
comparison's own error budget before collecting new results for scientific use;
the periodic refinement aggregate does not automatically cover this diagnostic.
Historical returns without these operands cannot supply this comparison.
The separate GPU-electronic/Reference-MM selection uses binary64 molecular parameters directly.
Its baseline does not repeat this CUDA comparison or infer a missing historical comparison.
Preserve an earlier CUDA discrepancy with its original inputs and producing environment.

The independent reader accepts the complete original configuration tuple, model,
coordinate bytes, available original results, and a function returning each
result's original native-subwork store. It authenticates definitions, requests,
receipts, complete archives and raw arrays. For successful calls, it compares
the archived coordinates and numerical input files with the declared point.
It independently reconstructs `geometry_quality` from authenticated
`original.prmtop` and `coordinate-array.npy`, using the prospective
`PeriodicMMSettings.geometry_quality` policy and explicit wholly-QM bonded
exemptions. A producer's geometry verdict is not trusted as the independent
result. Successful archives that omit these required operands refuse reading;
failed/missing or unsupported geometry remains unevaluable. Force operands
with a rejected or unevaluable screen do not enter directional or refinement
comparisons. `SCREEN_PASSED` establishes the declared gross geometry screen,
not MolProbity, chemical-state, ensemble or kinetic admission.
Missing completed results remain visible in the full point denominator; the
reader does not infer their contact state. Use existing contact inspection to
distinguish a point that was never entered from an uncertain contact.

The directional calculation compares independently retained energy differences
with the original baseline gradient projected onto the actual coordinate
secant. It uses the exact PySCF conversion, 0.52917721092 angstrom per Bohr, and
retains displacement rounding through that secant. The report includes each
error, the change between successive step sizes, midpoint shift and the
binary64 energy-rounding contribution. That last quantity does not bound SCF
error or physical-model error.

Supply both prospective absolute error and step-change tolerances to obtain a
directional assessment. Without those selections, the report gives comparisons
and an unevaluable directional disposition. Missing or failed operands cannot
satisfy a criterion. An observed violation remains falsified even when another
point is missing. Refinements retain signed energy changes, maximum component
changes and RMS component changes over the complete physical gradient, together
with the original typed budget and its disposition. The reader rejects a
substituted budget or changed point. Comparison with an energy tolerance uses
the absolute energy difference, including a negative signed change.

The readout keeps three propositions separate:

| Field | Meaning |
| --- | --- |
| `directional_disposition` | The selected derivative and step-change criteria; software/derivative conformance only. |
| `refinement_disposition` | Every selected numerical refinement meets its prospective sensitivity budget; no selected refinements leaves this unevaluable. |
| `numerical_disposition` | Every selected directional and refinement criterion is satisfied. A selected failure makes it falsified; missing/failed required operands prevent satisfaction. |

A passing directional comparison cannot conceal a failed or missing selected
refinement. A violated maximum component cannot be diluted by a small RMS over
the rest of the enzyme. The combined result covers only the selected numerical
questions; all chemical, ensemble, physical-rate and forecast requirements
remain separate. M50 continues to expose unavailable native force uncertainty
instead of interpreting these empirical controls as a rigorous error enclosure.

Measured costs remain attached to every original point, including known failed
calls. Preserve the complete attempted denominator when estimating a sampling
tranche. Repeated numerical directions and refinements are not extra independent
units, and execution time is not molecular time.
