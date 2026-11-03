# SPDX-License-Identifier: MPL-2.0
"""Exposed filesystem/source representations; no molecular engines or qualification."""

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
import sys

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurablePreparationPlan
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import definitions
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_runner import validate_current_source_descriptor
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from tests.runtime_platform.test_native_subwork import ExposedInput


PREFIX = "src/empirical_lawhood/"
FILES = (("__init__.py", b'"""Exposed fixture package, never imported as science."""\n'),
    ("methods/native.py", b'"""Exposed declaration only; no native functions."""\n'),
    ("stock/coefficients.dat", b"exposed complete non-Python source stock\x00\xff\n"))
LOCK = b"# Exposed dependency-lock bytes; no dependency resolver runs.\n"


@dataclass(frozen=True)
class _SourceCase:
    root: Path
    package: Path
    plan: DurablePreparationPlan
    implementation: RecursiveImplementationBinding
    parent: NativeEffectContact


def _source_case(tmp_path, *, legacy=False):
    root = tmp_path / "exposed-source"
    package = root / "src" / "empirical_lawhood"
    package.mkdir(parents=True)
    for name, raw in FILES:
        path = package / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (root / "uv.lock").write_bytes(LOCK)
    # Literal expected member list and actual byte hashes are independent of
    # the production inventory scanner. This is a small exposed package, not
    # a claim about any installed molecular source or scientific environment.
    rows = tuple((name, sha256(raw).hexdigest()) for name, raw in FILES)
    code_sha = sha256(canonical_json_bytes(rows)).hexdigest()
    lock_sha = sha256(LOCK).hexdigest()
    implementation = RecursiveImplementationBinding(rows, code_sha, lock_sha, "a" * 40, False)
    records = tuple(ExposedInput(name + ".exposed", "exposed descriptor operand " + name)
        for name in ("source", "nomination", "inventory", "coordinates"))
    identities = tuple(ObjectIdentity.from_record(row.selected_id, row) for row in records)
    code = tuple((PREFIX + name if legacy else name, digest) for name, digest in rows)
    interpreter_sha = sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()
    plan = DurablePreparationPlan("exposed.preparation-plan", *identities, str(tmp_path / "unentered-working"),
        sys.executable, interpreter_sha, sys.executable, interpreter_sha, "b" * 64, code, lock_sha)
    parent = NativeEffectContact("exposed.run", "exposed.preparation", "exposed.attempt",
        ObjectIdentity("exposed.execution-plan", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "c" * 64),
        ObjectIdentity("exposed.preparation", "empirical-lawhood/runtime/execution-task", "1.0.0", "d" * 64),
        "a" * 40, ("materialization.exposed",), ())
    return _SourceCase(root, package, plan, implementation, parent)


@pytest.mark.parametrize("legacy", (False, True))
def test_complete_actual_source_representation_has_one_exact_standard_digest(tmp_path, legacy):
    case = _source_case(tmp_path, legacy=legacy)
    original = case.plan.canonical_bytes()
    assert validate_current_source_descriptor(case.plan, case.implementation, case.root) == case.implementation.code_sources_sha256
    assert case.plan.canonical_bytes() == original
    assert case.plan.physical_independent_units == 0
    assert not Path(case.plan.workdir).exists()


def test_new_attempt_standard_digest_preserves_legacy_plan_and_historical_definitions(tmp_path):
    case = _source_case(tmp_path, legacy=True)
    original = case.plan.canonical_bytes()
    sources = (case.plan.source, case.plan.nomination, case.plan.inventory, case.plan.coordinates)
    old = definitions(case.plan, case.parent, sources=sources,
        input_materialization_ids=case.parent.input_materialization_ids)
    saved = tuple(row.canonical_bytes() for row in old)
    current = definitions(case.plan, case.parent, sources=sources,
        input_materialization_ids=case.parent.input_materialization_ids,
        implementation=case.implementation, source_root=case.root)
    legacy_digest = sha256(canonical_json_bytes(case.plan.code_sources)).hexdigest()
    assert legacy_digest != case.implementation.code_sources_sha256
    assert len(old) == len(current) == 37
    assert all(row.code_sources_sha256 == legacy_digest for row in old)
    assert all(row.code_sources_sha256 == case.implementation.code_sources_sha256 for row in current)
    assert tuple(row.subwork_id for row in current) == tuple(row.subwork_id for row in old)
    assert sum(row.subwork_id.startswith("geometry.") for row in current) == 12
    assert sum(row.subwork_id.startswith("model.") for row in current) == 24
    for previous, fresh in zip(old, current, strict=True):
        assert replace(fresh, code_sources_sha256=previous.code_sources_sha256) == previous
    assert case.plan.canonical_bytes() == original
    assert tuple(row.canonical_bytes() for row in old) == saved


