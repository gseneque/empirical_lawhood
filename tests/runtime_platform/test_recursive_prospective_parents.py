# SPDX-License-Identifier: MPL-2.0
"""Actual issued parent custody conformance; synthetic results qualify no real law."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.api.recursive_qualified_parents import authenticate_recursive_qualified_parents
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    ConditionRole, ContributionRole, ScientificConditionScope, ScientificConnectionSpec,
    ScientificRequirementSpec,
)
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_qualified_parents import RecursiveQualifiedParentBinding
from tests.runtime_platform.test_recursive_prospective_workflow import (
    _factories, _issue_public_handoff, _public_run_handoff_fixture, _registrations, _run_public_handoff,
)


def _assess_synthetic_parent(*, requirement, connection, contribution, product, parent_evidence):
    """An installed synthetic consumer validates its exact earlier scientific role."""
    record = parent_evidence.adjudication
    system = parent_evidence.package.system
    source = parent_evidence.package.issued_study.candidate.base_candidate.base_candidate.source_locks[0]
    if (requirement.scope != contribution.scope
        or contribution.scope.instance_id != record.independent_unit_id
        or contribution.scope.quantity_ids != ('receiver',) or contribution.scope.native_units != ('1',)
        or contribution.scope.receiver_id != 'receiver-out' or contribution.scope.clock_id != system.clocks[0].clock_id
        or contribution.scope.source_id != source.source_id or contribution.scope.source_config_sha256 != source.source_config_sha256
        or record.evidence_world_kind.value != 'ANALYTIC_REFERENCE'
        or parent_evidence.package.system.world.label != 'Truth-known w01-stable-linear'
        or record.plumbing_only or record.fixture_scope_id is not None
        or record.reason_codes != ('SYNTHETIC_PARENT_SUPPORTED',)
        or connection.evidence_role is not ContributionRole.QUALIFIED_EVIDENTIAL_PARENT
        or product.record.object_fingerprint != record.fingerprint()):
        raise PermissionError('synthetic parent changes its declared scientific scope or evaluator semantics')


@pytest.fixture(scope='module')
def parent_fixture(tmp_path_factory):
    from empirical_lawhood.adapters.reference_worlds.runtime import REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE
    positive = replace(REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE,
        fixture_id='fixture.synthetic-parent-supported', scientific_status=ScientificStatus.SUPPORTED,
        admission_status=AdmissionStatus.ADMITTED, reason_codes=('SYNTHETIC_PARENT_SUPPORTED',))
    patch = pytest.MonkeyPatch()
    with patch.context() as monkeypatch:
        yield _public_run_handoff_fixture(tmp_path_factory.mktemp('qualified-parent'), monkeypatch,
                                         sealed_fixture=positive, reveal_terminal=True)


def _parent_inputs(fixture):
    receipt, logical, record = fixture.qualification_receipt, fixture.qualification_logical, fixture.adjudication
    source = fixture.package.issued_study.candidate.base_candidate.base_candidate.source_locks[0]
    product = ContributionProduct('product.synthetic-qualified-response', ObjectIdentity.from_record(record.adjudication_id, record),
        ArtifactIdentity(logical.logical_artifact_id, 'qualified-response', logical.payload_schema, logical.content_sha256,
                         logical.media_type, len(record.canonical_bytes())),
        ObjectIdentity.from_record(receipt.receipt_id, receipt), ContributionRole.QUALIFIED_EVIDENTIAL_PARENT,
        EvidenceCeiling.RESPONSE, logical.outcome_access, logical.visibility_ceiling)
    scope = ScientificConditionScope(fixture.package.system.system_id, fixture.package.system.world.world_id,
        source.source_id, ('receiver',), ('1',), 'receiver-out', fixture.package.system.clocks[0].clock_id,
        'Previously issued and separately evaluated finite-horizon synthetic response', source_config_sha256=source.source_config_sha256,
        instance_id=record.independent_unit_id, valid_from=Decimal(0), valid_until=Decimal(1))
    manifest = ContributionManifest('contribution.synthetic-qualified-parent',
        'Does the synthetic issued evaluator support this fixture?', 'Software-only supported parent custody', scope,
        (product,), (ObjectIdentity.from_record(record.adjudication_id, record),), ())
    requirement = ScientificRequirementSpec('requirement.earlier-qualified-response', 'evaluate', ConditionRole.EVIDENTIAL,
        'Use the earlier response while evaluating independent later data', 'Exact prior supported response in declared scope',
        scope, 'evaluate', 'Earlier exposed or unsupported custody cannot satisfy this evidential role',
        (ContributionRole.QUALIFIED_EVIDENTIAL_PARENT,))
    connection = ScientificConnectionSpec('connection.earlier-qualified-response', requirement.requirement_id, None, None,
        'qualified-parent', 'evaluate', 'synthetic-reference-response-claim', ContributionRole.QUALIFIED_EVIDENTIAL_PARENT,
        requirement.falsifier, ObjectIdentity.from_record(manifest.contribution_id, manifest), product.product_id,
        'input.earlier-qualified-response')
    external = RecursiveExternalInput(connection.external_input_id, 'earlier-qualified-response', logical.payload_schema,
        logical.media_type, len(record.canonical_bytes()), logical.outcome_access, logical.visibility_ceiling,
        logical.content_sha256, 'HISTORY')
    link = RecursiveInputLink('edge.earlier-qualified-response', 'evaluate', connection.consumer_input_id,
        external_input_id=external.input_id, scientific_role='HISTORY', requirement_id=requirement.requirement_id,
        connection_id=connection.connection_id)
    original = fixture.handoff.compilation.draft
    draft = replace(original, requirements=(requirement,), connections=(connection,), contribution_parents=(manifest,),
        external_inputs=tuple(sorted((*original.external_inputs, external), key=lambda value: value.input_id)),
        links=tuple(sorted((*original.links, link), key=lambda value: value.edge_id)))
    registrations = tuple(replace(value, input_ports=tuple(sorted((*value.input_ports,
        RecursivePortContract(connection.consumer_input_id, logical.payload_schema, logical.media_type,
                              len(record.canonical_bytes()))), key=lambda port: port.port_id)),
        qualified_parent_assessor=_assess_synthetic_parent) if value.selection.capability_key == 'recursive-fixture.evaluate'
        else value for value in _registrations(fixture.handoff.compilation))
    binding = RecursiveQualifiedParentBinding('binding.synthetic-qualified-parent', external.input_id, manifest.contribution_id,
        product.product_id, ObjectIdentity.from_record(fixture.package.issued_study.issue_id, fixture.package.issued_study),
        ObjectIdentity.from_record(fixture.package.execution_authority.authority_id, fixture.package.execution_authority),
        ObjectIdentity.from_record(fixture.reveal.authority_id, fixture.reveal), receipt.run_id, receipt.task_id,
        receipt.receipt_id, receipt.task_id, receipt.receipt_id, 'evaluate.evaluation',
        ObjectIdentity.from_record(record.adjudication_id, record))
    return draft, registrations, binding


def _authenticate(fixture, draft=None, registrations=None, binding=None):
    default_draft, default_registrations, default_binding = _parent_inputs(fixture)
    return authenticate_recursive_qualified_parents(spec_bindings=(binding or default_binding,),
        draft=draft or default_draft, artifact_writer=fixture.plane, registrations=registrations or default_registrations,
        output_codecs=fixture.handoff.compilation.output_codecs)


def test_actual_positive_issued_parent_replays_complete_custody_without_reexecution(parent_fixture):
    fixture = parent_fixture
    parent, = _authenticate(fixture)
    assert parent.adjudication.scientific_status is ScientificStatus.SUPPORTED
    assert parent.adjudication.admission_status is AdmissionStatus.ADMITTED
    assert parent.product_payload == fixture.adjudication.canonical_bytes()
    assert parent.execution_plan == fixture.execution_plan
    assert fixture.executor.invocations == 5
    assert decode_canonical_bytes(parent.binding.canonical_bytes(), RecursiveQualifiedParentBinding,
                                  maximum_bytes=64 * 1024) == parent.binding


@pytest.mark.parametrize('missing', ['binding', 'assessor'])
def test_qualified_role_cannot_authorize_parent_read_from_matching_labels(parent_fixture, monkeypatch, missing):
    from empirical_lawhood.api import recursive_qualified_parents as owner
    draft, registrations, binding = _parent_inputs(parent_fixture)
    monkeypatch.setattr(owner, '_authenticate', lambda *args: pytest.fail('read before exact role authentication'))
    bindings = () if missing == 'binding' else (binding,)
    if missing == 'assessor':
        registrations = tuple(replace(value, qualified_parent_assessor=None) for value in registrations)
    with pytest.raises(PermissionError):
        authenticate_recursive_qualified_parents(spec_bindings=bindings, draft=draft,
            artifact_writer=parent_fixture.plane, registrations=registrations)


@pytest.mark.parametrize('field', ['issued_study', 'execution_authority', 'reveal_authority', 'adjudication'])
def test_exact_prior_identity_substitution_refuses(parent_fixture, field):
    _, _, binding = _parent_inputs(parent_fixture)
    value = getattr(binding, field)
    changed = replace(binding, **{field: replace(value, object_fingerprint='0' * 64)})
    with pytest.raises(PermissionError):
        _authenticate(parent_fixture, binding=changed)
    assert parent_fixture.executor.invocations == 5


def test_domain_assessor_rejects_changed_unit_quantity_and_false_return(parent_fixture):
    draft, registrations, _ = _parent_inputs(parent_fixture)
    scope = replace(draft.requirements[0].scope, native_units=('volts',))
    changed = replace(draft, requirements=(replace(draft.requirements[0], scope=scope),))
    with pytest.raises(PermissionError, match='scientific scope'):
        _authenticate(parent_fixture, draft=changed)
    false_assessor = tuple(replace(value, qualified_parent_assessor=lambda **kwargs: False)
        if value.qualified_parent_assessor else value for value in registrations)
    with pytest.raises(PermissionError, match='returning None'):
        _authenticate(parent_fixture, registrations=false_assessor)


def test_missing_actual_dependency_receipt_refuses_before_scientific_payload(parent_fixture, monkeypatch):
    from empirical_lawhood.api import recursive_qualified_parents as owner
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    actual = ExternalTaskReceiptStore.read_by_receipt_id
    monkeypatch.setattr(ExternalTaskReceiptStore, 'read_by_receipt_id',
        lambda self, run, task, receipt: None if task == 'prepare' else actual(self, run, task, receipt))
    monkeypatch.setattr(owner, '_output_payload', lambda *args: pytest.fail('protected parent payload read before dependency closure'))
    with pytest.raises(PermissionError, match='dependency'):
        _authenticate(parent_fixture)
    assert parent_fixture.executor.invocations == 5


def test_missing_primary_receipt_pair_refuses_before_scientific_payload(parent_fixture, tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_qualified_parents as owner
    fixture = parent_fixture
    run_id = fixture.package.run_plan_id
    relative = f'runs/{run_id}/receipts/prepare/{run_id}.prepare.attempt-001.json'
    pair = tuple(fixture.plane.root.resolve(relative + suffix, for_write=False) for suffix in ('', '.manifest.json'))
    moved = tuple(tmp_path / path.name for path in pair)
    monkeypatch.setattr(owner, '_output_payload', lambda *args: pytest.fail('parent payload read before actual missing custody refusal'))
    for original, destination in zip(pair, moved, strict=True):
        original.rename(destination)
    try:
        with pytest.raises(PermissionError, match='dependency'):
            _authenticate(fixture)
    finally:
        for original, destination in zip(pair, moved, strict=True):
            destination.rename(original)
    assert fixture.executor.invocations == 5


@pytest.mark.parametrize('field,value', [('clock_id', 'clock.other'), ('source_config_sha256', '1' * 64),
                                      ('instance_id', 'unit.other'), ('receiver_id', 'receiver.other')])
def test_parent_scope_cannot_extend_prior_qualification_by_matching_output(parent_fixture, field, value):
    draft, _, _ = _parent_inputs(parent_fixture)
    requirement = replace(draft.requirements[0], scope=replace(draft.requirements[0].scope, **{field: value}))
    with pytest.raises(PermissionError, match='scientific scope'):
        _authenticate(parent_fixture, draft=replace(draft, requirements=(requirement,)))


def test_parent_reveal_grant_replayed_before_scientific_payload(parent_fixture, monkeypatch):
    from empirical_lawhood.api import recursive_qualified_parents as owner
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    actual = ExternalStudyOperationAuthorityStore.load
    def absent(self, authority_id):
        if authority_id == parent_fixture.reveal.authority_id:
            raise FileNotFoundError('selected actual reveal grant absent')
        return actual(self, authority_id)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', absent)
    monkeypatch.setattr(owner, '_output_payload', lambda *args: pytest.fail('scientific payload read before current reveal grant'))
    with pytest.raises(FileNotFoundError, match='reveal grant'):
        _authenticate(parent_fixture)


def test_changed_complete_external_input_census_refuses_before_parent_payload(parent_fixture, monkeypatch):
    from empirical_lawhood.api import recursive_qualified_parents as owner
    from empirical_lawhood.infrastructure.artifacts import _ScopedArtifactPlane
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    actual = _ScopedArtifactPlane.read_manifest
    logical_id = 'materialization.reference-medium'
    selected_path, _, _ = provider_input_location(parent_fixture.plane, parent_fixture.package.run_plan_id, logical_id)
    intercepted = []
    def substituted(self, relative_path, *, maximum_bytes=None):
        from empirical_lawhood.runtime.artifacts import (
            artifact_publication_batch_id, artifact_publication_commit_relative_path, artifact_publication_member,
        )
        manifest = actual(self, relative_path, maximum_bytes=maximum_bytes)
        if relative_path == selected_path:
            assert manifest.logical.logical_artifact_id == logical_id
            intercepted.append(relative_path)
            logical = replace(manifest.logical, content_sha256='0' * 64)
            members = tuple(artifact_publication_member(logical, manifest.materialization)
                if member.logical_artifact_id == logical.logical_artifact_id else member
                for member in manifest.publication.members)
            batch_id = artifact_publication_batch_id(manifest.publication.publication_scope, members)
            publication = replace(manifest.publication, members=members, publication_batch_id=batch_id,
                commit_marker_relative_path=artifact_publication_commit_relative_path(manifest.publication.publication_scope, batch_id))
            return replace(manifest, logical=logical, publication=publication)
        return manifest
    monkeypatch.setattr(_ScopedArtifactPlane, 'read_manifest', substituted)
    monkeypatch.setattr(owner, '_output_payload', lambda *args: pytest.fail('protected parent payload read before input closure'))
    with pytest.raises(PermissionError, match='external input'):
        _authenticate(parent_fixture)
    assert intercepted and set(intercepted) == {selected_path}


def test_exposed_development_product_cannot_be_relabelled_qualified(parent_fixture):
    draft, registrations, _ = _parent_inputs(parent_fixture)
    product = draft.contribution_parents[0].products[0]
    with pytest.raises(ValueError, match='non-promotable'):
        replace(product, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE)
    with pytest.raises(ValueError, match='non-promotable'):
        replace(product, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    manifest = draft.contribution_parents[0]
    exposed = replace(product, role=ContributionRole.DESIGN_OPERAND, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
                      outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
    manifest = replace(manifest, products=(exposed,))
    changed = replace(draft, contribution_parents=(manifest,), connections=(replace(draft.connections[0],
        supplier_contribution=ObjectIdentity.from_record(manifest.contribution_id, manifest)),))
    with pytest.raises(PermissionError, match='scientific role'):
        _authenticate(parent_fixture, draft=changed, registrations=registrations)


def _later_public_handoff(parent, tmp_path, monkeypatch):
    """Declare another bounded synthetic unit/source before the later public act."""
    from empirical_lawhood.api import recursive_prospective_authoring as owner
    from empirical_lawhood.api.facade import EmpiricalLawhoodApi
    from empirical_lawhood.api.results import CompileCandidateRequest
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring.executable_binding import REGISTRATION
    from empirical_lawhood.adapters.reference_worlds.runtime import REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE
    from empirical_lawhood.infrastructure.recursive_prospective_inputs import RecursiveContentInputSupplier
    from empirical_lawhood.planning.study_issue import HumanProposerAttestation, ImplementationSourceClosure, StudyOperationAuthority
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec, RecursiveProspectiveOperand
    from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig, SourceReadMode
    from empirical_lawhood.runtime.study_issue import project_standard_study_extensions
    from tests.experiment_entry_support import standard_authoring_for_draft
    from tests.prospective_source_capture_fixture import synthetic_capture
    from tests.runtime_platform.test_recursive_prospective_workflow import FixtureCanonicalSource

    plane = parent.plane
    draft, registrations, binding = _parent_inputs(parent)
    original = decode_canonical_bytes((parent.handoff.directory / 'recursive-prospective.json').read_bytes(),
                                     RecursiveProspectiveAuthoringSpec, maximum_bytes=16 * 1024**2)
    unit_id = 'synthetic-later-preparation'
    root = draft.prospective_draft
    system = replace(root.system, independent_unit=replace(root.system.independent_unit, unit_id=unit_id),
                     numerical_views=tuple(replace(view, physical_preparation_id=unit_id) for view in root.system.numerical_views))
    experiment = replace(root.experiment, experiment_id='synthetic-later-experiment', independent_unit_id=unit_id,
        claims=tuple(replace(claim, physical_independent_unit_id=unit_id) for claim in root.experiment.claims),
        assignment=replace(root.experiment.assignment, independent_unit_id=unit_id),
        obligations=replace(root.experiment.obligations,
            support=replace(root.experiment.obligations.support, independent_unit_id=unit_id),
            uncertainty=replace(root.experiment.obligations.uncertainty, independent_unit_id=unit_id)),
        reveal_barrier=replace(root.experiment.reveal_barrier, evaluation_cohort_id='synthetic-later-evaluation-cohort',
            evaluation_manifest_sha256=sha256(b'predeclared-distinct-synthetic-later-evaluation-material').hexdigest()),
        predecessor_experiment_ids=(root.experiment.experiment_id,))
    experiment_identity = ObjectIdentity.from_record(experiment.experiment_id, experiment)
    campaign = replace(root.campaign, campaign_id='synthetic-later-campaign',
        nodes=tuple(replace(node, object_identity=experiment_identity) for node in root.campaign.nodes),
        evidence_state=(experiment_identity,))
    later_source = FixtureCanonicalSource('distinct later synthetic source for ' + unit_id)
    assert later_source.SCHEMA == draft.external_inputs[1].payload_schema
    raw = later_source.canonical_bytes()
    assert raw != parent.raw
    source_sha = sha256(raw).hexdigest()
    source_ref = root.source_materializations[0]
    config = SourceMaterializationConfig('source-config.synthetic-later', source_ref.source_id, source_ref.role, source_sha,
        len(raw), len(raw), draft.external_inputs[1].payload_schema, 'application/json', SourceReadMode.ORDINARY_BOUNDED,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    qualification = replace(original.qualifications[0], content_sha256=source_sha,
                            materialization=replace(original.qualifications[0].materialization, object_fingerprint=source_sha))
    source_ref = replace(source_ref, materialization=qualification.materialization, content_sha256=source_sha,
        source_config_sha256=config.fingerprint(), qualification_receipt=ObjectIdentity.from_record(qualification.receipt_id, qualification))
    root = replace(root, draft_id='draft.synthetic-later', system=system, experiment=experiment, campaign=campaign,
                   evaluation_unit_ids=('unit.synthetic-later',), evaluation_seed_ids=('seed.synthetic-later',),
                   source_materializations=(source_ref,))
    draft = replace(draft, draft_id='draft.recursive-synthetic-later', prospective_draft=root, campaign=campaign,
        operations=tuple(replace(operation, obligation_ids=tuple(sorted(value.replace(
            'synthetic-reference-experiment.', 'synthetic-later-experiment.') for value in operation.obligation_ids)))
            for operation in draft.operations),
        external_inputs=tuple(replace(value, expected_content_sha256=source_sha)
            if value.scientific_role == 'PREPARED_MEDIUM' else value for value in draft.external_inputs))
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=parent.handoff.compilation.registry,
        implementation_commit='a' * 40, qualifications=(qualification,), known_design_inputs=original.known_design_inputs,
        output_codecs=parent.handoff.compilation.output_codecs,
        implementation_sha256=parent.handoff.compilation.candidate_context.implementation_sha256)
    assert compilation.candidate_report.candidate is not None, tuple(
        (value.field_path, value.message) for value in compilation.candidate_report.diagnostics)
    standard, context = standard_authoring_for_draft(compilation.candidate_draft, compilation.candidate_context,
                                                   formal_method_capability_key='recursive-fixture.evaluate')
    outcome = replace(REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE, fixture_id='fixture.synthetic-later-negative')
    operands = tuple(replace(value, content_sha256=source_sha, size_bytes=len(raw))
        if value.logical_artifact_id == source_ref.materialization.object_id else value for value in original.external_operands)
    operands = tuple(replace(value, content_sha256=outcome.fingerprint(), size_bytes=len(outcome.canonical_bytes()))
        if value.outcome_access is OutcomeAccess.EVALUATION_SEALED else value for value in operands)
    parent_external = next(value for value in draft.external_inputs if value.input_id == binding.external_input_id)
    operand = RecursiveProspectiveOperand(parent_external.logical_artifact_id, parent.adjudication.fingerprint(),
        len(parent.adjudication.canonical_bytes()), parent.adjudication.SCHEMA, 'application/json',
        OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)
    spec = replace(original, spec_id='fixture.synthetic-later-public', draft=draft, entry_package=standard.entry_package,
        formal_methods=context.formal_methods, formal_source_inventories=context.source_inventories,
        qualifications=(qualification,), qualified_parent_bindings=(binding,),
        external_operands=tuple(sorted((*operands, operand), key=lambda value: value.logical_artifact_id)))
    original_closure = decode_canonical_bytes((parent.handoff.directory / 'source-closure.json').read_bytes(),
                                             ImplementationSourceClosure, maximum_bytes=1024**2)
    capture = lambda project_root, closure_id: synthetic_capture(closure_id, original_closure.implementation_sha256)
    closure = capture(None, spec.spec_id + '.source-closure').closure
    monkeypatch.setattr(owner, 'capture_target_closure', capture)
    composition = (registrations, compilation.registry, compilation.output_codecs)
    compilation, authoring, _, registrations = owner._compile(spec, closure, composition=composition)
    supplier = RecursiveContentInputSupplier(root=plane.root, operands=owner._operands(spec, compilation))
    factories, _, discovery = _factories(compilation, supplier, outcome, registrations=registrations)
    candidate_context = owner._context(spec, compilation, registrations, plane.root, discovery.candidate_capability_catalog)
    def api_factory(*, repo_root, candidate_context_provider, candidate_capability_catalog):
        return EmpiricalLawhoodApi(repo_root=repo_root, external_root=None,
            candidate_context_provider=candidate_context_provider, candidate_capability_catalog=candidate_capability_catalog,
            extension_bundle_aggregate=discovery, executable_binding_aggregate=factories.aggregate,
            executable_factory_registry=factories, study_extension_codec_registry=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY)
    local = tmp_path / 'inputs'
    local.mkdir()
    payloads = {value.logical_artifact_id: parent.adjudication.canonical_bytes() if value.logical_artifact_id == operand.logical_artifact_id
                else outcome.canonical_bytes() if value.outcome_access is OutcomeAccess.EVALUATION_SEALED else raw for value in spec.external_operands}
    payloads[config.fingerprint()] = config.canonical_bytes()
    bindings = []
    for key, payload in payloads.items():
        path = local / (sha256(key.encode()).hexdigest() + '.json')
        path.write_bytes(payload)
        bindings.append((key, path))
    # Resolve the new candidate source through the actual immutable publisher.
    from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher
    publisher = ExternalCandidateInputPublisher(plane.root)
    for payload in (*payloads.values(), *(row.payload for row in compilation.config_inputs), qualification.canonical_bytes()):
        publisher.publish(payload, maximum_bytes=16 * 1024**2)
    preview = tmp_path / 'preview'
    preview.mkdir()
    for name, value in (('authoring', authoring), ('selection', compilation.selected_scientific_projection), ('decoder', REGISTRATION)):
        (preview / (name + '.json')).write_bytes(value.canonical_bytes())
    result = api_factory(repo_root=tmp_path, candidate_context_provider=candidate_context,
        candidate_capability_catalog=candidate_context.catalog).compile_candidate(CompileCandidateRequest(preview / 'authoring.json',
              (preview / 'selection.json',), (preview / 'decoder.json',)))
    assert result.succeeded, (result.reason_codes, result.errors)
    report = result.payload.report
    extensions, _, _ = project_standard_study_extensions(candidate=report.candidate,
        extension_payload_bytes=(compilation.selected_scientific_projection.canonical_bytes(),), decoder_registrations=(REGISTRATION,),
        extension_materializations=report.extension_materializations)
    spec = replace(spec, resources=replace(spec.resources,
        issued_study_extensions=ObjectIdentity.from_record(extensions.issued_extension_set_id, extensions)))
    project = tmp_path / 'checkout'
    project.mkdir()
    destination = Path(plane.root.contract.canonical_path) / 'later-authoring'
    result = owner.author_recursive_prospective(spec=spec, project_root=project, artifact_writer=plane, output_dir=destination,
        input_bindings=tuple(bindings), composition=composition, api_factory=api_factory,
        candidate_catalog=discovery.candidate_capability_catalog)
    assert result['scientific_authority'] == 'NONE'
    monkeypatch.setattr(owner, 'resolve_authoring_directory', lambda directory, **kwargs: (directory.resolve(), plane.root.contract))
    loaded = owner.load_recursive_prospective_handoff(directory=destination, root=project, storage_profile=object(),
        artifact_writer=plane, composition=composition, candidate_catalog=discovery.candidate_capability_catalog)
    proof = owner.prove_recursive_prospective_handoff(loaded, factory_registry=factories)
    assert proof['scientific_execution_performed'] is False
    assert loaded.compilation.draft.contribution_parents == draft.contribution_parents
    assert loaded.compilation.candidate_draft.evaluation_unit_ids == ('unit.synthetic-later',)
    # Genuine public issuance uses independently supplied accountable test records.
    old_base = parent.handoff.directory.parent.parent
    source_paths = {key: old_base / filename for key, filename in (
        ('attestation', 'proposer-attestation.json'), ('authority', 'custody-authority.json'))}
    paths = {key: tmp_path / (key + '.json') for key in ('authoring', 'expected_candidate', 'attestation', 'authority', 'source_closure')}
    attestation = decode_canonical_bytes(source_paths['attestation'].read_bytes(), HumanProposerAttestation, maximum_bytes=1024**2)
    custody = decode_canonical_bytes(source_paths['authority'].read_bytes(), StudyOperationAuthority, maximum_bytes=1024**2)
    paths['attestation'].write_bytes(attestation.canonical_bytes())
    paths['authority'].write_bytes(custody.canonical_bytes())
    return loaded, factories, discovery, plane, raw, None, paths, custody


def test_genuine_qualified_parent_flows_through_later_public_author_load_issue_and_run(parent_fixture, tmp_path, monkeypatch):
    parts = _later_public_handoff(parent_fixture, tmp_path, monkeypatch)
    issued = _issue_public_handoff(tmp_path, monkeypatch, handoff_parts=parts, namespace='synthetic-later-recursive')
    later = _run_public_handoff(tmp_path, issued_parts=issued)
    assert later.adjudication.independent_unit_id == 'synthetic-later-preparation'
    assert later.adjudication.scientific_status is ScientificStatus.NOT_SUPPORTED
    assert later.adjudication.admission_status is AdmissionStatus.EMPTY
    assert later.package.issued_study != parent_fixture.package.issued_study
    assert later.execution_plan.source_plan != parent_fixture.execution_plan.source_plan
    assert later.executor.invocations == 5 and parent_fixture.executor.invocations == 5
    assert parent_fixture.adjudication.scientific_status is ScientificStatus.SUPPORTED
    assert later.handoff.compilation.draft.contribution_parents[0].products[0].record == ObjectIdentity.from_record(
        parent_fixture.adjudication.adjudication_id, parent_fixture.adjudication)


def test_exposed_method_nomination_fresh_qualification_then_genuine_later_parent_reuse(tmp_path, monkeypatch):
    from tests.runtime_platform.test_recursive_prospective_nomination import _nominated_public_run
    previous_dir = tmp_path / 'nominated-parent'
    previous_dir.mkdir()
    parent, method, original_directory, products, preserved, _ = _nominated_public_run(previous_dir, monkeypatch)
    assert method.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
    assert parent.adjudication.scientific_status is ScientificStatus.SUPPORTED
    child_dir = tmp_path / 'qualified-child'
    child_dir.mkdir()
    parts = _later_public_handoff(parent, child_dir, monkeypatch)
    issued = _issue_public_handoff(child_dir, monkeypatch, handoff_parts=parts, namespace='qualified-nominated-child')
    later = _run_public_handoff(child_dir, issued_parts=issued)
    assert later.adjudication.scientific_status is ScientificStatus.NOT_SUPPORTED
    assert later.adjudication.independent_unit_id != parent.adjudication.independent_unit_id
    assert parent.executor.invocations == 5 and later.executor.invocations == 5
    assert method.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
    assert products
    assert (original_directory / 'inspected-method.json').read_bytes() == method.canonical_bytes()
    assert products['records']['use']['use.result'].canonical_bytes() == preserved[0]
    assert products['receipts']['use'].canonical_bytes() == preserved[1]


def test_complete_multioutput_dependency_custody_joins_exact_logical_ids(tmp_path, monkeypatch):
    from empirical_lawhood.api.facade import EmpiricalLawhoodApi
    from empirical_lawhood.adapters.reference_worlds.runtime import REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from tests.experiment_entry_support import standard_authoring_for_draft
    from tests.runtime_platform import test_recursive_prospective_workflow as workflow
    actual_source = workflow._actual_source
    def multioutput_source(original):
        compilation, _, _, raw, config = actual_source(original)
        registrations = tuple(replace(value, outputs=tuple(sorted((*value.outputs,
            replace(value.outputs[0], output_id='model-z')), key=lambda output: output.output_id)))
            if value.selection.capability_key == 'recursive-fixture.develop-a' else value for value in _registrations(compilation))
        compilation = compile_recursive_wave(draft=compilation.draft, registrations=registrations, registry=compilation.registry,
            implementation_commit='a' * 40, qualifications=compilation.candidate_context.qualifications,
            known_design_inputs=compilation.candidate_context.known_design_inputs, output_codecs=compilation.output_codecs)
        standard, context = standard_authoring_for_draft(compilation.candidate_draft, compilation.candidate_context,
                                                       formal_method_capability_key='recursive-fixture.evaluate')
        return compilation, standard, context, raw, config
    monkeypatch.setattr(workflow, '_actual_source', multioutput_source)
    def show_cause(self, operation, error):
        raise error
    monkeypatch.setattr(EmpiricalLawhoodApi, '_execution_error', show_cause)
    positive = replace(REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE,
        fixture_id='fixture.synthetic-parent-supported', scientific_status=ScientificStatus.SUPPORTED,
        admission_status=AdmissionStatus.ADMITTED, reason_codes=('SYNTHETIC_PARENT_SUPPORTED',))
    fixture = _public_run_handoff_fixture(tmp_path, monkeypatch, sealed_fixture=positive, reveal_terminal=True)
    parent, = _authenticate(fixture)
    task = next(value for value in parent.execution_plan.tasks if value.task_id == 'develop-a')
    assert len(task.outputs) == 2
    assert len({value.logical_artifact_id for value in task.outputs}) == 2
    assert len({value.payload_schema for value in task.outputs}) == 1
    assert fixture.executor.invocations == 5
