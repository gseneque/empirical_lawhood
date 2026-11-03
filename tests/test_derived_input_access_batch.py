"""Disclosed software custody only; no actual science, source capture or acts."""
from dataclasses import replace
import pytest
from empirical_lawhood.api import derived_array_access as batch
from empirical_lawhood.api import derived_metadata_access as metadata
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.runtime_platform.test_artifact_verification_scope import _publication
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.runtime_platform.test_derived_array_access import array_access  # noqa: F401
from tests.test_matrix_selected_opportunity import opportunity, transfer  # noqa: F401
from tests.test_matrix_source_evidence import source_case  # noqa: F401


def supplied(tmp_path, count=4, shared=False):
    writer, _ = _publication(tmp_path, count=1)
    root, _ = _fixture()
    operator = ObjectIdentity("observation.software-closed-access", ObjectIdentity.SCHEMA, "1.0.0", "a"*64)
    requests = []
    records = []
    externals = []
    for i in range(count):
        record = ObjectIdentity("subject.closed." + str(i), ObjectIdentity.SCHEMA, "1.0.0", "b"*64)
        logical = "closed.metadata." + str(i)
        scope = "closed.shared" if shared else "closed.scope." + str(i)
        requests.append(ArtifactWriteRequest(logical, "closed/member-" + str(i) + ".json", record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", scope, "closed",
            record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        records.append(record)
        externals.append(RecursiveExternalInput("external.closed." + str(i), logical, record.SCHEMA,
            "application/json", len(record.canonical_bytes()), OutcomeAccess.OUTCOME_BLIND,
            VisibilityCeiling.PROSPECTIVE, record.fingerprint(), "HISTORY" if i%2 else "SOURCE"))
    publications = writer.write_batch(tuple(requests)) if shared else tuple(writer.write(v) for v in requests)
    inputs = tuple(batch.DerivedInputAccess(pub, record, external)
        for pub,record,external in zip(publications,records,externals,strict=True))
    return writer,root,operator,inputs


@pytest.mark.parametrize("shared,count", [(False,4),(False,16),(True,4),(True,16)])
def test_closed_access_is_exact_singular_semantic_and_byte_parity(tmp_path,shared,count):
    writer,root,operator,inputs = supplied(tmp_path,count,shared)
    expected = tuple(metadata.derive_canonical_metadata_access(writer=writer,publication=v.publication,
        record=v.operand,external=v.external,root=root,observation_operator=operator) for v in inputs)
    with writer.verification_scope() as scoped:
        actual = batch.derive_matrix_input_access_batch(writer=scoped,inputs=inputs,root=root,
            observation_operator=operator)
    assert actual == expected
    assert tuple(tuple(v.canonical_bytes() for v in pair) for pair in actual) == tuple(
        tuple(v.canonical_bytes() for v in pair) for pair in expected)
    for item,(config,qualification) in zip(inputs,actual,strict=True):
        metadata.validate_derived_metadata_access(external=item.external,root=root,
            observation_operator=operator,version=item.operand.VERSION,config=config,qualification=qualification)


@pytest.mark.parametrize("damage",["hash","logical","outcome","type"])
def test_late_bad_operand_refuses_before_any_writer_contact(tmp_path,damage):
    _,root,operator,inputs = supplied(tmp_path,2)
    item=inputs[-1]
    if damage=="type": item=object()
    else:
        external=replace(item.external,**({"expected_content_sha256":"f"*64} if damage=="hash"
            else {"logical_artifact_id":"foreign.logical"} if damage=="logical"
            else {"outcome_access":OutcomeAccess.DEVELOPMENT_VISIBLE}))
        item=replace(item,external=external)
    class Forbidden:
        def __getattr__(self,name): pytest.fail("bad late operand contacted writer: "+name)
    with pytest.raises((TypeError,ValueError)):
        batch.derive_matrix_input_access_batch(writer=Forbidden(),inputs=inputs[:-1]+(item,),
            root=root,observation_operator=operator)


def test_corrupt_later_member_refuses_before_any_decode(tmp_path,monkeypatch):
    writer,root,operator,inputs = supplied(tmp_path)
    path=writer.root.resolve(inputs[-1].publication.materialization.relative_path,for_write=False)
    path.write_bytes(b"x"*path.stat().st_size)
    def forbidden(**kwargs): pytest.fail("decode ran before closed member verification")
    monkeypatch.setattr(batch,"_read_canonical_metadata_binding",forbidden)
    with pytest.raises((ValueError,ArtifactIdentityConflict)):
        batch.derive_matrix_input_access_batch(writer=writer,inputs=inputs,root=root,observation_operator=operator)


def test_mutation_of_earlier_input_during_later_decode_refuses_at_boundary(tmp_path,monkeypatch):
    writer,root,operator,inputs = supplied(tmp_path)
    path=writer.root.resolve(inputs[0].publication.materialization.relative_path,for_write=False)
    original=batch._read_canonical_metadata_binding
    count=0
    def changed(**kwargs):
        nonlocal count
        count+=1
        original(**kwargs)
        if count==2: path.write_bytes(b"x"*path.stat().st_size)
    monkeypatch.setattr(batch,"_read_canonical_metadata_binding",changed)
    with pytest.raises((ValueError,ArtifactIdentityConflict)):
        with writer.verification_scope() as scoped:
            batch.derive_matrix_input_access_batch(writer=scoped,inputs=inputs,root=root,observation_operator=operator)


def test_changed_unrelated_previous_scope_member_refuses_before_callback(tmp_path,monkeypatch):
    writer,root,operator,inputs = supplied(tmp_path)
    first=inputs[0].publication
    with pytest.raises((ValueError,ArtifactIdentityConflict)):
        with writer.verification_scope() as scoped:
            metadata.derive_canonical_metadata_access(writer=scoped,publication=first,record=inputs[0].operand,
                external=inputs[0].external,root=root,observation_operator=operator)
            path=writer.root.resolve(first.materialization.relative_path,for_write=False)
            path.write_bytes(b"x"*path.stat().st_size)
            def forbidden(**kwargs): pytest.fail("decode bypassed earlier scope mutation")
            monkeypatch.setattr(batch,"_read_canonical_metadata_binding",forbidden)
            batch.derive_matrix_input_access_batch(writer=scoped,inputs=inputs[1:],root=root,observation_operator=operator)


def test_duplicate_publication_can_supply_distinct_declared_consumers(tmp_path):
    writer,root,operator,inputs=supplied(tmp_path,1)
    second=replace(inputs[0],external=replace(inputs[0].external,input_id="external.another-consumer",scientific_role="HISTORY"))
    actual=batch.derive_matrix_input_access_batch(writer=writer,inputs=(inputs[0],second),root=root,
        observation_operator=operator)
    assert len(actual)==2 and actual[0][0].source_id!=actual[1][0].source_id
    assert actual[0][1].materialization==actual[1][1].materialization


def test_array_and_metadata_share_one_closed_boundary_and_keep_exact_original_values(array_access):  # noqa: F811
    writer,root,profile,arrays,external,publication=array_access
    expected_array=batch.derive_matrix_array_access(writer=writer,publication=publication,arrays=arrays,
        external=external,root=root,source_profile=profile)
    record=ObjectIdentity("subject.mixed.closed",ObjectIdentity.SCHEMA,"1.0.0","c"*64)
    pub=writer.write(ArtifactWriteRequest("mixed.metadata","mixed/metadata.json",record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,"application/json","mixed.metadata","mixed",record.canonical_bytes(),
        VisibilityCeiling.PROSPECTIVE,(),OutcomeAccess.OUTCOME_BLIND))
    ext=RecursiveExternalInput("external.mixed.metadata","mixed.metadata",record.SCHEMA,"application/json",
        len(record.canonical_bytes()),OutcomeAccess.OUTCOME_BLIND,VisibilityCeiling.PROSPECTIVE,record.fingerprint())
    expected_metadata=metadata.derive_canonical_metadata_access(writer=writer,publication=pub,record=record,
        external=ext,root=root,source_profile=profile)
    before=arrays.canonical_bytes()
    actual=batch.derive_matrix_input_access_batch(writer=writer,
        inputs=(batch.DerivedInputAccess(pub,record,ext),batch.DerivedInputAccess(publication,arrays,external)),
        root=root,source_profile=profile)
    assert actual==(expected_metadata,expected_array)
    assert arrays.canonical_bytes()==before
