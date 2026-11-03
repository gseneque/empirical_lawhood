# SPDX-License-Identifier: MPL-2.0
"""Pure E4 banks from the settled original programme inputs.

No seed material, allocation reconstruction, publication or source authority is
introduced here. Each bank retains C's original matched population and assay.
"""
from dataclasses import dataclass

from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import (
    SelectedE3E4DevelopmentBank, SelectedE3E4DevelopmentProgramme, SelectedE3E4ForecastDesign,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import (
    SelectedE4PhaseBank, SelectedE4PhaseProgramme, validate_phase_separation,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex

from .input_records import ResolvedMatrixProgrammeInputs, validate_programme_input_records


PHASE_ROLES = (("DEVELOPMENT", "e4.development"), ("CALIBRATION", "e4.calibration"),
    ("CONFIRMATION", "e4.confirmation"))


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE4Banks:
    """Transient current composition, never another canonical input index."""
    inputs: ResolvedMatrixProgrammeInputs
    original_e3: ConfiguredMatrixSelectedPublicPackage
    banks: tuple
    programmes: tuple


def compose_programme_e4_banks(inputs, *, original_e3, criterion_publication):
    """Join all original roles before resolving the three complete E4 banks."""
    validate_programme_input_records(inputs)
    if type(original_e3) is not ConfiguredMatrixSelectedPublicPackage:
        raise TypeError("programme E4 requires its exact current original E3 public package")
    original_e3.__post_init__()
    design, original = inputs.scientific_design, inputs.commitments
    if original_e3.specification != design.e3:
        raise ValueError("programme E4 substitutes the original E3 scientific specification")
    phases = tuple(inputs.phase(role) for _, role in PHASE_ROLES)
    parent = phases[0]
    if any((value.reservation, value.native_specification) != (parent.reservation, parent.native_specification)
            for value in phases[1:]):
        raise ValueError("programme E4 phases require the same original matched reservation and native specification")
    index = ScheduledSourceIndex.from_shared(reservation=parent.reservation,
        specification=parent.native_specification, provenances=(inputs.producing_provenance,))
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import selected_e3_fit_target
    namespace = original.namespace + ".e4"
    forecast = SelectedE3E4ForecastDesign("forecast-design." + namespace, original_e3,
        scheduled.identity(parent.reservation.allocation), design.training_protocol.mathematical_protocol,
        criterion_publication, fit_target=selected_e3_fit_target(original_e3))
    banks, programmes = [], []
    for (phase, role), selected in zip(PHASE_ROLES, phases, strict=True):
        references = []
        for protocol in selected.responses.protocols:
            public = protocol.public_source
            reference = index.reference(source_id=public.source.object_id, root_id=public.root.root_id,
                provenance=inputs.producing_provenance.identity)
            public.validate_source(index.resolve(reference))
            references.append(reference)
        references = tuple(sorted(references, key=lambda value: value.root_id))
        values = ("bank." + namespace + "." + phase.lower(), parent.reservation,
            parent.native_specification, (inputs.producing_provenance,), references,
            inputs.exposure_audit, original.exposure_audit.publication, forecast, selected.responses,
            original.phase(role).responses.publication, getattr(design, role.replace(".", "_")))
        if phase == "DEVELOPMENT":
            bank = SelectedE3E4DevelopmentBank(*values)
            programme = SelectedE3E4DevelopmentProgramme.from_selected_bank(bank,
                programme_id="programme." + namespace + "." + phase.lower())
        else:
            bank = SelectedE4PhaseBank(*values, phase)
            programme = SelectedE4PhaseProgramme.from_bank(bank,
                programme_id="programme." + namespace + "." + phase.lower())
            validate_phase_separation(programmes[0][1], programme)
        banks.append((phase, bank))
        programmes.append((phase, programme))
    return MatrixProgrammeE4Banks(inputs, original_e3, tuple(banks), tuple(programmes))
