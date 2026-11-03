# SPDX-License-Identifier: MPL-2.0
"""Bind actual original E3 metadata without decoding a TRAIN bank.

This byte-custody and domain projection seam does not establish current source
qualification, original chronology, candidate eligibility, issue or authority.
Those checks compose at the owning public/current-task entry before TRAIN.
"""

from decimal import Decimal

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseErrorSpecification
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import ProtectedE3SourceInputs, project_protected_e3_allocation
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_original_publications import ProtectedE3OriginalPublications, authenticate_protected_e3_fit_originals
from empirical_lawhood.kernel.experimental_design import UnitAllocation


def bind_protected_e3_original_inputs(plane, originals, *, specification, allocation, publications, fit_cutoff):
    """Authenticate exact locators, then bind the actual selected domain projection."""
    if (type(originals) is not ProtectedE3OriginalPublications or type(specification) is not MatrixResponseErrorSpecification
            or type(allocation) is not UnitAllocation):
        raise TypeError("protected E3 original binding requires its actual fit/specification/allocation records")
    specification.__post_init__()
    allocation.__post_init__()
    if specification.identity != originals.specification:
        raise ValueError("protected E3 original binding changes actual selected specification/allocation")
    manifest, training = authenticate_protected_e3_fit_originals(plane, originals,
        specification=specification.identity, allocation=allocation.identity, source_manifest=originals.source_manifest,
        training_allocation=originals.training_allocation, publications=publications, fit_cutoff=fit_cutoff)
    by_temperature = {row.primary_view.bath_temperature: row for row in manifest.reservation.allocation.coordinates}
    inputs = ProtectedE3SourceInputs(specification, training, manifest.reservation, manifest.native_specification,
        by_temperature[Decimal(1)], by_temperature[Decimal("1.25")], by_temperature[Decimal(3)])
    if project_protected_e3_allocation(inputs) != allocation:
        raise ValueError("protected E3 original binding substitutes its complete selected role projection")
    return inputs, manifest
