# SPDX-License-Identifier: MPL-2.0
"""Exposed local custody controls; no scientific acquisition or qualification.

The fixture facts have no numerical assessor. Real artifact publication, replica
recovery and guarded SQLite projection are exercised with disclosed mount
inspectors. Installed original certificate verification is separate acceptance.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api import knowledge_store as owner
from empirical_lawhood.api.recursive_contributions import _publish
from empirical_lawhood.storage import artifact_replication
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.storage.guarded_catalog import GuardedCatalogAccess
from empirical_lawhood.storage.portable_closure import bounded_custody_members, current_closure_budget, recursive_closure_limits
from empirical_lawhood.storage.sql.repository import CatalogQueryWorkLimitExceeded, SQLiteCatalogRepository
from empirical_lawhood.science.records.decoding import decode_canonical_record
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.storage.contracts.catalog import CatalogArtifactQuery
from empirical_lawhood.storage.contracts.knowledge_store import KnowledgeObjectLocator, KnowledgeStoreLimits, PortableKnowledgeObject, ScientificTypeDescriptor, ScientificTypeRegistry, dependency_order, object_key
from empirical_lawhood.execution.recursive_handoff import RecursiveClosureLimits
from tests.test_recursive_public_service import _plane


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class DisclosedFact(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/portable-fact"
    fact_id: str
    assertion: str
    dependencies: tuple[ObjectIdentity, ...] = ()

    def __post_init__(self):
        if self.assertion not in ("supported", "adverse", "correction"):
            raise ValueError("disclosed fixture assertion is not selected")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.fact_id, self)


def registry():
    return ScientificTypeRegistry((ScientificTypeDescriptor("fixture.portable-fact", DisclosedFact,
        "fact_id", "fact.json", lambda record: record.dependencies),))


def plane(path, name):
    original = _plane(path)
    return ExternalArtifactPlane(GuardedExternalRoot(replace(original.root.contract, storage_root_id=name),
        inspector=original.root.inspector), validators=original.validators)


def census(directory):
    return {p.relative_to(directory).as_posix(): (p.stat().st_ino, sha256(p.read_bytes()).hexdigest())
            for p in directory.rglob("*") if p.is_file() and not p.name.endswith(".lock")}


@pytest.fixture
def case(tmp_path):
    original = plane(tmp_path / "original", "fixture.original")
    a = plane(tmp_path / "a", "fixture.store-a")
    b = plane(tmp_path / "b", "fixture.store-b")
    scratch = plane(tmp_path / "scratch", "fixture.catalog-scratch")
    access = SimpleNamespace(revoked=False, calls=[])

    def guard(identity, action):
        access.calls.append((identity, action))
        if access.revoked:
            raise PermissionError("disclosed current knowledge access revoked")

    types = registry()
    stores = tuple(owner.KnowledgeStore(directory=Path(p.root.contract.canonical_path) / "store", namespace=name,
        artifact_writer=p, registry=types, require_access=guard, project_root=ROOT) for p, name in ((a, "store.a"), (b, "store.b")))
    for store in stores:
        store.initialize()
    facts = (DisclosedFact("same-human-id", "supported"), DisclosedFact("same-human-id", "adverse"))
    sources = []
    for index, fact in enumerate(facts):
        directory = Path(original.root.contract.canonical_path) / str(index)
        _publish(original, directory, "fact.json", fact, "fixture.fact." + str(index))
        sources.append(owner.KnowledgeObjectSource(fact.identity, directory, "publisher.original", "same-label", "fact.json"))
    return SimpleNamespace(original=original, a=stores[0], b=stores[1], scratch=scratch, types=types,
        guard=guard, access=access, facts=facts, sources=tuple(sources), root=tmp_path)


def transfer(case, *, sources=None, name="transfer", roots=None):
    sources = case.sources if sources is None else sources
    roots = tuple(s.identity for s in sources) if roots is None else roots
    directory = Path(case.original.root.contract.canonical_path) / name
    report = owner.create_knowledge_transfer(sources=sources, roots=roots, output_directory=directory,
        project_root=ROOT, artifact_writer=case.original, registry=case.types, require_access=case.guard)
    identity = decode_canonical_record(report["transfer"], ObjectIdentity)
    return directory, identity


def import_into(store, case, directory, identity, **options):
    return store.import_transfer(directory=directory, source_artifact_writer=case.original,
        source_require_access=case.guard, expected_transfer=identity, **options)


def catalog(case, name):
    return GuardedCatalogAccess(case.scratch.root, name + ".sqlite3", True)


def test_two_store_exchange_keeps_full_identity_labels_and_current_resolution(case, monkeypatch):
    before = {s.directory: census(s.directory) for s in case.sources}
    directory, identity = transfer(case)
    imported = import_into(case.a, case, directory, identity)
    assert imported["status"] == "IMPORTED" and len(imported["locators"]) == 2
    exported = case.a.export(locators=imported["locators"], roots=tuple(f.identity for f in case.facts),
        output_directory=Path(case.a.artifact_writer.root.contract.canonical_path) / "export")
    selected = decode_canonical_record(exported["transfer"], ObjectIdentity)
    received = case.b.import_transfer(directory=Path(exported["directory"]), source_artifact_writer=case.a.artifact_writer,
        source_require_access=case.guard, expected_transfer=selected)
    assert {v.object_identity for v in received["locators"]} == {f.identity for f in case.facts}
    assert all(v.store_namespace == "store.b" for v in received["locators"])
    db = catalog(case, "projection")
    rebuilt = case.b.rebuild_projection(catalog_access=db)
    assert rebuilt["complete_imports"] == 1 and rebuilt["scientific_objects_reclassified"] == 0
    monkeypatch.setattr(SQLiteCatalogRepository, "snapshot", lambda *_: pytest.fail("query materialized an unbounded snapshot"))
    queried = case.b.query(catalog_access=db)
    rows = queried["imports"][0]["objects"]
    assert len(rows) == 2 and {row["publisher_label"] for row in rows} == {"same-label"}
    assert len({row["identity"]["value"]["object_fingerprint"] for row in rows}) == 2
    assert {row["identity"]["value"]["object_id"] for row in rows} == {"same-human-id"}
    assert queried["status"] == "DISCOVERY_ONLY" and queried["unseen_updates"] == "UNKNOWN"
    locator = decode_canonical_record(rows[0]["locator"], KnowledgeObjectLocator)
    resolved = case.b.resolve(locator)
    assert resolved["interpretation"] == "EXACT_REGISTERED_RECORD" and resolved["scientific_assessment"] == "NOT_ASSESSED"
    assert resolved["consumer_admission"] == "NOT_EVALUATED"
    assert all(census(path) == saved for path, saved in before.items())


def test_duplicate_transfer_preserves_original_import_and_replica_bytes(case):
    directory, identity = transfer(case)
    first = import_into(case.b, case, directory, identity)
    before = census(Path(first["directory"]))
    repeated = import_into(case.b, case, directory, identity)
    assert repeated["status"] == "DUPLICATE_VERIFIED" and repeated["locators"] == first["locators"]
    assert census(Path(first["directory"])) == before


def test_unknown_type_is_opaque_until_an_exact_registered_reader_is_selected(case):
    directory, identity = transfer(case, sources=case.sources[:1])
    case.b.registry = ScientificTypeRegistry(())
    imported = import_into(case.b, case, directory, identity)
    locator, = imported["locators"]
    opaque = case.b.resolve(locator)
    assert opaque["interpretation"] == "OPAQUE_UNINTERPRETED"
    assert opaque["scientific_assessment"] == "NOT_INTERPRETED"
    before = census(Path(imported["directory"]))
    case.b.registry = registry()
    read = case.b.resolve(locator)
    assert read["interpretation"] == "EXACT_REGISTERED_RECORD" and read["scientific_assessment"] == "NOT_ASSESSED"
    assert census(Path(imported["directory"])) == before


def test_dependency_export_preserves_both_original_conflicting_facts(case):
    dependencies = tuple(sorted((value.identity for value in case.facts), key=object_key))
    correction = DisclosedFact("later-notice", "correction", dependencies)
    directory = Path(case.original.root.contract.canonical_path) / "correction"
    _publish(case.original, directory, "fact.json", correction, "fixture.correction")
    source = owner.KnowledgeObjectSource(correction.identity, directory, "publisher.later", "same-label", "fact.json")
    exported, identity = transfer(case, sources=(*case.sources, source), roots=(correction.identity,))
    imported = import_into(case.b, case, exported, identity)
    assert {v.object_identity for v in imported["locators"]} == {*dependencies, correction.identity}
    before = {s.directory: census(s.directory) for s in (*case.sources, source)}
    for locator in imported["locators"]:
        assert case.b.resolve(locator)["status"] == "RESOLVED_CURRENT_CUSTODY"
    assert all(census(path) == saved for path, saved in before.items())
    with pytest.raises(ValueError, match="missing dependency"):
        transfer(case, sources=(source,), name="missing", roots=(correction.identity,))
    assert not (Path(case.original.root.contract.canonical_path) / "missing").exists()


def test_interrupted_import_reuses_the_existing_replica_recovery_owner(case, monkeypatch):
    directory, identity = transfer(case, sources=case.sources[:1])
    original = artifact_replication.copy_bounded_file
    calls = []

    def interrupt(source, destination, **kwargs):
        calls.append(source.name)
        if len(calls) == 3:
            destination.write_bytes(b"disclosed unfinished replica file")
            raise InterruptedError("disclosed interrupted import")
        return original(source, destination, **kwargs)

    monkeypatch.setattr(artifact_replication, "copy_bounded_file", interrupt)
    with pytest.raises(InterruptedError):
        import_into(case.b, case, directory, identity)
    target, = case.b._import_directories()
    assert not (target / "import.json").exists() and (target / "replica.json.progress.json").exists()
    complete = {p: p.stat().st_ino for p in (target / "packet").rglob("*") if p.is_file() and not p.name.endswith(".partial")}
    assert len(complete) == 2
    empty = case.b.rebuild_projection(catalog_access=catalog(case, "incomplete"))
    assert empty["complete_imports"] == 0 and empty["incomplete_imports"] == (str(target),)
    with pytest.raises(ValueError, match="incomplete"):
        import_into(case.b, case, directory, identity)
    monkeypatch.setattr(artifact_replication, "copy_bounded_file", original)
    recovered = import_into(case.b, case, directory, identity, resume=True)
    assert recovered["status"] == "IMPORTED" and all(p.stat().st_ino == inode for p, inode in complete.items())
    assert not tuple((target / "packet").rglob("*.partial"))


def test_revoked_current_access_never_completes_an_import(case, monkeypatch):
    directory, identity = transfer(case, sources=case.sources[:1])
    original = artifact_replication.copy_bounded_file

    def revoke(*args, **kwargs):
        result = original(*args, **kwargs)
        case.access.revoked = True
        return result

    monkeypatch.setattr(artifact_replication, "copy_bounded_file", revoke)
    with pytest.raises(PermissionError, match="revoked"):
        import_into(case.b, case, directory, identity)
    target, = case.b._import_directories()
    assert not (target / "import.json").exists() and not (target / "replica.json").exists()


def test_cached_discovery_cannot_hide_a_missing_original_member(case):
    directory, identity = transfer(case, sources=case.sources[:1])
    imported = import_into(case.b, case, directory, identity)
    locator, = imported["locators"]
    db = catalog(case, "before-missing")
    case.b.rebuild_projection(catalog_access=db)
    selected = Path(imported["directory"]) / "packet/objects" / object_key(locator.object_identity) / "fact.json"
    selected.unlink()  # Disclosed missing-evidence fault, confined to the replica.
    assert case.b.query(catalog_access=db)["status"] == "DISCOVERY_ONLY"
    with pytest.raises((ValueError, FileNotFoundError, RuntimeError)):
        case.b.resolve(locator)
    report = case.b.resolve(locator, allow_incomplete=True)
    assert report["status"] == "UNAVAILABLE_OR_UNVERIFIED" and report["identity"] == locator.object_identity.to_document()
    assert report["scientific_assessment"] == "NOT_VERIFIED"


def test_physical_catalog_page_enforces_query_work_and_current_root(case):
    directory, identity = transfer(case, sources=case.sources[:1])
    import_into(case.b, case, directory, identity)
    db = catalog(case, "bounded-query")
    case.b.rebuild_projection(catalog_access=db)
    engine = db.read_only_engine()
    try:
        query = CatalogArtifactQuery(case.b.artifact_writer.root.contract.storage_root_id,
            owner.KnowledgeImportReceipt.SCHEMA, "store/imports", 1)
        page = SQLiteCatalogRepository(engine).query_artifacts(query)
        assert len(page.rows) == 1 and not page.has_more
        with pytest.raises(CatalogQueryWorkLimitExceeded):
            SQLiteCatalogRepository(engine, query_work_limit=1).query_artifacts(query)
        foreign = replace(query, storage_root_id="foreign.root")
        assert SQLiteCatalogRepository(engine).query_artifacts(foreign).rows == ()
    finally:
        engine.dispose()


def test_original_registered_verifier_refuses_before_any_export_copy(case):
    selected = next(iter(case.types.descriptors.values()))

    def reject(context):
        assert context.directory == case.sources[0].directory
        raise ValueError("disclosed original scientific prerequisite is absent")

    case.types = ScientificTypeRegistry((replace(selected, verify=reject),))
    with pytest.raises(ValueError, match="prerequisite"):
        transfer(case, sources=case.sources[:1])
    assert not (Path(case.original.root.contract.canonical_path) / "transfer").exists()


def test_export_preview_retains_complete_identity_without_copy_and_apply_refuses_changed_selection(case, monkeypatch):
    destination = Path(case.original.root.contract.canonical_path) / "reviewed"
    arguments = dict(sources=case.sources, roots=tuple(row.identity for row in case.sources),
        output_directory=destination, project_root=ROOT, artifact_writer=case.original,
        registry=case.types, require_access=case.guard)
    before = census(case.root)
    copy = owner.copy_closure_members
    monkeypatch.setattr(owner, "copy_closure_members", lambda **k: pytest.fail("review copied original bytes"))
    reviewed = owner.preview_knowledge_transfer(**arguments)
    assert reviewed["physical_closure"]["objects"] == 2 and reviewed["physical_closure"]["bytes"] > 0
    assert census(case.root) == before and not destination.exists()
    expected = decode_canonical_record(reviewed["transfer"], ObjectIdentity)
    with pytest.raises(ValueError, match="reviewed complete transfer"):
        owner.create_knowledge_transfer(**{**arguments, "sources": case.sources[:1], "roots": (case.facts[0].identity,)},
            expected_transfer=expected)
    assert not destination.exists()
    monkeypatch.setattr(owner, "copy_closure_members", copy)
    applied = owner.create_knowledge_transfer(**arguments, expected_transfer=expected)
    assert applied["transfer"] == reviewed["transfer"] and applied["physical_closure"] == reviewed["physical_closure"]


def test_export_review_never_caches_current_access(case):
    directory, identity = transfer(case)
    imported = import_into(case.a, case, directory, identity)
    destination = Path(case.a.artifact_writer.root.contract.canonical_path) / "new-export"
    arguments = dict(locators=imported["locators"], roots=tuple(row.identity for row in case.facts), output_directory=destination)
    reviewed = case.a.preview_export(**arguments)
    case.access.revoked = True
    with pytest.raises(PermissionError, match="revoked"):
        case.a.export(**arguments, expected_transfer=decode_canonical_record(reviewed["transfer"], ObjectIdentity))
    assert not destination.exists()


def test_changed_copied_member_during_completion_publication_cannot_return_verified(case, monkeypatch):
    directory, identity = transfer(case, sources=case.sources[:1])
    publish = owner._publish

    def changed(writer, destination, name, record, packet_id):
        publish(writer, destination, name, record, packet_id)
        if name == "import.json":
            path = destination / "packet/objects" / object_key(case.facts[0].identity) / "fact.json"
            path.write_bytes(path.read_bytes().replace(b"supported", b"corrupted"))

    monkeypatch.setattr(owner, "_publish", changed)
    with pytest.raises(ValueError, match="replica completion"):
        import_into(case.b, case, directory, identity)
    target, = case.b._import_directories()
    assert (target / "import.json").exists()  # Original completed-at-publication record is retained.
    with pytest.raises(ValueError, match="closure bytes"):
        import_into(case.b, case, directory, identity)


def test_restricted_resolution_retains_the_selected_identity_without_scientific_verdict(case):
    directory, identity = transfer(case, sources=case.sources[:1])
    imported = import_into(case.b, case, directory, identity)
    locator, = imported["locators"]
    case.access.revoked = True
    with pytest.raises(PermissionError, match="revoked"):
        case.b.resolve(locator)
    report = case.b.resolve(locator, allow_incomplete=True)
    assert report["status"] == "ACCESS_REFUSED" and report["scientific_assessment"] == "NOT_VERIFIED"
    assert report["identity"] == locator.object_identity.to_document()


@pytest.mark.parametrize("failure", ("member", "aggregate", "depth", "entries", "link"))
def test_selected_closure_bounds_refuse_without_truncation(tmp_path, failure):
    root = tmp_path / "closure"
    root.mkdir()
    (root / "a").write_bytes(b"abc")
    (root / "b").write_bytes(b"def")
    limits = RecursiveClosureLimits()
    if failure == "member":
        limits = replace(limits, maximum_members=1)
    elif failure == "aggregate":
        limits = replace(limits, maximum_member_bytes=4, maximum_total_bytes=5)
    elif failure == "depth":
        (root / "nested").mkdir()
        (root / "nested/c").write_bytes(b"abc")
        limits = replace(limits, maximum_path_depth=1)
    elif failure == "entries":
        limits = replace(limits, maximum_scanned_entries=1)
    else:
        (root / "link").symlink_to(root / "a")
    with pytest.raises((ValueError, RuntimeError)):
        bounded_custody_members(root, ("",), limits=limits)


def test_parent_work_bound_and_nested_scope_cannot_reset_the_budget():
    limits = replace(RecursiveClosureLimits(), maximum_authentications=1, maximum_parent_depth=1)
    with recursive_closure_limits(limits) as budget:
        budget.authenticate(1)
        with recursive_closure_limits(limits):
            assert current_closure_budget() is budget
            with pytest.raises(ValueError, match="authentication"):
                budget.authenticate(1)
        with pytest.raises(ValueError, match="changes"):
            with recursive_closure_limits(RecursiveClosureLimits()):
                pytest.fail("nested read reset its selected budget")
    assert current_closure_budget() is None


@pytest.mark.parametrize("defect", ("cycle", "depth", "count"))
def test_explicit_dependency_graph_limits_preserve_complete_denominators(defect):
    identities = tuple(ObjectIdentity("fixture." + str(i), DisclosedFact.SCHEMA, "1.0.0", str(i + 1) * 64) for i in range(3))
    rows = [PortableKnowledgeObject(value, "fixture.publisher", "fixture.label", "fact.json",
        () if i == 2 else (identities[i + 1],), "REGISTERED_COMPLETE") for i, value in enumerate(identities)]
    limits = KnowledgeStoreLimits()
    if defect == "cycle":
        rows[-1] = replace(rows[-1], dependencies=(identities[0],))
    elif defect == "depth":
        limits = replace(limits, maximum_dependency_depth=2)
    else:
        limits = replace(limits, maximum_objects=2)
    with pytest.raises(ValueError, match="cycles|depth|object bound"):
        dependency_order(tuple(rows), (identities[0],), limits)
