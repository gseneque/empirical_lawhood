# SPDX-License-Identifier: MPL-2.0
"""Explicit exposed structural choices for existing E4 engineering fixtures."""
from decimal import Decimal

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryTarget
from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixE4StructuralChoices
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import ScheduledFullFactorResources
from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import selected_structural_prediction
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import selected_original_factor_rule


def disclosed_structure(bank, *, budget):
    """The literal .01 is an exposed test operand, never a production default."""
    criterion = bank.forecast_design.criterion_record
    index = bank.source_index()
    source = bank.source(bank.sources[0].root_id, index=index)
    choices = MatrixE4StructuralChoices("structure.disclosed." + bank.bank_id,
        selected_original_factor_rule(criterion), source.policy.factor_numerical_design, ("PRIMARY", "FINE"),
        "COMPLETE_ORIGINAL_LATTICE_ASSOCIATIVE_LIE_FACTOR_TRANSPORT_ORIGIN_FIXED_SCALAR_CONTRAST",
        "ORIGINAL_MATCHED_GROUPS_COORDINATES_VIEWS_SECTORS_AND_TICKS_ARE_NESTED",
        disclosed_secondary_target(bank), selected_structural_prediction("prediction.disclosed." + bank.bank_id))
    resources = ScheduledFullFactorResources("structural-resources.disclosed." + bank.bank_id,
        tuple((phase, budget) for phase in ("assess", "measure", "reduce")))
    return choices, resources


def disclosed_secondary_target(bank):
    """Literal frozen E4 convention; this body alone grants no publication."""
    return MatrixE4SecondaryTarget("secondary.disclosed." + bank.forecast_design.criterion_record.fingerprint(),
        bank.forecast_design.criterion_record, Decimal(".01"),
        (Decimal(".005"), Decimal(".02"), Decimal(".05")),
        tuple(range(16, 129, 4)), Decimal(".001"))


def publish_secondary(writer, bank, directory):
    """Use the real early blind publisher, before any E4 entry or future."""
    from empirical_lawhood.api.matrix_full_factor_secondary import publish_e4_secondary_target
    target = disclosed_secondary_target(bank)
    secondary = publish_e4_secondary_target(writer=writer, directory=directory,
        target=target, bank=bank)
    return target, secondary


def published_secondary(bank, directory):
    """One actual guarded publication for shared exposed E4 worker fixtures."""
    from pathlib import Path
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.runtime.artifacts import ExternalRootContract
    directory = Path(directory)
    assert directory.is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    directory.mkdir(parents=True, exist_ok=False)
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "matrix-e4-target-disclosed", "Exposed E4 early target custody", str(directory.resolve()),
        "/media/chevre/EL", "empirical-lawhood/testing/matrix-e4-target", 1)),
        integration_artifact_profile_validators())
    assert plane.root.diagnostic().write_ready
    target, secondary = publish_secondary(plane, bank, directory / "early-target")
    return target, secondary, plane


