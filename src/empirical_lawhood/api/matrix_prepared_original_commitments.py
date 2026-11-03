# SPDX-License-Identifier: MPL-2.0
"""Original TRAIN/E4 prerequisite replay before selected prepared acquisition.

The same actual source/receipt owners serve derivation, public authoring and
cold parent entry. No pass flag, exclusion inventory or authority is retained.
"""
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import (
    require_original_commitments, validate_original_prepared_scope,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_opportunity import (
    MatrixSelectedOpportunityProgramme, public_programme,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import (
    MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme,
)


def authenticate_prepared_original_commitments(*, writer, programme, evidence, source_scan_bytes,current_access=None):
    """Authenticate exact originals and return facts for this boundary only."""
    commitments = require_original_commitments(getattr(evidence, "original_commitments", None))
    # Static protocol discovery must not load runtime owners or generated
    # executable bindings while their aggregates are being regenerated.
    from .matrix_prepared_source_runtime import _native_training_prerequisite, _committed_e4_selections, _e4_phases, _prepared_phases, _require_original_e4_scope, _future_source_selections
    evidence.__post_init__()
    if type(programme) is MatrixSelectedOpportunityProgramme:
        programme = public_programme(programme)
    elif type(programme) is MatrixSelectedProtectedProgramme:
        programme = MatrixSelectedPublicProgramme.from_programme(programme)
    programme.__post_init__()
    if source_scan_bytes is not None and (type(source_scan_bytes) is not int or source_scan_bytes < 1):
        raise ValueError("prepared original custody requires the actual current source byte ceiling")
    maximum = commitments.maximum_source_bytes if source_scan_bytes is None else min(commitments.maximum_source_bytes, source_scan_bytes)
    specification, request, _, future = _native_training_prerequisite(writer, commitments.native_training_locator)
    with _committed_e4_selections(writer, commitments.input_commitments, request,
            maximum_source_bytes=maximum, native_training_locator=commitments.native_training_locator) as inputs:
        _require_original_e4_scope(writer, inputs, programme, evidence,
            training_specification=specification, training_request=request,current_access=current_access)
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import (
            validate_committed_prepared_sources, validate_committed_prepared_panels,
        )
        phases = _prepared_phases(inputs)
        validate_committed_prepared_sources(phase=programme.phase, sources=programme.sources,
            phases=phases, producing_provenance=inputs.producing_provenance)
        validate_committed_prepared_panels(phase=programme.phase, assay=programme.assay,
            panels=programme.panels, selections=tuple((role, selected.responses) for role, selected in phases))
        validate_original_prepared_scope(phase=programme.phase, sources=programme.sources,
            assay=programme.assay, panels=programme.panels, request=request, future_selections=_future_source_selections(inputs),
            e4_phases=_e4_phases(inputs))
    return request, future


def prepare_selected_commitment_authoring(preparation, *, project_root, artifact_writer, output_dir):
    """Existing public lifecycle hook; validate before authoring effects."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import (
        MatrixSelectedOpportunityEvidenceV2, MatrixSelectedEntryEvidenceV3, MatrixRevisionEntryEvidenceV2,
    )
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionPreparedProgramme
    records = tuple(value for _, value in preparation.design_records)
    programmes = tuple(value for value in records if type(value) in (
        MatrixSelectedOpportunityProgramme, MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme,
        MatrixRevisionPreparedProgramme))
    if not programmes:
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_opportunity import MatrixSelectedOpportunityPublicProgramme
        programmes = tuple(value for value in records if type(value) is MatrixSelectedOpportunityPublicProgramme)
    evidence = tuple(value for value in records if type(value) in (
        MatrixSelectedOpportunityEvidenceV2, MatrixSelectedEntryEvidenceV3, MatrixRevisionEntryEvidenceV2))
    if len(programmes) != 1 or len(evidence) != 1:
        require_original_commitments(None)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as opportunity
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as protected, selected_revision_bindings as revision
    keys = {opportunity.COMMITTED_DESIGN_KEY,
        protected.ENTRY_ORIGINAL_COMMITMENTS_KEY, protected.ENTRY_TRANSPORT_KEY,
        revision.capability_key("entry", "DEVELOPMENT", "2.0.0"),
        revision.capability_key("entry", "PROTECTED", "2.0.0")}
    operations = tuple(value for value in preparation.draft.operations
        if value.node_id in preparation.draft.selected_operation_ids
        and value.selection.capability_key in keys)
    if len(operations) != 1:
        raise PermissionError("prepared authoring requires one actual selected original entry/design source budget")
    authenticate_prepared_original_commitments(writer=artifact_writer, programme=programmes[0], evidence=evidence[0],
        source_scan_bytes=operations[0].resource_budget.source_scan_bytes)
    return preparation
