# SPDX-License-Identifier: MPL-2.0
"""Real package/grant reads with disclosed receipt metadata, software only.

Literal product and receipt locators isolate E4's repeated control reads. They
do not claim four completed scientific products or authorize native work.
"""
from collections import Counter
from contextlib import nullcontext
from types import SimpleNamespace
import sys

import pytest

from empirical_lawhood.api import matrix_programme_e4_inputs as owner
from empirical_lawhood.api import recursive_qualified_parents as parents
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, ArtifactIdentityConflict
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.decoding import _decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401
from tests.test_selected_e3_current_access import literal_originals, evidence


def _case(f, monkeypatch):
    originals = literal_originals(f, f.control.reveal)
    lineage = evidence(originals).produced_input_parents
    logical = SimpleNamespace(visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        outcome_access=OutcomeAccess.EVALUATION_SEALED)
    exported = SimpleNamespace(publication=SimpleNamespace(logical=SimpleNamespace(
        lineage_parents=lineage, parent_visibility_ceilings=tuple(value.visibility_ceiling for value in lineage),
        outcome_access=logical.outcome_access, visibility_ceiling=logical.visibility_ceiling)))

    def metadata(writer, original, expected, *, _control_reader=None, _issued_reader=None):
        assert expected == original.record
        package = parents._actual_package(writer, original.prior_execution.run_id, control_reader=_control_reader)
        issued, reveal = parents._replay_parent_authority(original, package, writer, _issued_reader=_issued_reader)
        # Only the unrelated receipt/output join is disclosed. Package, issue,
        # grants, scope, bytes and the E4 producer-lineage join remain real.
        return package, issued, reveal, None, logical, ('disclosed.e3',)

    monkeypatch.setattr(owner, '_original_product_metadata', metadata)
    return originals, exported


def test_e4_publication_reads_share_the_already_verified_package_body(
        actual_issued_current_task_controls, monkeypatch):  # noqa: F811
    f = actual_issued_current_task_controls
    originals, _ = _case(f, monkeypatch)
    with f.control.service.artifact_plane.read_context() as writer:
        with owner._original_e3_metadata_context(writer) as read:
            package, issued, *_ = read(originals[0])
            assert issued == package.issued_study
            assert issued is package.issued_study
            repeated = read(originals[1])
            assert repeated[0] is package and repeated[1] is issued
    assert not f.control.executor.invocations


@pytest.mark.parametrize('shared,custom', ((False, False), (True, False), (True, True)))
def test_e4_access_reuses_exact_packages_without_reusing_grant_decisions(
        actual_issued_current_task_controls, monkeypatch, record_property, shared, custom):  # noqa: F811
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    originals, exported = _case(f, monkeypatch)
    if custom:
        original_verify = ExternalArtifactPlane.verify_manifest
        def verify(current, *args, **kwargs):
            return original_verify(current, *args, **kwargs)
        monkeypatch.setattr(ExternalArtifactPlane, 'verify_manifest', verify)
    counts = Counter()
    def observe(frame, event, _arg):
        if event != 'call':
            return
        if frame.f_code is _decode_canonical_bytes.__code__:
            if frame.f_locals['record_type'] is type(f.control.package):
                counts['package_decodes'] += 1
            if frame.f_locals['record_type'] is type(f.control.package.issued_study.base):
                counts['issued_base_decodes'] += 1
        if frame.f_code is ExternalStudyOperationAuthorityStore.load.__code__:
            counts['fresh_grant_loads'] += 1
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        with plane.read_context() as writer:
            with (owner._original_e3_metadata_context(writer) if shared else nullcontext(None)) as read:
                for _ in range(3):
                    owner._require_original_e3_access(writer=writer, original_e3=exported,
                        original_products=originals, read_metadata=read)
    finally:
        sys.setprofile(previous)
    record_property('actual_control_work', dict(counts))
    expected = 1 if shared and not custom else 12
    # The package already constructs the complete immutable issued base.
    # Its original publication compares every byte without a second decode.
    expected_base = 0 if shared and not custom else 12
    assert counts == Counter(package_decodes=expected, issued_base_decodes=expected_base, fresh_grant_loads=48)
    if shared:
        with pytest.raises(PermissionError, match='ended'):
            read(originals[0])
    assert not f.control.executor.invocations


@pytest.mark.parametrize('damage', ('revoked', 'package-bytes'))
def test_e4_metadata_reuse_keeps_current_access_and_final_original_bytes(
        actual_issued_current_task_controls, monkeypatch, damage):  # noqa: F811
    from tests.test_reduced_artifact_verification import _mask_changed_stat
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    originals, _ = _case(f, monkeypatch)
    with pytest.raises((PermissionError, ArtifactIdentityConflict)):
        with plane.read_context() as writer, owner._original_e3_metadata_context(writer) as read:
            read(originals[0])
            if damage == 'revoked':
                load = ExternalStudyOperationAuthorityStore.load
                def revoked(store, identity):
                    if identity == f.control.reveal.authority_id:
                        raise PermissionError('actual stored reveal revoked')
                    return load(store, identity)
                monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', revoked)
            else:
                path = plane.root.resolve('runs/' + f.control.package.run_plan_id + '/plans/campaign-package.json',
                    for_write=False)
                raw = path.read_bytes()
                _mask_changed_stat(monkeypatch, path)
                path.write_bytes(b'[' + raw[1:])
            read(originals[0])
    assert not f.control.executor.invocations
