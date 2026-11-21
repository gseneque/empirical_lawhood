# SPDX-License-Identifier: MPL-2.0
"""Run selected bounded fixtures at existing owning call sites.

This operation is never part of catalogue inspection. Ordinary installed
dispatch remains intact; a selected fixture cannot replace its registry.
"""

from collections.abc import Mapping
from hashlib import sha256
from inspect import signature
from time import monotonic, process_time

from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.execution.extension_conformance import ConformanceCall, ConformanceProfile, ExtensionConformanceSelection, inspect_extension_contracts


def canonical_roundtrip(*, record, codec):
    """Exercise the actual strict encoder and decoder on one disclosed record."""
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes

    if type(record) is not codec or not isinstance(record, CanonicalRecord):
        raise TypeError("conformance round trip requires its exact canonical record codec")
    raw = record.canonical_bytes()
    result = decode_canonical_bytes(raw, codec, maximum_bytes=2 * 1024**2)
    if result.canonical_bytes() != raw:
        raise ValueError("canonical conformance round trip changes original bytes")
    return result


def decode_selected_output(*, operations, producer, payload_schema, payload):
    """Exercise the original producer selection and strict bounded decoder."""
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
    from empirical_lawhood.storage.contracts.record_codecs import OperationOutputRecordBinding, RecordCodecCatalog
    codecs = RecordCodecCatalog((kind for operation in operations for kind in operation.record_codecs.values()),
        output_bindings=tuple(OperationOutputRecordBinding(operation.registration().selection,
            output.payload_schema, operation.record_codecs[output.payload_schema].VERSION)
            for operation in operations for output in operation.outputs
            if output.profile is ArtifactProfile.CANONICAL_JSON))
    kind = codecs.for_operation(producer, payload_schema)
    return decode_canonical_bytes(payload, kind, maximum_bytes=2 * 1024**2)


def _owner(call):
    # Imports select only this explicit conformance operation. Discovery does
    # not import the runner or invoke any of the selected callbacks.
    if call is ConformanceCall.CODEC_ROUNDTRIP:
        return canonical_roundtrip
    if call is ConformanceCall.OUTPUT_RECORD_DECODE:
        return decode_selected_output
    if call is ConformanceCall.PREPARE:
        from empirical_lawhood.api.experiment_preparation import prepare_experiment
        return prepare_experiment
    if call is ConformanceCall.VALIDATE_INSTANCE:
        from empirical_lawhood.api.experiment_runtime_bindings import authenticate_experiment_instance
        return authenticate_experiment_instance
    if call is ConformanceCall.DEVELOPMENT_READ:
        from empirical_lawhood.api.experiment_scientific_read import read_prepared_development_science
        return read_prepared_development_science
    if call is ConformanceCall.DEVELOPMENT_COMPLETE:
        from empirical_lawhood.api.experiment_scientific_read import complete_prepared_development_science
        return complete_prepared_development_science
    if call is ConformanceCall.COMPILE:
        from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
        return compile_recursive_wave
    if call is ConformanceCall.ASSESS:
        from empirical_lawhood.execution.recursive_compiler import project_recursive_assessments
        return project_recursive_assessments
    if call is ConformanceCall.OUTPUT_CENSUS:
        from empirical_lawhood.execution.local.execution import validate_runner_output_contract
        return validate_runner_output_contract
    if call is ConformanceCall.NATIVE_PREPARE:
        from empirical_lawhood.execution.local.execution import _prepare_native_work
        return _prepare_native_work
    if call is ConformanceCall.LIVE_APPLICATION:
        from empirical_lawhood.execution.continuing_source import require_live_application
        return require_live_application
    if call is ConformanceCall.LIVE_EVENT_GAPS:
        from empirical_lawhood.science.inquiry.continuing_source import source_sequence_gaps
        return source_sequence_gaps
    if call is ConformanceCall.ACTOR_EVIDENCE:
        from empirical_lawhood.design.inquiry_methods import require_actor_evidence
        return require_actor_evidence
    if call is ConformanceCall.ASSESSMENT_CONTRACT:
        from empirical_lawhood.design.inquiry_methods import DependentAssessmentContract
        return DependentAssessmentContract
    if call is ConformanceCall.CERTIFICATE_READ:
        from empirical_lawhood.api.knowledge_certificates import verify_assessment_certificate
        return verify_assessment_certificate
    if call is ConformanceCall.KNOWLEDGE_DEPENDENCIES:
        from empirical_lawhood.storage.contracts.knowledge_store import dependency_order
        return dependency_order
    raise ValueError("unimplemented conformance call site")


