# SPDX-License-Identifier: MPL-2.0
"""Read structural product observations and reduce explicitly assigned tagged-gas trials."""

from collections.abc import Mapping
from dataclasses import asdict

from empirical_lawhood.domains.rubisco.rubisco_response.val1_flux import (
    TaggedGasFluxMeasure, TaggedGasFluxTrial, rate_interval,
)


def read_oxygen_bound_products(*, original_pdf: bytes, extracted_text: bytes) -> dict:
    """Classify all original oxygen-path geometries after verifying their atom order and source tokens."""
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.bound_products import bound_products
    from empirical_lawhood.domains.rubisco.rubisco_response.oxygen_encounter import oxygen_source_roles
    from empirical_lawhood.domains.rubisco.rubisco_response.oxygen_source_geometry import prepare_oxygen_source_projection

    projection = prepare_oxygen_source_projection(original_pdf_bytes=original_pdf, extracted_text_bytes=extracted_text)
    anchors, gas_ordinals = oxygen_source_roles(projection)
    backbone = tuple(i - 1 for i in anchors[:2])
    gas = tuple(i - 1 for i in gas_ordinals)
    phosphorus = tuple(i for i, atom in enumerate(projection.geometries[0].atoms) if atom.element == "P")
    rows = []
    for state in projection.geometries:
        elements = tuple(atom.element for atom in state.atoms)
        coordinates = np.array([atom.coordinate_tokens for atom in state.atoms], dtype=float)
        product = bound_products(elements, coordinates, phosphorus, gas, backbone, singlet=True)
        rows.append(dict(ordinal=state.ordinal, state=state.native_state_label, path=state.native_pathway, product=product))
    return dict(original_pdf_sha256=projection.original_pdf_sha256, extracted_text_sha256=projection.extracted_text_sha256,
                source_ordinals=dict(gas=gas_ordinals, backbone=anchors[:2], phosphorus=tuple(i + 1 for i in phosphorus)),
                oxygen=rows, scope="Bound structural products under the singlet geometry criterion in the original oxygen paths.")


def assess_tagged_flux_panel(*, assigned_ids: tuple[str, ...], trials: Mapping[str, TaggedGasFluxTrial | None],
                             measure: TaggedGasFluxMeasure) -> dict:
    """Calculate finite-panel bounds for one selected host, bath and Hamiltonian in natural units."""
    if not isinstance(measure, TaggedGasFluxMeasure):
        raise TypeError("select the physical crossing surface and solvent bath")
    if (not isinstance(trials, Mapping) or type(assigned_ids) is not tuple or not assigned_ids
            or any(type(i) is not str or not i.strip() for i in assigned_ids)
            or len(set(assigned_ids)) != len(assigned_ids) or set(trials) != set(assigned_ids)):
        raise ValueError("every assigned tagged-gas draw needs one named observation or explicit nonentry")
    if any(row is not None and not isinstance(row, Mapping) for row in trials.values()):
        raise TypeError("supply each tagged-gas observation as a mapping or explicit nonentry")
    rows = [trials[i] if trials[i] is not None else {} for i in assigned_ids]
    return dict(assigned_ids=assigned_ids, measure={k: str(v) for k, v in asdict(measure).items()},
                nonentered_ids=tuple(i for i in assigned_ids if trials[i] is None), interval=rate_interval(rows, measure=measure),
                scope="Realized nested draws conditional on a single source preparation, bath and Hamiltonian.")
