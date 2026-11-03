# SPDX-License-Identifier: MPL-2.0
"""Independent consistency adversaries; uninstalled records grant no authority.

All publications and streams below are exposed fixture metadata. These checks
exercise no acquisition, TRAIN payload, runtime worker, signature or source
qualification. Complete byte authentication remains an API responsibility.
"""

from dataclasses import replace
from hashlib import sha256
import json

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_protocol as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as sr
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from tests import test_matrix_e3_protected_source_records as producer
from tests.test_matrix_factor_confirmation_eligibility import publish, stock
from tests.test_matrix_parameter_history import source as parameter_template
from tests.test_matrix_scheduled_history import scheduled


@pytest.fixture(scope='module')
def case(tmp_path_factory):
    root = tmp_path_factory.mktemp('independent-protected-sources')
    exposed = stock.__wrapped__(root, parameter_template().provenance)
    return producer.fixture(scheduled.__wrapped__(exposed))


@pytest.fixture(scope='module')
def responses(case):
    return producer.response_fixture(case)


def _protocol_references(selection, protocols):
    return replace(selection, root_protocols=tuple((p.public_source.root.root_id,
        ObjectIdentity.from_record(p.protocol_id, p)) for p in protocols))


def test_shared_template_bytes_cannot_have_conflicting_member_hashes(case, responses):
    selection, protocols, panels = responses
    first = protocols[0]
    member = first.templates.members[0]
    changed = replace(first.templates, members=(replace(member, sha256='f' * 64), *first.templates.members[1:]))
    protocols = (replace(first, templates=changed), *protocols[1:])
    selection = _protocol_references(selection, protocols)
    # The whole NPZ identity/publication remains identical in every protocol;
    # only one root now attributes different values to a named member.
    assert protocols[0].templates.array_artifact == protocols[1].templates.array_artifact
    assert protocols[0].templates.members != protocols[1].templates.members
    with pytest.raises(ValueError):
        producer.validate_responses(case, selection, protocols, panels)


def test_template_publication_must_retain_its_matrix_array_codec_profile(case, responses):
    selection, protocols, panels = responses
    original, = selection.template_publications
    validation = replace(original.logical.generic_validation, profile=ArtifactProfile.RAW_SOURCE_BYTES)
    semantic = original.logical.semantic_validation
    logical = replace(original.logical, profile=ArtifactProfile.RAW_SOURCE_BYTES,
        generic_validation=validation, semantic_validation=None if semantic is None else
            replace(semantic, profile=ArtifactProfile.RAW_SOURCE_BYTES))
    changed = replace(original, logical=logical)
    selection = replace(selection, template_publications=(changed,))
    assert changed.logical.content_sha256 == original.logical.content_sha256
    assert changed.materialization == original.materialization
    with pytest.raises(ValueError):
        producer.validate_responses(case, selection, protocols, panels)


def test_audit_reference_media_must_match_actual_canonical_publication(case):
    original = case.manifest
    allocation = original.reservation.allocation
    audit = replace(allocation.exposure.scheduled_audit, media_type='text/plain')
    allocation = replace(allocation, exposure=replace(allocation.exposure, scheduled_audit=audit))
    reservation = replace(original.reservation, allocation=allocation,
        publication=publish(case.plane, allocation, 'independent.audit-media.allocation'))
    selection = replace(original.native_specification.selection, reservation=sr.identity(reservation))
    native = replace(original.native_specification, selection=selection,
        publication=publish(case.plane, selection, 'independent.audit-media.selection'))
    published = publish(case.plane, reservation, 'independent.audit-media.reservation')
    assert audit.sha256 == original.audit_publication.logical.content_sha256
    assert audit.media_type != original.audit_publication.logical.media_type
    with pytest.raises(ValueError):
        replace(original, reservation=reservation, native_specification=native, reservation_publication=published)


def test_original_scalar_source_same_size_changed_bytes_are_refused(case):
    raw = case.args['normalization_source_bytes']
    changed = raw[:-1] + (b'X' if raw[-1:] != b'X' else b'Y')
    assert len(changed) == len(raw) and sha256(changed).digest() != sha256(raw).digest()
    with pytest.raises(ValueError, match='source bytes'):
        owner.project_protected_e3_protocol(**{**case.args, 'normalization_source_bytes': changed})


@pytest.mark.parametrize('field,value', (('schema', 'empirical-lawhood/tests/foreign-coordinate'), ('bytes', 1)))
def test_actual_candidate_coordinate_schema_and_size_cannot_be_rebound(case, field, value):
    document = json.loads(case.args['candidate_bytes'])
    document['population']['nominal_coordinate'][field] = value
    raw = json.dumps(document).encode()
    specification = replace(case.args['specification'], protocol_sha256=sha256(raw).hexdigest())
    with pytest.raises(ValueError, match='coordinate'):
        owner.project_protected_e3_protocol(**{**case.args, 'candidate_bytes': raw, 'specification': specification})


def test_independent_future_alias_in_consumed_rng_bits_is_refused(case, responses):
    selection, protocols, panels = responses
    indices = tuple(index for index, panel in enumerate(panels) if panel.role == 'INDEPENDENT_FUTURE')
    first, other = panels[indices[0]], panels[indices[1]]
    # Different complete stream identities still collide in the actual native
    # first128-bit seed. Re-labeling or changing unused suffix bits adds no unit.
    stream = replace(first.streams[0], digest_sha256=other.streams[0].digest_sha256[:32] + '0' * 32)
    assert stream.digest_sha256 != other.streams[0].digest_sha256
    assert stream.effective_seed == other.streams[0].effective_seed
    first = replace(first, streams=(stream, *first.streams[1:]))
    panels = tuple(first if index == indices[0] else panel for index, panel in enumerate(panels))
    selection = replace(selection, group_panels=tuple((group, tuple(ObjectIdentity.from_record(p.panel_id, p)
        for p in panels if p.independent_group_id == group)) for group, _ in selection.group_panels))
    with pytest.raises(ValueError, match='ownership'):
        producer.validate_responses(case, selection, protocols, panels)