def _observed(value):
    result = {"type": type(value).__module__ + "." + type(value).__qualname__}
    if isinstance(value, CanonicalRecord):
        result["canonical_sha256"] = value.fingerprint()
    elif type(value) is tuple and all(isinstance(row, CanonicalRecord) for row in value):
        encoded = canonical_json_bytes(value)
        if len(encoded) > 2 * 1024**2:
            raise ValueError("conformance census exceeds its 2 MiB result bound")
        result.update(canonical_census_sha256=sha256(encoded).hexdigest(), count=len(value))
    elif isinstance(value, Mapping):
        from empirical_lawhood.storage.numerical_provenance import immutable_json
        encoded = canonical_json_bytes(immutable_json(dict(value)))
        if len(encoded) > 2 * 1024**2:
            raise ValueError("conformance report exceeds its 2 MiB result bound")
        result["report_sha256"] = sha256(encoded).hexdigest()
        # Keep the original independent axes and complete denominators in the
        # disclosed report. Do not manufacture absent keys or connections.
        result["report"] = dict(value)
    return result


def _require_selected_operands(selection, case):
    """A fixture cannot test unrelated installed code under the selected name."""
    arguments = case.arguments
    selected_codecs = {*selection.imported_record_types, *(row.specification_type for row in selection.protocols),
                       *(row.record_type for row in selection.knowledge_types)}
    for operation in selection.operations:
        selected_codecs.update((operation.config_record_type, *operation.record_codecs.values(), *operation.input_record_types))
    service_calls = {
        ConformanceCall.LIVE_APPLICATION: ConformanceProfile.CONTINUING_SOURCE_CONTRACTS,
        ConformanceCall.LIVE_EVENT_GAPS: ConformanceProfile.CONTINUING_SOURCE_CONTRACTS,
        ConformanceCall.ACTOR_EVIDENCE: ConformanceProfile.DEPENDENT_ASSESSMENT_CONTRACTS,
        ConformanceCall.ASSESSMENT_CONTRACT: ConformanceProfile.DEPENDENT_ASSESSMENT_CONTRACTS,
        ConformanceCall.CERTIFICATE_READ: ConformanceProfile.PORTABLE_CERTIFICATE_READ,
        ConformanceCall.KNOWLEDGE_DEPENDENCIES: ConformanceProfile.KNOWLEDGE_STORE_CONTRACTS,
    }
    if case.call in service_calls and selection.profile is not service_calls[case.call]:
        raise ValueError("conformance call changes its selected service profile")
    if case.call is ConformanceCall.LIVE_APPLICATION:
        from empirical_lawhood.science.inquiry.continuing_source import ContinuingSourceSession, FiniteLiveOperation, LiveActorLease
        for key, kind in (("operation", FiniteLiveOperation), ("session", ContinuingSourceSession), ("current_lease", LiveActorLease)):
            if kind not in selected_codecs or type(arguments.get(key)) is not kind:
                raise ValueError("live conformance changes its selected typed source/operation census")
        if arguments["operation"].effect_key not in {key for key, port in selection.effect_ports}:
            raise ValueError("live conformance changes its selected effect port")
    if case.call is ConformanceCall.LIVE_EVENT_GAPS:
        from empirical_lawhood.science.inquiry.continuing_source import LiveObservation
        events = arguments.get("events")
        if (LiveObservation not in selected_codecs or type(events) is not tuple or len(events) > 64
                or any(type(event) is not LiveObservation for event in events)):
            raise ValueError("live gap conformance changes its bounded observation census")
    if case.call in (ConformanceCall.ACTOR_EVIDENCE, ConformanceCall.ASSESSMENT_CONTRACT):
        from empirical_lawhood.design.inquiry_methods import DependentAssessmentContract, InquiryMethodEvidence
        required = InquiryMethodEvidence if case.call is ConformanceCall.ACTOR_EVIDENCE else DependentAssessmentContract
        if required not in selected_codecs:
            raise ValueError("inquiry conformance changes its selected shared record contracts")
        if case.call is ConformanceCall.ASSESSMENT_CONTRACT and arguments.get("method") not in {
                row.registration().selection for row in selection.operations}:
            raise ValueError("assessment conformance changes its selected method implementation")
    if case.call is ConformanceCall.CERTIFICATE_READ:
        from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeAssessmentCertificate
        from empirical_lawhood.science.identity.provenance import ObjectIdentity
        expected = arguments.get("expected_certificate")
        if (KnowledgeAssessmentCertificate not in selected_codecs or type(expected) is not ObjectIdentity
                or (expected.object_schema, expected.object_version) != (
                    KnowledgeAssessmentCertificate.SCHEMA, KnowledgeAssessmentCertificate.VERSION)):
            raise ValueError("certificate conformance requires its selected exact original identity and reader")
        if arguments.get("allow_incomplete", False):
            raise ValueError("certificate conformance requires complete original assessment verification")
    if case.call is ConformanceCall.KNOWLEDGE_DEPENDENCIES:
        from empirical_lawhood.storage.contracts.knowledge_store import KnowledgeStoreLimits, PortableKnowledgeObject
        if (PortableKnowledgeObject not in selected_codecs or type(arguments.get("objects")) is not tuple
                or len(arguments["objects"]) > 64 or not arguments["objects"]
                or any(type(row) is not PortableKnowledgeObject for row in arguments["objects"])
                or type(arguments.get("roots")) is not tuple or not 1 <= len(arguments["roots"]) <= 64
                or type(arguments.get("limits")) is not KnowledgeStoreLimits):
            raise ValueError("knowledge conformance requires a finite selected typed dependency census")
        arguments["limits"].__post_init__()
    if case.call is ConformanceCall.OUTPUT_RECORD_DECODE:
        if (selection.profile is not ConformanceProfile.RECORD_REVISIONS
                or arguments.get('operations') != selection.operations):
            raise ValueError('revision decoding changes its selected operation census or profile')
    if case.call is ConformanceCall.NATIVE_PREPARE:
        selected = tuple(row for row in selection.operations
            if row.execution_properties.native_effect
            and row.execution_properties.native_work_preparer is arguments.get("callback"))
        if (selection.profile is not ConformanceProfile.ISOLATED_NATIVE_CONTRACTS or len(selected) != 1
                or getattr(arguments.get("runner"), "manifest", None) != selected[0].manifest()):
            raise ValueError("native preparation changes its selected operation and callback")
        if getattr(arguments.get("context"), "prepared_invocation", False) is not None:
            raise ValueError("native conformance selects only the initial pure preparation")
    if case.call is ConformanceCall.CODEC_ROUNDTRIP:
        if arguments.get("codec") not in selected_codecs:
            raise ValueError("conformance round trip changes its selected codec census")
    if case.call is ConformanceCall.VALIDATE_INSTANCE and arguments.get("declaration") not in selection.protocols:
        raise ValueError("conformance instance validator changes the selected protocol")
    if case.call in (ConformanceCall.COMPILE, ConformanceCall.ASSESS):
        if arguments.get("registrations") != tuple(row.registration() for row in selection.operations):
            raise ValueError("conformance compiler changes the complete selected operation census")
    if case.call in (ConformanceCall.PREPARE, ConformanceCall.DEVELOPMENT_READ,
                     ConformanceCall.DEVELOPMENT_COMPLETE, ConformanceCall.VALIDATE_INSTANCE):
        from empirical_lawhood.api.experiment_preparation import experiment_protocols
        from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
        installed = {row.protocol_id: row for row in experiment_protocols()}
        bindings = {row.protocol_id: row for row in selection.bindings}
        for protocol in selection.protocols:
            if installed.get(protocol.protocol_id) != protocol or experiment_runtime_binding(protocol) != bindings.get(protocol.protocol_id):
                raise ValueError("conformance selection differs from its actual installed protocol/binding")
        if case.call is ConformanceCall.PREPARE and type(arguments.get("specification")) not in {
                row.specification_type for row in selection.protocols}:
            raise ValueError("conformance preparation changes its selected specification codec")


