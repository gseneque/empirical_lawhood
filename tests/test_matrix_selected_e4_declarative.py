# SPDX-License-Identifier: MPL-2.0
"""Copied declarative E4 intent and strict first stops; no authority/native work."""
from tests.matrix_e4_structure_support import disclosed_structure
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_declarative as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as acquisition
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as scientific
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_operational_resources import SelectedE4OperationalResources
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
from empirical_lawhood.api import selected_e4_declarative as public
from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.runtime_platform.test_artifact_verification_scope import _publication
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase
from empirical_lawhood.kernel.worlds import NumericalCoordinateKind
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.execution_envelope import ChildResourceTokenLimit, ProgressHeartbeat, ProgressLivenessContract
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from tests.experiment_entry_support import entry_package_for_draft
from tests.runtime_platform.test_candidate_compiler import _fixture
from tests.runtime_platform.test_standard_formal_candidate import _standard_fixture
from tests.test_matrix_selected_e4_fixtures import selected_e4_populations, selected_bridge, transfer  # noqa: F401
from tests.test_matrix_selected_e4_methods import selected_revision  # noqa: F401
from tests.test_matrix_selected_protected import unpublished
from tests.test_matrix_selected_e3_e4_bridge import disclosed_produced_parents,disclosed_produced_publication


def pin(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, "a" * 64)


@pytest.fixture(scope="module")
def declarative_case(selected_revision, selected_bridge):  # noqa: F811
    fitted = selected_revision
    bank, programme = fitted.populations.calibration_bank, fitted.populations.calibration
    coordinate = bank.source(bank.sources[0].root_id,index=bank.source_index()).coordinate
    root, _ = _fixture()
    cutoff = replace(root.design_inputs[0].information_cutoff, clock_id=coordinate.clock_id,
        phase=CausalPhase.PREPARATION, coordinate=Decimal(0))
    root = replace(root, design_inputs=tuple(replace(value, information_cutoff=cutoff) for value in root.design_inputs),
        development_unit_ids=(), evaluation_unit_ids=(), development_seed_ids=(), evaluation_seed_ids=(),
        source_materializations=(), capability_selections=(), conditional_successor=None)
    primary = root.system.numerical_views[0]
    timestep = replace(primary.coordinates[0], kind=NumericalCoordinateKind.TIMESTEP,
        value=coordinate.primary_view.timestep, unit=coordinate.primary_view.time_unit)
    primary = replace(primary, precision=coordinate.primary_view.precision, coordinates=(timestep,))
    fine = replace(primary, view_id="view.disclosed-fine-template",
        coordinates=(replace(timestep, value=coordinate.fine_view.timestep),))
    clock = replace(root.system.clocks[0], clock_id="clock.disclosed-source-template",
        time_unit=coordinate.primary_view.time_unit)
    selection = domain.SelectedE4RootSelection("root-selection.disclosed", root, clock, primary, fine,
        timestep.coordinate_id, cutoff, "operator.disclosed-release")
    def original(value, operation):
        return native.SelectedE4DevelopmentProduct(value.identity, "original-dev", "run.original-dev",
            pin("plan.original-dev", DevelopmentExecutionPlan), "method." + operation, pin("receipt." + operation, CanonicalTaskReceipt),
            unpublished(value, "publication." + operation))
    budget = ResourceBudget(1, 1024**3, 0, None, 128 * 1024**2, 64 * 1024**2)
    native_budgets = native.SelectedE4NativeBudgets("native-budgets.disclosed",
        tuple((phase, budget) for phase in sorted(acquisition.PHASES)), budget)
    phases = {*acquisition.PHASES, "phase-collect", "revision-calibrate"}
    controls = ExecutionResourceSelection("resources.disclosed", (),
        (ChildResourceTokenLimit("child.disclosed", 3 * len(programme.cases), 0),), (), (), (), None, None,
        4, 4 * budget.memory_bytes, (), (), "c" * 64, True, True, True, True)
    operational = SelectedE4OperationalResources("operational.disclosed", controls,
        tuple((phase, 100) for phase in sorted(phases)),
        ProgressLivenessContract("progress.disclosed", ProgressHeartbeat.SCHEMA,
            "disclosed-software-conformance", Decimal(30), True, True), 1)
    formal = _standard_fixture()[1]
    nomination=original(fitted.nomination, "revision-fit")
    frozen=original(fitted.frozen, "revision-freeze")
    request = domain.SelectedE4DeclarativeRequest("request.disclosed", programme.programme_id, "authored/e4",
        disclosed_produced_publication(bank,bank.identity.object_id,selected_bridge.evidence.produced_input_parents),
        None, selected_bridge.evidence.upstream_products,
        nomination, frozen, None, None,
        selection, entry_package_for_draft(root), formal.formal_methods, formal.source_inventories[0], native_budgets,
        methods.SelectedE4MethodResources("method-resources.disclosed", (("revision-calibrate", budget),)),
        operational, Decimal(1) - programme.confidence, None, None,
        *disclosed_structure(bank, budget=budget),disclosed_produced_parents(selected_bridge.evidence.upstream_products,
            development=(nomination,frozen)))
    specification = domain.SelectedE4DeclarativeSpecification("specification.disclosed", bank.identity, None,
        "CALIBRATION", len(programme.group_ids), programme.design.cases_per_group, "Declared complete calibration question")
    return SimpleNamespace(specification=specification, request=request, bank=bank, fitted=fitted,secondary_readout=selected_bridge.secondary_readout)


