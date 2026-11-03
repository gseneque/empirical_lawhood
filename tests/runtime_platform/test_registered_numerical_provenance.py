# SPDX-License-Identifier: MPL-2.0
"""Shared observation and registered numerical predicates; no qualification."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_bindings import (
    operation_declarations as matrix_declarations,
)
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import (
    MATRIX_PROVENANCE_REQUIREMENT,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.operation_bindings import (
    operation_declarations as kinetic_declarations,
)
from empirical_lawhood.api import numerical_provenance as observation
from empirical_lawhood.infrastructure import numerical_provenance as producing_observation
from empirical_lawhood.api.matrix_native_custody import MatrixNativeRuntimeObservation
from empirical_lawhood.api.matrix_numerical_provenance import authenticate_recorded_matrix_provenance
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.recursive_compiler import RegisteredProvenanceRequirement


ROOT = Path(__file__).resolve().parents[2]
# Literal historical schema/value bytes, rather than a serialization oracle.
HISTORICAL_OBSERVATION = (
    '{"machine":"x86_64","numpy":"2.4.6","python":"3.11.14","scipy":"1.17.1",'
    '"system":"linux","threadpools":[{"num_threads":1}]}\n'
)
HISTORICAL_MATRIX_BYTES = (
    b'{"schema":"empirical-lawhood/matrix-native/runtime-observation","value":'
    b'{"observation_json":"{\\"machine\\":\\"x86_64\\",\\"numpy\\":\\"2.4.6\\",'
    b'\\"python\\":\\"3.11.14\\",\\"scipy\\":\\"1.17.1\\",\\"system\\":\\"linux\\",'
    b'\\"threadpools\\":[{\\"num_threads\\":1}]}\\n"},"version":"1.0.0"}\n'
)


def _record(**changes):
    """Disclosed predicate fixture: these digests assert no producing custody."""
    value = json.loads(HISTORICAL_OBSERVATION)
    value.update(changes)
    sources = (("exposed-numerical-profile-fixture.py", sha256(b"exposed predicate fixture").hexdigest()),)
    return NumericalProducingProvenance(
        canonical_json_bytes(observation.immutable_json(value)).decode(), sha256(b"fixture lock").hexdigest(),
        sources, sha256(canonical_json_bytes(sources)).hexdigest(), "a" * 40, False,
    )


def _draft(registrations, *, selected=None):
    """Only the dispatcher's operation-selection interface is exercised here."""
    operations = tuple(SimpleNamespace(node_id="node." + str(index), selection=registration.selection)
        for index, registration in enumerate(registrations))
    return SimpleNamespace(operations=operations,
        selected_operation_ids=tuple(row.node_id for row in operations) if selected is None else selected)


def _dispatch(record, draft, registrations):
    return observation.validate_registered_provenance(provenance=record, draft=draft, registrations=registrations)


def _forbidden(*_args, **_kwargs):
    raise AssertionError("retained numerical evidence consulted reader/source/native state")


@pytest.mark.parametrize("nodes", (2, 80))
def test_selected_shared_requirement_runs_once_per_boundary_regardless_of_node_count(nodes):
    calls = []

    def check(record):
        calls.append(record)

    shared = RegisteredProvenanceRequirement("profile.fixture.shared", check)
    registration = replace(matrix_declarations()[0].registration(), provenance_requirements=(shared,))
    draft = _draft((registration,) * nodes)
    record = _record()
    assert _dispatch(record, draft, (registration,)) is None
    assert calls == [record]
    assert _dispatch(record, draft, (registration,)) is None
    assert calls == [record, record]


def test_distinct_selected_requirements_are_grouped_across_operations_and_ordered_by_id():
    calls = []

    def first(record):
        calls.append(("first", record))

    def last(record):
        calls.append(("last", record))

    alpha = RegisteredProvenanceRequirement("profile.fixture.a", first)
    zeta = RegisteredProvenanceRequirement("profile.fixture.z", last)
    declarations = matrix_declarations()
    first_registration = replace(declarations[0].registration(), provenance_requirements=(alpha, zeta))
    second_registration = replace(declarations[1].registration(), provenance_requirements=(zeta,))
    registrations = (first_registration, second_registration)
    draft = _draft(registrations)
    record = _record()
    _dispatch(record, replace_namespace(draft, operations=tuple(reversed(draft.operations))), registrations)
    assert calls == [("first", record), ("last", record)]


