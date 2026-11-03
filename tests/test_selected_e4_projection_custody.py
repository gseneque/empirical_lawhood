# SPDX-License-Identifier: MPL-2.0
"""Actual score publication and process transport; disclosed receipt seam."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.selected_e4_case_projection import original_score_projections
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.test_matrix_dense_response_measurements import assay  # noqa: F401
from tests.test_reduced_artifact_verification import _mask_changed_stat
from tests.test_selected_e4_parallel_projection import _matched_record


@pytest.mark.parametrize('damage', (None, 'body', 'access'))
def test_published_case_pipeline_uses_selected_pool_and_retains_final_guards(assay, tmp_path, monkeypatch, damage):  # noqa: F811
    payload, protocol, panels, _ = _matched_record(assay, available=False)
    score = decode_canonical_bytes(payload[0], ScheduledResponseScore, maximum_bytes=len(payload[0]))
    plane, _ = _publication(tmp_path, 1)
    plane.maximum_parallel_verifications = 8
    roots = tuple('exposed.root.' + str(index) for index in range(8))
    requests, protocols = [], {}
    for root in roots:
        value = replace(score, score_id='score.' + root, root_id=root)
        protocols[root] = SimpleNamespace(**{**vars(protocol), 'public_source': SimpleNamespace(
            **{**vars(protocol.public_source), 'root': SimpleNamespace(root_id=root, independent_group_id=score.independent_group_id)})})
        requests.append(ArtifactWriteRequest('artifact.' + root, 'scores/' + root + '.json', value.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'exposed.scores', 'scores', value.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    publications = plane.write_batch(tuple(requests))
    receipts, rows = {}, []
    for root, publication in zip(roots, publications, strict=True):
        task = owner.local_node(root, 'response-score')
        receipts[task] = SimpleNamespace(output_logical_artifacts=(publication.logical,),
            output_materializations=(publication.materialization,))
        rows.append(dict(task_id=task, schema=score.SCHEMA, logical_artifact_id=publication.logical.logical_artifact_id,
            sha256=publication.logical.content_sha256))
    products = dict(receipts=receipts, product_index=rows)
    programme = SimpleNamespace(cases=tuple(SimpleNamespace(root_id=root) for root in (*roots, 'exposed.missing')))
    bank = SimpleNamespace(source_index=lambda: {}, source=lambda root, **_: root,
        response_selection=SimpleNamespace(validate_source=lambda root: (protocols.get(root, protocol), panels)))
    current = True
    def access():
        if not current:
            raise PermissionError('current original access revoked')
    original_access = SimpleNamespace(require_current=access)

    def read():
        with plane.read_context() as reading:
            pool = reading._read_verification.canonical_pool
            project = pool.project_ordered
            def after_projection(*args):
                nonlocal current
                result = project(*args)
                assert pool.projected_records == 9 and len(pool.worker_pids) == 8
                if damage == 'access':
                    current = False
                elif damage == 'body':
                    path = plane.root.resolve(publications[0].materialization.relative_path, for_write=False)
                    _mask_changed_stat(monkeypatch, path)
                    path.write_bytes(b'[' + path.read_bytes()[1:])
                return result
            monkeypatch.setattr(pool, 'project_ordered', after_projection)
            return original_score_projections(writer=reading, products=products, programme=programme,
                bank=bank, original_input_access=original_access)
    if damage is None:
        results = read()
        assert tuple(row.root_id for row in results[:-1]) == roots and results[-1] is None
        assert all(row.disposition == 'NO_ORIGIN' and row.paired_log_targets == (None,) * 58 for row in results[:-1])
    else:
        with pytest.raises((PermissionError, ArtifactIdentityConflict)):
            read()