def copied_selection(tmp_path, case, *, request=None):
    records = {"request": case.request if request is None else request, "bank": case.bank,"secondary_readout":case.secondary_readout}
    bindings = []
    for role, record in records.items():
        payload = record.canonical_bytes()
        (tmp_path / (role + ".json")).write_bytes(payload)
        bindings.append(ExperimentInputBinding(role, record.identity, role + ".json", len(payload)))
    selector = ExperimentFileInputSelection("selection.disclosed", domain.PROTOCOL_ID,
        tuple(sorted(bindings, key=lambda value: value.key)), ())
    path = tmp_path / "sources.json"
    path.write_bytes(selector.canonical_bytes())
    return path


def test_copied_file_load_and_public_prepare_derive_counts_and_honest_original_source_dependencies(tmp_path, declarative_case):
    case = declarative_case
    path = copied_selection(tmp_path, case)
    inputs = load_experiment_inputs(case.specification, path)
    preparation = prepare_experiment(case.specification, scientific_inputs=inputs.scientific_inputs,
        method_inputs=inputs.method_inputs, execution=ExecutionSelection(workers=4))
    assert preparation.specification == case.specification.identity and not preparation.executable
    assert dict(preparation.census.role_counts) == {"groups": 64, "cases": 576}
    assert {value.code for value in preparation.dependencies} == {
        "matrix.selected-e4.derive-inputs", "matrix.selected-e4.source-qualification"}
    assert preparation.programme is None and preparation.draft is None
    assert inputs.method_inputs.request.source is None


def test_supported_copied_question_edit_rederives_root_without_touching_original_coefficients_or_authority(declarative_case):
    case = declarative_case
    revision = scientific.SelectedE4RevisionExport.from_products(case.fitted.programme, case.fitted.nomination,
        case.fitted.frozen, record_id="export.disclosed")
    summary = scientific.SelectedE4OriginalCalibrationSummary.from_package(case.fitted.populations.selected.package,
        record_id="summary.disclosed")
    programme = domain.validate_request(case.specification, case.request, case.bank)
    evidence = SimpleNamespace(identity=pin("evidence.disclosed", native.SelectedE4ProtectedEvidence))
    before = case.fitted.nomination.canonical_bytes()
    first = domain.derive_root(case.specification, case.request, case.bank, programme, evidence, revision, summary, None)
    edited = replace(case.specification, question="Edited pre-entry calibration question")
    second = domain.derive_root(edited, case.request, case.bank, programme, evidence, revision, summary, None)
    assert first.question != second.question and first.fingerprint() != second.fingerprint()
    assert first.evaluation_unit_ids == second.evaluation_unit_ids == programme.group_ids
    assert first.system.authority_policy == second.system.authority_policy == case.request.root.template.system.authority_policy
    assert first.resource_ceiling == second.resource_ceiling == case.request.root.template.resource_ceiling
    assert first.experiment.information_cutoffs == tuple(value.information_cutoff for value in programme.cases)
    assert edited.identity in {value.object_identity for value in second.design_inputs}
    assert case.fitted.nomination.canonical_bytes() == before


