# SPDX-License-Identifier: MPL-2.0
"""Real publication/validator custody with disclosed, unexecuted receipt premises."""
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.configured_e3_closeout_custody import ClosedE3Custody
from empirical_lawhood.api.configured_e3_retained_custody import RetainedE3Custody
from empirical_lawhood.api.configured_e3_unfinished_custody import UnfinishedE3Custody
from empirical_lawhood.api import configured_e3_retained_assembly as assembly
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
from empirical_lawhood.runtime.artifacts import (
    ArtifactProfile, ArtifactSemanticValidation, ArtifactSemanticValidationRegistration,
    ArtifactSemanticValidationRegistry, ArtifactWriteRequest,
)
from tests.runtime_platform.test_artifact_verification_scope import _publication


def _custody(kind, **values):
    return kind(**{field.name: values.get(field.name) for field in fields(kind)})


@pytest.fixture
def imported(tmp_path):
    plane, _ = _publication(tmp_path, count=1)
    revoked, accesses = set(), []
    owners, payloads = {}, {}
    for label in ('earlier', 'later'):
        node, logical_id = 'task.disclosed.' + label, 'artifact.disclosed.' + label
        record = ObjectIdentity('subject.disclosed.' + label, ObjectIdentity.SCHEMA, '1.0.0', 'a' * 64)
        validation = ArtifactSemanticValidation('validator.disclosed.' + label, '1.0.0', 'b' * 64,
            record.SCHEMA, ArtifactProfile.CANONICAL_JSON, ('schema', 'value', 'version'),
            tuple(sorted(record.to_document()['value'])), (('version', record.VERSION),))
        registry = ArtifactSemanticValidationRegistry('registry.disclosed.' + label,
            (ArtifactSemanticValidationRegistration(logical_id, validation),))
        writer = plane.with_semantic_validation_registry(registry)
        publication = writer.write(ArtifactWriteRequest(logical_id, label + '/product.json', record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.disclosed.' + label, label,
            record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.EVALUATION_SEALED,
            semantic_validation=validation))
        # These receipt premises carry real publication bindings but are not
        # scientific receipts and never enter a native/issued result reader.
        receipt = SimpleNamespace(output_logical_artifacts=(publication.logical,),
            output_materializations=(publication.materialization,))

        def access(label=label):
            accesses.append(label)
            if label in revoked:
                raise PermissionError('disclosed access revoked: ' + label)

        owners[label] = _custody(UnfinishedE3Custody, writer=writer, receipts={node: receipt}, require_access=access)
        external = RecursiveExternalInput('external.' + logical_id, logical_id, record.SCHEMA, 'application/json',
            len(record.canonical_bytes()), OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.DEVELOPMENT_ONLY,
            record.fingerprint(), 'HISTORY')
        payloads[label] = SimpleNamespace(node=node, publication=publication, external=external, raw=record.canonical_bytes())
    earlier, later = owners['earlier'], owners['later']
    original = _custody(ClosedE3Custody, writer=later.writer, predecessor=earlier,
        receipts={**earlier.receipts, **later.receipts}, require_access=later.require_access)
    retained = {row.external.logical_artifact_id: (row.node, row.publication.logical, row.publication.materialization)
        for row in payloads.values()}
    return SimpleNamespace(original=original, earlier=earlier, later=later, retained=retained,
        payloads=payloads, revoked=revoked, accesses=accesses)


def _read(case, label, **options):
    return assembly._original_input(original=options.get('original', case.original), retained_files=case.retained,
        external=options.get('external', case.payloads[label].external), original_run_id='run.disclosed')


def test_imported_outputs_keep_their_producing_semantic_registry(imported):
    case = imported
    first = case.payloads['earlier']
    # This is the exact prior failure: a later plan has no registration for
    # the earlier output, even though both plans share one physical root.
    with pytest.raises(ArtifactIdentityConflict, match='registered semantic validator'):
        case.original.writer.verify_manifest(case.original.writer.read_manifest(first.publication.materialization.relative_path))
    for label, owner in (('earlier', case.earlier), ('later', case.original)):
        producer, selected, manifest, raw = _read(case, label)
        row = case.payloads[label]
        assert selected is owner and producer == row.node
        assert raw == row.raw
        assert (manifest.logical, manifest.materialization) == (row.publication.logical, row.publication.materialization)
        assert manifest.logical.semantic_validation == owner.writer.semantic_validations.registrations[0].validation
    assert 'earlier' in case.accesses and 'later' in case.accesses


@pytest.mark.parametrize('damage', ('receipt', 'producer', 'bytes', 'visibility', 'access'))
def test_imported_output_copy_refuses_changed_custody(imported, damage):
    case = imported
    row = case.payloads['earlier']
    external = row.external
    if damage == 'receipt':
        case.earlier.receipts[row.node].output_materializations = ()
    elif damage == 'producer':
        case.retained[row.external.logical_artifact_id] = ('task.disclosed.foreign',
            row.publication.logical, row.publication.materialization)
    elif damage == 'bytes':
        case.earlier.writer.root.resolve(row.publication.materialization.relative_path, for_write=False).write_bytes(row.raw + b' ')
    elif damage == 'visibility':
        external = replace(external, visibility_ceiling=VisibilityCeiling.PROSPECTIVE)
    else:
        case.revoked.add('earlier')
    with pytest.raises((PermissionError, ArtifactIdentityConflict)):
        _read(case, 'earlier', external=external)


def test_imported_output_copy_rechecks_access_after_read(imported, monkeypatch):
    original_read = assembly.read_bounded_bytes

    def revoke_after_read(*args, **kwargs):
        result = original_read(*args, **kwargs)
        imported.revoked.add('earlier')
        return result

    monkeypatch.setattr(assembly, 'read_bounded_bytes', revoke_after_read)
    with pytest.raises(PermissionError, match='revoked'):
        _read(imported, 'earlier')


def test_imported_copy_retains_producing_scope_final_byte_guard(imported):
    case = imported
    row = case.payloads['earlier']
    with pytest.raises(ArtifactIdentityConflict, match='changed'):
        with case.earlier.writer.read_context() as reading:
            original = replace(case.original, predecessor=replace(case.earlier, writer=reading))
            assert _read(case, 'earlier', original=original)[-1] == row.raw
            reading.root.resolve(row.publication.materialization.relative_path, for_write=False).write_bytes(row.raw + b' ')


@pytest.mark.parametrize('kind', (RetainedE3Custody, UnfinishedE3Custody))
def test_single_producer_copy_keeps_its_original_owner(imported, kind):
    current = imported.earlier
    original = _custody(kind, writer=current.writer, receipts=current.receipts, require_access=current.require_access)
    assert _read(imported, 'earlier', original=original)[1] is original
    with pytest.raises(PermissionError, match='producing receipt'):
        original.product_source('task.disclosed.foreign')
