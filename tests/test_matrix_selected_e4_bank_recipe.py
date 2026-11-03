# SPDX-License-Identifier: MPL-2.0
"""Pure recipe and disclosed orchestration controls; no genuine source authority.

Actual issued-producer custody remains the existing protected owner and held
workflow acceptance. These tests do not substitute their locators for that chain.
"""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3PreparationSelection
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_bank_recipe as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe, STREAM_RULE
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeFactor
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledCalibrationCriterion
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Design
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.api import matrix_selected_e3_e4_runtime as owner
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_selected_package import package as literal_package
from tests.test_matrix_sampling_follow_on import prior_product


def reference(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, sha256(("DISCLOSED." + name).encode()).hexdigest())


def recipe():
    path = Path(__file__).parents[1] / "programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/matrix.e3.deanneal.nominal.canonical.json"
    nominal = decode_canonical_bytes(path.read_bytes(), MatrixParameterCoordinate, maximum_bytes=None)
    families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
    coordinates = tuple(replace(nominal, coordinate_id="coordinate.recipe." + str(index), family_id=family)
        for index, family in enumerate(families))
    factors = tuple(ScheduledProgrammeFactor(name, "LINEAR", Decimal(1), Decimal(2), Decimal(3))
        for name in ("temperature", "friction", "coupling"))
    return domain.SelectedE4BankRecipe("recipe.disclosed-e4",
        reference("original.preparation", ProtectedE3PreparationSelection),
        reference("original.public-package", MatrixSelectedPublicPackage), old.coordinate_identity(nominal),
        reference("original.assay", ScheduledResponseProtocol), reference("original.policy", old.ScheduledPrefixPolicy),
        coordinates, tuple((phase, SelectedE3E4Design("design." + phase.lower(), count, Decimal(".95"), factors, 4))
            for phase, count in (("CALIBRATION", 64), ("CONFIRMATION", 64), ("DEVELOPMENT", 32))),
        SelectedE4StreamRecipe("streams.disclosed-e4", "a" * 64, "b" * 64, STREAM_RULE),
        ScheduledCalibrationCriterion("criterion.disclosed-e4", "unit.disclosed-whole-group", 64, Decimal(0), families,
            "COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY"))


def test_explicit_all_phase_recipe_roundtrip_and_no_hidden_population_choices():
    selected = recipe()
    raw = selected.canonical_bytes()
    assert decode_canonical_bytes(raw, domain.SelectedE4BankRecipe, maximum_bytes=len(raw)) == selected
    assert tuple((phase, design.group_count, design.cases_per_group, design.wave_group_count)
        for phase, design in selected.population_designs) == (
        ("CALIBRATION", 64, 9, 4), ("CONFIRMATION", 64, 9, 4), ("DEVELOPMENT", 32, 9, 4))
    edited = replace(selected, population_designs=tuple((phase, replace(design, group_count=8))
        for phase, design in selected.population_designs), calibration_criterion=replace(selected.calibration_criterion, minimum_group_count=8))
    assert all(design.group_count == 8 for _, design in edited.population_designs)
    assert edited.identity != selected.identity
    assert b"qualifications" not in raw and b"gate" not in raw


@pytest.mark.parametrize("damage", ("mutable", "missing-phase", "missing-family", "reordered-phase"))
def test_recipe_refuses_mutable_or_incomplete_full_census(damage):
    selected = recipe()
    with pytest.raises((TypeError, ValueError)):
        if damage == "mutable":
            replace(selected, population_designs=list(selected.population_designs))
        elif damage == "missing-phase":
            replace(selected, population_designs=selected.population_designs[:-1])
        elif damage == "missing-family":
            replace(selected, coordinates=selected.coordinates[:-1])
        else:
            replace(selected, population_designs=tuple(reversed(selected.population_designs)))


def test_declared_streams_preserve_four_purposes_and_separate_effective_numeric_inputs():
    selected = recipe().streams
    values = [selected.streams("group.disclosed." + str(index), future=future)
        for index in range(160) for future in (False, True)]
    seeds = tuple(stream.effective_seed for row in values for stream in row)
    assert len(seeds) == len(set(seeds)) == 160 * 2 * 4
    assert values[0] == selected.streams("group.disclosed.0", future=False)
    assert values[0] != selected.streams("group.disclosed.0", future=True)
    assert decode_canonical_bytes(selected.canonical_bytes(), type(selected), maximum_bytes=None) == selected
    with pytest.raises(ValueError):
        replace(selected, future_seed_material_sha256=selected.prefix_seed_material_sha256)
    with pytest.raises(ValueError):
        replace(selected, derivation_rule_id="unreviewed-rule")
    with pytest.raises(TypeError):
        selected.streams("group.disclosed", future=1)