@pytest.mark.parametrize("change", ("groups", "phase", "workers", "alpha", "extra-role"))
def test_copied_intent_refuses_population_operational_or_scope_substitution(tmp_path, declarative_case, change):
    case = declarative_case
    specification, request = case.specification, case.request
    if change == "groups":
        specification = replace(specification, independent_group_count=specification.independent_group_count - 1)
    elif change == "phase":
        specification = replace(specification, population_phase="CONFIRMATION")
    elif change == "alpha":
        request = replace(request, calibration_alpha=Decimal(".10"))
    elif change == "extra-role":
        with pytest.raises(ValueError, match="optional"):
            domain.bind_inputs(specification, {"request": request, "bank": case.bank, "hand-made-task-map": case.bank})
        return
    inputs_path = copied_selection(tmp_path, case, request=request)
    if change == "workers":
        inputs = load_experiment_inputs(specification, inputs_path)
        with pytest.raises(ValueError, match="workers differ"):
            prepare_experiment(specification, scientific_inputs=inputs.scientific_inputs,
                method_inputs=inputs.method_inputs, execution=ExecutionSelection(workers=2))
        return
    with pytest.raises(ValueError, match="bank population|CONF request|exact explicit alpha"):
        load_experiment_inputs(specification, inputs_path)


def test_new_public_protocol_has_closed_editable_request_and_existing_typed_programme_without_runtime_authority():
    declaration = domain.protocol_declaration()
    assert declaration.programme_record_type.__name__ == "SelectedE4ProtectedProgrammePlan"
    assert not declaration.requires_prospective_runtime_binding and not declaration.requires_development_runtime_binding
    assert declaration.configuration_inputs[0].consumer_id == "matrix-selected-e4-request"
    assert declaration.configuration_inputs[0].record_type is domain.SelectedE4DeclarativeRequest


def test_default_installed_factory_and_deriver_select_the_exact_declarative_owner():
    from empirical_lawhood.api.domain_composition.matrix_selected_e4_declarative import experiment_binding
    declaration = domain.protocol_declaration()
    binding = experiment_runtime_binding(declaration)
    assert binding == experiment_binding.EXPERIMENT_RUNTIME_BINDING
    assert callable(binding.derive_inputs) and binding.bind_handoff is None
    service = binding.programme_service_factory(service=SimpleNamespace())
    assert type(service) is public.SelectedE4DeclarativeProgrammeService
    with pytest.raises(ValueError, match="no separate retained execution"):
        binding.programme_service_factory(service=SimpleNamespace(), descriptor=object())


def project_public_metadata(tmp_path, case, *, failure=None, monkeypatch=None):
    writer, _ = _publication(tmp_path, count=1)
    plane = tmp_path / "custody"
    source = copied_selection(plane, case)
    selector = decode_canonical_bytes(read_bounded_bytes(source, maximum_bytes=1024**2),
        ExperimentFileInputSelection, maximum_bytes=1024**2)
    selected = load_experiment_inputs(case.specification, source).method_inputs
    destination = plane / "prepared-sources.json"
    arguments = dict(specification=case.specification, selector=selector, selected=selected, plan=None,
        writer=writer, metadata_relative="derived", metadata_to_inputs=type(source)("derived"),
        destination=destination, selector_relative="prepared-sources.json", execution=ExecutionSelection(workers=4),
        publications=())
    if failure is not None:
        original = type(writer).write
        def fail_at_selected_publication(self, request):
            if request.relative_path == failure:
                raise RuntimeError("disclosed interrupted selector publication")
            return original(self, request)
        with monkeypatch.context() as patch:
            patch.setattr(type(writer), "write", fail_at_selected_publication)
            with pytest.raises(RuntimeError, match="interrupted selector"):
                public._result(**arguments)
        assert not destination.exists()
    return writer, selected, arguments


