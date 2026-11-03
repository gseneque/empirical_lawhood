"""Bounded closed-access eligibility; all bytes are disclosed software metadata."""
from dataclasses import replace
import pytest
from empirical_lawhood.api import derived_array_access as owner
from empirical_lawhood.api.derived_metadata_access import derive_canonical_metadata_access
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.runtime_platform.test_candidate_compiler import _fixture


def inputs_for(tmp_path):
    writer, manifests = _publication(tmp_path,count=1)
    manifest=manifests[0]
    from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
    pub=_publication_from_manifest(writer,manifest)
    raw=writer.root.resolve(pub.materialization.relative_path,for_write=False).read_bytes()
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    record=decode_canonical_bytes(raw,ObjectIdentity,maximum_bytes=len(raw))
    external=RecursiveExternalInput("external.bound-first",pub.logical.logical_artifact_id,record.SCHEMA,
        "application/json",len(raw),pub.logical.outcome_access,pub.logical.visibility_ceiling,record.fingerprint())
    root,_=_fixture();op=ObjectIdentity("operator.bound",ObjectIdentity.SCHEMA,"1.0.0","a"*64)
    return writer,root,op,owner.DerivedInputAccess(pub,record,external)


def test_oversized_group_keeps_valid_singular_member_contract(tmp_path):
    writer,root,op,item=inputs_for(tmp_path)
    writer.custody_limits=ArtifactCustodyLimits(publication_members=1)
    second=replace(item,external=replace(item.external,input_id="external.bound-second"))
    assert not owner.supports_derived_input_access_batch(writer,2)
    expected=tuple(derive_canonical_metadata_access(writer=writer,publication=v.publication,
        record=v.operand,external=v.external,root=root,observation_operator=op) for v in (item,second))
    assert len(expected)==2
    with pytest.raises(ValueError,match="roster exceeds"):
        owner.derive_matrix_input_access_batch(writer=writer,inputs=(item,second),root=root,observation_operator=op)


def test_exact_bound_single_member_still_consumes_full_body(tmp_path):
    writer,root,op,item=inputs_for(tmp_path)
    writer.custody_limits=ArtifactCustodyLimits(publication_members=1)
    assert owner.supports_derived_input_access_batch(writer,1)
    value=owner.derive_matrix_input_access_batch(writer=writer,inputs=(item,),root=root,observation_operator=op)
    assert value[0][1].materialization.object_fingerprint==item.operand.fingerprint()


def test_empty_or_untyped_count_never_selects_effect_ordering(tmp_path):
    writer,_,_,_=inputs_for(tmp_path)
    assert not any(owner.supports_derived_input_access_batch(writer,n) for n in (0,-1,True,None,"1"))
