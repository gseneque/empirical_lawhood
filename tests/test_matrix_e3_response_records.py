# SPDX-License-Identifier: MPL-2.0
"""Disclosed response metadata and original pure nonuse arithmetic.

No fixture authenticates custody, qualifies numerics, fits models or acquires a
trajectory. The completed-native fixture is header/receipt metadata only; the
existing cold reader deliberately rejects its non-archive transport bytes.
"""

from dataclasses import fields, replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as old
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_inputs as inputs
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as methods
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_records as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_source_records as sources
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as sr, response_records as rr
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import array_product, forecast_response_arrays
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history, parameter_history_segments, parameter_source
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.study_authoring import MaterializationQualificationReceipt, SourceAccessDisposition
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion
from tests.test_matrix_e3_prefix_records import current_case
from tests.test_matrix_e3_protected_methods import reference
from tests.test_matrix_e3_protected_source_records import response_fixture
from tests.test_matrix_factor_confirmation_eligibility import stock
from tests.test_matrix_parameter_history import source as parameter_template
from tests.test_matrix_scheduled_history import scheduled


def blocked(*args, **kwargs):
    raise AssertionError("response record control entered a forbidden native/fit producer")


def publication(case, record, suffix, *, access=Access.OUTCOME_BLIND, visibility=Visibility.PROSPECTIVE):
    return case.plane.write(ArtifactWriteRequest("literal.response." + suffix, "metadata/" + suffix + ".json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "literal-response", "metadata", record.canonical_bytes(), visibility, (), access))


def qualification(record, pub, suffix):
    return MaterializationQualificationReceipt("qualification.literal." + suffix, "source.literal." + suffix,
        ObjectIdentity(pub.logical.logical_artifact_id, record.SCHEMA, record.VERSION, record.fingerprint()), record.fingerprint(),
        "world.literal.software", ObjectIdentity("operator.literal.metadata", "empirical-lawhood/testing/metadata", "1.0.0", "a" * 64),
        ("view.literal",), ("unit.literal",), ("frame.literal",), ("clock.literal",), "receiver.literal", "validity.literal",
        "uncertainty.literal", SourceAccessDisposition.VERIFIED_ACCESS, pub.logical.outcome_access, pub.logical.visibility_ceiling)


def physical(case, causal, *, available=False):
    protocol, profile, config = case.protocol, case.profile, case.physical_config
    producers = (protocol.public_source.source, sources.identity(causal), owner._object(protocol), sources.identity(profile))
    if not available:
        values, disposition, statuses = forecast_response_arrays(protocol, {}, {}, disposition=causal.disposition)
        raw, arrays = array_product(protocol, values, role="FORECAST", artifact_id="ordinary.literal.physical-arrays",
            producers=producers, access=Access.OUTCOME_BLIND, visibility=Visibility.PROSPECTIVE, nonfinite=tuple(values))
    else:
        # Authored finite metadata, not a physical forecast or numerical witness.
        members = tuple(MatrixArrayMember(name, dtype, shape, "a" * 64)
            for name, (dtype, shape) in sorted(owner._physical_members(protocol, "AVAILABLE").items()))
        arrays = replace(case.physical.arrays, members=members, producers=tuple(sorted(producers, key=lambda row: row.object_id)))
        raw, disposition = b"literal metadata only", "AVAILABLE"
        statuses = tuple((view, predictor, "AVAILABLE", None) for view in ("PRIMARY", "FINE") for predictor in old.DESCRIPTIONS)
    record = owner.ProtectedE3PhysicalForecast("physical.literal.current", sr.identity(config), protocol.public_source.source,
        sources.identity(causal), owner._object(protocol), sources.identity(profile), owner._object(protocol.mechanical_model),
        causal.frame_sha256, arrays, disposition, statuses)
    return raw, record


def error_operands(case, causal, *, available=False):
    allocation = case.allocation
    # Complete selected training IDs, with explicitly absent fitted targets.
    # These neutral records exercise joins only and produce no prediction.
    neutral = tuple(old.MatrixE3EstimatorModel(method.method_key, () if method.method_key == "RAW_TRAIN_MEDIAN" else ("literal",),
        (None,) * 15, (None,) * 15, allocation.unit_ids("train"), (0,) * 15) for method in case.specification.methods)
    model = methods.ProtectedE3ModelSet("model.literal.response", case.specification.identity, allocation.identity,
        reference("prefit", inputs.ProtectedE3PreFitJoin), reference("train-features", old.MatrixE3FeatureBank),
        reference("train-outcomes", old.MatrixE3OutcomeBank), neutral)
    frozen = methods.ProtectedE3FrozenProducts("freeze.literal.response", case.specification.identity, allocation.identity,
        methods.identity(model), model.reservation_join, None, None)
    feature = methods.ProtectedE3CausalFeature("feature.literal.response", case.config.source.allocation, case.protocol.public_source,
        sources.identity(causal), causal.frame_sha256, "AVAILABLE" if available else "UNAVAILABLE",
        tuple((name, causal.cutoff_tick * case.specification.measurement.primary_timestep if name == "cutoff" else D(0))
            for name in FEATURES) if available else (), tuple(sorted((sources.identity(causal), sources.identity(case.numerical),
                sources.identity(case.witness), sources.identity(case.frames)), key=lambda row: row.object_id)))
    error = methods.ProtectedE3Forecast("forecast.literal.response", case.specification.identity, allocation.identity,
        methods.identity(model), methods.identity(frozen), feature, "calibration", tuple((method, (None,) * 15) for method in old.METHODS), None, "UNCALIBRATED")
    return model, frozen, error


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    temporary = tmp_path_factory.mktemp("literal-protected-response")
    exposed = stock.__wrapped__(temporary, parameter_template().provenance)
    with pytest.MonkeyPatch.context() as patch:
        prefix = current_case(scheduled.__wrapped__(exposed), patch)
        selection, protocols, panels = response_fixture(prefix.originals)
        protocol = next(row for row in protocols if row.public_source.source == prefix.config.source.identity)
        selected_panels = tuple(row for row in panels if row.independent_group_id == prefix.source.root.root.independent_group_id)
        pub = publication(prefix, selection, "selection")
        q = qualification(selection, pub, "selection")
        profile = owner.project_protected_e3_response_numerics(protocol, provenance=selection, publication=pub, qualification=q)
        physical_config = owner.ProtectedE3PhysicalForecastConfig("config.matrix-e3-protected." + prefix.source.root_id + ".physical-forecast",
            prefix.source.root_id, prefix.specification.identity, owner._object(protocol), sources.identity(profile))
        config = owner.ProtectedE3ResponseConfig("config.matrix-e3-protected." + prefix.source.root_id + ".responses", "responses",
            prefix.specification.identity, sources.identity(prefix.manifest), prefix.config.source, sources.identity(selection),
            owner._object(protocol), sources.identity(profile))
        allocation = inputs.project_protected_e3_allocation(replace(prefix.originals.inputs,
            reservation=prefix.manifest.reservation, native_specification=prefix.manifest.native_specification))
        result = SimpleNamespace(**vars(prefix), selection=selection, protocols=protocols, panels=selected_panels, protocol=protocol,
            profile=profile, publication=pub, qualification=q, physical_config=physical_config, native_config=config, allocation=allocation)
        result.physical_raw, result.physical = physical(result, result.causal)
        result.models, result.frozen, result.error = error_operands(result, result.causal)
        raw, arrays = array_product(protocol, {"unentered_branches": np.arange(48, dtype="<i8")}, role="RESPONSES",
            artifact_id="ordinary.literal.response-arrays", producers=(config.source.identity, sources.identity(selection),
                sr.identity(result.physical), sources.identity(result.error), sources.identity(profile)),
            access=Access.EVALUATION_SEALED, visibility=Visibility.PROSPECTIVE)
        result.response_raw = raw
        result.response = owner.ProtectedE3NativeResponse("responses.literal.current", sr.identity(config), config.source.identity,
            sources.identity(result.history), sources.identity(result.causal), sr.identity(result.physical), sources.identity(result.error),
            owner._object(protocol), sources.identity(profile), sources.identity(selection), arrays,
            tuple(row[0] for row in rr.branch_census(protocol, selected_panels)), (), "UNEVALUABLE", ("prefix-unevaluable",))
        yield result


@pytest.fixture(autouse=True)
def forbid_native(monkeypatch):
    for module, name in ((parameter_history_segments, "acquire_parameter_segment"), (parameter_source, "acquire_parameter_history"),
            (parameter_history, "advance_parameter_pair"), (methods, "fit_protected_e3_models")):
        monkeypatch.setattr(module, name, blocked)
    monkeypatch.setattr(np.random, "Generator", blocked)
    monkeypatch.setattr(np.random, "PCG64DXSM", blocked)
    monkeypatch.setattr(np.random, "default_rng", blocked)


def arguments(case, **changes):
    result = dict(source=case.source, specification=case.specification, manifest=case.manifest, selection=case.selection,
        protocol=case.protocol, numerical_profile=case.profile, panels=case.panels, history=case.history, causal=case.causal,
        physical_config=case.physical_config, physical=case.physical, error=case.error, allocation=case.allocation,
        models=case.models, frozen=case.frozen, calibration=None, model_freeze=None,
        mathematical_protocol=case.originals.mathematical, projection=case.originals.projection)
    result.update(changes)
    return result


def test_current_records_roundtrip_without_historical_alias_or_qualification(case):
    assert case.source.policy.cutoff_tick == 256 and case.causal.disposition == "UNEVALUABLE"
    assert case.response.validate_source(case.native_config, **arguments(case)) is case.source
    for record in (case.profile, case.physical_config, case.native_config, case.physical, case.response):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
        assert not hasattr(record, "qualified") and not hasattr(record, "standing")
    assert len(case.response.branch_ids) == 48
    assert tuple(f.name for f in fields(case.physical_config)) == ("config_id", "root_id", "specification", "protocol", "numerical_profile")


def test_profile_accepts_actual_original_containers_and_preserves_development_access(case):
    protocol = case.protocols[-1]  # Actual supplied CONF protocol; no legacy bank.
    group = protocol.public_source.root.independent_group_id
    panels = tuple(p for p in response_fixture(case.originals)[2] if p.independent_group_id == group)
    historical = ScheduledResponseSelection("selection.literal.original", ObjectIdentity.from_record(case.manifest.reservation.allocation.allocation_id, case.manifest.reservation.allocation), (protocol,),
        ((group, panels),), case.selection.template_publications, None)
    historical.validate_allocation(case.manifest.reservation.allocation)
    for suffix, container in (("direct", protocol), ("current", case.selection), ("historical", historical)):
        selected = case.protocol if suffix == "current" else protocol
        pub = publication(case, container, "original." + suffix, access=Access.DEVELOPMENT_VISIBLE, visibility=Visibility.DEVELOPMENT_ONLY)
        q = qualification(container, pub, suffix)
        profile = owner.project_protected_e3_response_numerics(selected, provenance=container, publication=pub, qualification=q)
        profile.validate_original(selected, provenance=container, publication=pub, qualification=q)
        assert profile.provenance_publication.logical.outcome_access is Access.DEVELOPMENT_VISIBLE
        assert profile.provenance_publication.logical.visibility_ceiling is Visibility.DEVELOPMENT_ONLY
        assert tuple(getattr(profile, name) for name in owner.NUMERICAL_FIELDS) == tuple(getattr(selected, name) for name in owner.NUMERICAL_FIELDS)


@pytest.mark.parametrize("damage", ("number", "protocol", "publication-hash", "publication-size", "qualification-bytes", "qualification-access", "foreign-container", "ducktype"))
def test_original_numerical_profile_refuses_substitution(case, damage):
    pub, q, protocol, provenance = case.publication, case.qualification, case.protocol, case.selection
    with pytest.raises((TypeError, ValueError)):
        if damage == "number":
            replace(case.profile, native_reference_tolerance=case.profile.native_reference_tolerance * 2).validate_protocol(protocol)
            return
        if damage == "protocol":
            protocol = replace(protocol, native_reference_tolerance=protocol.native_reference_tolerance * 2)
        elif damage == "publication-hash":
            pub = replace(pub, logical=replace(pub.logical, content_sha256="e" * 64))
        elif damage == "publication-size":
            pub = replace(pub, materialization=replace(pub.materialization, size_bytes=pub.materialization.size_bytes + 1))
        elif damage == "qualification-bytes":
            q = replace(q, content_sha256="e" * 64)
        elif damage == "qualification-access":
            q = replace(q, outcome_access=Access.DEVELOPMENT_VISIBLE)
        elif damage == "foreign-container":
            provenance = replace(provenance, root_protocols=provenance.root_protocols[1:])
        else:
            protocol = SimpleNamespace(**{f.name: getattr(protocol, f.name) for f in fields(protocol)})
        owner.project_protected_e3_response_numerics(protocol, provenance=provenance, publication=pub, qualification=q)


@pytest.mark.parametrize("damage", ("source", "frame", "criterion", "force", "receivers", "profile", "cutoff", "missing-view", "finite-nonuse"))
def test_seedless_physical_scope_refuses_changed_selected_science(case, damage):
    physical_record, protocol, causal = case.physical, case.protocol, case.causal
    with pytest.raises((TypeError, ValueError)):
        if damage == "source":
            physical_record = replace(physical_record, source=replace(physical_record.source, object_fingerprint="e" * 64))
        elif damage == "frame":
            physical_record = replace(physical_record, frame_sha256="e" * 64)
        elif damage == "criterion":
            protocol = replace(protocol, criterion=replace(protocol.criterion, object_fingerprint="e" * 64))
        elif damage == "force":
            protocol = replace(protocol, actions=tuple(replace(action, force_norm=D(2)) for action in protocol.actions))
        elif damage == "receivers":
            protocol = replace(protocol, receiver_count=47)
        elif damage == "profile":
            physical_record = replace(physical_record, numerical_profile=replace(physical_record.numerical_profile, object_fingerprint="e" * 64))
        elif damage == "cutoff":
            causal = replace(causal, cutoff_tick=255)
        elif damage == "missing-view":
            physical_record = replace(physical_record, arrays=replace(physical_record.arrays, members=physical_record.arrays.members[:-1]))
        else:
            physical_record = replace(physical_record, arrays=replace(physical_record.arrays,
                members=tuple(replace(member, finite_required=True) for member in physical_record.arrays.members)))
        physical_record.validate_public_inputs(case.physical_config, specification=case.specification, protocol=protocol,
            numerical_profile=case.profile, causal=causal, mathematical_protocol=case.originals.mathematical, projection=case.originals.projection)


@pytest.mark.parametrize("damage", ("source", "history", "freeze", "models", "feature-source", "role", "exposed", "panel", "branches", "nonuse-census", "calibration", "config-operation"))
def test_current_response_source_role_freeze_and_nonuse_guards(case, damage):
    response, config, args = case.response, case.native_config, arguments(case)
    with pytest.raises((TypeError, ValueError)):
        if damage == "source":
            args["source"] = replace(case.source, source_id="source.literal.foreign")
        elif damage == "history":
            response = replace(response, history=replace(response.history, object_fingerprint="e" * 64))
        elif damage == "freeze":
            args["frozen"] = replace(case.frozen, record_id="freeze.literal.foreign")
        elif damage == "models":
            args["models"] = replace(case.models, record_id="models.literal.foreign")
        elif damage == "feature-source":
            args["error"] = replace(case.error, feature=replace(case.error.feature, prefix=replace(case.error.feature.prefix, object_fingerprint="e" * 64)))
        elif damage == "role":
            args["allocation"] = replace(case.allocation, roles=tuple(replace(row, role="evaluation") if row.unit_id == case.error.feature.unit_id else row for row in case.allocation.roles))
        elif damage == "exposed":
            args["allocation"] = replace(case.allocation, units=tuple(replace(row, exposed=True) if row.unit_id == case.error.feature.unit_id else row for row in case.allocation.units))
        elif damage == "panel":
            args["panels"] = (replace(case.panels[0], panel_id="panel.literal.foreign"), case.panels[1])
        elif damage == "branches":
            response = replace(response, branch_ids=response.branch_ids[:-1])
        elif damage == "nonuse-census":
            response = replace(response, arrays=replace(response.arrays, members=(replace(response.arrays.members[0], shape=(47,)),)))
        elif damage == "calibration":
            args["model_freeze"] = case.frozen
        else:
            config = replace(config, operation="response-score", config_id=config.config_id.removesuffix("responses") + "response-score")
        response.validate_source(config, **args)


def test_compact_native_metadata_uses_exact_direct_operands_and_eight_streams(case, monkeypatch):
    # No per-root reconstruction/full population validation is called here.
    monkeypatch.setattr(sources, "bind_protected_e3_source", blocked)
    monkeypatch.setattr(ScheduledSourceIndex, "from_shared", blocked)
    result = owner.protected_e3_response_native_contract(case.native_config, **{key: value for key, value in arguments(case).items()
        if key in ("source", "manifest", "specification", "selection", "protocol", "numerical_profile", "panels", "history", "causal", "physical", "error")})
    subject, config, task, operation, direct, streams, outputs = result
    assert subject == case.native_config.source.identity and config == sr.identity(case.native_config)
    assert task == "matrix-e3-protected." + case.source.root_id + ".responses"
    assert operation == "matrix-e3-protected.scheduled-paired-pulse-responses.v1"
    assert len(direct) == 15 and len(streams) == 8
    assert direct.count(case.native_config.source.identity) == 1
    assert not any(row.object_schema == sr.ScheduledAllocation.SCHEMA for row in direct)
    assert outputs[0].output_id == "arrays"


def test_one_root_reference_lookup_never_iterates_complete_roster():
    class Census:
        reads = 0

        def __len__(self):
            return 1024

        def __iter__(self):
            raise AssertionError("local lookup walked a complete roster")

        def __getitem__(self, index):
            self.reads += 1
            return (str(index).zfill(4), index)

    census = Census()
    assert owner._lookup(census, "0517") == ("0517", 517)
    assert census.reads <= 12


def confirmation_operands(case):
    """Local frozen-chain metadata; no CAL observations or qualification."""
    protocol = next(row for row in case.protocols if row.public_source.root.role.value == "CONFIRMATION")
    descriptor = next(row for row in case.originals.descriptors if row.identity == protocol.public_source.source)
    causal = replace(case.causal, source=descriptor.identity, root=descriptor.root.root,
        arrays=replace(case.causal.arrays, source=descriptor.identity, producers=tuple(sorted(
            (descriptor.identity, case.causal.history, case.causal.witness, case.causal.frame_assessment), key=lambda row: row.object_id))))
    feature = replace(case.error.feature, public_source=protocol.public_source, prefix=sources.identity(causal),
        evidence=tuple(sorted((sources.identity(causal), sources.identity(case.numerical), sources.identity(case.witness), sources.identity(case.frames)), key=lambda row: row.object_id)))
    units = case.allocation.unit_ids("calibration")
    calibration = methods.ProtectedE3Calibration("calibration.literal.response", case.specification.identity, case.allocation.identity,
        sources.identity(case.models), sources.identity(case.frozen), tuple((unit, D(0), ("FINITE",)) for unit in units), len(units), D(0),
        tuple(reference("cal-forecast." + str(i), methods.ProtectedE3Forecast) for i in range(len(units))),
        tuple(reference("cal-outcome." + str(i), methods.ProtectedE3PairedOutcome) for i in range(len(units))))
    frozen = replace(case.frozen, record_id="freeze.literal.response.calibrated", calibration=sources.identity(calibration), model_freeze=sources.identity(case.frozen))
    error = replace(case.error, record_id="forecast.literal.response.conf", feature=feature, frozen_products=sources.identity(frozen),
        role="evaluation", radius=D(0), radius_kind="FINITE")
    return dict(specification=case.specification, allocation=case.allocation, models=case.models, frozen=frozen,
        calibration=calibration, model_freeze=case.frozen, causal=causal, protocol=protocol, error=error, descriptor=descriptor)


def test_conf_joins_actual_original_pre_calibration_freeze_without_refit(case):
    owner._error_forecast(**confirmation_operands(case))


@pytest.mark.parametrize("damage", ("missing", "specification", "allocation", "models", "reservation", "calibrated-prior", "radius"))
def test_conf_rejects_foreign_actual_prior_freeze_even_with_retagged_references(case, damage):
    args = confirmation_operands(case)
    with pytest.raises((TypeError, ValueError)):
        if damage == "missing":
            args["model_freeze"] = None
        elif damage == "radius":
            args["error"] = replace(args["error"], radius=D(1))
        else:
            prior = args["model_freeze"]
            if damage in ("specification", "allocation", "models"):
                prior = replace(prior, **{damage: replace(getattr(prior, damage), object_fingerprint="e" * 64)})
            elif damage == "reservation":
                prior = replace(prior, reservation_join=replace(prior.reservation_join, object_fingerprint="e" * 64))
            else:
                prior = args["frozen"]
            calibration = replace(args["calibration"], model_freeze=sources.identity(prior))
            frozen = replace(args["frozen"], model_freeze=sources.identity(prior), calibration=sources.identity(calibration))
            args.update(model_freeze=prior, calibration=calibration, frozen=frozen,
                error=replace(args["error"], frozen_products=sources.identity(frozen)))
        owner._error_forecast(**args)


def test_withheld_e6_response_acquisition_config_is_refused(case):
    descriptor = next(row for row in case.originals.descriptors if row.root.root.role.value == "WITHHELD_TRANSFER")
    with pytest.raises(ValueError, match="reserved transfer"):
        replace(case.native_config, source=descriptor, config_id="config.matrix-e3-protected." + descriptor.root_id + ".responses")


def completed_metadata(case):
    """A coherent local header/receipt control, explicitly no acquired arrays."""
    from tests.native_completion_fixtures import completion_parents
    causal = replace(case.causal, frame_sha256="a" * 64, disposition="AVAILABLE", reason=None,
        arrays=replace(case.causal.arrays, members=tuple(replace(member, finite_required=True, sha256="a" * 64)
            if member.name == "frame" else member for member in case.causal.arrays.members)))
    _, physical_record = physical(case, causal, available=True)
    models, frozen, error = error_operands(case, causal, available=True)
    args = arguments(case, causal=causal, physical=physical_record, models=models, frozen=frozen, error=error)
    contract = owner.protected_e3_response_native_contract(case.native_config, **{key: value for key, value in args.items()
        if key in ("source", "manifest", "specification", "selection", "protocol", "numerical_profile", "panels", "history", "causal", "physical", "error")})
    _, configuration, task, operation, direct, streams, outputs = contract
    parent = replace(case.history.native.definition.parent_contact, task_id=task, execution_task=replace(case.history.native.definition.parent_contact.execution_task, object_id=task))
    definition = replace(case.history.native.definition, subwork_id="responses." + case.source.root_id, operation_id=operation,
        parent_contact=parent, configuration=configuration, sources=direct, streams=streams, outputs=outputs)
    native_task = "native-subwork." + sha256((task + ":" + definition.subwork_id).encode()).hexdigest()
    raw, _ = encode_matrix_arrays({"literal_metadata_only": np.zeros(1, dtype="<f8")})
    pub = case.plane.write(ArtifactWriteRequest(native_task + ".output.arrays", "literal/native-response-metadata.bin", sr.MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "literal-response", "literal", raw, Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED))
    # The explicit one-member payload fails the complete cold native reader.
    assert case.source.policy.cutoff_tick == case.source.coordinate.ramp_ticks == 256
    consumed = tuple(row for row in streams if row.object_id.endswith(("autonomous-coarse-driver", "autonomous-fine-bridge")))
    completion = NativeSubworkCompletion(definition.identity, case.history.native.completion.contact, OperationalStatus.SUCCEEDED,
        ("arrays",), (), consumed, tuple(row for row in streams if row not in consumed), (), InquiryCost(None, None, None), "literal metadata only", None, ())
    complete_pub = case.plane.write(ArtifactWriteRequest(native_task + ".completion", "literal/native-completion.json", completion.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "literal-response", "literal", completion.canonical_bytes(),
        Visibility.PROSPECTIVE, (Visibility.PROSPECTIVE, Visibility.PROSPECTIVE), Access.EVALUATION_SEALED,
        lineage_parents=completion_parents(completion,Visibility.PROSPECTIVE,Access.EVALUATION_SEALED)))
    attempt = parent.run_id + "." + native_task + ".attempt-001"
    receipt = CanonicalTaskReceipt("receipt." + attempt, parent.run_id, native_task, attempt, parent.implementation_commit,
        definition.input_materialization_ids, (complete_pub.materialization, pub.materialization), (complete_pub.logical, pub.logical), (), OperationalStatus.SUCCEEDED, ())
    names = {"noise." + panel.panel_id + "." + name for panel in case.panels for name in ("primary", "fine", "bridge")}
    names.update("branch." + branch + "." + name for branch in case.response.branch_ids for name in ("positions", "momenta", "innovations", "ticks", "alpha_tilde"))
    arrays = replace(case.response.arrays, array_artifact=replace(case.response.arrays.array_artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw)),
        members=tuple(MatrixArrayMember(name, "<f8", (1,), "b" * 64) for name in sorted(names)),
        producers=tuple(sorted((case.native_config.source.identity, sources.identity(case.selection), sr.identity(physical_record),
            sources.identity(error), sources.identity(case.profile)), key=lambda row: row.object_id)))
    response = replace(case.response, causal_prefix=sources.identity(causal), physical_forecast=sr.identity(physical_record), error_forecast=sources.identity(error),
        arrays=arrays, native=(sr.ScheduledNativeEvidence(definition, completion, receipt),), disposition="COMPLETED", reason_codes=())
    return response, args, raw


def test_native_metadata_ordinary_alias_requires_independent_cold_bytes(case):
    response, args, raw = completed_metadata(case)
    assert response.validate_source(case.native_config, **args) is case.source
    assert len(response.arrays.members) == 48 * 5 + 2 * 3 == 246
    assert response.arrays.array_artifact.artifact_id != response.native[0].receipt.task_id + ".output.arrays"
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_bindings import unpack_native
    with pytest.raises(Exception):
        unpack_native(raw, case.protocol, case.panels)


def shared_native_metadata(case):
    """Actual shared contract over disclosed metadata, without an acquisition."""
    from tests.native_completion_fixtures import publish_completion
    response, args, _ = completed_metadata(case)
    history, causal, physical_record, error = (args[name] for name in ('history', 'causal', 'physical', 'error'))
    selection = sources.identity(case.selection)
    event, = response.native
    pins = tuple(sorted((sr.identity(history), sr.identity(history.checkpoint), sr.identity(causal),
        sr.identity(error), ObjectIdentity.from_record(physical_record.forecast_id, physical_record), selection),
        key=lambda value: value.object_id))
    definition = replace(event.definition, sources=pins)
    completion = replace(event.completion, definition=definition.identity)
    receipt = publish_completion(case.plane, event.receipt, completion, visibility=Visibility.PROSPECTIVE,
        access=Access.EVALUATION_SEALED)
    response = replace(response, native=(sr.ScheduledNativeEvidence(definition, completion, receipt),))
    kwargs = dict(configuration=definition.configuration, parent_task=definition.parent_contact.task_id,
        operation=definition.operation_id, shared_sources=(), panels=case.panels, protocol=case.protocol)
    arguments = (case.source, selection, history, causal, physical_record, error)
    return response, arguments, kwargs


def test_shared_native_completion_exact_replay_preserves_actual_phase_use(case):
    response, arguments, kwargs = shared_native_metadata(case)
    original = response.canonical_bytes()
    rr.validate_response_native_evidence(response, *arguments, **kwargs)
    replayed = decode_canonical_bytes(original, type(response), maximum_bytes=None)
    rr.validate_response_native_evidence(replayed, *arguments, **kwargs)
    event, = replayed.native
    assert len(event.definition.streams) == 8 and len(event.completion.consumed_streams) == 4
    assert replayed.canonical_bytes() == original


@pytest.mark.parametrize('damage', ('stale-completion', 'zero-consumed', 'all-reserved-consumed', 'exposed-completion'))
def test_shared_native_completion_and_actual_rng_use_refuse_inconsistent_receipted_metadata(case, damage):
    from tests.native_completion_fixtures import publish_completion
    response, arguments, kwargs = shared_native_metadata(case)
    event, = response.native
    completion, receipt = event.completion, event.receipt
    with pytest.raises(ValueError, match='completion|stream consumption'):
        if damage == 'stale-completion':
            completion = replace(completion, cost=InquiryCost(D(1), None, None))
        else:
            if damage == 'zero-consumed':
                completion = replace(completion, consumed_streams=(), unconsumed_streams=event.definition.streams)
            elif damage == 'all-reserved-consumed':
                completion = replace(completion, consumed_streams=event.definition.streams, unconsumed_streams=())
            receipt = publish_completion(case.plane, receipt, completion,
                visibility=Visibility.DEVELOPMENT_ONLY if damage == 'exposed-completion' else Visibility.PROSPECTIVE,
                access=Access.DEVELOPMENT_VISIBLE if damage == 'exposed-completion' else Access.EVALUATION_SEALED)
        changed = replace(response, native=(replace(event, completion=completion, receipt=receipt),))
        rr.validate_response_native_evidence(changed, *arguments, **kwargs)


@pytest.mark.parametrize("damage", ("config", "source", "streams", "consumption", "receipt", "array-hash", "array-size", "member", "nonfinite", "native-after-nonuse"))
def test_completed_native_metadata_rejects_replay_and_thinning(case, damage):
    response, args, _ = completed_metadata(case)
    event = response.native[0]
    with pytest.raises((TypeError, ValueError)):
        if damage in ("config", "source", "streams"):
            if damage == "config":
                definition = replace(event.definition, configuration=replace(event.definition.configuration, object_fingerprint="e" * 64))
            elif damage == "source":
                definition = replace(event.definition, sources=event.definition.sources[:-1])
            else:
                definition = replace(event.definition, streams=event.definition.streams[:-1])
            event = replace(event, definition=definition, completion=replace(event.completion, definition=definition.identity))
        elif damage == "consumption":
            event = replace(event, completion=replace(event.completion, consumed_streams=(), unconsumed_streams=event.definition.streams))
        elif damage == "receipt":
            event = replace(event, receipt=replace(event.receipt, receipt_id="receipt.literal.foreign"))
        elif damage in ("array-hash", "array-size"):
            response = replace(response, arrays=replace(response.arrays, array_artifact=replace(response.arrays.array_artifact,
                **({"sha256": "e" * 64} if damage == "array-hash" else {"size_bytes": response.arrays.array_artifact.size_bytes + 1}))))
        elif damage == "member":
            response = replace(response, arrays=replace(response.arrays, members=response.arrays.members[:-1]))
        elif damage == "nonfinite":
            response = replace(response, arrays=replace(response.arrays, members=(replace(response.arrays.members[0], finite_required=False), *response.arrays.members[1:])))
        else:
            args.update(causal=case.causal, physical=case.physical, error=case.error, models=case.models, frozen=case.frozen)
        response = replace(response, native=(event,))
        response.validate_source(case.native_config, **args)