def test_actual_public_metadata_projection_cold_loads_and_returns_bounded_complete_index(tmp_path, declarative_case):
    writer, selected, arguments = project_public_metadata(tmp_path, declarative_case)
    result = public._result(**arguments)
    assert result.specification == declarative_case.specification.identity
    assert not result.preparation.executable and result.preparation.programme is None
    assert len(result.publications) == 4
    assert result.requirements_publication in result.publications
    index_path = writer.root.resolve("derived/index.json", for_write=False)
    raw = read_bounded_bytes(index_path, maximum_bytes=64 * 1024**2)
    index = decode_canonical_bytes(raw, public.SelectedE4DerivedMetadataIndex, maximum_bytes=len(raw))
    assert {value.materialization.relative_path for value in index.members} == {
        "derived/request.json", "derived/bank.json", "derived/specification.json", "derived/secondary_readout.json"}
    retained, members = public._retained_selected(writer=writer, specification=declarative_case.specification,
        original=selected, destination=arguments["destination"], metadata=index_path.parent,
        selector_relative="prepared-sources.json")
    assert retained.request.bank_publication == selected.request.bank_publication
    assert retained.bank == selected.bank and retained.plan is None
    assert members == index.members
    # These are ordinary metadata/access publications with explicit missing
    # source gates; they establish no issue, reveal or scientific qualification.
    assert any(value.code == "matrix.selected-e4.source-qualification" for value in result.preparation.dependencies)


def test_interrupted_selector_publication_replays_actual_committed_prefix_without_changing_bank_flags(
        tmp_path, monkeypatch, declarative_case):
    writer, selected, arguments = project_public_metadata(tmp_path, declarative_case,
        failure="prepared-sources.json", monkeypatch=monkeypatch)
    before = read_bounded_bytes(writer.root.resolve("derived/index.json", for_write=False), maximum_bytes=64 * 1024**2)
    result = public._result(**arguments)
    assert result.source_selection_path.exists()
    assert read_bounded_bytes(writer.root.resolve("derived/index.json", for_write=False),
        maximum_bytes=64 * 1024**2) == before
    actual = load_experiment_inputs(declarative_case.specification, result.source_selection_path).method_inputs
    assert actual.request.bank_publication == selected.request.bank_publication
    assert not result.publications[0].created


def test_retained_projection_refuses_changed_copied_scientific_intent(tmp_path, declarative_case):
    writer, selected, arguments = project_public_metadata(tmp_path, declarative_case)
    public._result(**arguments)
    changed = replace(selected, request=replace(selected.request, record_id="request.changed-copied-intent"))
    with pytest.raises(ValueError, match="copied scientific or operational intent"):
        public._retained_selected(writer=writer, specification=declarative_case.specification, original=changed,
            destination=arguments["destination"], metadata=arguments["destination"].parent / "derived",
            selector_relative="prepared-sources.json")


def test_retained_retry_does_not_normalize_an_explicitly_changed_publication(tmp_path, declarative_case):
    writer, selected, arguments = project_public_metadata(tmp_path, declarative_case)
    public._result(**arguments)
    changed = replace(selected, request=replace(selected.request,
        bank_publication=replace(selected.request.bank_publication, created=not selected.request.bank_publication.created)))
    with pytest.raises(ValueError, match="explicitly selected original programme or bank publication"):
        public._retained_selected(writer=writer, specification=declarative_case.specification, original=changed,
            destination=arguments["destination"], metadata=arguments["destination"].parent / "derived",
            selector_relative="prepared-sources.json")