def dense_array_operands(fixture):
    """Declared software operands, never acquired/qualified prefix observations.

    The early target is a real blind publication. Prefix states are explicit
    literal operands; later responses are computed by the existing equation
    kernel with supplied zero innovations, without any custody/native entry.
    """
    from dataclasses import replace
    from hashlib import sha256
    from pathlib import Path
    from types import SimpleNamespace

    import numpy as np

    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import expected_members
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import records, science
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as development
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays
    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import initial_parameter_state
    from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest

    plane = fixture.secondary_plane
    pauli = np.asarray(([[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]), dtype='<c16')
    frame = np.asarray([np.kron(value, np.eye(2)) / 2 for value in pauli], dtype='<c16')
    templates = dict(generic_basis=np.asarray([np.kron(np.eye(2), value) / 2 for value in pauli], dtype='<c16'),
        force_coefficients=np.stack((np.eye(3), np.eye(3))).astype('<f8') / np.sqrt(6),
        trace_coefficients=np.ones((2, 3), dtype='<f8') / np.sqrt(6),
        receiver_coefficients=np.eye(48, dtype='<f8').reshape(48, 2, 2, 3, 4))
    template_raw, members = encode_matrix_arrays(templates)
    artifact = ArtifactIdentity('array.e4-dense-equations.templates', 'disclosed-software-instrument', MATRIX_ARRAY_SCHEMA,
        sha256(template_raw).hexdigest(), 'application/x-npz', len(template_raw))
    publication = plane.write(ArtifactWriteRequest(artifact.artifact_id, 'dense-equations/templates.npz',
        MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', 'dense-equations',
        'dense-equations', template_raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    protocols = tuple(replace(protocol, templates=ScheduledResponseArrays(
        'templates.e4-dense-equations.' + protocol.public_source.root.root_id, 'TEMPLATES', protocol.public_source.source,
        artifact, members, (protocol.public_source.source,), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE))
        for protocol in fixture.bank.response_selection.protocols)
    selection = replace(fixture.bank.response_selection, protocols=protocols, template_publications=(publication,))
    selection_publication = plane.write(ArtifactWriteRequest('publication.e4-dense-equations.responses',
        'dense-equations/responses.json', selection.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json',
        'dense-equations', 'dense-equations', selection.canonical_bytes(), VisibilityCeiling.PROSPECTIVE,
        (), OutcomeAccess.OUTCOME_BLIND))
    bank = replace(fixture.bank, response_selection=selection, response_selection_publication=selection_publication)
    programme = development.SelectedE3E4DevelopmentProgramme.from_selected_bank(bank,
        programme_id='programme.e4-dense-equations.disclosed')
    evidence = replace(fixture.evidence, programme=programme.identity)
    selected = SimpleNamespace(**{**vars(fixture), 'bank': bank, 'programme': programme, 'evidence': evidence})
    # Same criterion/action/clock contract, genuinely published before operands.
    from empirical_lawhood.api.matrix_full_factor_secondary import authenticate_e4_secondary_target
    assert authenticate_e4_secondary_target(writer=plane, selection=selected.secondary_readout,
        bank=bank) == selected.secondary_target
    source = bank.source(bank.sources[0].root_id, index=bank.source_index())
    protocol = next(value for value in protocols if value.public_source.source == records.identity(source))
    panels = dict(selection.panels)[source.root.root.independent_group_id]
    coordinate = source.coordinate
    shapes = expected_members(science._prefix_coordinate(source))
    prefix = {name: np.zeros(shape, dtype=dtype) for name, (dtype, shape) in shapes.items()}
    initial = initial_parameter_state(coordinate)
    for view, multiplier in (('primary', 1), ('fine', 2)):
        count = multiplier * source.policy.cutoff_tick + 1
        phase = np.asarray([np.diag([.1, .3, .7, 1.1]) + .03 * index * np.eye(4)
            + .01 * (index + 1) * frame[index % 3] for index in range(6)], dtype='<c16').reshape(2, 3, 4, 4)
        phase += (multiplier - 1) * .002 * np.eye(4)
        prefix[view + '_positions'][:] = phase
        prefix[view + '_momenta'][:] = .01 * phase
        prefix[view + '_positions'][0] = initial.positions
        prefix[view + '_momenta'][0] = initial.momenta
        prefix[view + '_ticks'] = np.arange(count, dtype='<i8')
        prefix[view + '_alpha_tilde'] = np.asarray([coordinate.couplings(tick, refinement=multiplier)
            for tick in range(count)], dtype='<f8')
    science.validate_prefix_arrays(source, prefix)
    causal = {**prefix, 'frame': frame}
    return SimpleNamespace(f=selected, source=source, protocol=protocol, panels=panels,
        prefix_arrays=prefix, causal_arrays=causal, templates=templates, template_raw=template_raw,
        directory=Path(plane.root.contract.canonical_path))


def dense_response_arrays(source, protocol, panels, prefix_arrays, frozen_arrays):
    """All48 real128-step equation branches; no native receipt/contact claim."""
    import numpy as np

    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import native_scheduled_branch
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
    from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState

    values = {}
    for panel in panels:
        for view, count in (('primary', 128), ('fine', 256), ('bridge', 128)):
            values['noise.' + panel.panel_id + '.' + view] = np.zeros((count, 2, 3, 4, 4), dtype='<c16')
    for branch, view, panel, action, sign in branch_census(protocol, panels):
        label, multiplier = view.lower(), 1 if view == 'PRIMARY' else 2
        start = multiplier * source.policy.cutoff_tick
        state = SixMatrixState(2, prefix_arrays[label + '_positions'][-1], prefix_arrays[label + '_momenta'][-1],
            start, *source.coordinate.couplings(start, refinement=multiplier))
        branch_values = native_scheduled_branch(state, coordinate=source.coordinate, refinement=multiplier,
            direction=frozen_arrays['forces'][protocol.actions.index(action)],
            amplitude=0 if sign == 'HOLD' else float(action.amplitude) * (1 if sign == 'PLUS' else -1),
            pulse_steps=multiplier * action.pulse_steps,
            innovations=values['noise.' + panel.panel_id + '.' + label])
        values.update({'branch.' + branch + '.' + name: value for name, value in branch_values.items()})
    return dict(sorted(values.items()))


def unentered_dense_functional_rows(bank, case, score, *, dense_score, target, secondary):
    """Explicit absent-account projection for disclosed unentered test seams."""
    from dataclasses import replace
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_secondary_readout import dense_e4_functional_rows
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import prediction_case
    assert score is dense_score is case.forecast is None
    row = dense_e4_functional_rows(bank, case, score, dense_score=dense_score, target=target, secondary=secondary)
    return replace(row, prediction=prediction_case(bank, case, row, None))
