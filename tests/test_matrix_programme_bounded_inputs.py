"""Exposed custody controls for bounded programme input reads."""
import os

import pytest

from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from tests.test_matrix_programme_source_continuation import metadata_case  # noqa: F401


def options(case, writer):
    return dict(writer=writer, commitment=case.commitment,
        maximum_source_bytes=case.case.request.metadata_budget.source_scan_bytes)


def test_exact_values_and_lifetime(metadata_case):  # noqa: F811
    writer = metadata_case.case.writer
    with authenticated_programme_inputs(**options(metadata_case, writer)) as expected:
        with writer.read_context() as reading:
            with authenticated_programme_inputs(**options(metadata_case, reading)) as first:
                with authenticated_programme_inputs(**options(metadata_case, reading)) as second:
                    assert first == second == expected
                    assert first.scientific_design is second.scientific_design
            reading.require_verification_snapshot()
        with pytest.raises(ArtifactIdentityConflict, match='ended'):
            reading.require_verification_snapshot()
    with authenticated_programme_inputs(**options(metadata_case, writer)) as third:
        assert third == expected
        assert third.scientific_design is not expected.scientific_design


@pytest.mark.parametrize('change', ('body', 'restored-mtime', 'sidecar', 'commit', 'sibling', 'missing-sibling'))
def test_nested_current_custody_refuses_before_yield(metadata_case, change):  # noqa: F811
    writer = metadata_case.case.writer
    publication = metadata_case.commitment.publication
    if change in ('sibling', 'missing-sibling'):
        publication = metadata_case.continued.commitments.scientific_design.publication
    path = writer.root.resolve(publication.materialization.relative_path, for_write=False)
    if change == 'sidecar':
        path = path.with_name(path.name + '.manifest.json')
    elif change == 'commit':
        path = writer.root.resolve(writer.read_manifest(publication.materialization.relative_path)
            .publication.commit_marker_relative_path, for_write=False)
    before, stat = path.read_bytes(), path.stat()
    try:
        with pytest.raises((PermissionError, ValueError, ArtifactIdentityConflict)):
            with writer.read_context() as reading:
                with authenticated_programme_inputs(**options(metadata_case, reading)):
                    if change == 'missing-sibling':
                        path.unlink()
                    else:
                        path.write_bytes(bytes([before[0] ^ 1]) + before[1:])
                    if change == 'restored-mtime':
                        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                    with authenticated_programme_inputs(**options(metadata_case, reading)):
                        pytest.fail('changed original custody reached a consumer')
    finally:
        path.write_bytes(before)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))


def test_current_access_revocation_refuses(metadata_case):  # noqa: F811
    current, calls = [True], []
    def guard(manifest):
        calls.append(manifest.logical.logical_artifact_id)
        if not current[0]:
            raise PermissionError('exposed current access revoked')
    with pytest.raises(PermissionError, match='access revoked'):
        with metadata_case.case.writer.read_context(before_member=guard) as reading:
            with authenticated_programme_inputs(**options(metadata_case, reading)):
                assert calls
                current[0] = False
                with authenticated_programme_inputs(**options(metadata_case, reading)):
                    pytest.fail('revoked access reached a consumer')


def test_nested_budget_stays_current(metadata_case):  # noqa: F811
    with metadata_case.case.writer.read_context() as reading:
        with authenticated_programme_inputs(**options(metadata_case, reading)):
            selected = options(metadata_case, reading)
            selected['maximum_source_bytes'] = 1
            with pytest.raises(ValueError, match='source byte budget'):
                with authenticated_programme_inputs(**selected):
                    pytest.fail('reused records bypassed current budget')


def test_custom_reader_falls_back(metadata_case):  # noqa: F811
    writer = metadata_case.case.writer
    original, calls = writer.verification_scope, []
    def scope(**kwargs):
        calls.append(True)
        return original(**kwargs)
    assert 'verification_scope' not in vars(writer)
    writer.verification_scope = scope
    try:
        with authenticated_programme_inputs(**options(metadata_case, writer)) as actual:
            assert actual == metadata_case.continued
        assert calls == [True]
    finally:
        del writer.verification_scope


@pytest.mark.parametrize('registry', ('semantic', 'format'))
def test_changed_validation_registry_revalidates_physical_members(metadata_case, registry):  # noqa: F811
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
    from empirical_lawhood.runtime.artifacts import ArtifactSemanticValidationRegistry
    from tests.test_artifact_read_context import _work
    with metadata_case.case.writer.read_context() as reading:
        with authenticated_programme_inputs(**options(metadata_case, reading)) as first:
            with _work() as same:
                with authenticated_programme_inputs(**options(metadata_case, reading)) as repeated:
                    assert repeated == first
            assert same['payloads'] == 0
            changed = reading.with_semantic_validation_registry(
                ArtifactSemanticValidationRegistry('exposed.benchmark.changed-registry', ()))
            if registry == 'format':
                changed = reading.with_semantic_validation_registry(reading.semantic_validations)
                changed.validators = ArtifactProfileValidatorRegistry(binary_codecs=operation_storage_codecs())
            with _work() as other:
                with authenticated_programme_inputs(**options(metadata_case, changed)) as actual:
                    assert actual == first
            assert other['payloads'] > 0