def run_extension_conformance(selection: ExtensionConformanceSelection, *, source: Mapping) -> dict:
    """Return every selected check and failure; never return scientific authority."""
    from empirical_lawhood.storage.extension_conformance import forbid_conformance_contact
    from empirical_lawhood.api.experiment_runtime_bindings import validate_experiment_runtime_binding

    started, cpu = monotonic(), process_time()
    profile = getattr(selection, "profile", None)
    report = dict(status="FAILED", source=dict(source), profile=getattr(profile, "value", profile),
        evidence_scope="EXPOSED_SOFTWARE_CONFORMANCE", scientific_authority="NONE",
        qualification="NOT_ESTABLISHED", full_installed_lifecycle=False,
        checks=[], unmet_prerequisites=list(getattr(selection, "unmet_prerequisites", ())), contact_attempts=[])
    try:
        contracts = inspect_extension_contracts(selection)
        protocols = {row.protocol_id: row for row in selection.protocols}
        for binding in selection.bindings:
            validate_experiment_runtime_binding(protocols[binding.protocol_id], binding)
        report["contracts"] = contracts
        report["checks"].append(dict(check_id="declarations", status="PASSED"))
        if selection.unmet_prerequisites:
            report["status"] = "PREREQUISITES_UNMET"
            return report
        # Validate all argument shapes before the first executable callback.
        owners = []
        for case in selection.cases:
            case.__post_init__()
            _require_selected_operands(selection, case)
            owner = _owner(case.call)
            signature(owner).bind(**case.arguments)
            owners.append(owner)
        with forbid_conformance_contact(source_access=selection.source_access, effect_ports=selection.effect_ports) as contacts:
            for case, owner in zip(selection.cases, owners, strict=True):
                row = dict(check_id=case.case_id, call_site=owner.__module__ + "." + owner.__name__, status="FAILED")
                initial_contacts = len(contacts)
                case_started, case_cpu = monotonic(), process_time()
                try:
                    value = owner(**case.arguments)
                    row["observed"] = _observed(value)
                    if case.refusal_contains is not None:
                        raise AssertionError("expected owning refusal was not returned")
                    if type(value) is not type(case.expected) or value != case.expected:
                        raise AssertionError("owning return differs from the complete expected fixture result")
                    row["status"] = "PASSED"
                except Exception as error:
                    row["exception"] = dict(type=type(error).__name__, message=str(error)[:2000])
                    if (case.refusal_contains is not None and type(error).__name__ == case.expected
                            and case.refusal_contains in str(error)):
                        row["status"] = "PASSED_EXPECTED_REFUSAL"
                if len(contacts) != initial_contacts:
                    row["status"] = "FAILED_CONTACT_ATTEMPT"
                row.update(wall_seconds=str(monotonic() - case_started), cpu_seconds=str(process_time() - case_cpu))
                report["checks"].append(row)
            report["contact_attempts"] = list(contacts)
            report["storage_diagnostics"] = contacts.storage_diagnostics
        if all(row["status"] in ("PASSED", "PASSED_EXPECTED_REFUSAL") for row in report["checks"]):
            report["status"] = "PASSED_SELECTED_CHECKS"
        return report
    except Exception as error:
        report["failure"] = dict(type=type(error).__name__, message=str(error)[:2000])
        return report
    finally:
        report.update(wall_seconds=str(monotonic() - started), cpu_seconds=str(process_time() - cpu))
