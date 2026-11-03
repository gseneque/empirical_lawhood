# SPDX-License-Identifier: MPL-2.0
"""Read an actual complete E4 decision into existing E5 revision input records.

The returned records are locators and exact public coefficients, not cached
custody or admission. E5 derivation and worker entry replay original grants and
producer custody independently. This operation publishes and executes nothing.
"""
from dataclasses import replace
from functools import partial
from pathlib import Path


def derive_selected_e4_revision_request(*, service, directory, programme_request_path, specification, request):
    """Fill a declared DEV request from the actual complete E4 REVISION decision.

    Select science and original physical inputs explicitly, with both revision
    fields empty. This read derives their exact package and producer locators;
    ordinary declarative derivation reauthenticates them and derives exclusions.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_prepared_choices as scientific_choices
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as domain
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as preparation
    from empirical_lawhood.api.results import CampaignStatusRequest
    from empirical_lawhood.api.selected_e4_programme_service import SelectedE4ProgrammeService, _codecs, _locator
    from empirical_lawhood.api.selected_e4_native_read import _read_selected_e4_component, read_selected_e4_programme

    if (type(specification) is not scientific_choices.SelectedPreparedDevelopmentSpecification
            or specification.account != "REVISION" or specification.phase != "E5_OPPORTUNITY"):
        raise TypeError("selected E4 export requires an exact declarative revision DEV specification")
    specification.__post_init__()
    if type(request) is not domain.SelectedPreparedDerivationRequestV2:
        raise TypeError("selected E4 export requires its explicit declarative request")
    request.__post_init__()
    if (request.revision is not None or request.revision_evidence is not None
            or request.original_e3 is not None or request.original_e3_products
            or request.original_e3_source is not None or request.original_e3_nomination is not None
            or request.interpretations):
        raise ValueError("select empty revision fields and no original-E3 fallback before authentic E4 projection")
    owner = service._composite_programme(directory=directory)
    if type(owner) is not SelectedE4ProgrammeService:
        raise TypeError("selected E4 export requires its actual public composite programme owner")
    plan, _ = owner._state(directory)
    if plan.declaration.bank_phase != "CONFIRMATION":
        raise ValueError("selected E4 export requires complete original CONF, never CAL or DEV alone")
    programme_request = owner._request(programme_request_path, plan)
    if (programme_request is None or programme_request.collection is None
            or tuple(value.component_id for value in programme_request.components) != tuple(sorted(plan.component_ids))):
        raise PermissionError("selected E4 export needs the exact complete actual wave and assessment selections")
    assessment, = (value for value in programme_request.components if value.component_id == preparation.ASSESSMENT_COMPONENT_ID)
    directory = Path(directory) / "components" / preparation.ASSESSMENT_COMPONENT_ID
    selected, api = service._prospective_context(directory, lifecycle="read")
    status = api.campaign_status(CampaignStatusRequest(assessment.run_id), expected_candidate=selected.association.candidate)
    if not status.succeeded or status.payload is None or status.payload.operational_status != "SUCCEEDED":
        raise PermissionError("selected E4 export refuses incomplete or failed original CONF assessment")
    # Each actual wave closure is read once by its existing owner. This read
    # supplies no reusable authority and does not reopen the original E3 run.
    collection = programme_request.collection.evidence
    locators = tuple(_locator(owner.writer, value, plan.declaration) for value in programme_request.components
        if value.component_id != preparation.ASSESSMENT_COMPONENT_ID)
    if (collection.declaration != plan.declaration.identity
            or tuple(value.locator for value in collection.waves) != locators):
        raise PermissionError("selected E4 export changes the exact original CONF collection or wave locators")
    observations, _ = read_selected_e4_programme(writer=owner.writer, declaration=plan.declaration,
        locators=locators, codecs=_codecs())
    if (len(observations) != len(plan.declaration.programme.waves)
            or sum(len(value.cases) for value in observations) != len(plan.declaration.programme.cases)
            or tuple((value.identity, len(value.canonical_bytes())) for value in observations)
                != tuple((value.observation, value.size_bytes) for value in collection.waves)):
        raise PermissionError("selected E4 export changes the complete assigned original CONF observations")
    return _read_selected_e4_component(selected=selected, artifact_writer=service.artifact_writer,
        run_id=assessment.run_id, reveal_authority_id=assessment.reveal_authority_id,
        consume_tail=partial(_revision_entry, confirmation=plan, specification=specification,
            request=request, collection=collection))


def _revision_entry(*, writer, package, plan, entry, receipts, products, reveal, confirmation, specification, request, collection):
    """Project within the original reader's live complete-payload mutation guard."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4DownstreamNomination
    from empirical_lawhood.api.matrix_selected_runtime import _published_input
    from empirical_lawhood.api.selected_e4_method_runtime import validate_selected_e4_downstream_producer
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding

    pin = ObjectIdentity.from_record
    if (entry.declaration != confirmation.declaration or entry.evidence != confirmation.evidence.identity
            or entry.programme_pin != confirmation.declaration.programme.identity or entry.wave_id is not None
            or entry.phase != "phase-entry" or entry.wave_evidence != collection.identity
            or entry.wave_evidence_size_bytes != len(collection.canonical_bytes())):
        raise PermissionError("selected E4 export substitutes its actual original full CONF declaration")
    candidates = tuple(row for row in products if type(row[0]) is SelectedE4DownstreamNomination)
    if len(candidates) != 1:
        raise PermissionError("selected E4 export requires one exact completed downstream nomination")
    nomination, receipt, logical = candidates[0]
    nomination.__post_init__()
    if nomination.selected != "REVISION":
        raise PermissionError("selected E4 did not nominate REVISION; dependent revision work remains unentered")
    revision, calibration = confirmation.tail.revision, confirmation.tail.confirmation.calibration
    original_e3 = confirmation.declaration.original_summary.original_package
    if (revision.models is None or calibration is None or nomination.frozen_product != revision.decision
            or nomination.calibration_product != calibration or nomination.original_e3_package != original_e3
            or nomination.frozen_revision != revision.decision.frozen or nomination.calibration != calibration.original
            or receipts.get(receipt.task_id) != receipt):
        raise PermissionError("selected E4 export changes actual original E3, fit/freeze, CAL or CONF selection pins")
    entry_task, = (task for task in plan.tasks if task.capability.config.config_id == entry.config_id)
    evidence_spec, = (value for value in entry_task.external_inputs
        if value.expected_payload_schema == native.SelectedE4ProtectedEvidence.SCHEMA)
    actual = _published_input(writer, package.run_plan_id, evidence_spec, native.SelectedE4ProtectedEvidence)
    if actual != confirmation.evidence:
        raise PermissionError("selected E4 export substitutes actual original fit/freeze or CAL producer locators")
    binding = RecursivePriorExecutionBinding("binding.selected-e4-export." + nomination.fingerprint(),
        pin(package.issued_study.issue_id, package.issued_study),
        pin(package.execution_authority.authority_id, package.execution_authority), pin(package.package_id, package),
        pin(plan.execution_plan_id, plan), package.run_plan_id, receipt.task_id, pin(receipt.receipt_id, receipt),
        logical.logical_artifact_id, nomination.identity)
    validate_selected_e4_downstream_producer(binding=binding, package=package, execution_plan=plan, receipt=receipt,
        logical=logical, writer=writer, read_scope=None, expected_revision=revision,
        expected_calibration=calibration, expected_e3_package=original_e3)
    original = MatrixSelectedOriginalProduct(binding, pin(reveal.authority_id, reveal))
    return _project_revision_request(specification=specification, request=request,
        revision=revision, nomination=nomination,
        revision_fit=confirmation.evidence.development_nomination,
        revision_freeze=confirmation.evidence.development_freeze,
        calibration_product=confirmation.evidence.calibration_product,
        downstream_nomination=original, reference_package=confirmation.bank.forecast_design.package)