@pytest.mark.parametrize("changed", ("mixed", "omitted", "extra", "renamed", "same-byte-alias", "digest", "duplicate-physical-alias"))
def test_new_attempt_refuses_aliases_or_incomplete_descriptors_even_with_valid_digest_syntax(tmp_path, changed):
    case = _source_case(tmp_path, legacy=True)
    rows = case.plan.code_sources
    if changed == "mixed":
        rows = ((FILES[0][0], rows[0][1]), *rows[1:])
    elif changed == "omitted":
        rows = rows[:-1]
    elif changed == "extra":
        rows = (*rows, (PREFIX + "unused.py", "e" * 64))
    elif changed == "renamed":
        rows = ((PREFIX + "renamed.py", rows[0][1]), *rows[1:])
    elif changed == "same-byte-alias":
        rows = ((PREFIX + "./" + FILES[0][0], rows[0][1]), *rows[1:])
    elif changed == "digest":
        rows = ((rows[0][0], "e" * 64), *rows[1:])
    else:
        rows = (*rows, (FILES[0][0], rows[0][1]))
    plan = replace(case.plan, code_sources=tuple(sorted(rows)))
    with pytest.raises(ValueError, match="source|bijection"):
        validate_current_source_descriptor(plan, case.implementation, case.root)
    assert not Path(case.plan.workdir).exists()


@pytest.mark.parametrize("changed", ("changed-python", "changed-stock", "missing-python", "missing-stock", "added-python", "added-stock"))
def test_new_attempt_rescans_actual_complete_python_and_non_python_member_bytes(tmp_path, changed):
    case = _source_case(tmp_path)
    if changed == "changed-python":
        (case.package / FILES[1][0]).write_bytes(b"different actual source bytes\n")
    elif changed == "changed-stock":
        (case.package / FILES[2][0]).write_bytes(b"different actual parameter stock\x00\xff\n")
    elif changed == "missing-python":
        (case.package / FILES[1][0]).unlink()
    elif changed == "missing-stock":
        (case.package / FILES[2][0]).unlink()
    else:
        name = "additional.py" if changed == "added-python" else "stock/additional.dat"
        (case.package / name).write_bytes(b"unlisted actual member\n")
    with pytest.raises(ValueError, match="source files|inventory"):
        validate_current_source_descriptor(case.plan, case.implementation, case.root)


@pytest.mark.parametrize("changed", ("plan-lock", "actual-lock", "missing-lock"))
def test_new_attempt_requires_both_declared_and_actual_exact_dependency_lock(tmp_path, changed):
    case = _source_case(tmp_path)
    plan = case.plan
    if changed == "plan-lock":
        plan = replace(plan, dependency_lock_sha256="e" * 64)
    elif changed == "actual-lock":
        (case.root / "uv.lock").write_bytes(b"actual lock changed\n")
    else:
        (case.root / "uv.lock").unlink()
    with pytest.raises((ValueError, OSError)):
        validate_current_source_descriptor(plan, case.implementation, case.root)


@pytest.mark.parametrize("changed", ("member-link", "package-link", "src-link", "root-link", "lock-link"))
def test_new_attempt_refuses_actual_source_or_lock_symlink_substitution(tmp_path, changed):
    case = _source_case(tmp_path)
    root = case.root
    if changed == "member-link":
        member = case.package / FILES[1][0]
        target = tmp_path / "external-member.py"
        member.rename(target)
        member.symlink_to(target)
    elif changed == "package-link":
        target = tmp_path / "external-package"
        case.package.rename(target)
        case.package.symlink_to(target, target_is_directory=True)
    elif changed == "src-link":
        target = tmp_path / "external-src"
        (root / "src").rename(target)
        (root / "src").symlink_to(target, target_is_directory=True)
    elif changed == "root-link":
        root = tmp_path / "aliased-root"
        root.symlink_to(case.root, target_is_directory=True)
    else:
        target = tmp_path / "external.lock"
        (root / "uv.lock").rename(target)
        (root / "uv.lock").symlink_to(target)
    with pytest.raises((ValueError, OSError), match="source|symlink|regular|lock|selected|link"):
        validate_current_source_descriptor(case.plan, case.implementation, root)