def replace_namespace(value, **changes):
    return SimpleNamespace(**{**vars(value), **changes})


def test_unselected_domain_requirement_does_not_constrain_the_selected_scope():
    declarations = matrix_declarations()
    selected = replace(declarations[0].registration(), provenance_requirements=())
    unselected = replace(declarations[1].registration(), provenance_requirements=(
        RegisteredProvenanceRequirement("profile.fixture.unselected", _forbidden),))
    registrations = (selected, unselected)
    assert _dispatch(_record(numpy="reader-independent-value"), _draft(registrations, selected=("node.0",)), registrations) is None


def test_conflicting_same_id_validators_refuse_before_running_any_scientific_predicate():
    def other(*_args):
        raise AssertionError("conflicting second numerical validator ran")

    declarations = matrix_declarations()
    registrations = (
        replace(declarations[0].registration(), provenance_requirements=(RegisteredProvenanceRequirement("profile.fixture.same", _forbidden),)),
        replace(declarations[1].registration(), provenance_requirements=(RegisteredProvenanceRequirement("profile.fixture.same", other),)),
    )
    with pytest.raises(ValueError, match="conflicting scientific validators"):
        _dispatch(_record(), _draft(registrations), registrations)


@pytest.mark.parametrize("mutation,message", (
    ("missing", "substitutes a selected operation"),
    ("implementation", "substitutes a selected operation"),
    ("duplicate", "repeats an operation registration"),
))
def test_incomplete_or_substituted_registrations_refuse_before_any_numerical_predicate(mutation, message):
    registration = replace(matrix_declarations()[0].registration(), provenance_requirements=(
        RegisteredProvenanceRequirement("profile.fixture.selected", _forbidden),))
    draft = _draft((registration,))
    if mutation == "missing":
        registrations = ()
    elif mutation == "implementation":
        registrations = (replace(registration, selection=replace(registration.selection, implementation_sha256="b" * 64)),)
    else:
        registrations = (registration, registration)
    with pytest.raises(ValueError, match=message):
        _dispatch(_record(), draft, registrations)


def test_refusal_propagates_unchanged_and_prevents_later_predicates():
    refusal = ValueError("original domain numerical refusal")

    def refuse(_record):
        raise refusal

    registration = replace(matrix_declarations()[0].registration(), provenance_requirements=(
        RegisteredProvenanceRequirement("profile.fixture.a", refuse),
        RegisteredProvenanceRequirement("profile.fixture.z", _forbidden),))
    with pytest.raises(ValueError) as caught:
        _dispatch(_record(), _draft((registration,)), (registration,))
    assert caught.value is refusal


@pytest.mark.parametrize("result", (True, False, 0, (), {}))
def test_validator_success_requires_exact_none_instead_of_a_truthy_or_falsey_result(result):
    registration = replace(matrix_declarations()[0].registration(), provenance_requirements=(
        RegisteredProvenanceRequirement("profile.fixture.selected", lambda _record: result),))
    with pytest.raises(ValueError, match="return None on success or raise on refusal"):
        _dispatch(_record(), _draft((registration,)), (registration,))


@pytest.mark.parametrize("declarations", (matrix_declarations, kinetic_declarations), ids=("matrix", "kinetic"))
@pytest.mark.parametrize("field,value", (
    ("python", "3.11.99"), ("numpy", "2.4.99"), ("scipy", "1.17.99"),
    ("system", "darwin"), ("machine", "arm64"),
))
def test_domain_declared_profiles_refute_wrong_recorded_producing_versions_and_host(declarations, field, value):
    registrations = tuple(row.registration() for row in declarations() if row.provenance_requirements)
    assert registrations
    draft = _draft(registrations)
    assert _dispatch(_record(), draft, registrations) is None
    with pytest.raises(ValueError, match="selected numerical profile"):
        _dispatch(_record(**{field: value}), draft, registrations)


