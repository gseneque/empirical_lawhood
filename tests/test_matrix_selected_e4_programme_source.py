# SPDX-License-Identifier: MPL-2.0
"""Source selection and child forwarding only; no scientific authoring claim."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_authoring, selected_e4_programme_service as owner
from empirical_lawhood.api import composite_experiment_programme as source_owner
from empirical_lawhood.infrastructure import source_closure
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.infrastructure.test_selected_candidate import candidate_case as candidate_case  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def controlled_source(monkeypatch):
    """Real current source; only the parent-binding substitution is disclosed.

    This exercises actual full byte/membership guards. It supplies no original
    scientific input, authority, qualification or native execution.
    """
    source = source_closure.capture_admitted_target_source(ROOT)
    binding = recursive_authoring.implementation_binding(ROOT, _admitted_source=source)
    current, observed, captured = [binding], [source], []
    monkeypatch.setattr(recursive_authoring, "implementation_binding", lambda root, **_kwargs: current[0])
    monkeypatch.setattr(source_closure, "capture_admitted_target_source", lambda root: observed[0])
    capture = source_closure.capture_target_closure
    def record_capture(root, closure_id, **kwargs):
        result = capture(root, closure_id, **kwargs)
        captured.append(result)
        return result
    monkeypatch.setattr(source_closure, "capture_target_closure", record_capture)
    return SimpleNamespace(binding=binding,
        snapshot=ObjectIdentity.from_record("recursive-member.implementation", binding),
        current=current, observed=observed, captured=captured)


def test_exact_operational_source_preserves_actual_checkout_status(controlled_source):
    case = controlled_source
    assert case.binding.observed_checkout_clean == case.observed[0].final_source_admission.observed_checkout_clean
    assert source_owner.require_programme_source(ROOT, case.snapshot) == case.binding
    source_owner.preflight_programme_source(ROOT, case.snapshot)
    assert not case.captured


@pytest.mark.parametrize("when", ("before", "after"))
def test_changed_parent_source_refuses_child_capture_without_publication(controlled_source, monkeypatch, when):
    case = controlled_source
    changed = replace(case.binding, dependency_lock_sha256="e" * 64)
    calls = []
    def current(root, **_kwargs):
        calls.append(root)
        return case.binding if when == "after" and len(calls) == 1 else changed
    monkeypatch.setattr(recursive_authoring, "implementation_binding", current)

    with pytest.raises((TypeError, ValueError, PermissionError)):
        source_owner.component_source_snapshot(ROOT, case.snapshot, "prospective.specification.disclosed-wave")

    assert len(case.captured) == (0 if when == "before" else 1)


def test_historical_closure_cannot_supply_a_new_parent_operational_binding(controlled_source):
    case = controlled_source
    closure = source_closure.capture_target_closure(ROOT, "historical.disclosed-source").closure
    case.captured.clear()
    old = ObjectIdentity.from_record("recursive-member.implementation", closure)
    with pytest.raises((TypeError, ValueError, PermissionError)):
        source_owner.component_source_snapshot(ROOT, old, "prospective.specification.disclosed-wave")
    assert not case.captured


def test_child_closure_from_another_commit_is_refused(controlled_source):
    case = controlled_source
    case.observed[0] = replace(case.observed[0], implementation_commit="f" * 40)
    with pytest.raises((TypeError, ValueError, PermissionError)):
        source_owner.component_source_snapshot(ROOT, case.snapshot, "prospective.specification.disclosed-wave")
    # The actual current-source guard rejects the forged admitted commit
    # before constructing a purported child closure.
    assert not case.captured


@pytest.fixture
def controlled_lowering(monkeypatch):
    # Only operational source capture/forwarding is under test. Scientific
    # inputs, file custody and full prospective authoring remain their owners.
    files, prepared, authored = [], [], []
    declaration = ObjectIdentity("declaration.disclosed-source", owner.r.SelectedE4NativeProgrammeDeclaration.SCHEMA,
        owner.r.SelectedE4NativeProgrammeDeclaration.VERSION, "a" * 64)
    programme = SimpleNamespace(group_ids=("group.disclosed-a", "group.disclosed-b"))
    plan = SimpleNamespace(plan_id="plan.disclosed-source",identity=ObjectIdentity("plan.disclosed-source",
        owner.d.SelectedE4ProtectedProgrammePlan.SCHEMA,owner.d.SelectedE4ProtectedProgrammePlan.VERSION,"b"*64),declaration=SimpleNamespace(
        bank_phase="CONFIRMATION", programme=programme, maximum_parallel_tasks=4,
        wave=lambda component: SimpleNamespace(group_ids=("group.disclosed-a",))))
    def specification(plan, component):
        wave = None if component == "assessment" else component
        return owner.d.SelectedE4NativeComponentSpecification("specification.disclosed-source." + component,
            declaration, component, wave, "ASSESS_PHASE" if wave is None else "ACQUIRE_WAVE")
    monkeypatch.setattr(owner.d, "component_specification", specification)
    monkeypatch.setattr(owner.d, "SelectedE4NativeComponentInputs", lambda *args: SimpleNamespace(values=args))
    monkeypatch.setattr(owner.d, "resolve_component_inputs", lambda selected, plan: SimpleNamespace(selection=selected,plan=plan))
    monkeypatch.setattr(owner.d, "SelectedE4PreparedComponentInputs", lambda selected, resolved, handles: (selected,resolved,handles))
    monkeypatch.setattr(owner, "_files", lambda *args: files.append(args) or ())
    monkeypatch.setattr(owner.d, "programme_allocation", lambda plan, *, group_ids: group_ids)
    def prepare(specification, **kwargs):
        result = SimpleNamespace(specification=specification, **kwargs)
        prepared.append(result)
        return result
    monkeypatch.setattr(owner.d, "prepare_component", prepare)
    def author(**kwargs):
        authored.append(kwargs)
        return kwargs["preparation"]
    writer = SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(
        canonical_path="/media/chevre/EL/empirical-lawhood/disclosed-source-routing")))
    service = SimpleNamespace(project_root=ROOT, artifact_writer=writer, author=author)
    return SimpleNamespace(wrapper=owner.SelectedE4ProgrammeService(service=service), plan=plan,
        files=files, prepared=prepared, authored=authored, output_root=writer.root.contract.canonical_path)


def test_child_components_receive_distinct_exact_closures_and_four_core_selection(controlled_source, controlled_lowering):
    case, lower = controlled_source, controlled_lowering
    # Opaque forwarding sentinels only: the controlled lowerer does not
    # authenticate original products or claim source/access authority.
    upstream_products, calibration_product = (object(),), object()
    state = SimpleNamespace(source_snapshot=case.snapshot, environment_id="main-locked",plan_publication=object(),
        upstream_products=upstream_products,calibration_product=calibration_product)
    directory = Path(lower.output_root) / "programme"
    for component in ("wave.disclosed-a", "assessment"):
        result = lower.wrapper._author_component(directory=directory, plan=lower.plan, state=state,
            declaration_publication=object(), component=component)
        assert result is lower.prepared[-1]
    assert len(case.captured) == len(lower.prepared) == len(lower.authored) == 2
    snapshots = []
    for captured, prepared, forwarded in zip(case.captured, lower.prepared, lower.authored, strict=True):
        expected = ObjectIdentity.from_record("recursive-member.implementation", captured.closure)
        assert captured.closure.source_closure_id == "prospective." + prepared.specification.specification_id + ".source-closure"
        assert captured.closure.implementation_commit == case.binding.observed_git_head
        execution = prepared.execution
        assert execution.source_snapshot == expected
        assert execution.workers == 4 and execution.environment_id == state.environment_id
        assert execution.output_root == lower.output_root
        assert forwarded["preparation"] is prepared
        selected,resolved,_=prepared.method_inputs
        assert selected.values[1]==lower.plan.identity
        assert selected.values[2] is state.plan_publication
        assert selected.values[3] is upstream_products
        assert selected.values[4] is calibration_product
        assert selected.values[5]==prepared.specification.component_id
        assert resolved.plan is lower.plan
        assert forwarded["output_dir"] == directory / "components" / prepared.specification.component_id
        snapshots.append(execution.source_snapshot)
    assert snapshots[0] != snapshots[1]


def test_changed_source_refuses_before_child_files_preparation_or_author(controlled_source, controlled_lowering):
    case, lower = controlled_source, controlled_lowering
    case.current[0] = replace(case.binding, observed_git_head="e" * 40)
    state = SimpleNamespace(source_snapshot=case.snapshot, environment_id="main-locked",plan_publication=object())
    with pytest.raises((TypeError, ValueError, PermissionError)):
        lower.wrapper._author_component(directory=Path(lower.output_root) / "programme", plan=lower.plan,
            state=state, declaration_publication=object(), component="wave.disclosed-a")
    assert not lower.files and not lower.prepared and not lower.authored
    assert not case.captured


@pytest.mark.parametrize("damage", ("parent-before", "parent-after", "captured-commit"))
def test_programme_preflight_refuses_changed_source_before_publication(controlled_source, monkeypatch, damage):
    case = controlled_source
    changed = replace(case.binding, dependency_lock_sha256="e" * 64)
    calls = []
    def current(root, **_kwargs):
        calls.append(root)
        if damage == "parent-before" or damage == "parent-after" and len(calls) > 1:
            return changed
        return case.binding
    monkeypatch.setattr(recursive_authoring, "implementation_binding", current)
    if damage == "captured-commit":
        case.observed[0] = replace(case.observed[0], implementation_commit="f" * 40)
    def forbidden(*args, **kwargs):
        pytest.fail("source preflight reached publication")
    monkeypatch.setattr(owner, "_publish", forbidden)

    with pytest.raises((TypeError, ValueError, PermissionError)):
        source_owner.preflight_programme_source(ROOT, case.snapshot)

    assert not case.captured


def test_actual_installed_preflight_reuses_one_census_for_distinct_current_child_closures(candidate_case, monkeypatch):
    case = candidate_case
    binding = recursive_authoring.implementation_binding(case.source)
    snapshot = ObjectIdentity.from_record("recursive-member.implementation", binding)
    captures, capture = [], source_closure.capture_admitted_target_source
    def observe_source(root):
        source = capture(root)
        captures.append(source)
        return source
    monkeypatch.setattr(source_closure, "capture_admitted_target_source", observe_source)
    source = source_owner.preflight_programme_source(case.source, snapshot)
    assert captures == [source]
    checked, verify = [], source_closure._verify_selected_member
    def observe_member(root, member):
        checked.append(member.relative_path)
        return verify(root, member)
    monkeypatch.setattr(source_closure, "_verify_selected_member", observe_member)
    first = source_owner.component_source_snapshot(case.source, snapshot, "prospective.specification.installed-wave", _admitted_source=source)
    second = source_owner.component_source_snapshot(case.source, snapshot, "prospective.specification.installed-assessment", _admitted_source=source)
    assert captures == [source]
    assert first != second
    assert first.object_id == second.object_id == "recursive-member.implementation"
    assert set(source.final_source_admission.selected_paths) <= set(checked)
    # Same operation, actual same-size byte corruption after its contexts close.
    path = case.source / "src/empirical_lawhood/math.py"
    raw = path.read_bytes()
    changed = raw.replace(b"7", b"8")
    assert changed != raw and len(changed) == len(raw)
    path.write_bytes(changed)
    with pytest.raises((PermissionError, ValueError), match="bytes|identity|source"):
        source_owner.component_source_snapshot(case.source, snapshot, "prospective.specification.installed-later", _admitted_source=source)
    assert captures == [source]