def original_locators(public):
    pins = (old.identity(public.models), old.identity(public.model_freeze),
        public.calibration, old.identity(public.calibrated_freeze))
    return tuple(MatrixSelectedOriginalProduct(prior_product(pin).prior_execution, prior_product(pin).reveal_authority)
        for pin in sorted(pins, key=lambda value: value.object_id))


def test_public_package_extraction_replays_all_four_actual_typed_originals_and_keeps_cal_parent_only(monkeypatch):
    original = literal_package(missing=1)
    public = MatrixSelectedPublicPackage.from_package(original)
    products = original_locators(public)
    by_pin = {old.identity(record): record for record in
        (original.models, original.model_freeze, original.calibration, original.calibrated_freeze)}
    calls = []

    def disclosed_original_read(writer, pairs, codecs, *, scope_validator):
        # This control replaces original I/O only; the real callback is still
        # passed to the owning original-product loader in production.
        calls.extend(pairs)
        assert scope_validator.keywords["frozen"] is public
        return tuple(by_pin[pin].canonical_bytes() for _, pin in pairs)

    from empirical_lawhood.api import matrix_sampling_runtime
    monkeypatch.setattr(matrix_sampling_runtime, "_original_products", disclosed_original_read)
    before = original.canonical_bytes()
    assert owner.authenticate_selected_e3_public_package(writer=object(), public=public,
        upstream_products=products, codecs={}) is None
    assert tuple(pin for _, pin in calls) == tuple(product.record for product in products)
    assert original.canonical_bytes() == before and original.calibration.radius is None


@pytest.mark.parametrize("damage", ("missing", "foreign", "duplicate", "mutable"))
def test_public_package_extraction_refuses_foreign_census_before_original_payload_io(monkeypatch, damage):
    public = MatrixSelectedPublicPackage.from_package(literal_package())
    products = original_locators(public)
    if damage == "missing":
        products = products[:-1]
    elif damage == "foreign":
        foreign = prior_product(reference("foreign.models", type(public.models)))
        products = tuple(sorted((*products[:-1], MatrixSelectedOriginalProduct(foreign.prior_execution, foreign.reveal_authority)),
            key=lambda value: value.record.object_id))
    elif damage == "duplicate":
        products = (*products[:-1], products[0])
    else:
        products = list(products)
    from empirical_lawhood.api import matrix_sampling_runtime
    monkeypatch.setattr(matrix_sampling_runtime, "_original_products",
        lambda *_args, **_kwargs: pytest.fail("invalid original producer census reached protected payload"))
    with pytest.raises(PermissionError):
        owner.authenticate_selected_e3_public_package(writer=object(), public=public, upstream_products=products, codecs={})


def test_recipe_publisher_refuses_missing_original_custody_before_any_new_publication(metadata_publisher, monkeypatch):
    """Real typed inputs/custody; disclosed source seam grants no source acceptance."""
    api,f=metadata_publisher.api,metadata_publisher.f
    directory=Path(f.case.plane.root.contract.canonical_path)/"refused-original-custody"

    def refused(**_kwargs):
        raise PermissionError("DISCLOSED_MISSING_ORIGINAL_PRODUCER")

    monkeypatch.setattr(api, "authenticate_selected_e4_bank_recipe_inputs", refused)
    monkeypatch.setattr(f.case.plane,"write",lambda *_a,**_kw:pytest.fail("refused original custody reached publication"))
    with pytest.raises(PermissionError, match="MISSING_ORIGINAL_PRODUCER"):
        api.publish_selected_e4_bank_recipe(inputs=f.inputs, project_root=metadata_publisher.root,
            artifact_writer=f.case.plane, metadata_directory=directory, execution=object())
    assert not directory.exists()