@pytest.mark.parametrize("declarations", (matrix_declarations, kinetic_declarations), ids=("matrix", "kinetic"))
@pytest.mark.parametrize("pools", (
    ({"num_threads": 2},), ({"num_threads": 0},), ({},),
    ({"num_threads": 1}, {"num_threads": 4}), ({"num_threads": True},),
))
def test_domain_declared_profiles_keep_every_loaded_thread_pool_in_the_refusal_census(declarations, pools):
    registrations = tuple(row.registration() for row in declarations() if row.provenance_requirements)
    with pytest.raises(ValueError, match="single-thread bootstrap"):
        _dispatch(_record(threadpools=pools), _draft(registrations), registrations)


@pytest.mark.parametrize("pools", ((None,), ("not-a-pool",)))
@pytest.mark.parametrize("declarations", (matrix_declarations, kinetic_declarations), ids=("matrix", "kinetic"))
def test_malformed_retained_pool_members_refuse_as_invalid_observation(declarations, pools):
    registrations = tuple(row.registration() for row in declarations() if row.provenance_requirements)
    with pytest.raises(ValueError, match="pool|observation|bootstrap"):
        _dispatch(_record(threadpools=pools), _draft(registrations), registrations)


def test_retained_authentication_and_both_domain_dispatchers_never_observe_reader_environment(monkeypatch):
    record = _record()
    matrix = tuple(row.registration() for row in matrix_declarations())
    kinetic = tuple(row.registration() for row in kinetic_declarations())
    monkeypatch.setattr(producing_observation, "numerical_runtime_observation", _forbidden)
    monkeypatch.setattr(producing_observation, "numerical_package_sources", _forbidden)
    monkeypatch.setattr(producing_observation, "selected_dependency_lock_sha256", _forbidden)
    monkeypatch.setattr(producing_observation, "run_bounded_command", _forbidden)
    monkeypatch.setattr(producing_observation, "read_bounded_bytes", _forbidden)
    monkeypatch.setattr("platform.python_version", _forbidden)
    monkeypatch.setattr("platform.machine", _forbidden)
    monkeypatch.setattr("threadpoolctl.threadpool_info", _forbidden)
    assert observation.authenticate_recorded_numerical_provenance(record) is record
    assert authenticate_recorded_matrix_provenance(record) is record
    assert _dispatch(record, _draft(matrix), matrix) is None
    assert _dispatch(record, _draft(kinetic), kinetic) is None


def test_fraction_only_contrast_uses_parent_profile_requirements_without_inventing_its_own():
    declarations = kinetic_declarations()
    contrast, = (row for row in declarations if row.capability_key.endswith(".gas-contrast"))
    parents = tuple(row.registration() for row in declarations if row is not contrast)
    assert contrast.provenance_requirements == ()
    assert {row.provenance_requirements[0].requirement_id for row in parents} == {
        "rubisco-kinetic-join.selected-numerical-profile.v1"}
    assert MATRIX_PROVENANCE_REQUIREMENT.requirement_id == "matrix-response-study.selected-numerical-profile.v1"
    registration = contrast.registration()
    alternate = _record(python="another-python", numpy="not-used-by-fraction", scipy="not-used-by-fraction",
                        system="another-system", machine="another-machine", threadpools=())
    assert _dispatch(alternate, _draft((registration,)), (registration,)) is None
    with pytest.raises(ValueError, match="selected numerical profile"):
        _dispatch(alternate, _draft(parents), parents)


def test_historical_matrix_runtime_canonical_record_bytes_and_empty_pool_semantics_are_preserved():
    record = MatrixNativeRuntimeObservation(HISTORICAL_OBSERVATION)
    assert record.canonical_bytes() == HISTORICAL_MATRIX_BYTES
    recovered = decode_canonical_bytes(HISTORICAL_MATRIX_BYTES, MatrixNativeRuntimeObservation,
                                      maximum_bytes=len(HISTORICAL_MATRIX_BYTES))
    assert recovered == record and recovered.canonical_bytes() == HISTORICAL_MATRIX_BYTES
    for declarations in (matrix_declarations, kinetic_declarations):
        registrations = tuple(row.registration() for row in declarations() if row.provenance_requirements)
        assert _dispatch(_record(threadpools=()), _draft(registrations), registrations) is None


def test_noncanonical_recorded_runtime_is_rejected_before_any_profile_callback():
    registration = replace(matrix_declarations()[0].registration(), provenance_requirements=(
        RegisteredProvenanceRequirement("profile.fixture.selected", _forbidden),))
    record = replace(_record(), runtime_observation_json=json.dumps(json.loads(HISTORICAL_OBSERVATION), indent=2))
    with pytest.raises(ValueError, match="exact canonical JSON"):
        _dispatch(record, _draft((registration,)), (registration,))


