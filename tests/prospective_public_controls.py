# SPDX-License-Identifier: MPL-2.0
"""Disclosed software signers and control inputs for the unmodified public CLI.

These records exercise custody and replay only. They are exposed conformance
fixtures, never accountable scientific approval, fresh evidence or qualification.
No source inspector, candidate provider, clock, storage or execution is patched.
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

from empirical_lawhood.kernel.provenance import ObjectIdentity


def _record(path, record):
    with path.open('xb') as stream:
        stream.write(record.canonical_bytes())
    return path


def issue_public_child(*, copied, writer, selected, namespace, invoke,
        previous_registrations=()):
    """Create explicit test inputs; issue and assemble through the real CLI."""
    from empirical_lawhood.api.composition import compose_operator_approval_runtime
    from empirical_lawhood.api.models import StudyIssueSummary, ExecutableStudyIssueSummary, ExperimentPackage, assemble_issued_study_package
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    from empirical_lawhood.kernel.authority import AuthorityAction, SourceAccessClass
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.evidence import OutcomeAccess
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes, validate_stable_id
    from empirical_lawhood.planning.approval import ApprovalCheckerRegistry, AttestationResult, SystemDecisionClock, issue_approval_gate_attestation
    from empirical_lawhood.planning.study_issue import AccountableHumanIdentity, HumanProposerAttestation, StudyAuthorityKind, StudyOperationAuthority
    from empirical_lawhood.runtime.study_issue import ISSUE_PUBLICATION_RELATIVE_ROOT, build_study_approval_proposal
    from tests.approval_support import deterministic_approval_signer
    from tests.runtime_platform.test_study_approval import _checker_registrations

    validate_stable_id(namespace)
    assert namespace.startswith('software.')
    handoff, candidate = selected.handoff, selected.candidate
    base_candidate = candidate.base_candidate
    system = base_candidate.base_candidate.system
    policy = system.authority_policy
    assert AuthorityAction.SIMULATION_EXECUTION in policy.allowed_actions
    scope, = policy.scope_ids
    root = Path(writer.root.contract.canonical_path)
    directory = root / 'software-control-inputs' / namespace
    directory.mkdir(mode=0o700, parents=True)
    clock = SystemDecisionClock()
    now = clock.now_utc()
    expires = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(timespec='seconds').replace('+00:00', 'Z')
    human = AccountableHumanIdentity('human.' + namespace, 'role.disclosed-software-fixture',
        'identity.disclosed-software-fixture', sha256(namespace.encode()).hexdigest())
    person = ObjectIdentity.from_record(human.human_id, human)
    attestation = HumanProposerAttestation('attestation.' + namespace + '.base',
        ObjectIdentity.from_record(base_candidate.candidate_id, base_candidate), person, human.human_id,
        base_candidate.base_candidate.design_origin.origin_id,
        base_candidate.base_candidate.design_input_ids,
        base_candidate.base_candidate.source_qualification_receipts,
        base_candidate.base_candidate.authoring_materialization.raw_materialization_sha256,
        base_candidate.base_candidate.semantic_config_sha256,
        True, True, False, False, now, OutcomeAccess.OUTCOME_BLIND)
    custody = StudyOperationAuthority('authority.' + namespace + '.base-custody',
        StudyAuthorityKind.CUSTODY_PUBLICATION,
        ObjectIdentity.from_record(base_candidate.candidate_id, base_candidate), None, person,
        'operator.issue-service', 'scope.' + namespace + '.custody', writer.root.contract.storage_root_id,
        ISSUE_PUBLICATION_RELATIVE_ROOT, False, True, False, False, False, now, expires,
        OutcomeAccess.OUTCOME_BLIND)
    authorities = ExternalStudyOperationAuthorityStore(writer)
    authorities.persist(custody)
    base_inputs = {name: _record(directory / (name + '.json'), value) for name, value in (
        ('base-authoring', handoff.authoring.base), ('base-candidate', base_candidate),
        ('base-attestation', attestation), ('base-custody', custody))}
    issued = invoke(copied, 'issue', '--spec', str(base_inputs['base-authoring']),
        '--expected-candidate', str(base_inputs['base-candidate']),
        '--proposer-attestation', str(base_inputs['base-attestation']),
        '--custody-authority', str(base_inputs['base-custody']),
        '--source-closure', str(handoff.directory / 'source-closure.json'), '--yes', '--format', 'json',
        authoring_dir=handoff.directory)
    base = decode_canonical_bytes(canonical_json_document_bytes(issued['payload']), StudyIssueSummary, maximum_bytes=None)
    assert base.confirmed and not base.workers_created
    extension_attestation = replace(attestation, attestation_id='attestation.' + namespace + '.extension',
        candidate=ObjectIdentity.from_record(candidate.candidate_id, candidate),
        raw_materialization_sha256=sha256(b'application/json\x00' + handoff.authoring.canonical_bytes()).hexdigest())
    extension_custody = replace(custody, authority_id='authority.' + namespace + '.extension-custody',
        subject=ObjectIdentity.from_record(candidate.candidate_id, candidate))
    authorities.persist(extension_custody)
    ext_attestation_path = _record(directory / 'extension-attestation.json', extension_attestation)
    ext_custody_path = _record(directory / 'extension-custody.json', extension_custody)
    issued = invoke(copied, 'issue-extensions', '--spec', str(handoff.directory / 'authoring.json'),
        '--extension-payload', str(handoff.directory / 'scientific-projection.json'),
        '--decoder-registration', str(handoff.directory / 'decoder.json'),
        '--expected-candidate', str(handoff.directory / 'candidate.json'),
        '--base-issue', base.manifest.issue_id, '--proposer-attestation', str(ext_attestation_path),
        '--custody-authority', str(ext_custody_path), '--yes', '--format', 'json',
        authoring_dir=handoff.directory)
    extension = decode_canonical_bytes(canonical_json_document_bytes(issued['payload']), ExecutableStudyIssueSummary, maximum_bytes=None)
    assert extension.confirmed and not extension.workers_created

    registrations = {row.gate_id: row for row in previous_registrations}
    for row in _checker_registrations(policy.required_gate_ids):
        assert registrations.setdefault(row.gate_id, row) == row
    registry = ApprovalCheckerRegistry('registry.' + namespace,
        tuple(registrations[key] for key in sorted(registrations)))
    trust = _record(directory / 'checker-registry.json', registry)
    trust.chmod(0o600)
    approval = compose_operator_approval_runtime(artifact_plane=writer, checker_trust_path=trust)

    def approve(manifest, receipt, suffix):
        proposal = build_study_approval_proposal(issued_study=manifest, publication_receipt=receipt)
        identity = approval.service.freeze_study_proposal(proposal=proposal, system=system,
            requested_scope_id=scope, implementation_commit=manifest.implementation_commit,
            authority_action=AuthorityAction.SIMULATION_EXECUTION, source_access=SourceAccessClass.NONE)
        authorization_id = 'authorization.' + namespace + '.' + suffix
        signed = []
        for row in registry.registrations:
            if row.gate_id not in policy.required_gate_ids:
                continue
            time = clock.now_utc()
            signed.append(approval.attestation_store.persist(issue_approval_gate_attestation(
                registration=row, signer=deterministic_approval_signer(row.gate_id),
                attestation_id='attestation.' + namespace + '.' + suffix + '.' + row.gate_id,
                authorization_id=authorization_id, subject=identity, result=AttestationResult.PASSED,
                checked_at_utc=time, issued_at_utc=time, information_cutoff=proposal.decision_cutoff)))
        approved = approval.service.authorize(policy=policy, frozen_proposal=identity,
            attestations=tuple(signed), authorization_id=authorization_id, approver_id=policy.delegate_id)
        assert approved.decision_clock_id == clock.clock_id
        authority = replace(custody, authority_id='authority.' + namespace + '.' + suffix + '.execution',
            kind=StudyAuthorityKind.EXPERIMENT_EXECUTION,
            subject=ObjectIdentity.from_record(manifest.issue_id, manifest),
            prerequisite_authority=ObjectIdentity.from_record(approved.authorization_id, approved),
            grantee_id='operator.execution-service', storage_root_id=None, relative_root=None,
            allows_external_publication=False, allows_execution=True,
            outcome_access=OutcomeAccess.EVALUATION_SEALED, issued_at_utc=clock.now_utc())
        authorities.persist(authority)
        return approval.study_proposal_store.load(identity.object_id), approved, authority

    base_frozen, base_approval, base_execution = approve(base.manifest, base.publication_receipt, 'base')
    base_package = assemble_issued_study_package(issued_study=base.manifest,
        publication_receipt=base.publication_receipt, frozen_proposal=base_frozen,
        scientific_approval=base_approval, execution_authority=base_execution,
        run_plan_id='run.' + namespace + '.base', grantee_id='operator.execution-service', at_utc=clock.now_utc())
    frozen, approved, execution = approve(extension.manifest, extension.publication_receipt, 'extension')
    resources = replace(handoff.resources, issued_study_extensions=ObjectIdentity.from_record(
        extension.manifest.issued_extensions.issued_extension_set_id, extension.manifest.issued_extensions))
    controls = {name: _record(directory / (name + '.json'), value) for name, value in (
        ('base-package', base_package), ('issued-study', extension.manifest),
        ('publication-receipt', extension.publication_receipt), ('frozen-proposal', frozen),
        ('scientific-approval', approved), ('execution-authority', execution), ('resource-envelope', resources))}
    # Public compact emission belongs to the local operator input tree.
    # The exact assembled bytes are then copied as an explicit operation input;
    # every ordinary consumer still replays their issue/execution authority.
    local = root.parent / 'software-control-emission' / namespace
    local.mkdir(mode=0o700, parents=True)
    assert not local.resolve().is_relative_to(root.resolve())
    controls['base-package'] = _record(local / 'base-package.json', base_package)
    emitted_path = local / 'execution-package.json'
    arguments = [arg for key, path in controls.items() for arg in ('--' + key, str(path))]
    assembled = invoke(copied, 'assemble-package', *arguments, '--run-plan-id', 'run.' + namespace,
        '--grantee-id', 'operator.execution-service', '--at-utc', clock.now_utc(),
        '--emit', emitted_path.name, '--format', 'json', authoring_dir=handoff.directory, checker_trust=trust)
    assert assembled['status'] == 'SUCCEEDED' and emitted_path.is_file()
    raw = emitted_path.read_bytes()
    package = decode_canonical_bytes(raw, ExperimentPackage, maximum_bytes=None)
    assert package.canonical_bytes() == raw
    summary = assembled['payload']
    assert summary['authority_replayed'] and not summary['executed']
    assert summary['local_package_sha256'] == sha256(raw).hexdigest()
    assert summary['package_fingerprint'] == package.fingerprint()
    package_path = _record(directory / emitted_path.name, package)
    assert package_path.read_bytes() == raw
    reveal = replace(execution, authority_id='authority.' + namespace + '.reveal',
        kind=StudyAuthorityKind.OUTCOME_REVEAL,
        prerequisite_authority=ObjectIdentity.from_record(execution.authority_id, execution),
        grantee_id='operator.evaluator-service', allows_execution=False, allows_reveal=True,
        outcome_access=OutcomeAccess.EVALUATOR_REVEAL, issued_at_utc=clock.now_utc())
    authorities.persist(reveal)
    return SimpleNamespace(package_path=package_path, run_id='run.' + namespace, reveal=reveal,
        checker_trust=trust, registrations=registry.registrations)