@pytest.fixture(scope="module")
def literal_recipe_source_inputs(tmp_path_factory):
    """Actual typed/guarded metadata, with disclosed unissued producer locators."""
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as e3
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import ProtectedE3PreFitJoin
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import adapt_e3_frozen_package
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.runtime.experimental_statistics import split_upper_calibration
    from tests.test_matrix_e3_protected_public_lowering import prepared_case
    from tests.test_matrix_factor_confirmation_eligibility import publish

    case = prepared_case(tmp_path_factory.mktemp("declared-e4-recipe"))
    source, configuration = case.inputs, case.fit_config
    publications = tuple((key, ArtifactIdentity(publication.logical.logical_artifact_id, "disclosed-original-metadata",
        publication.logical.payload_schema, publication.logical.content_sha256, publication.logical.media_type,
        publication.materialization.size_bytes), publication.materialization.materialization_id, availability)
        for key, publication, availability in configuration.publications)
    join = ProtectedE3PreFitJoin("prefit.disclosed-e4-recipe", case.specification.identity, case.allocation.identity,
        source.training_allocation.identity, old.identity(source.reservation.allocation), old.identity(source.reservation),
        old.identity(source.native_specification), publications, configuration.fit_cutoff)
    models = e3.fit_protected_e3_models(source, join, case.train_features, case.train_outcomes,
        record_id="models.disclosed-e4-recipe")
    frozen = e3.freeze_protected_e3(case.specification, case.allocation, models, record_id="freeze.disclosed-e4-recipe")
    groups = case.allocation.unit_ids("calibration")
    rank = split_upper_calibration((None,) * len(groups), alpha=case.specification.calibration_alpha).rank
    calibration = e3.ProtectedE3Calibration("calibration.disclosed-e4-recipe", case.specification.identity,
        case.allocation.identity, old.identity(models), old.identity(frozen),
        tuple((group, None, ("MISSING_POINT_OR_TARGET",)) for group in groups), rank, None,
        tuple(reference("forecast." + group, e3.ProtectedE3Forecast) for group in groups),
        tuple(reference("outcome." + group, e3.ProtectedE3PairedOutcome) for group in groups))
    calibrated = e3.freeze_protected_e3(case.specification, case.allocation, models,
        record_id="calibrated.disclosed-e4-recipe", model_freeze=frozen, calibration=calibration)
    complete = adapt_e3_frozen_package(record_id="selected.disclosed-e4-recipe", specification=case.specification,
        allocation=case.allocation, prefit=join, models=models, model_freeze=frozen, calibration=calibration,
        calibrated_freeze=calibrated, selection_unit_ids=tuple(sorted((*groups, *case.allocation.unit_ids("evaluation")))))
    public = MatrixSelectedPublicPackage.from_package(complete)
    assay = case.protocols[0]
    prototype = assay.public_source.coordinate
    selected = recipe()
    factors = tuple(ScheduledProgrammeFactor(name, "LOG", Decimal(".5"), Decimal(1), Decimal(2))
        for name in ("temperature", "friction", "coupling"))
    coordinates = tuple(replace(prototype, coordinate_id="coordinate.recipe.actual." + str(index), family_id=family)
        for index, family in enumerate(sorted(FOUR_FAMILY_PREPARATION_IDS)))
    selected = replace(selected, original_preparation=ObjectIdentity.from_record(case.selection.selection_id, case.selection),
        original_public_package=public.identity, prototype=old.coordinate_identity(prototype),
        assay=ObjectIdentity.from_record(assay.protocol_id, assay), prefix_policy=old.identity(assay.public_source.policy),
        coordinates=coordinates, population_designs=tuple((phase, replace(design, group_count=4, factors=factors))
            for phase, design in selected.population_designs),
        calibration_criterion=replace(selected.calibration_criterion, minimum_group_count=4))
    inputs = domain.SelectedE4BankRecipeSourceInputs("inputs.disclosed-e4-recipe", selected, case.selection,
        publish(case.plane, case.selection, "disclosed-recipe.original-preparation"), public, original_locators(public), assay,
        publish(case.plane, assay, "disclosed-recipe.original-assay"), case.response_selection.template_publications[0])
    return SimpleNamespace(inputs=inputs, case=case, publish=publish, package=complete)