def test_shared_source_inventory_hashes_exact_resources_and_omits_only_interpreter_caches(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    resources = {"__init__.py": b"# selected original\r\n", "retained.bin": bytes((0, 255, 1)),
                 "subdir/member.py": b"# member\n"}
    for name, raw in resources.items():
        path = package / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw)
    cache = package / "__pycache__"
    cache.mkdir()
    (cache / "ignored.pyc").write_bytes(b"interpreter cache")
    assert observation.numerical_package_sources(package) == tuple(sorted(
        (name, sha256(raw).hexdigest()) for name, raw in resources.items()))
    (package / "linked.py").symlink_to(package / "__init__.py")
    with pytest.raises(ValueError, match="symbolic links"):
        observation.numerical_package_sources(package)


def test_shared_capture_observes_actual_selected_package_lock_git_and_runtime_once(monkeypatch):
    from threadpoolctl import threadpool_limits

    observed = []
    actual_observer = producing_observation.numerical_runtime_observation

    def once():
        value = actual_observer()
        observed.append(value)
        return value

    monkeypatch.setattr(producing_observation, "numerical_runtime_observation", once)
    with threadpool_limits(limits=1):
        record = observation.capture_numerical_provenance(project_root=ROOT)
    assert len(observed) == 1
    assert record.runtime_observation_json == canonical_json_bytes(observed[0]).decode()
    assert record.dependency_lock_sha256 == sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
    assert record.code_sources_sha256 == sha256(canonical_json_bytes(record.package_sources)).hexdigest()
    rows = dict(record.package_sources)
    assert rows["kernel/serialization.py"] == sha256((ROOT / "src/empirical_lawhood/kernel/serialization.py").read_bytes()).hexdigest()
    assert rows["api/numerical_provenance.py"] == sha256((ROOT / "src/empirical_lawhood/api/numerical_provenance.py").read_bytes()).hexdigest()
    assert not any("__pycache__" in Path(name).parts or Path(name).suffix in (".pyc", ".pyo") for name in rows)
    assert observation.authenticate_recorded_numerical_provenance(record) is record
    assert authenticate_recorded_matrix_provenance(record) is record


@pytest.mark.parametrize("drift", ("code", "lock"))
def test_expected_source_or_lock_drift_refuses_before_observing_runtime(monkeypatch, drift):
    monkeypatch.setattr(producing_observation, "numerical_runtime_observation", _forbidden)
    argument = {"expected_code_sha256": "0" * 64} if drift == "code" else {"expected_lock_sha256": "0" * 64}
    with pytest.raises(ValueError, match="code/source bytes changed|dependency lock changed"):
        observation.capture_numerical_provenance(project_root=ROOT, **argument)


def test_loaded_foreign_source_module_refuses_before_package_or_environment_observation(monkeypatch, tmp_path):
    import sys

    monkeypatch.setitem(sys.modules, "empirical_lawhood.exposed_foreign_module",
                        SimpleNamespace(__file__=str(tmp_path / "foreign.py")))
    monkeypatch.setattr(producing_observation, "numerical_package_sources", _forbidden)
    monkeypatch.setattr(producing_observation, "numerical_runtime_observation", _forbidden)
    with pytest.raises(ValueError, match="loaded module differs from selected checkout"):
        observation.capture_numerical_provenance(project_root=ROOT)


@pytest.fixture(scope="module")
def actual_admitted_source():
    """Real selected checkout admission; never an exposed source-identity fixture."""
    from empirical_lawhood.infrastructure.source_closure import capture_admitted_target_source

    return capture_admitted_target_source(ROOT)


