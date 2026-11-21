# SPDX-License-Identifier: MPL-2.0
"""Public authoring composition and current retained finite-opportunity findings."""

from pathlib import Path

from empirical_lawhood.methods.assigned_opportunity_assessment import bindings, design
from empirical_lawhood.methods.assigned_opportunity_assessment.records import MAX_BYTES, OpportunityAuthorInput, OpportunityOutcomes
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


def author_assigned_opportunity_wave(*, actor_path, outcomes_path, project_root, artifact_writer, output_directory):
    """Use the ordinary source-admitted authoring and guarded input-copy owner."""
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave

    actor = decode_canonical_bytes(read_bounded_bytes(Path(actor_path), maximum_bytes=MAX_BYTES),
                                   OpportunityAuthorInput, maximum_bytes=MAX_BYTES)
    outcomes = decode_canonical_bytes(read_bounded_bytes(Path(outcomes_path), maximum_bytes=MAX_BYTES),
                                      OpportunityOutcomes, maximum_bytes=MAX_BYTES)
    draft, sources = design.lower(actor, outcomes)
    paths = {actor.record_id: Path(actor_path), outcomes.record_id: Path(outcomes_path)}
    return author_recursive_wave(draft=draft, project_root=project_root, artifact_writer=artifact_writer,
        output_dir=output_directory, input_bindings=tuple((key, paths[value.record_id]) for key, value in sources))


def read_assigned_opportunity_result(*, directory, artifact_writer, allow_partial=False):
    """Authenticate current custody; validate the bounded original mathematical result."""
    from empirical_lawhood.api.recursive_execution import read_recursive_wave

    report, products, draft, _ = read_recursive_wave(directory=directory, artifact_writer=artifact_writer,
        include_products=True, allow_partial=allow_partial,
        terminal_product_format="compact" if allow_partial else "documents")
    config, _ = bindings.config_from_draft(draft)
    base = {"run_id": report["run_id"], "assigned_opportunities": len(config.source.opportunity_ids),
        "independent_units": len(config.assessment.allocation.units), "nested_views_per_opportunity": len(config.source.numerical_view_ids),
        "source": config.source.identity.to_document(), "assessment_contract": config.assessment.identity.to_document(),
        "qualification": "NOT_ESTABLISHED", "evidence_scope": "EXPOSED_DEPENDENT_SOFTWARE_FIXTURE",
        "inference_scope": "DETERMINISTIC_FINITE_ASSIGNED_CENSUS_CONDITIONAL_ON_OUTCOME_BOUNDS",
        "native_acquisition_performed": False, "current_access": "CHECKED_BY_ORDINARY_RETAINED_READER"}
    if allow_partial:
        return {**base, "scientific_completion": "DEFERRED", "operational_status": report["status"],
                "operational_census": report["operational_census"],
                "reason_codes": ("ASSESSMENT_DECODE_DEFERRED",)}
    record = bindings.authenticated_assessment(draft, products)
    if record is None:
        return {**base, "scientific_completion": "INCOMPLETE", "claim_disposition": "UNEVALUABLE",
                "lower_ratio": None, "upper_ratio": None, "reason_codes": ("ORIGINAL_ASSESSMENT_UNAVAILABLE",)}
    requirement, connection = design.scientific_contract(config.source)
    phases = bindings.assessment_projector(record, requirement, connection)
    return {**base, "scientific_completion": "COMPLETED", "claim_disposition": record.disposition,
        "lower_ratio": record.lower_ratio, "upper_ratio": record.upper_ratio,
        "threshold": str(record.procedure.parameters[0].value), "reason_codes": record.reason_codes,
        "assessment": record.identity.to_document(), "procedure": record.procedure.identity.to_document(),
        "status_axes": {row.phase.value: row.disposition.value for row in phases},
        "opportunities": tuple({"opportunity_id": row.opportunity_id, "status": row.status,
            "dependence_root": row.dependence_root.to_document(), "independent_unit_id": row.independent_unit_id,
            "views": tuple(v.to_document() for v in row.views)} for row in record.outcomes.rows)}