def test_knowable_public_preparation_refusal_precedes_any_metadata_publication(tmp_path, declarative_case, monkeypatch):
    writer, _, arguments = project_public_metadata(tmp_path, declarative_case)
    def forbidden(self, request):
        pytest.fail("metadata publication preceded deterministic preparation refusal")
    monkeypatch.setattr(type(writer), "write", forbidden)
    with pytest.raises(ValueError, match="workers differ"):
        public._result(**{**arguments, "execution": ExecutionSelection(workers=2)})
    assert not arguments["destination"].exists()
    assert not (arguments["destination"].parent / "derived").exists()


def test_development_product_locator_preserves_actual_development_plan_and_refuses_issued_plan():
    """Pure constructor/codec control; these descriptors confer no custody."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4DevelopmentProgramme
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4FrozenRevision, SelectedE4RevisionNomination
    from empirical_lawhood.runtime.plans import ExecutionPlan

    frozen = SelectedE4FrozenRevision("frozen.disclosed-plan-locator",
        pin("programme.disclosed-plan-locator", SelectedE3E4DevelopmentProgramme),
        pin("nomination.disclosed-plan-locator", SelectedE4RevisionNomination), None, None, "UNENTERED")
    locator = native.SelectedE4DevelopmentProduct(frozen.identity, "original-development", "run.disclosed-plan-locator",
        pin("plan.disclosed-plan-locator", DevelopmentExecutionPlan), "task.disclosed-plan-locator",
        pin("receipt.disclosed-plan-locator", CanonicalTaskReceipt), unpublished(frozen, "publication.disclosed-plan-locator"))
    assert decode_canonical_bytes(locator.canonical_bytes(), native.SelectedE4DevelopmentProduct, maximum_bytes=None) == locator
    with pytest.raises(ValueError, match="exact versioned scientific operand"):
        replace(locator, execution_plan=pin("plan.disclosed-plan-locator", ExecutionPlan))


@pytest.mark.parametrize("retired_version", ("1.0.0", "2.0.0", "3.0.0", "4.0.0", "5.0.0"))
def test_e4_request_codec_requires_current_component_aware_contract(declarative_case, retired_version):
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    current=declarative_case.request
    assert current.VERSION=="6.0.0"
    assert decode_canonical_bytes(current.canonical_bytes(),domain.SelectedE4DeclarativeRequest,maximum_bytes=None)==current
    document=current.to_document()
    document["version"]=retired_version
    with pytest.raises(ValueError,match="unsupported canonical document version"):
        decode_canonical_bytes(canonical_json_document_bytes(document),domain.SelectedE4DeclarativeRequest,maximum_bytes=None)
    request_types=tuple(value for value in domain.protocol_declaration().input_record_types
        if value.SCHEMA==current.SCHEMA)
    assert request_types==(domain.SelectedE4DeclarativeRequest,)


def _protected_parent_roles(case):
    """Unpublished locators test owner routing, never issued CAL acceptance."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4Calibration
    from tests.test_matrix_sampling_follow_on import prior_product
    original=prior_product(pin("calibration.disclosed-parent-roster",SelectedE4Calibration))
    return (case.request.upstream_products,MatrixSelectedOriginalProduct(original.prior_execution,original.reveal_authority),
        (case.request.development_nomination,case.request.development_freeze))


@pytest.mark.parametrize("include_calibration",(False,True))
def test_protected_parent_owner_preserves_complete_e3_cal_and_dev_roles(declarative_case,monkeypatch,include_calibration):
    from empirical_lawhood.api import selected_prepared_access as access
    upstream,calibration,development=_protected_parent_roles(declarative_case)
    if not include_calibration:calibration=None
    before=tuple(value.canonical_bytes() for value in (*upstream,*(() if calibration is None else (calibration,)),*development))
    calls=[];answer=object();writer=object()
    def authenticate(**kwargs):
        calls.append(kwargs)
        return answer
    monkeypatch.setattr(access,"_authenticate_original_input_access",authenticate)
    assert access.selected_e4_original_input_access(artifact_writer=writer,upstream_products=upstream,
        calibration_product=calibration,development=development) is answer
    expected=tuple(sorted((*upstream,*(() if calibration is None else (calibration,))),key=lambda value:value.record.object_id))
    assert calls==[{"artifact_writer":writer,"originals":expected,"development":development,"read_access":None}]
    current=access.SelectedPreparedCurrentAccess(expected)
    assert current.effective_originals(expected)==expected
    assert current.development_access().originals==upstream
    assert tuple(value.canonical_bytes() for value in (*upstream,*(() if calibration is None else (calibration,)),*development))==before
    if calibration is not None:
        with pytest.raises(ValueError,match="four E3 or two E4"):
            access.original_input_access(artifact_writer=writer,
                locators=tuple(("original."+str(index),value) for index,value in enumerate(expected)))


