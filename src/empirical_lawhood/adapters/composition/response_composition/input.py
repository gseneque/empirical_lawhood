"response composition exposed-source qualification selection with a pre-outcome target authority stop."
from empirical_lawhood.domains.matrix.response_composition.authoring.input import ResponseCompositionInput as _science_ResponseCompositionInput

from pathlib import Path

from empirical_lawhood.adapters.composition.response_parent_custody import ResponseParentTargetAuthorityStore
from empirical_lawhood.adapters.composition.response_parent_reader import read_authenticated_parent
from empirical_lawhood.science.records.decoding import decode_canonical_bytes




def check_response_composition_input(
    config: _science_ResponseCompositionInput,
    *,
    source_root: Path | None,
    parent_manifest: Path | None,
    custody: Path | None,
    reveal_record: Path | None,
    analysis_record: Path | None,
    authority_store: ResponseParentTargetAuthorityStore | None = None,
) -> dict[str, object]:
    """Authenticate the exact scalar product before exposing it to response composition."""

    parent = read_authenticated_parent(
        route="response-composition",
        source_root=source_root,
        parent_manifest=parent_manifest,
        custody=custody,
        reveal_record=reveal_record,
        analysis_record=analysis_record,
        authority_store=authority_store,
    )
    from empirical_lawhood.domains.matrix.response_composition.authoring.scalar_parent import ResponseCompositionScalarParent

    if parent.grant.parent.source_schema != ResponseCompositionScalarParent.SCHEMA:
        raise ValueError("RESPONSE_COMPOSITION_TYPED_SCALAR_PARENT_REQUIRED")
    scalars = decode_canonical_bytes(
        parent.raw, ResponseCompositionScalarParent, maximum_bytes=8 * 1024**2
    )
    if scalars.original_root_ids != parent.custody.original_root_ids:
        raise ValueError("RESPONSE_COMPOSITION_ORIGINAL_ROOTS_MISMATCH")
    return {
        "status": "RESPONSE_COMPOSITION_AUTHENTICATED_DEVELOPMENT_INPUT_READY",
        "config_id": config.config_id,
        "evidence_role": config.evidence_role,
        "parent_sha256": parent.grant.parent.physical_sha256,
        "parent_custody_sha256": parent.custody.fingerprint(),
        "parent_custody_authenticated": True,
        "target_reveal_authorized": True,
        "target_analysis_authorized": True,
        "consumer_selected": "response_composition.development.develop_context",
        "independent_units": 32,
        "roots_per_context": 16,
        "nested_views_per_unit": 2,
        "native_tasks_executed": 0,
        "analysis_tasks_executed": 0,
        "campaign_issued": False,
        "prospective_issue_eligible": False,
    }


__all__ = ['check_response_composition_input']