def test_complete_three_phase_bank_recipe_uses_actual_original_typed_operands_and_cold_replays(literal_recipe_source_inputs):
    f = literal_recipe_source_inputs
    inputs, writer = f.inputs, f.case.plane
    before = inputs.original_preparation.canonical_bytes()
    allocation = domain.recipe_allocation(inputs)
    assert len(allocation.roots) == 4 * 9 * 3 and len(allocation.independent_group_ids) == 12
    reservation = old.ScheduledReservation("reservation." + inputs.recipe.record_id, allocation,
        f.publish(writer, allocation, "disclosed-recipe.allocation"))
    selection = domain.recipe_selection(inputs, reservation)
    specification = old.ScheduledSpecification("specification." + inputs.recipe.record_id, selection,
        f.publish(writer, selection, "disclosed-recipe.selection"))
    criterion = f.publish(writer, inputs.original_preparation.mathematical_protocol, "disclosed-recipe.criterion")
    for phase in domain.PHASES:
        descriptors, responses = domain.recipe_responses(inputs, reservation, specification, f.case.provenance, phase)
        phase_roots = tuple(value for value in allocation.roots if value.root.role.value == phase)
        assert tuple(value.root for value in descriptors) == phase_roots
        groups = tuple(sorted({value.root.independent_group_id for value in phase_roots}))
        assert tuple(group for group, _ in responses.panels) == groups
        assert len(descriptors) == len(responses.protocols) == 9 * len(groups)
        compact_by_root = {value.root_id: value for value in descriptors}
        for protocol in responses.protocols:
            compact = compact_by_root[protocol.public_source.root.root_id]
            assert protocol.public_source.root == compact.root.root
            assert protocol.public_source.source == compact.identity
            assert protocol.templates.source == compact.identity
        for group, panels in responses.panels:
            common, future = panels
            roots = tuple(value for value in phase_roots if value.root.independent_group_id == group)
            assert common.role == "COMMON_NOISE_PANEL" and future.role == "INDEPENDENT_FUTURE"
            assert all(common.streams == value.streams for value in roots)
            assert future.streams == inputs.recipe.streams.streams(group, future=True)
        publication = f.publish(writer, responses, "disclosed-recipe.responses." + phase.lower())
        bank = domain.recipe_bank(inputs, reservation=reservation, specification=specification,
            provenance=f.case.provenance, criterion_publication=criterion, response_publication=publication, phase=phase)
        programme = domain.recipe_programme(bank, phase)
        assert len(bank.sources) == len(programme.cases) == 36 and len(programme.group_ids) == 4
        for record in (inputs, bank, programme):
            raw = record.canonical_bytes()
            assert decode_canonical_bytes(raw, type(record), maximum_bytes=len(raw)) == record
        assert domain.validate_selected_e4_recipe_bank(inputs, bank, phase) is None
        changed = replace(inputs, recipe=replace(inputs.recipe, streams=replace(inputs.recipe.streams,
            future_seed_material_sha256="c" * 64)))
        with pytest.raises(ValueError, match="differs|changes|exact original blind prospective publication"):
            domain.validate_selected_e4_recipe_bank(changed, bank, phase)
    assert inputs.original_preparation.canonical_bytes() == before


@pytest.fixture
def metadata_publisher(literal_recipe_source_inputs, monkeypatch):
    """Real metadata custody; original/source seams are stubs, not source acceptance."""
    from empirical_lawhood.api import selected_e4_bank_recipe as api
    f = literal_recipe_source_inputs
    root = Path(__file__).resolve().parents[1]
    admitted = SimpleNamespace(implementation_commit=f.case.provenance.observed_git_head, implementation_sha256="a" * 64)
    calls = []
    monkeypatch.setattr(api, "authenticate_selected_e4_bank_recipe_inputs", lambda **_kwargs: calls.append("fresh-original-replay"))
    monkeypatch.setattr(api, "_current_selection", lambda **_kwargs: (root, admitted))

    def source_current_stub(selected_root, selected):
        assert selected_root == root and selected is admitted

    monkeypatch.setattr(api, "require_admitted_target_source_current", source_current_stub)
    monkeypatch.setattr(api, "capture_matrix_provenance", lambda **_kwargs: f.case.provenance)
    return SimpleNamespace(api=api, f=f, root=root, calls=calls)