def test_admitted_source_projection_preserves_canonical_source_and_observes_runtime_freshly(
        actual_admitted_source, monkeypatch):
    from threadpoolctl import threadpool_limits
    from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current

    observed = []
    actual_observer = producing_observation.numerical_runtime_observation

    def fresh_runtime():
        value = actual_observer()
        observed.append(value)
        return value

    monkeypatch.setattr(producing_observation, "numerical_runtime_observation", fresh_runtime)
    with threadpool_limits(limits=1):
        ordinary = observation.capture_numerical_provenance(project_root=ROOT)
        monkeypatch.setattr(producing_observation, "numerical_package_sources", _forbidden)
        monkeypatch.setattr(producing_observation, "selected_dependency_lock_sha256", _forbidden)
        projected = []
        for _ in range(2):
            # The projection is metadata reuse, not an admission/current-source verdict.
            require_admitted_target_source_current(ROOT, actual_admitted_source)
            projected.append(observation.capture_numerical_provenance(
                project_root=ROOT, _admitted_source=actual_admitted_source))
    assert len(observed) == 3
    for record, runtime in zip((ordinary, *projected), observed, strict=True):
        assert record.runtime_observation_json == canonical_json_bytes(runtime).decode()
        assert replace(ordinary, runtime_observation_json=record.runtime_observation_json).canonical_bytes() == record.canonical_bytes()
    assert projected[0].dependency_lock_sha256 == sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
    resource = "resources/matrix_factor_response/mandatory-exposure-floor.json"
    assert dict(projected[0].package_sources)[resource] == sha256(
        (ROOT / "src/empirical_lawhood" / resource).read_bytes()).hexdigest()


@pytest.mark.parametrize("damage", (
    "missing-root", "wrong-source-type", "wrong-member-type", "duplicate-member", "missing-package",
    "missing-resource", "missing-script", "missing-lock", "missing-build", "partial-scope", "invalid-mode", "invalid-digest",
))
def test_admitted_projection_refuses_malformed_or_partial_census_before_runtime_or_raw_inventory(
        actual_admitted_source, monkeypatch, damage):
    source, selected_root = actual_admitted_source, ROOT
    package = "src/empirical_lawhood/kernel/serialization.py"
    member = next(row for row in source.tracked_files if row.relative_path == package)
    if damage == "missing-root":
        selected_root = None
    elif damage == "wrong-source-type":
        source = object()
    elif damage == "wrong-member-type":
        source = replace(source, tracked_files=(object(),))
    elif damage == "duplicate-member":
        source = replace(source, tracked_files=(*source.tracked_files, member))
    elif damage.startswith("missing-"):
        missing = {
            "missing-package": package,
            "missing-resource": "src/empirical_lawhood/resources/matrix_factor_response/mandatory-exposure-floor.json",
            "missing-script": next(row.relative_path for row in source.tracked_files if row.relative_path.startswith("scripts/")),
            "missing-lock": "uv.lock", "missing-build": "pyproject.toml",
        }[damage]
        source = replace(source, tracked_files=tuple(row for row in source.tracked_files if row.relative_path != missing))
    elif damage == "partial-scope":
        source = replace(source,
            source_admission=replace(source.source_admission,
                selected_paths=tuple(name for name in source.source_admission.selected_paths if name != package)),
            final_source_admission=replace(source.final_source_admission,
                selected_paths=tuple(name for name in source.final_source_admission.selected_paths if name != package)))
    else:
        changed = replace(member, **({"mode": "120000"} if damage == "invalid-mode" else {"sha256": "g" * 64}))
        source = replace(source, tracked_files=tuple(changed if row is member else row for row in source.tracked_files))
    for name in ("numerical_runtime_observation", "numerical_package_sources", "selected_dependency_lock_sha256", "run_bounded_command"):
        monkeypatch.setattr(producing_observation, name, _forbidden)
    with pytest.raises((TypeError, ValueError)):
        observation.capture_numerical_provenance(project_root=selected_root, _admitted_source=source)


def test_actual_source_guard_refuses_consistently_trimmed_census_before_dependent_effects(actual_admitted_source):
    from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current

    omitted = "src/empirical_lawhood/resources/matrix_factor_response/mandatory-exposure-floor.json"
    source = actual_admitted_source
    partial = replace(source,
        tracked_files=tuple(row for row in source.tracked_files if row.relative_path != omitted),
        source_admission=replace(source.source_admission,
            selected_paths=tuple(name for name in source.source_admission.selected_paths if name != omitted)),
        final_source_admission=replace(source.final_source_admission,
            selected_paths=tuple(name for name in source.final_source_admission.selected_paths if name != omitted)))
    # A self-consistent metadata projection cannot replace the full physical membership guard.
    with pytest.raises(PermissionError, match="source membership changed"):
        require_admitted_target_source_current(ROOT, partial)