def test_interpreter_caches_do_not_become_declared_scientific_source_members(tmp_path):
    case = _source_case(tmp_path)
    cache = case.package / "__pycache__"
    cache.mkdir()
    (cache / "cached.cpython-311.pyc").write_bytes(b"exposed non-source cache bytes")
    (case.package / "ignored.pyc").write_bytes(b"exposed non-source cache bytes")
    assert validate_current_source_descriptor(case.plan, case.implementation, case.root) == case.implementation.code_sources_sha256


@pytest.mark.parametrize("legacy", (False, True))
def test_child_source_loader_maps_both_exact_representations_to_the_same_actual_bytes(tmp_path, legacy):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import _SelectedSourceFinder

    case = _source_case(tmp_path, legacy=legacy)
    finder = _SelectedSourceFinder(case.root, case.plan.code_sources)
    specification = finder.find_spec("empirical_lawhood.methods.native")
    assert specification.origin == str(case.package / "methods/native.py")
    assert specification.loader.get_code(specification.name).co_filename == specification.origin
    # No finder is installed and no selected fixture code is executed. Reading
    # authentic exposed bytes does not establish a scientific helper's meaning.
    (case.package / "methods/native.py").write_bytes(b"changed original source bytes\n")
    with pytest.raises(ValueError, match="source bytes changed"):
        specification.loader.get_code(specification.name)


def test_child_source_loader_refuses_ambiguous_labels_and_unlisted_modules(tmp_path):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import _SelectedSourceFinder

    case = _source_case(tmp_path, legacy=True)
    finder = _SelectedSourceFinder(case.root,
        (*case.plan.code_sources, ("methods/native.py", sha256(FILES[1][1]).hexdigest())))
    with pytest.raises(ValueError, match="aliased"):
        finder.find_spec("empirical_lawhood.methods.native")
    with pytest.raises(ValueError, match="outside authenticated"):
        _SelectedSourceFinder(case.root, case.plan.code_sources).find_spec("empirical_lawhood.methods.unlisted")
    assert finder.find_spec("unrelated_external_package") is None


def test_registered_durable_operation_selects_the_actual_preparation_callback():
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import durable_operation_bindings as ob
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_runner import prepare_native_work

    registration, = ob.operation_registrations()
    assert registration.native_effect is True
    assert registration.native_work_preparer is prepare_native_work


def test_durable_worker_refuses_missing_preparation_before_attempting_any_child(tmp_path):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import durable_operation_bindings as ob
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_runner import DurablePreparationWorker
    from tests.runtime_platform.test_worker_preflight import _case

    # The complete exposed task/input context is a software guard fixture. It
    # does not contain molecular operands and cannot establish their readiness.
    _, bundle, _, context, _, _ = _case(tmp_path, native=True)
    try:
        assert context.prepared_invocation is None
        with pytest.raises(ValueError, match="SOFTWARE:.*complete original prepared invocation"):
            DurablePreparationWorker("prepare", ob.operation_manifests()[0]).preflight(context)
    finally:
        bundle.close()


@pytest.fixture(scope="module")
def exposed_geometry(tmp_path_factory):
    """Reuse actual exposed receipt/archive custody, with no molecular engine."""
    from tests import test_rubisco_geometry_reuse as fixtures
    generator = fixtures.original.__wrapped__(tmp_path_factory)
    try:
        yield next(generator)
    finally:
        next(generator, None)


def _geometry_transport_case(original):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import geometry_reuse as owner
    from tests.test_rubisco_geometry_reuse import fresh
    source, plan = fresh(original)
    parent = original.supply.definition.parent_contact
    selected = definitions(plan, parent,
        sources=(plan.source, plan.nomination, plan.inventory, plan.coordinates,
            original.supply.identity, original.supply.independent_integrity),
        input_materialization_ids=parent.input_materialization_ids)
    arguments = (plan, source, original.nomination, original.inventory, original.coordinates, selected,
        "/exposed/selected/source", (original.supply,), (original.assessment,))
    return owner, arguments, parent