def _project_revision_request(*, specification, request, revision, nomination, revision_fit,
        revision_freeze, calibration_product, downstream_nomination, reference_package=None):
    """Pure projection after original custody; this creates no authority."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as domain
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_entry import MatrixRevisionEntryEvidence, validate_entry_evidence
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionSelectedPackage
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4DownstreamNomination
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4PointModels
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4RevisionExport

    if type(nomination) is not SelectedE4DownstreamNomination or type(revision) is not SelectedE4RevisionExport:
        raise TypeError("selected E4 projection requires exact original scientific products")
    nomination.__post_init__(); revision.__post_init__()
    if nomination.selected != "REVISION":
        raise PermissionError("selected E4 did not nominate REVISION; dependent revision work remains unentered")
    calibration = nomination.calibration_product
    if (revision.models is None or calibration is None or nomination.frozen_product != revision.decision
            or nomination.frozen_revision != revision.decision.frozen):
        raise PermissionError("selected E4 projection changes actual selected models, freeze or CAL pins")
    models = SelectedE4PointModels.from_models(revision.models,
        record_id="models.selected-e4-export." + revision.models.fingerprint())
    selected_package = MatrixRevisionSelectedPackage("package.selected-e4-export." + nomination.fingerprint(),
        models, nomination.identity, calibration.original, calibration if models.relation_fit is not None else None,
        reference_package if models.relation_fit is not None else None)
    selected = replace(request, revision=selected_package)
    programme = domain.revision_programme(specification, selected)
    evidence = MatrixRevisionEntryEvidence("evidence.selected-e4-export." + programme.fingerprint(), programme.identity,
        revision_fit, revision_freeze, downstream_nomination, calibration_product, revision.identity, calibration,
        nomination.original_e3_package, None, None, None, (), (), None)
    evidence = domain.committed_entry_evidence(evidence, request.original_commitments)
    validate_entry_evidence(evidence, programme)
    return replace(selected, revision_evidence=evidence)