def test_actual_immutable_publications_resume_partial_prefix_and_keep_created_descriptors_exact(
        metadata_publisher, monkeypatch):
    f, api = metadata_publisher.f, metadata_publisher.api
    writer, inputs = f.case.plane, f.inputs
    directory = Path(writer.root.contract.canonical_path) / "metadata-recipe-resume"
    actual_write = writer.write
    observations, interrupted = [], False

    def observed(request):
        nonlocal interrupted
        result = actual_write(request)
        observations.append((Path(request.relative_path).name, result.created))
        if Path(request.relative_path).name == "CALIBRATION.responses.json" and not interrupted:
            interrupted = True
            raise RuntimeError("DISCLOSED_INTERRUPTION_AFTER_REAL_COMMIT_BEFORE_INDEX")
        return result

    monkeypatch.setattr(writer, "write", observed)
    arguments = dict(inputs=inputs, project_root=metadata_publisher.root, artifact_writer=writer,
        metadata_directory=directory, execution=object())
    with pytest.raises(RuntimeError, match="AFTER_REAL_COMMIT"):
        api.publish_selected_e4_bank_recipe(**arguments)
    assert not (directory / "index.json").exists()
    recovered = api.publish_selected_e4_bank_recipe(**arguments)
    assert (directory / "index.json").is_file()
    assert len(recovered.banks) == 3
    assert observations[:2] == [("allocation.json", True), ("allocation.json", False)]
    assert all(not publication.created for _, publication in recovered.publications)
    for key, publication in recovered.publications:
        assert publication.logical.logical_artifact_id == (
            "selected-e4.bank-recipe." + key.lower() + "." + publication.logical.content_sha256)
        assert Path(publication.materialization.relative_path).name == key + ".json"
    assert all(bank.reservation.publication.created is False and bank.specification.publication.created is False
        and bank.response_selection_publication.created is False for _, bank in recovered.banks)
    expected = recovered.index.canonical_bytes()
    repeated = api.publish_selected_e4_bank_recipe(**arguments)
    assert repeated.index.canonical_bytes() == expected
    assert repeated.banks == recovered.banks and repeated.publications == recovered.publications
    loaded = api.load_selected_e4_bank_recipe(**arguments)
    assert loaded.index.canonical_bytes() == expected and loaded.banks == recovered.banks
    assert loaded.publications == recovered.publications
    assert len(metadata_publisher.calls) == 4
    assert all(row.kind.value == "SCIENTIFIC_EVIDENCE" for row in loaded.requirements)
    assert all("DEVELOPMENT" not in row.code for row in loaded.requirements)


def test_foreign_metadata_path_refuses_before_any_new_publication(metadata_publisher, monkeypatch):
    f, api = metadata_publisher.f, metadata_publisher.api
    writer = f.case.plane
    directory = Path(writer.root.contract.canonical_path) / "metadata-recipe-foreign"
    directory.mkdir()
    (directory / "unrelated.json").write_bytes(b"foreign bytes must stay untouched")
    monkeypatch.setattr(writer, "write", lambda *_args, **_kwargs: pytest.fail("foreign namespace reached publication"))
    with pytest.raises(PermissionError, match="foreign|orphan"):
        api.publish_selected_e4_bank_recipe(inputs=f.inputs, project_root=metadata_publisher.root,
            artifact_writer=writer, metadata_directory=directory, execution=object())
    assert (directory / "unrelated.json").read_bytes() == b"foreign bytes must stay untouched"


@pytest.mark.parametrize("changed", ("prefix", "full"))
def test_selected_original_projection_refuses_changed_factor_math(literal_recipe_source_inputs, changed):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import (
        selected_original_factor_rule, validate_selected_prefix_projection,
    )
    inputs = literal_recipe_source_inputs.inputs
    criterion = inputs.original_preparation.mathematical_protocol
    policy = inputs.assay.public_source.policy
    cutoff = inputs.original_public_package.specification.measurement.origin_tick
    validate_selected_prefix_projection(criterion, policy, cutoff)
    field = "associative_leakage_maximum"
    if changed == "prefix":
        rule = replace(policy.factor_rule, **{field: getattr(policy.factor_rule, field) + Decimal("0.01")})
        policy = replace(policy, factor_rule=rule)
    else:
        full = selected_original_factor_rule(criterion)
        altered = replace(full, **{field: getattr(full, field) + Decimal("0.01")})
        compatibilities = tuple(replace(value, target=altered,
            original=replace(value.original, **{field: getattr(value.original, field) + Decimal("0.01")}))
            for value in criterion.factor_rule_compatibilities)
        criterion = replace(criterion, factor_rule=altered.identity, factor_rule_compatibilities=compatibilities)
    with pytest.raises(ValueError, match="full-to-prefix"):
        validate_selected_prefix_projection(criterion, policy, cutoff)


