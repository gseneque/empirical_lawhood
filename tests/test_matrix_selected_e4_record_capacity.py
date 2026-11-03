# SPDX-License-Identifier: MPL-2.0
"""Current E4 record capacity and early refusal over disclosed metadata bytes."""
from dataclasses import dataclass, replace
from typing import ClassVar

import pytest

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure import publication_metadata
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.api import selected_e4_bank_recipe as owner
from tests.runtime_platform.test_native_subwork import _plane


@dataclass(frozen=True,slots=True)
class DisclosedCanonicalMetadata(CanonicalRecord):
    SCHEMA:ClassVar[str]='empirical-lawhood/testing/e4-canonical-record-capacity'
    record_id:str
    text:str


def _publication(plane,value,relative):
    return plane.write(ArtifactWriteRequest(value.record_id,relative,value.SCHEMA,ArtifactProfile.CANONICAL_JSON,
        'application/json','exposed-e4-capacity-software','.',value.canonical_bytes(),
        VisibilityCeiling.PROSPECTIVE,(),OutcomeAccess.OUTCOME_BLIND))


def test_actual_e4_record_reader_accepts_real_canonical_publication_larger_than_parent_metadata_cap(
        tmp_path):
    plane=_plane(tmp_path/'large-canonical-record')
    value=DisclosedCanonicalMetadata('record.large.exposed-software','x'*(16*1024**2))
    raw=value.canonical_bytes()
    assert len(raw)>16*1024**2
    publication=_publication(plane,value,'large.json')
    actual=owner._read_exact_record(plane,publication,DisclosedCanonicalMetadata)
    assert actual.canonical_bytes()==raw and actual==value


@pytest.mark.parametrize('allowance',('owning','custody'))
def test_actual_e4_record_exact_limit_passes_and_one_extra_byte_refuses_before_full_decode(
        tmp_path,monkeypatch,allowance):
    plane=_plane(tmp_path/('exact-'+allowance))
    exact=DisclosedCanonicalMetadata('record.boundary.exposed-software','x'*31)
    excess=replace(exact,text=exact.text+'x')
    size=len(exact.canonical_bytes())
    assert len(excess.canonical_bytes())==size+1
    first=_publication(plane,exact,'exact.json');second=_publication(plane,excess,'excess.json')
    selected=plane if allowance=='owning' else ExternalArtifactPlane(plane.root,plane.validators,
        custody_limits=ArtifactCustodyLimits(in_memory_payload_bytes=size))
    kwargs={'maximum_bytes':size} if allowance=='owning' else {}
    assert owner._read_exact_record(selected,first,DisclosedCanonicalMetadata,**kwargs)==exact
    def forbidden(*_args,**_kwargs):pytest.fail('oversized record entered full payload read/decode')
    monkeypatch.setattr(publication_metadata,'read_published_canonical_record',forbidden)
    with pytest.raises(ValueError,match='owning maximum_bytes|selected in_memory_payload_bytes'):
        owner._read_exact_record(selected,second,DisclosedCanonicalMetadata,**kwargs)
    assert plane.root.resolve('exact.json',for_write=False).read_bytes()==exact.canonical_bytes()
    assert plane.root.resolve('excess.json',for_write=False).read_bytes()==excess.canonical_bytes()


@pytest.mark.parametrize('maximum',(0,-1,True))
def test_actual_e4_record_refuses_invalid_owning_bound(tmp_path,maximum):
    plane=_plane(tmp_path/'invalid-bound')
    value=DisclosedCanonicalMetadata('record.invalid-bound.exposed-software','x')
    publication=_publication(plane,value,'value.json')
    with pytest.raises(ValueError,match='positive or None'):
        owner._read_exact_record(
            plane,publication,DisclosedCanonicalMetadata,maximum_bytes=maximum)