def test_geometry_transport_preserves_all_original_canonical_operands_and_full37_roster(exposed_geometry):
    import json
    owner, arguments, _ = _geometry_transport_case(exposed_geometry)
    raw = owner._invocation_transport(*arguments)
    data = json.loads(raw)
    assert set(data) == {"plan", "source", "nomination", "inventory", "coordinates", "definitions", "source_root", "supplies", "assessments"}
    for name, record in zip(("plan", "source", "nomination", "inventory", "coordinates"), arguments[:5], strict=True):
        assert data[name].encode() == record.canonical_bytes()
    assert tuple(row.encode() for row in data["definitions"]) == tuple(row.canonical_bytes() for row in arguments[5])
    assert len(data["definitions"]) == 37
    assert tuple(row.encode() for row in data["supplies"]) == (exposed_geometry.supply.canonical_bytes(),)
    assert tuple(row.encode() for row in data["assessments"]) == (exposed_geometry.assessment.canonical_bytes(),)
    assert data["source_root"] == "/exposed/selected/source"
    assert not Path(arguments[0].workdir).exists()


def test_geometry_strict_public_builder_still_refuses_actual_invalid_stock_before_transport(exposed_geometry, monkeypatch):
    owner, arguments, _ = _geometry_transport_case(exposed_geometry)
    monkeypatch.setattr(owner, "_invocation_transport", lambda *a, **kw: pytest.fail("strict scientific refusal reached transport"))
    with pytest.raises(ValueError, match="source stock"):
        owner.invocation_bytes(*arguments)


def test_geometry_actual_child_still_uses_strict_builder_before_engine_archive_or_native_contact(exposed_geometry, monkeypatch):
    import json
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import durable_native_entry, geometry_reuse_native_entry
    owner, arguments, parent = _geometry_transport_case(exposed_geometry)
    data = json.loads(owner._invocation_transport(*arguments))
    def forbidden(*args, **kwargs):
        pytest.fail("scientifically invalid stock reached engine/archive entry")
    monkeypatch.setattr(durable_native_entry, "authenticate_engine_stock", forbidden)
    monkeypatch.setattr(owner, "_scan_archive", forbidden)
    with pytest.raises(ValueError, match="source stock"):
        geometry_reuse_native_entry._prepare_child(data, parent)


def test_geometry_conditional_admitted_branch_has_exact_transport_bytes_without_claiming_valid_science(exposed_geometry, monkeypatch):
    """Control-flow parity only: the predicate is a declared test conditional.

    The exposed original is actually invalid and is refused again after this
    conditional branch. It supplies no worker readiness or scientific admission.
    """
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import science
    owner, arguments, _ = _geometry_transport_case(exposed_geometry)
    expected = owner._invocation_transport(*arguments)
    called = []
    def conditional_admission(*operands):
        called.append(operands)
        return operands[0]
    with monkeypatch.context() as conditional:
        conditional.setattr(science, "validate_source", conditional_admission)
        assert owner.invocation_bytes(*arguments) == expected
    assert called == [arguments[1:5]]
    with pytest.raises(ValueError, match="source stock"):
        owner.invocation_bytes(*arguments)


@pytest.mark.parametrize("damage", ("missing-definition", "definition-owner", "definition-code", "definition-lock", "definition-parent",
    "nomination", "inventory", "coordinates", "missing-supply", "missing-assessment", "changed-assessment", "relative-source-root"))
def test_geometry_transport_retains_original_schema_supplier_parent_and_definition_refusals(exposed_geometry, damage):
    owner, arguments, _ = _geometry_transport_case(exposed_geometry)
    arguments = list(arguments)
    if damage == "missing-definition":
        arguments[5] = arguments[5][:-1]
    elif damage.startswith("definition-"):
        changes = {"definition-owner": {"operation_id": "operation.foreign"},
            "definition-code": {"code_sources_sha256": "9"*64},
            "definition-lock": {"dependency_lock_sha256": "9"*64},
            "definition-parent": {"parent_contact": replace(arguments[5][0].parent_contact, attempt_id="attempt.foreign")}}
        arguments[5] = (replace(arguments[5][0], **changes[damage]), *arguments[5][1:])
    elif damage in ("nomination", "inventory", "coordinates"):
        index = {"nomination": 2, "inventory": 3, "coordinates": 4}[damage]
        arguments[index] = arguments[1]  # Exact record type/schema substitution.
    elif damage == "missing-supply":
        arguments[7] = ()
    elif damage == "missing-assessment":
        arguments[8] = ()
    elif damage == "changed-assessment":
        arguments[8] = (replace(exposed_geometry.assessment, product_id="assessment.foreign"),)
    else:
        arguments[6] = "relative/source"
    with pytest.raises(ValueError):
        owner._invocation_transport(*arguments)
