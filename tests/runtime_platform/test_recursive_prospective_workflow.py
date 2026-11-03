# SPDX-License-Identifier: MPL-2.0
"""Truth-known public lifecycle conformance; no scientific qualification evidence."""
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
import os
from typing import ClassVar

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution, ExecutableCapabilityProviderFactoryRegistry, ExecutablePlatformPort, LayeredCampaignRuntimeProviderResolver, compose_executable_binding_aggregate
from empirical_lawhood.runtime.providers import CampaignRuntimeProviderRegistry, ExternalInputPayload
from empirical_lawhood.runtime.plans import ScientificInputRole
from empirical_lawhood.runtime.recursive_compiler import RecursiveOperationRegistration, RecursivePortContract, compile_recursive_wave
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort, RecursiveOperationProviderFactory, recursive_input_port_key, recursive_operation_binding
from tests.runtime_platform.test_recursive_compiler import Config, prospective_fixture


@dataclass(frozen=True, slots=True)
class FixtureCanonicalSource(CanonicalRecord):
    """Exact disclosed source for current high-level FILE contract checks."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/fixtures/reference-source"
    source: str


class _TypedFixtureRunner:
    def __init__(self, manifest, sealed_fixture=None):
        self.manifest = manifest
        self.sealed_fixture = sealed_fixture

    def execute(self, context):
        process_check = ReceiptCheck("synthetic-process-" + str(os.getpid()), True, ())
        if context.task_id == 'evaluate':
            from empirical_lawhood.adapters.reference_worlds.runtime import ReferenceAdjudicationFixture
            sealed = tuple(port for port in context.input_ports if port.payload_schema == ReferenceAdjudicationFixture.SCHEMA)
            assert len(sealed) == 1
            fixture = decode_canonical_bytes(sealed[0].read(), ReferenceAdjudicationFixture, maximum_bytes=3000)
            value = context.scientific_adjudication_context
            record = ScientificAdjudicationRecord('adjudication.' + context.run_id + '.' + context.task_id,
                context.run_id, context.task_id, value.execution_plan, tuple(sorted(context.input_materialization_ids)),
                tuple(sorted(output.logical_artifact_id for output in context.output_ports)), context.dependency_receipt_ids,
                value.evidence_world_id, value.evidence_world_kind, value.relation, value.independent_unit_id,
                value.information_cutoffs, value.visibility_ceiling, value.outcome_access, fixture.evaluability,
                fixture.scientific_status, fixture.admission_status, fixture.reason_codes)
            return RunnerResult(tuple(TaskOutputPayload(output.output_id, record.canonical_bytes()) for output in context.output_ports),
                                (ReceiptCheck('synthetic-common-scientific-adjudication', True, ()), process_check))
        for port in context.input_ports:
            if port.outcome_access is not OutcomeAccess.EVALUATION_SEALED:
                port.read(port.size_bytes + 1)
        if context.task_id == 'freeze':
            from empirical_lawhood.adapters.reference_worlds.runtime import REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE
            record = self.sealed_fixture or REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE
        else:
            record = Config('product.' + context.task_id, 3)
        return RunnerResult(tuple(TaskOutputPayload(output.output_id, record.canonical_bytes()) for output in context.output_ports),
                            (ReceiptCheck('synthetic-common-operation-product', True, ()), process_check))


def _registrations(compilation):
    values = []
    for step in compilation.template.protocol.steps:
        manifest = compilation.registry.resolve(step.capability_key, step.capability_version)
        operation = next(value for value in compilation.operations if value.node_id == step.step_id)
        ports = tuple(RecursivePortContract(edge.consumer_input_id, edge.payload_schema, edge.media_type,
                      edge.maximum_size_bytes) for edge in sorted(compilation.template.graph.edges,
                      key=lambda value: value.consumer_input_id) if edge.consumer_node_id == step.step_id
                      and edge.scientific_role is not ScientificInputRole.CONFIGURATION)
        from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
        from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
        storage_codecs = MATRIX_STORAGE_CODECS if any(value.payload_schema == MATRIX_ARRAY_SCHEMA
            for value in (*ports, *step.outputs)) else ()
        values.append(RecursiveOperationRegistration(operation.selection, step.stage, Config, ports, step.outputs,
              step.required_permissions, step.requested_outcome_access, step.visibility_ceiling, manifest.resource_ceiling,
              step.barrier, adjudication_output_id=step.outputs[0].output_id if step.step_id == 'evaluate' else None,
              storage_codecs=storage_codecs,
              input_record_types=(FixtureCanonicalSource,) if any(port.payload_schema == FixtureCanonicalSource.SCHEMA
                  for port in ports) else ()))
    return tuple(values)


def _source_external(compilation):
    source, = compilation.candidate_draft.source_materializations
    external, = (value for value in compilation.template.graph.external_inputs
        if value.input_id == source.source_id)
    assert external.scientific_role is ScientificInputRole.PREPARED_MEDIUM
    assert external.payload_schema == FixtureCanonicalSource.SCHEMA
    return external


def _actual_source(compilation):
    """Replace deliberate old fixture digest labels with actually measured bytes."""
    from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig, SourceReadMode
    from tests.experiment_entry_support import standard_authoring_for_draft
    external = _source_external(compilation)
    raw = FixtureCanonicalSource('synthetic common source').canonical_bytes()
    content_sha = sha256(raw).hexdigest()
    qualification = compilation.candidate_context.qualifications[0]
    qualification = replace(qualification, content_sha256=content_sha,
                            materialization=replace(qualification.materialization, object_fingerprint=content_sha))
    source = compilation.candidate_draft.source_materializations[0]
    config = SourceMaterializationConfig('source-config.generic', source.source_id, source.role, content_sha,
                len(raw), len(raw), external.payload_schema, 'application/json',
                SourceReadMode.ORDINARY_BOUNDED, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    source = replace(source, materialization=qualification.materialization, content_sha256=content_sha,
                     source_config_sha256=config.fingerprint(), qualification_receipt=ObjectIdentity.from_record(qualification.receipt_id, qualification))
    draft = replace(compilation.draft, prospective_draft=replace(compilation.candidate_draft, source_materializations=(source,)),
             external_inputs=tuple(replace(operand, expected_content_sha256=content_sha) for operand in compilation.draft.external_inputs))
    compilation = compile_recursive_wave(draft=draft, registrations=_registrations(compilation), registry=compilation.registry,
            implementation_commit='a' * 40, qualifications=(qualification,),
            known_design_inputs=compilation.candidate_context.known_design_inputs,
            output_codecs=compilation.output_codecs)
    assert compilation.candidate_report.candidate is not None
    authoring, context = standard_authoring_for_draft(compilation.candidate_draft, compilation.candidate_context,
                                                   formal_method_capability_key='recursive-fixture.evaluate')
    return compilation, authoring, context, raw, config


class _FixtureSupplier:
    def __init__(self, compilation, source):
        self.configs = {row.config_id: row for row in compilation.config_inputs}
        self.source = source
        self.source_id = _source_external(compilation).logical_artifact_id
        self.calls = 0

    def resolve_input(self, spec):
        from empirical_lawhood.adapters.reference_worlds.runtime import REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE
        self.calls += 1
        row = self.configs.get(spec.logical_artifact_id)
        parents = ()
        if row is not None:
            raw, schema = row.payload, row.payload_schema
        elif spec.logical_artifact_id == self.source_id:
            raw, schema = self.source, spec.expected_payload_schema
        else:
            raw, schema = REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE.canonical_bytes(), REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE.SCHEMA
            if spec.identity_scope_sha256 is not None:
                parents = (ArtifactLineageParent(ObjectIdentity('scope.synthetic', 'empirical-lawhood/runtime/external-input-scope',
                        '1.0.0', spec.identity_scope_sha256), VisibilityCeiling.PROSPECTIVE, OutcomeAccess.EVALUATION_SEALED),)
        return ExternalInputPayload.from_bytes(logical_artifact_id=spec.logical_artifact_id, payload_schema=schema,
            profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json', payload=raw,
            outcome_access=spec.expected_outcome_access or OutcomeAccess.OUTCOME_BLIND,
            visibility_ceiling=spec.expected_visibility_ceiling or VisibilityCeiling.PROSPECTIVE,
            parent_visibility_ceilings=tuple(parent.visibility_ceiling for parent in parents), lineage_parents=parents)


def _factories(compilation, supplier, sealed_fixture=None, *, registrations=None):
    from empirical_lawhood.adapters.composition.discovery import bundle
    from empirical_lawhood.adapters.composition.generated_extension_bundles import EXTENSION_BUNDLE_CONTRIBUTIONS
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_BINDING_CONTRIBUTIONS, EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind, compose_extension_bundle_aggregate
    discoveries, factories, ports = [], [], []
    codecs = dict(compilation.output_codecs)
    for registration in _registrations(compilation) if registrations is None else registrations:
        manifest = compilation.registry.resolve(registration.selection.capability_key, registration.selection.capability_version)
        contribution, components = bundle(manifest.capability_key.removeprefix('recursive-fixture.'),
                   ExtensionContributionKind.METHOD, manifest, (), None, namespace='recursive-fixture', maximum_config_bytes=16 * 1024**2)
        discoveries.append(contribution)
        binding = recursive_operation_binding(registration=registration, manifest=manifest,
                                              components=tuple(sorted(components, key=lambda value: value.registration_id)))
        factories.append(RecursiveOperationProviderFactory(binding, registration, manifest,
                                                           lambda manifest=manifest: _TypedFixtureRunner(manifest, sealed_fixture), codecs))
        ports.append(ExecutablePlatformPort(recursive_input_port_key(registration.selection), RecursiveOperationInputPort(supplier)))
    contribution = ExecutableBindingContribution('synthetic.generic-prospective-factories', '1.0.0',
                                                 tuple(sorted((factory.binding for factory in factories), key=lambda value: value.binding_id)))
    discovery = compose_extension_bundle_aggregate((*EXTENSION_BUNDLE_CONTRIBUTIONS, *discoveries))
    aggregate = compose_executable_binding_aggregate((*EXECUTABLE_BINDING_CONTRIBUTIONS, contribution), discovery_aggregate=discovery)
    installed = tuple(EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY.factory(key)
                      for key in EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY.binding_ids)
    registry = ExecutableCapabilityProviderFactoryRegistry(aggregate=aggregate,
                    factories=tuple(sorted((*installed, *factories), key=lambda value: value.binding.binding_id)))
    return registry, tuple(sorted(ports, key=lambda value: value.port_key)), discovery


def _issued_fixture(tmp_path, compilation, authoring, context):
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring.executable_binding import REGISTRATION
    from tests.issued_study_support import build_issued_study_fixture
    from tests.runtime_platform.test_study_issue import _issue_api_fixture
    return build_issued_study_fixture(tmp_path,
        issue_fixture_factory=lambda destination: _issue_api_fixture(destination, standard_fixture=lambda: (authoring, context)),
        additional_extensions=((compilation.selected_scientific_projection, REGISTRATION),), include_fixed_round_extension=False)


def _authored_handoff_fixture(tmp_path, monkeypatch, *, sealed_fixture=None, reveal_terminal=False, worker_memory_bytes=None):
    """Use actual public export/loader owners with isolated software-only science."""
    from empirical_lawhood.api import recursive_prospective_authoring as owner
    from empirical_lawhood.api.facade import EmpiricalLawhoodApi
    from empirical_lawhood.api.results import CompileCandidateRequest
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring.executable_binding import REGISTRATION
    from empirical_lawhood.adapters.reference_worlds.runtime import REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE
    from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher
    from tests.prospective_source_capture_fixture import SyntheticSourceInspector, synthetic_capture
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec, RecursiveProspectiveOperand
    from empirical_lawhood.runtime.study_issue import project_standard_study_extensions
    from tests.runtime_platform.test_deadline_free_execution_package import _execution_package_fixture, _compile as compile_resource_fixture
    from tests.runtime_platform.test_study_issue import _issue_api_fixture, _publisher

    original, _, _ = prospective_fixture(typed_outputs=True, reveal_terminal=reveal_terminal,
        worker_memory_bytes=worker_memory_bytes)
    compilation, standard, formal, raw, source_config = _actual_source(original)
    base_dir = tmp_path / 'base'
    base_dir.mkdir()
    scaffold_api, scaffold_paths, external, custody = _issue_api_fixture(base_dir, standard_fixture=lambda: (standard, formal))
    plane = _publisher(external, custody).artifact_plane
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
    from empirical_lawhood.runtime.recursive_storage_codecs import storage_codec_census
    plane.validators = ArtifactProfileValidatorRegistry(binary_codecs=storage_codec_census(_registrations(compilation)))
    resources_dir = tmp_path / 'resource-fixture'
    resources_dir.mkdir()
    resource_fixture = _issued_fixture(resources_dir, compilation, standard, formal)
    resource_package = _execution_package_fixture(resource_fixture, native_simulator=False, jit=False)
    _, resource_plan = compile_resource_fixture(resource_fixture, resource_package)
    outcome = sealed_fixture or REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE
    source_external = compilation.draft.external_inputs[0]
    operands = [RecursiveProspectiveOperand(source_external.logical_artifact_id, sha256(raw).hexdigest(), len(raw),
                 source_external.payload_schema, 'application/json', OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)]
    payloads = {source_external.logical_artifact_id: raw, source_config.fingerprint(): source_config.canonical_bytes()}
    for task in resource_plan.tasks:
        for source in task.external_inputs:
            if (source.expected_outcome_access is OutcomeAccess.EVALUATION_SEALED
                    and source.expected_payload_schema == outcome.SCHEMA):
                parents = () if source.identity_scope_sha256 is None else (
                    ArtifactLineageParent(ObjectIdentity('scope.synthetic', 'empirical-lawhood/runtime/external-input-scope',
                          '1.0.0', source.identity_scope_sha256), VisibilityCeiling.PROSPECTIVE, OutcomeAccess.EVALUATION_SEALED),)
                operands.append(RecursiveProspectiveOperand(source.logical_artifact_id, outcome.fingerprint(), len(outcome.canonical_bytes()),
                    outcome.SCHEMA, 'application/json', OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE, parents))
                payloads[source.logical_artifact_id] = outcome.canonical_bytes()
    spec = RecursiveProspectiveAuthoringSpec('fixture.recursive-public', compilation.draft, standard.entry_package,
          formal.formal_methods, formal.source_inventories, compilation.candidate_context.qualifications,
          compilation.candidate_context.known_design_inputs, resource_package.execution_resource_envelope_spec,
          tuple(sorted(operands, key=lambda row: row.logical_artifact_id)))
    capture = lambda project_root, closure_id: synthetic_capture(closure_id, compilation.candidate_context.implementation_sha256)
    closure = capture(None, spec.spec_id + '.source-closure').closure
    monkeypatch.setattr(owner, 'capture_target_closure', capture)
    monkeypatch.setattr(owner, 'GitStudySourceClosureInspector', SyntheticSourceInspector)
    composition = (_registrations(compilation), compilation.registry, compilation.output_codecs)
    compilation, authoring, _, registrations = owner._compile(spec, closure, composition=composition)
    publisher = ExternalCandidateInputPublisher(plane.root)
    for payload in (*payloads.values(), *(row.payload for row in compilation.config_inputs),
                    *(row.canonical_bytes() for row in spec.qualifications)):
        publisher.publish(payload, maximum_bytes=16 * 1024**2)
    factories, _, discovery = _factories(compilation, _FixtureSupplier(compilation, raw), outcome)
    context = owner._context(spec, compilation, registrations, plane.root, discovery.candidate_capability_catalog)
    def api_factory(*, repo_root, candidate_context_provider, candidate_capability_catalog):
        return EmpiricalLawhoodApi(repo_root=repo_root, external_root=None, candidate_context_provider=candidate_context_provider,
            candidate_capability_catalog=candidate_capability_catalog, extension_bundle_aggregate=discovery,
            executable_binding_aggregate=factories.aggregate, executable_factory_registry=factories,
            study_extension_codec_registry=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY)
    preview_dir = tmp_path / 'preview'
    preview_dir.mkdir()
    for name, record in (('authoring', authoring), ('selection', compilation.selected_scientific_projection), ('decoder', REGISTRATION)):
        (preview_dir / (name + '.json')).write_bytes(record.canonical_bytes())
    preview = api_factory(repo_root=tmp_path, candidate_context_provider=context, candidate_capability_catalog=context.catalog).compile_candidate(
          CompileCandidateRequest(preview_dir / 'authoring.json', (preview_dir / 'selection.json',), (preview_dir / 'decoder.json',)))
    assert preview.succeeded, (preview.reason_codes, preview.errors)
    report = preview.payload.report
    extensions, _, _ = project_standard_study_extensions(candidate=report.candidate,
         extension_payload_bytes=(compilation.selected_scientific_projection.canonical_bytes(),),
         decoder_registrations=(REGISTRATION,), extension_materializations=report.extension_materializations)
    spec = replace(spec, resources=replace(spec.resources,
                  issued_study_extensions=ObjectIdentity.from_record(extensions.issued_extension_set_id, extensions)))
    bindings = []
    for key, payload in payloads.items():
        path = preview_dir / ('input.' + sha256(key.encode()).hexdigest()[:12] + '.json')
        path.write_bytes(payload)
        bindings.append((key, path))
    project = tmp_path / 'checkout'
    project.mkdir()
    destination = external / 'authoring'
    result = owner.author_recursive_prospective(spec=spec, project_root=project, artifact_writer=plane,
            output_dir=destination, input_bindings=tuple(bindings), composition=composition, api_factory=api_factory,
            candidate_catalog=discovery.candidate_capability_catalog)
    assert result['scientific_authority'] == 'NONE' and result['native_contact'] == 'none'
    # This isolated test plane replaces only the unavailable real mount/profile resolution.
    monkeypatch.setattr(owner, 'resolve_authoring_directory', lambda directory, **kwargs: (directory.resolve(), plane.root.contract))
    handoff = owner.load_recursive_prospective_handoff(directory=destination, root=project, storage_profile=object(),
                  artifact_writer=plane, composition=composition, candidate_catalog=discovery.candidate_capability_catalog)
    proof = owner.prove_recursive_prospective_handoff(handoff, factory_registry=factories)
    assert proof['scientific_execution_performed'] is False
    assert handoff.compilation.candidate_context.implementation_sha256 == closure.implementation_sha256
    return handoff, factories, discovery, plane, raw, scaffold_api, scaffold_paths, custody


def test_public_recursive_export_fresh_loader_and_provider_proof(tmp_path, monkeypatch):
    handoff, _, _, plane, _, _, _, _ = _authored_handoff_fixture(tmp_path, monkeypatch)
    assert len(handoff.projection.tasks) == 5
    source = handoff.directory / 'scientific-projection.json'
    original = source.read_bytes()
    source.write_bytes(original.replace(b'generic-prospective', b'changed-prospective'))
    from empirical_lawhood.api.recursive_prospective_authoring import load_recursive_prospective_handoff
    with pytest.raises(Exception):
        load_recursive_prospective_handoff(directory=handoff.directory, root=tmp_path / 'checkout',
                                          storage_profile=object(), artifact_writer=plane)


def _public_issued_handoff_fixture(tmp_path, monkeypatch, *, sealed_fixture=None, reveal_terminal=False):
    parts = _authored_handoff_fixture(tmp_path, monkeypatch, sealed_fixture=sealed_fixture, reveal_terminal=reveal_terminal)
    return _issue_public_handoff(tmp_path, monkeypatch, handoff_parts=parts)


def _issue_public_handoff(tmp_path, monkeypatch, *, handoff_parts, namespace='public-recursive', compiled_candidate=None):
    """Actual public author/export/load and independently approved issue path."""
    from empirical_lawhood.api.facade import EmpiricalLawhoodApi
    from empirical_lawhood.api.models import assemble_issued_study_package, assemble_experiment_package
    from empirical_lawhood.api.results import IssueExtensionsRequest
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
    from empirical_lawhood.infrastructure.study_issue import ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore
    from empirical_lawhood.planning.study_issue import StudyAuthorityKind
    from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate, ExecutableStudyCompilationReport
    from empirical_lawhood.runtime.study_issue import build_study_approval_proposal
    from tests.approval_support import FixedDecisionClock
    from tests.issued_study_support import _approval_service, _authorize
    from tests.runtime_platform.test_study_issue import _AuthorityStore, _PassthroughSourceInspector, _issue_request

    handoff, factories, discovery, plane, raw, _, paths, custody = handoff_parts
    if compiled_candidate is None:
        report = decode_canonical_bytes((handoff.directory / 'candidate-report.json').read_bytes(),
                                       ExecutableStudyCompilationReport, maximum_bytes=16 * 1024**2)
        candidate = report.candidate
    elif type(compiled_candidate) is ExecutableStudyCandidate:
        # Public experiment loading already authenticates the exact candidate
        # under its installed profile; issuance independently checks it again.
        candidate = compiled_candidate
    else:
        raise TypeError('public issue scaffold requires its exact executable candidate')
    base_candidate = candidate.base_candidate
    from empirical_lawhood.planning.study_issue import HumanProposerAttestation, ImplementationSourceClosure
    original = decode_canonical_bytes(paths['attestation'].read_bytes(), HumanProposerAttestation, maximum_bytes=1024**2)
    attestation = replace(original, attestation_id='attestation.' + namespace + '.base', candidate=ObjectIdentity.from_record(base_candidate.candidate_id, base_candidate),
        design_origin_id=base_candidate.base_candidate.design_origin.origin_id,
        design_input_ids=base_candidate.base_candidate.design_input_ids,
        source_qualification_receipts=base_candidate.base_candidate.source_qualification_receipts,
        raw_materialization_sha256=base_candidate.base_candidate.authoring_materialization.raw_materialization_sha256,
        semantic_config_sha256=base_candidate.base_candidate.semantic_config_sha256)
    custody = replace(custody, authority_id='authority.custody.' + namespace + '.base',
        subject=ObjectIdentity.from_record(base_candidate.candidate_id, base_candidate),
        storage_root_id=plane.root.contract.storage_root_id)
    closure = decode_canonical_bytes((handoff.directory / 'source-closure.json').read_bytes(),
                                   ImplementationSourceClosure, maximum_bytes=1024**2)
    for name, record in (('authoring', handoff.authoring.base), ('expected_candidate', base_candidate),
                         ('attestation', attestation), ('authority', custody), ('source_closure', closure)):
        paths[name].write_bytes(record.canonical_bytes())
    external = Path(plane.root.contract.canonical_path)
    clock = FixedDecisionClock(clock_id='clock.' + namespace + '.issue', value='2026-07-24T20:32:00Z')
    def issue_api(authority):
        return EmpiricalLawhoodApi(repo_root=tmp_path, external_root=external,
            candidate_context_provider=handoff.context, extension_bundle_aggregate=discovery,
            executable_binding_aggregate=factories.aggregate, executable_factory_registry=factories,
            study_extension_codec_registry=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY,
            study_source_closure_inspector=_PassthroughSourceInspector(), study_issue_clock=clock,
            study_issue_publisher=ExternalIssuedStudyPublisher(artifact_plane=plane,
                authority_store=_AuthorityStore(authority), grantee_id='operator.issue-service'))
    base_result = issue_api(custody).issue_study(_issue_request(paths, confirmed=True))
    assert base_result.succeeded, (base_result.reason_codes, base_result.errors)
    base_manifest, base_publication = base_result.payload.manifest, base_result.payload.publication_receipt
    assert base_manifest.candidate == base_candidate
    extension_attestation = replace(attestation, attestation_id='attestation.' + namespace + '.extensions',
                 candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate),
                 raw_materialization_sha256=sha256(b'application/json\x00' + handoff.authoring.canonical_bytes()).hexdigest())
    extension_custody = replace(custody, authority_id='authority.custody.' + namespace + '.extensions',
                               subject=ObjectIdentity.from_record(candidate.candidate_id, candidate))
    extension_attestation_path, extension_custody_path = tmp_path / 'extension-attestation.json', tmp_path / 'extension-custody.json'
    extension_attestation_path.write_bytes(extension_attestation.canonical_bytes())
    extension_custody_path.write_bytes(extension_custody.canonical_bytes())
    issue = IssueExtensionsRequest(handoff.directory / 'authoring.json',
          (handoff.directory / 'scientific-projection.json',), (handoff.directory / 'decoder.json',),
          handoff.directory / 'candidate.json', base_manifest.issue_id,
          extension_attestation_path, extension_custody_path, True)
    api = issue_api(extension_custody)
    issued = api.issue_extensions(issue)
    assert issued.succeeded, (issued.reason_codes, issued.errors)
    assert api.issue_extensions(issue).payload == issued.payload
    manifest, publication = issued.payload.manifest, issued.payload.publication_receipt
    system = base_candidate.base_candidate.system
    approval, proposals, attestations, checkers = _approval_service(system.system_id, system.authority_policy.required_gate_ids)
    def approve(value, published, suffix):
        frozen, authorized = _authorize(service=approval, proposal_store=proposals, attestation_store=attestations,
             registrations=checkers, proposal=build_study_approval_proposal(issued_study=value, publication_receipt=published),
             system=system, implementation_commit=value.implementation_commit, authorization_id='authorization.' + namespace + '.' + suffix)
        authority = replace(custody, authority_id='authority.execution.' + namespace + '.' + suffix,
             kind=StudyAuthorityKind.EXPERIMENT_EXECUTION, subject=ObjectIdentity.from_record(value.issue_id, value),
             prerequisite_authority=ObjectIdentity.from_record(authorized.authorization_id, authorized),
             grantee_id='operator.execution-service', storage_root_id=None, relative_root=None,
             allows_external_publication=False, allows_execution=True, outcome_access=OutcomeAccess.EVALUATION_SEALED,
             issued_at_utc='2026-08-22T20:43:00Z', expires_at_utc='2027-08-23T20:43:00Z')
        return frozen, authorized, authority
    base_frozen, base_approved, base_execution = approve(base_manifest, base_publication, 'base')
    base = assemble_issued_study_package(issued_study=base_manifest, publication_receipt=base_publication,
          frozen_proposal=base_frozen, scientific_approval=base_approved, execution_authority=base_execution,
          run_plan_id='run.' + namespace + '-base', grantee_id='operator.execution-service', at_utc='2026-08-22T20:44:00Z')
    frozen, authorized, execution = approve(manifest, publication, 'extension')
    resources = replace(handoff.resources,
                  issued_study_extensions=ObjectIdentity.from_record(manifest.issued_extensions.issued_extension_set_id, manifest.issued_extensions))
    package = assemble_experiment_package(base=base, issued_study=manifest, publication_receipt=publication,
          frozen_proposal=frozen, scientific_approval=authorized, execution_authority=execution,
          execution_resource_envelope_spec=resources, predevelopment_jit_signature_census=None, jit_graph_signature_manifest=None,
          run_plan_id='run.' + namespace + '-extension', grantee_id='operator.execution-service', at_utc='2026-08-22T20:44:00Z')
    reveal = replace(execution, authority_id='authority.reveal.' + namespace + '-extension',
          kind=StudyAuthorityKind.OUTCOME_REVEAL, prerequisite_authority=ObjectIdentity.from_record(execution.authority_id, execution),
          grantee_id='operator.evaluator-service', allows_execution=False, allows_reveal=True, outcome_access=OutcomeAccess.EVALUATOR_REVEAL)
    authorities = ExternalStudyOperationAuthorityStore(plane)
    for authority in (custody, extension_custody, base_execution, execution, reveal):
        authorities.persist(authority)
    return handoff, factories, discovery, plane, raw, package, reveal, approval, authorities


def _public_run_handoff_fixture(tmp_path, monkeypatch, *, sealed_fixture=None, exercise_reveal_stop=False, reveal_terminal=False):
    parts = _public_issued_handoff_fixture(tmp_path, monkeypatch, sealed_fixture=sealed_fixture, reveal_terminal=reveal_terminal)
    return _run_public_handoff(tmp_path, issued_parts=parts, exercise_reveal_stop=exercise_reveal_stop)


def _run_public_handoff(tmp_path, *, issued_parts, exercise_reveal_stop=False, prepare_only=False, process_workers=False):
    from types import SimpleNamespace
    from empirical_lawhood.api.facade import EmpiricalLawhoodApi
    from empirical_lawhood.api.execution import CampaignExecutionService
    from empirical_lawhood.api.results import RunCampaignRequest
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
    from empirical_lawhood.infrastructure.execution import DurableExecutionResourceEnvelopeCoordinator
    from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
    from empirical_lawhood.infrastructure.study_issue import ExternalIssuedExtensionPayloadSource, ExternalIssuedStudyPublisher
    from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.runtime.issued_extension_payloads import IssuedExtensionPayloadResolver
    from tests.execution_support import EnforcingTestTaskExecutor
    from tests.runtime_platform.test_study_issue import _PassthroughSourceInspector

    handoff, factories, discovery, plane, raw, package, reveal, approval, authorities = issued_parts
    package_path = tmp_path / 'public-package.json'
    package_path.write_bytes(package.canonical_bytes())
    catalog = tmp_path / 'public-catalog.sqlite3'
    def engine_factory():
        engine = create_catalog_engine('sqlite+pysqlite:///' + str(catalog))
        upgrade_catalog(engine)
        return engine
    class CountingExecutor(EnforcingTestTaskExecutor):
        invocations = 0
        def __init__(self):
            from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
            super().__init__(delegate=LocalProcessExecutor(scratch_root=plane.root) if process_workers else None)
            self.prepared_invocations = []
            self.worker_process_ids = []
            if process_workers:
                self.enforcement_capability = self._delegate.enforcement_capability

        def execute_deadline_free(self, runner, task_context, *, progress_contract, progress_callback,
                prepared_contract=None, provenance_requirements=(), native_work_preparer=None, native_entry=None):
            self.invocations += 1
            if prepared_contract is not None:
                prepared_contract.__post_init__()
                prepared_contract.validate_context(task_context)
                self.prepared_invocations.append(prepared_contract)
            if process_workers:
                result = self._delegate.execute_deadline_free(runner, task_context,
                    progress_contract=progress_contract, progress_callback=progress_callback,
                    prepared_contract=prepared_contract, provenance_requirements=provenance_requirements,
                    native_work_preparer=native_work_preparer, native_entry=native_entry)
            else:
                # This older service double records parent preparation only.
                # It supplies no child preflight or native execution evidence.
                assert not provenance_requirements and native_work_preparer is None and native_entry is None
                if prepared_contract is not None:
                    assert not prepared_contract.native_effect
                    task_context = replace(task_context, prepared_invocation=prepared_contract)
                result = self._delegate.execute_deadline_free(runner, task_context,
                    progress_contract=progress_contract, progress_callback=progress_callback)
            self.worker_process_ids.extend(int(row.check_id.removeprefix("synthetic-process-"))
                for row in result.checks if row.check_id.startswith("synthetic-process-"))
            return result
    executor = CountingExecutor()
    service = CampaignExecutionService(repo_root=Path(__file__).resolve().parents[2], artifact_plane=plane,
        engine_factory=engine_factory, catalog_path=catalog, providers=CampaignRuntimeProviderRegistry(()),
        provider_resolver=LayeredCampaignRuntimeProviderResolver(precomposed=CampaignRuntimeProviderRegistry(()), factories=factories),
        executable_binding_aggregate=factories.aggregate,
        issued_extension_payload_resolver=IssuedExtensionPayloadResolver(source=ExternalIssuedExtensionPayloadSource(
                    ExternalIssuedStudyPublisher(artifact_plane=plane, authority_store=authorities, grantee_id='operator.issue-service')),
                            codecs=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY),
        executable_platform_ports=handoff.platform_ports, approval_service=approval, study_authority_store=authorities,
        study_source_closure_inspector=_PassthroughSourceInspector(), executor=executor, enforce_git_identity=False,
        execution_resource_envelope_coordinator=DurableExecutionResourceEnvelopeCoordinator(
            ExternalExecutionResourceEnvelopeStore(plane.root, artifact_plane=plane)))
    api = EmpiricalLawhoodApi(repo_root=tmp_path, external_root=Path(plane.root.contract.canonical_path),
            execution_service=service, approval_service=approval, study_authority_store=authorities)
    if prepare_only:
        return SimpleNamespace(api=api, service=service, executor=executor, package_path=package_path,
            package=package, reveal=reveal, catalog=catalog)
    if exercise_reveal_stop:
        stopped = api.run_campaign(RunCampaignRequest(package_path, confirmed=True))
        assert not stopped.succeeded and stopped.reason_codes == ('OUTCOME_REVEAL_AUTHORITY_REQUIRED',)
        assert executor.invocations == 4
    result = api.run_campaign(RunCampaignRequest(package_path, confirmed=True, reveal_authority_id=reveal.authority_id))
    assert result.succeeded, (result.reason_codes, result.errors)
    assert executor.invocations == 5
    plan = service._load_status_execution_plan(package.run_plan_id)
    receipts = ExternalTaskReceiptStore(plane)
    _, recovery, _, _ = service._load_status_recovery(package.run_plan_id)
    qualification = receipts.read(package.run_plan_id, 'evaluate', recovery.task('evaluate').attempts[0].attempt_id)
    assert qualification is not None
    logical = qualification.output_logical_artifacts[0]
    physical = qualification.output_materializations[0]
    adjudication = decode_canonical_bytes(plane.root.resolve(physical.relative_path, for_write=False).read_bytes(),
                                          ScientificAdjudicationRecord, maximum_bytes=3000)
    return SimpleNamespace(handoff=handoff, factories=factories, discovery=discovery, plane=plane, raw=raw, package=package,
             reveal=reveal, approval=approval, authorities=authorities, api=api, executor=executor,
             catalog=catalog, execution_plan=plan, qualification_receipt=qualification,
             adjudication=adjudication, qualification_logical=logical, result=result)


def test_public_authored_issue_package_execution_reveal_and_receipt_recovery(tmp_path, monkeypatch):
    from empirical_lawhood.api.results import CampaignStatusRequest, ResumeCampaignRequest
    fixture = _public_run_handoff_fixture(tmp_path, monkeypatch, exercise_reveal_stop=True)
    assert fixture.result.payload.scientific_status.value == 'NOT_SUPPORTED'
    retained = fixture.api.campaign_status(CampaignStatusRequest(fixture.package.run_plan_id, include_attempt_history=True))
    assert retained.succeeded
    resumed = fixture.api.resume_campaign(ResumeCampaignRequest(fixture.package.run_plan_id, confirmed=True,
                                                 reveal_authority_id=fixture.reveal.authority_id))
    assert resumed.succeeded, (resumed.reason_codes, resumed.errors)
    assert fixture.executor.invocations == 5
    fixture.catalog.unlink()
    for suffix in ('-wal', '-shm'):
        fixture.catalog.with_name(fixture.catalog.name + suffix).unlink(missing_ok=True)
    recovered = fixture.api.campaign_status(CampaignStatusRequest(fixture.package.run_plan_id, include_attempt_history=True))
    assert recovered.succeeded, (recovered.reason_codes, recovered.errors)
    assert recovered.payload.operational_status == retained.payload.operational_status == 'SUCCEEDED'
    assert recovered.payload.succeeded_task_ids == retained.payload.succeeded_task_ids
    assert tuple((row.receipt_id, row.receipt_sha256) for row in recovered.payload.attempt_history) == tuple(
                  (row.receipt_id, row.receipt_sha256) for row in retained.payload.attempt_history)
    assert fixture.executor.invocations == 5


def test_public_reveal_terminal_retains_actual_revealed_scientific_scope(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure.execution_resource_envelopes import (
        ExternalExecutionResourceEnvelopeStore, read_execution_launch_event,
    )
    from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeEventKind
    fixture = _public_run_handoff_fixture(tmp_path, monkeypatch, reveal_terminal=True)
    assert fixture.adjudication.outcome_access is OutcomeAccess.EVALUATION_REVEALED
    assert fixture.adjudication.visibility_ceiling is VisibilityCeiling.OUTCOME_VISIBLE
    primary = ExternalExecutionResourceEnvelopeStore(fixture.plane.root, artifact_plane=fixture.plane).load(
        f'run-resource-envelope.{fixture.package.run_plan_id}')
    launches = tuple(event for event in primary.events if event.kind is ExecutionResourceEnvelopeEventKind.LAUNCH)
    assert len(launches) == len(fixture.execution_plan.tasks) == 5
    tasks = {cell.cell_id: cell.task_id for cell in primary.spec.task_cells}
    for event in launches:
        published = read_execution_launch_event(artifact_plane=fixture.plane, execution_plan=fixture.execution_plan,
            resource_spec=fixture.package.execution_resource_envelope_spec, run_id=fixture.package.run_plan_id,
            task_id=tasks[event.cell_id], attempt_id=event.attempt_id)
        assert published == event
        assert published.canonical_bytes() == event.canonical_bytes()


def test_actual_issued_common_graph_reconstructs_without_constructor_capture_and_refuses_missing_authority(tmp_path):
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
    from empirical_lawhood.runtime.issued_extension_payloads import IssuedExtensionPayloadResolver, reconstruct_executable_provider, verify_executable_provider_recovery
    original, _, _ = prospective_fixture(typed_outputs=True)
    compilation, authoring, context, raw, _ = _actual_source(original)
    fixture = _issued_fixture(tmp_path, compilation, authoring, context)
    supplier = _FixtureSupplier(compilation, raw)
    factories, ports, _ = _factories(compilation, supplier)
    class SelectionSource:
        reads = 0
        def read_member(self, *, issue_id, member, maximum_bytes):
            self.reads += 1
            payload = compilation.selected_scientific_projection.canonical_bytes()
            assert issue_id == fixture.package.issued_study.issue_id and len(payload) <= maximum_bytes
            assert member.physical_sha256 == sha256(payload).hexdigest()
            return payload
    source = SelectionSource()
    payloads = IssuedExtensionPayloadResolver(source=source, codecs=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY)
    resolver = LayeredCampaignRuntimeProviderResolver(precomposed=CampaignRuntimeProviderRegistry(()), factories=factories)
    binding_ids = tuple(sorted(factory.binding.binding_id for factory in
          (factories.factory(key) for key in factories.binding_ids) if factory.binding.capability_key in
          {manifest.capability_key for manifest in compilation.registry.capabilities}))
    kwargs = dict(registry=compilation.registry, manifest=fixture.package.issued_study,
                  aggregate=factories.aggregate, selected_binding_ids=binding_ids, payload_resolver=payloads,
                  provider_resolver=resolver, platform_ports=ports)
    with pytest.raises(PermissionError, match='prior authorization'):
        reconstruct_executable_provider(**kwargs, authorization_replayed=False)
    assert source.reads == 0 and supplier.calls == 0
    first = reconstruct_executable_provider(**kwargs, authorization_replayed=True)
    assert len(first.provider.runners(compilation.registry)) == 5
    assert first.receipt.scientific_recomputation_count == 0 and source.reads == 1
    second = reconstruct_executable_provider(**kwargs, authorization_replayed=True)
    recovered = verify_executable_provider_recovery(source=first.receipt, recovered=second.receipt)
    assert recovered.scientific_recomputation_count == 0
    assert supplier.calls == 0