def test_actual_three_phase_recipe_refuses_reserved_e6_physics_before_publication(literal_recipe_source_inputs, monkeypatch):
    f = literal_recipe_source_inputs
    factors = tuple(ScheduledProgrammeFactor(name, "LINEAR", Decimal(1), Decimal(2), Decimal(3))
        for name in ("temperature", "friction", "coupling"))
    recipe = replace(f.inputs.recipe, population_designs=tuple((phase, replace(design, factors=factors))
        for phase, design in f.inputs.recipe.population_designs))
    inputs = replace(f.inputs, recipe=recipe)
    def forbidden(*args, **kwargs):
        raise AssertionError("reserved-physics refusal published an E4 input")
    monkeypatch.setattr(f.case.plane, "write", forbidden)
    with pytest.raises(ValueError, match="reserved E6 full physical key"):
        domain.recipe_allocation(inputs)


@pytest.mark.parametrize("selection_kind", ("implementation", "exact-closure"))
def test_standalone_recipe_reuses_actual_source_once_for_publish_load_and_exact_retry(
        literal_recipe_source_inputs, monkeypatch, selection_kind):
    """Real source admission and metadata custody; original E3 I/O is unissued.

    Only original producer/assay/publication authentication is replaced. This
    control proves no original E3 authority, native result or qualification.
    """
    from empirical_lawhood.api import recursive_authoring, selected_e4_bank_recipe as api
    from empirical_lawhood.infrastructure import numerical_provenance, source_closure
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection

    f=literal_recipe_source_inputs
    root=Path(__file__).resolve().parents[1]
    if selection_kind=="implementation":
        selected=recursive_authoring.implementation_binding(root)
    else:
        selected=source_closure.capture_target_closure(root,"selected-e4.bank-recipe.current-source").closure
    execution=ExecutionSelection(1,"main-locked",ObjectIdentity.from_record("recursive-member.implementation",selected),
        f.case.plane.root.contract.canonical_path)
    # These source controls retain the production original-input refusal in a
    # separate test above; their explicit E3 I/O seams do not fake issued custody.
    monkeypatch.setattr(api,"authenticate_selected_e3_public_package",lambda **_:None)
    monkeypatch.setattr(api,"authenticate_selected_e3_assay",lambda **_:None)
    monkeypatch.setattr(api,"authenticate_publication",lambda *_a,**_kw:None)
    captured,archives=[],[]
    actual_capture,actual_git=source_closure.capture_admitted_target_source,source_closure._git
    def capture(*args,**kwargs):
        actual=actual_capture(*args,**kwargs)
        captured.append(actual)
        return actual
    def git(root,*args):
        if args[0]=="archive":archives.append(args)
        return actual_git(root,*args)
    def raw_inventory(*_a,**_kw):
        pytest.fail("recipe rebuilt an already admitted numerical source inventory")
    monkeypatch.setattr(source_closure,"capture_admitted_target_source",capture)
    monkeypatch.setattr(api,"capture_admitted_target_source",capture)
    monkeypatch.setattr(source_closure,"_git",git)
    monkeypatch.setattr(numerical_provenance,"numerical_package_sources",raw_inventory)
    monkeypatch.setattr(numerical_provenance,"selected_dependency_lock_sha256",raw_inventory)
    arguments=dict(inputs=f.inputs,project_root=root,artifact_writer=f.case.plane,execution=execution,
        metadata_directory=Path(f.case.plane.root.contract.canonical_path)/("actual-source-recipe-"+selection_kind))
    original=f.inputs.canonical_bytes()
    published=api.publish_selected_e4_bank_recipe(**arguments)
    assert len(captured)==len(archives)==1
    loaded=api.load_selected_e4_bank_recipe(**arguments)
    assert len(captured)==len(archives)==2
    repeated=api.publish_selected_e4_bank_recipe(**arguments)
    assert len(captured)==len(archives)==3
    assert len({id(source) for source in captured})==3
    assert loaded.index.canonical_bytes()==repeated.index.canonical_bytes()==published.index.canonical_bytes()
    assert loaded.banks==repeated.banks==published.banks
    assert loaded.publications==repeated.publications==published.publications
    assert f.inputs.canonical_bytes()==original