@pytest.mark.parametrize("damage",("missing-e3","duplicate-e3","foreign-e3","wrong-cal","wrong-dev-role","foreign-dev-run"))
def test_protected_parent_owner_refuses_wrong_roles_before_metadata_or_bodies(declarative_case,monkeypatch,damage):
    from empirical_lawhood.api import selected_prepared_access as access
    upstream,calibration,development=_protected_parent_roles(declarative_case)
    if damage=="missing-e3":upstream=upstream[:-1]
    elif damage=="duplicate-e3":upstream=(*upstream[:-1],upstream[-2])
    elif damage=="foreign-e3":upstream=tuple(sorted((calibration,*upstream[1:]),key=lambda value:value.record.object_id))
    elif damage=="wrong-cal":calibration=upstream[0]
    elif damage=="wrong-dev-role":development=tuple(reversed(development))
    else:development=(development[0],replace(development[1],run_id="run.foreign-dev"))
    monkeypatch.setattr(access,"_authenticate_original_input_access",
        lambda **kwargs:pytest.fail("invalid protected roles reached original metadata or body authentication"))
    with pytest.raises((ValueError,TypeError,PermissionError)):
        access.selected_e4_original_input_access(artifact_writer=object(),upstream_products=upstream,
            calibration_product=calibration,development=development)


def test_protected_five_parent_route_enters_existing_fresh_metadata_owner(declarative_case,tmp_path,monkeypatch):
    from empirical_lawhood.api import selected_prepared_access as access,matrix_sampling_runtime
    from tests.test_recursive_public_service import _plane
    upstream,calibration,development=_protected_parent_roles(declarative_case)
    seen=[]
    def refused(writer,original,expected,**_options):
        seen.append((original,expected))
        raise PermissionError("disclosed actual stored authority revoked before protected body")
    monkeypatch.setattr(matrix_sampling_runtime,"_original_product_metadata",refused)
    with pytest.raises(PermissionError,match="stored authority revoked"):
        access.selected_e4_original_input_access(artifact_writer=_plane(tmp_path/"parent-authentication"),
            upstream_products=upstream,calibration_product=calibration,development=development)
    first=min((*upstream,calibration),key=lambda value:value.record.object_id)
    assert seen==[(first,first.record)]


def test_protected_component_guards_use_the_same_full_parent_authenticator(declarative_case,monkeypatch):
    from empirical_lawhood.api import selected_prepared_access as access,selected_e4_native_preparation as preparation
    upstream,calibration,development=_protected_parent_roles(declarative_case)
    parents=declarative_case.request.produced_input_parents
    calls=[];writer=object()
    def authenticate(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(parents=parents)
    monkeypatch.setattr(access,"selected_e4_original_input_access",authenticate)
    preparation.require_selected_e4_original_access(writer,upstream,calibration,produced_input_parents=parents)
    evidence=SimpleNamespace(upstream_products=upstream,calibration_product=calibration,
        development_nomination=development[0],development_freeze=development[1],produced_input_parents=parents)
    preparation.require_selected_e4_plan_access(writer,SimpleNamespace(evidence=evidence,
        declaration=SimpleNamespace(produced_input_parents=parents)))
    assert calls==[{"artifact_writer":writer,"upstream_products":upstream,"calibration_product":calibration},
        {"artifact_writer":writer,"upstream_products":upstream,"calibration_product":calibration,"development":development}]
