# SPDX-License-Identifier: MPL-2.0
"""Portable current-use contributions through the existing custody and inquiry APIs."""

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.recursive_inquiry import InquiryEvidenceBinding
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import validate_unchanged_sources
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.operation_bindings import MAX_INPUT_BYTES, NAMESPACE
from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import selected_configs
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import scientific_scope
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import ResponseAssessment, ResponsePredictions, assess_response_study


def inquiry_record_identity(record):
    kinds = {ResponsePredictions: "prediction_id", ResponseAssessment: "assessment_id", RubiscoResponseStudy: "study_id"}
    field = kinds.get(type(record))
    if field is None:
        raise ValueError("response inquiry received an undeclared scientific product type")
    exact(record, type(record))
    return ObjectIdentity.from_record(getattr(record, field), record)


def actual_products(draft, products):
    configs = selected_configs(draft)
    records, entries = {}, []
    for phase, kind, role in (("predict", ResponsePredictions, ContributionRole.INSTANCE_PRODUCT),
            ("assess", ResponseAssessment, ContributionRole.RETAINED_ANALYSIS_INPUT)):
        task_id = f"{NAMESPACE}.{phase}"
        found = tuple(row for row in products["records"].get(task_id, {}).values() if type(row) is kind)
        if not found or task_id not in products["receipts"]:
            return configs, None, ()
        if len(found) != 1:
            raise ValueError("response contribution repeats an actual scientific product")
        record, = found
        receipt = products["receipts"][task_id]
        if receipt.task_id != task_id or receipt.operational_status is not OperationalStatus.SUCCEEDED:
            raise ValueError("response contribution substitutes original producer custody")
        logicals = tuple(row for row in receipt.output_logical_artifacts
                         if row.payload_schema == record.SCHEMA and row.content_sha256 == record.fingerprint())
        if len(logicals) != 1 or logicals[0].logical_artifact_id not in products["outputs"]:
            raise ValueError("response contribution lacks its exact producing receipt output")
        logical = logicals[0]
        artifact = products["outputs"][logical.logical_artifact_id]
        physical = artifact.materialization
        if (artifact.logical != logical or physical not in receipt.output_materializations
                or physical.physical_sha256 != record.fingerprint()
                or physical.size_bytes != len(record.canonical_bytes()) or physical.compression != "none"):
            raise ValueError("response contribution changes complete retained output bytes")
        records[phase] = record
        entries.append(ContributionProduct("product." + task_id, inquiry_record_identity(record),
            ArtifactIdentity(logical.logical_artifact_id, "conditional-response-" + phase, record.SCHEMA,
                record.fingerprint(), logical.media_type, physical.size_bytes),
            ObjectIdentity.from_record(receipt.receipt_id, receipt), role, EvidenceCeiling.NON_PROMOTABLE,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
    config = configs["assess"]
    expected = assess_response_study(config.science, records["predict"],
        assessment_id=records["assess"].assessment_id, permitted_refinement_id=config.permitted_refinement_id)
    if records["assess"] != expected:
        raise ValueError("response contribution fails independent retained-product assessment")
    return configs, records, tuple(sorted(entries, key=lambda row: row.product_id))


def describe_response_contributions(draft, products):
    configs, records, entries = actual_products(draft, products)
    if records is None:
        return ()
    result = records["assess"]
    remaining = tuple(row for row in result.graph.requirements if row.requirement_id in result.remaining_requirement_ids)
    manifest = ContributionManifest("contribution.rubisco-response." + result.fingerprint()[:24],
        draft.question, "Conditional candidate action " + result.conditional_candidate_action
        + "; combined milestone OPEN; biological predictive calibration NOT_ESTABLISHED.",
        scientific_scope(configs["assess"].science), entries, (inquiry_record_identity(result),), remaining,
        tuple(ObjectIdentity.from_record(row.contribution_id, row) for row in draft.contribution_parents))
    return (manifest,)


def next_wave_builder(draft, manifest, products):
    if describe_response_contributions(draft, products) != (manifest,):
        raise ValueError("response successor changes the exact current retained contribution")
    # A scientific remaining requirement does not commission a native successor.
    return None


def inquiry_endpoint_validator(draft, endpoint):
    config = selected_configs(draft)["assess"]
    if endpoint != scientific_scope(config.science):
        raise ValueError("response inquiry changes its exact selected scientific scope")


def inquiry_outcome_projector(draft, specification, products):
    inquiry_endpoint_validator(draft, specification.endpoint)
    selected = next(row for row in draft.operations if row.node_id == f"{NAMESPACE}.assess")
    if specification.distinguishing_assessment != selected.config_identity:
        raise ValueError("response inquiry changes the designated independent assessor")
    _, records, _ = actual_products(draft, products)
    return "unresolved" if records is None or records["assess"].conditional_candidate_action == "HOLD" else "useful-supply"


def inquiry_evidence_projector(draft, payloads, products=None):
    config = selected_configs(draft)["assess"]
    external, = draft.external_inputs
    name = "external-" + sha256(external.input_id.encode()).hexdigest()[:24] + ".json"
    original = decode_canonical_bytes(payloads[name], RubiscoResponseStudy, maximum_bytes=MAX_INPUT_BYTES)
    if original.identity != config.original_study or external.expected_content_sha256 != original.fingerprint():
        raise ValueError("response inquiry substitutes original input evidence")
    validate_unchanged_sources(original, config.science)
    views = draft.development_study.numerical_view_ids
    bindings = [InquiryEvidenceBinding(external.input_id, original.fingerprint(), scientific_scope(original),
        ContributionRole.RETAINED_ANALYSIS_INPUT, (), views)]
    if products is not None:
        _, records, _ = actual_products(draft, products)
        if records is not None:
            for phase, record in records.items():
                bindings.append(InquiryEvidenceBinding(f"{NAMESPACE}.{phase}.product", record.fingerprint(),
                    replace(scientific_scope(config.science), receiver_id=f"{NAMESPACE}.{phase}"),
                    ContributionRole.INSTANCE_PRODUCT if phase == "predict" else ContributionRole.RETAINED_ANALYSIS_INPUT,
                    (), views))
    return tuple(sorted(bindings, key=lambda row: row.binding_id))
