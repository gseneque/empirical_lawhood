# SPDX-License-Identifier: MPL-2.0
"""Exposed metadata and literal equations; no fresh source or qualification.

All groups, streams and publication chronology in these fixtures are explicit
software controls. No native runner, issue, reveal or scientific fit is used.
"""

from dataclasses import fields, replace
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1FactorRule
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import ScalarClosureSpec
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.scalar_assessment import independent_scalar_closure_ratio
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_protocol as protocol_owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_source_records as source_owner
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorAction, MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as sr, response_records as rr
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit, corpus_artifact
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.test_matrix_e3_protected_inputs import build_source_inputs
from tests.test_matrix_factor_confirmation_eligibility import publish, stock as stock, provenance as provenance  # noqa: F401
from tests.test_matrix_scheduled_history import scheduled as scheduled  # noqa: F401

ROOT = Path(__file__).parents[1]


def fixture(scheduled, *, selected64=False):
    original = build_source_inputs(scheduled, selected64=selected64)
    plane, inputs = original.plane, original.inputs
    raw = (ROOT / "programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/candidate-design02.json").read_bytes()
    document = json.loads(raw)
    mathematical = decode_canonical_record(document["target"]["original_mathematical_protocol"], MatrixResponseFrontierProtocol)
    full_rule = mathematical.factor_rule_compatibilities[0].target
    definition = MatrixParameterScalarDefinition("scalar.literal.e3-source")
    scalar_pub = publish(plane, definition, "literal.e3-source.scalar")
    typed_owner = corpus_artifact(scalar_pub)
    rule_values = {field.name: getattr(full_rule, field.name) for field in fields(E1FactorRule)}
    rule_values.update(spec_id="rule.literal.e3-source.prefix", lattice=tuple(t for t in full_rule.lattice if t <= 256),
        scalar_closure=ScalarClosureSpec("scalar-rule.literal.e3-source", typed_owner, definition.threshold))
    policy = replace(inputs.native_specification.selection.prefix_policies[0], factor_rule=E1FactorRule(**rule_values))
    allocation = inputs.reservation.allocation
    corpus = (publish(plane, allocation.exposure.census, "literal.e3-source.census"),)
    audit = ScheduledExposureAudit("audit.literal.e3-source", allocation.exposure.census, (), corpus)
    audit_pub = publish(plane, audit, "literal.e3-source.audit")
    allocation = replace(allocation, exposure=replace(allocation.exposure, scheduled_audit=corpus_artifact(audit_pub)))
    reservation = replace(inputs.reservation, allocation=allocation, publication=publish(plane, allocation, "literal.e3-source.allocation"))
    selection = replace(inputs.native_specification.selection, reservation=sr.identity(reservation), prefix_policies=(policy,),
        coordinate_policies=tuple((coordinate, sr.identity(policy)) for coordinate, _ in inputs.native_specification.selection.coordinate_policies))
    native_spec = replace(inputs.native_specification, selection=selection,
        publication=publish(plane, selection, "literal.e3-source.selection"))
    manifest = source_owner.ProtectedE3NativeSourceManifest("manifest.literal.e3-source", reservation, native_spec,
        (original.provenance,), audit, audit_pub, publish(plane, reservation, "literal.e3-source.reservation"), definition, scalar_pub)
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=native_spec,
        provenances=manifest.provenances)
    descriptors = tuple(index.reference(source_id="source.literal.e3-source." + row.root.root_id,
        root_id=row.root.root_id, provenance=original.provenance.identity) for row in allocation.roots)
    sources = tuple(index.resolve(reference) for reference in descriptors)
    args = dict(specification=inputs.specification, candidate_bytes=raw, nominal=inputs.nominal, nearby=inputs.nearby,
        shifted=inputs.shifted, mathematical_protocol=mathematical, original_factor_rule=full_rule, prefix_policy=policy,
        scalar_definition=definition, normalization_source=full_rule.scalar_closure.normalization_owner,
        normalization_source_bytes=(ROOT / "src/empirical_lawhood/adapters/simulators/six_matrix_response/response_observer.py").read_bytes(),
        record_id="projection.literal.e3-source")
    projection = protocol_owner.project_protected_e3_protocol(**args)
    return SimpleNamespace(plane=plane, inputs=inputs, manifest=manifest, sources=sources, descriptors=descriptors,
        args=args, projection=projection, mathematical=mathematical)


@pytest.fixture
def case(scheduled):  # noqa: F811
    return fixture(scheduled)


def validate_population(case, **changes):
    args = dict(specification=case.inputs.specification, manifest=case.manifest,
        projections=(case.projection,), sources=case.descriptors)
    args.update(changes)
    return protocol_owner.validate_protected_e3_manifest_population(**args)


def response_fixture(case):
    raw, members = encode_matrix_arrays({"generic_basis": np.zeros((3, 4, 4), dtype="<c16"),
        "force_coefficients": np.zeros((2, 3, 3), dtype="<f8"), "trace_coefficients": np.zeros((2, 3), dtype="<f8"),
        "receiver_coefficients": np.zeros((48, 2, 2, 3, 4), dtype="<f8")})
    publication = case.plane.write(ArtifactWriteRequest("literal.e3-source.templates", "literal/templates.npz", sr.MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "literal-e3-source", "literal", raw,
        Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    protocols, panels = [], []
    for source in case.sources:
        if source.root.root.role.value == "WITHHELD_TRANSFER":
            continue
        arrays = rr.ScheduledResponseArrays("templates." + source.root_id, "TEMPLATES", sr.identity(source),
            corpus_artifact(publication), members, (sr.identity(source),), Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)
        protocol = rr.ScheduledResponseProtocol("protocol." + source.root_id, ScheduledPublicSource.from_source(source),
            case.mathematical.identity, MatrixFactorResponseModel("mechanical.literal.e3-source", rr.physical_forecast_implementation()),
            tuple(MatrixFactorAction("action.literal." + a.role.lower(), a.role, a.amplitude, a.pulse_steps, a.force_norm)
                for a in case.mathematical.action_scales), case.mathematical.horizon_steps, 48, arrays,
            D("1e-5"), D("1e-10"), D("1e-10"), D("1e-10"), D("1e-10"), D("1e-8"), D("1e-5"), D("1e-12"),
            case.mathematical.receiver_gram_tolerance, "PRESERVED_DISTINCT_PRIMARY_FINE_CUTOFF_STATES_ORIGIN_FIXED_PRIMARY_Y_FRAME")
        group = source.root.root.independent_group_id
        protocols.append(protocol)
        panels.extend((rr.ScheduledResponsePanel("panel.common." + group, group, "COMMON_NOISE_PANEL",
            "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES", source.root.streams),
            rr.ScheduledResponsePanel("panel.independent." + group, group, "INDEPENDENT_FUTURE", "FRESH_DECLARED_FUTURE_START_AT_CUTOFF",
                tuple(MatrixHistorySeed(p, sha256(("EXPOSED.SOURCE.CONTROL." + group + p).encode()).hexdigest()) for p in HISTORY_PURPOSES))))
    panels.sort(key=lambda p: (p.independent_group_id, p.panel_id))
    groups = tuple(sorted({p.independent_group_id for p in panels}))
    selection = source_owner.ProtectedE3ResponseSelection("responses.literal.e3-source", case.inputs.specification.identity,
        source_owner.identity(case.manifest), tuple((p.public_source.root.root_id, ObjectIdentity.from_record(p.protocol_id, p)) for p in protocols),
        tuple((group, tuple(ObjectIdentity.from_record(p.panel_id, p) for p in panels if p.independent_group_id == group)) for group in groups),
        (publication,), (source_owner.identity(case.projection),))
    return selection, tuple(protocols), tuple(panels)


def validate_responses(case, selection, protocols, panels, **changes):
    args = dict(specification=case.inputs.specification, manifest=case.manifest, projections=(case.projection,),
        mathematical_protocol=case.mathematical, sources=case.descriptors, protocols=protocols, panels=panels)
    args.update(changes)
    return protocol_owner.validate_protected_e3_response_selection(selection, **args)


def test_actual_original_manifest_compact_source_and_closed_roundtrips(case):
    validate_population(case)
    originals = tuple(source.reference.canonical_bytes() for source in case.sources)
    source = next(s for s in case.sources if s.root.root.role.value == "CALIBRATION")
    descriptor = source.reference
    for phase in source_owner.ProtectedE3SourcePhase:
        config = source_owner.ProtectedE3SourceConfig("config." + source_owner.source_task_id(source.root_id, phase),
            phase, case.inputs.specification.identity, source_owner.identity(case.manifest), descriptor)
        assert source_owner.bind_protected_e3_source(config, case.manifest, specification=case.inputs.specification) == source
        assert decode_canonical_bytes(config.canonical_bytes(), type(config), maximum_bytes=None) == config
        assert len(config.canonical_bytes()) < len(case.manifest.canonical_bytes()) / 4
        assert set(json.loads(descriptor.canonical_bytes())["value"]) == {
            "source_id", "root", "allocation", "reservation", "specification", "selection", "provenance"}
        document = json.loads(config.canonical_bytes())["value"]
        assert set(document) == {"record_id", "phase", "specification", "source_manifest", "source"}
        document["unexpected"] = None
        with pytest.raises(ValueError):
            decode_canonical_bytes(json.dumps({"schema": config.SCHEMA, "version": config.VERSION, "value": document}).encode(), type(config), maximum_bytes=None)
    for record in (case.manifest, case.projection):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    assert originals == tuple(source.reference.canonical_bytes() for source in case.sources)
    assert case.projection.original_normalization != case.projection.typed_normalization
    assert case.projection.original_factor_rule != case.projection.prefix_rule
    assert source_owner.prefix_native_operation_id() == "matrix-e3-protected.prefix-before-continuation.v1"


@pytest.mark.parametrize("selected,expected", ((False, 32), (True, 256)))
def test_selected320_and_alternative_complete_roles_are_derived(scheduled, selected, expected):  # noqa: F811
    case = fixture(scheduled, selected64=selected)
    validate_population(case)
    assert len(case.descriptors) == expected
    assert sum(p.expected_units for p in case.inputs.specification.populations) == (44 if not selected else 320)
    assert len({s.effective_seed for source in case.sources for s in source.root.streams}) == 4 * expected


@pytest.mark.parametrize("damage", ("missing-source", "duplicate-source", "aliased-source", "unused-provenance", "wrong-count", "foreign-spec", "withheld-config"))
def test_source_descriptor_role_provenance_and_scope_refusals(case, damage):
    with pytest.raises((TypeError, ValueError)):
        if damage == "missing-source":
            validate_population(case, sources=case.descriptors[:-1])
        elif damage == "duplicate-source":
            validate_population(case, sources=(*case.descriptors[:-1], case.descriptors[0]))
        elif damage == "aliased-source":
            source = replace(case.sources[1].reference, source_id=case.sources[0].source_id)
            validate_population(case, sources=(case.descriptors[0], source, *case.descriptors[2:]))
        elif damage == "unused-provenance":
            changed = replace(case.manifest.provenances[0], observed_git_head="b" * 40)
            manifest = replace(case.manifest, provenances=tuple(sorted((*case.manifest.provenances, changed), key=lambda p: p.fingerprint())))
            validate_population(case, manifest=manifest)
        elif damage == "wrong-count":
            spec = replace(case.inputs.specification, populations=tuple(replace(p, expected_units=p.expected_units + 1)
                if p.role == "TRANSFER_SHIFTED" else p for p in case.inputs.specification.populations))
            validate_population(case, specification=spec)
        elif damage == "foreign-spec":
            config = source_owner.ProtectedE3SourceConfig("config." + source_owner.source_task_id(case.descriptors[0].root_id,
                source_owner.ProtectedE3SourcePhase.PREFIX), source_owner.ProtectedE3SourcePhase.PREFIX,
                replace(case.inputs.specification, specification_id="specification.foreign").identity,
                source_owner.identity(case.manifest), case.descriptors[0])
            source_owner.bind_protected_e3_source(config, case.manifest, specification=case.inputs.specification)
        else:
            descriptor = next(s for s in case.descriptors if s.root.root.role.value == "WITHHELD_TRANSFER")
            source_owner.ProtectedE3SourceConfig("config." + source_owner.source_task_id(descriptor.root_id,
                source_owner.ProtectedE3SourcePhase.PREFIX), source_owner.ProtectedE3SourcePhase.PREFIX,
                case.inputs.specification.identity, source_owner.identity(case.manifest), descriptor)


@pytest.mark.parametrize("field,value", (("risk_start_tick", 0), ("trailing_persistence_ticks", 0),
    ("associative_leakage_maximum", D("0.06")), ("origin_angle_maximum_degrees", D(31)),
    ("identifiability_relative_gap", D("1e-9")), ("frame_alignment_minimum_overlap", D("0.6"))))
def test_prefix_projection_preserves_actual_admission_and_tracking(case, field, value):
    changed = replace(case.args["prefix_policy"], factor_rule=replace(case.args["prefix_policy"].factor_rule, **{field: value}))
    with pytest.raises(ValueError, match="admission/tracking"):
        protocol_owner.project_protected_e3_protocol(**{**case.args, "prefix_policy": changed})


@pytest.mark.parametrize("damage", ("candidate-bytes", "candidate-action", "candidate-physical-key", "coordinate", "raw-source", "scalar-owner", "full-rule"))
def test_candidate_source_coordinate_and_distinct_scalar_owner_refusals(case, damage):
    args = dict(case.args)
    if damage == "candidate-bytes":
        args["candidate_bytes"] += b" "
    elif damage == "candidate-action":
        document = json.loads(args["candidate_bytes"])
        document["target"]["original_mathematical_protocol"]["value"]["action_scales"][0]["value"]["force_norm"] = {"decimal": "2"}
        args["candidate_bytes"] = json.dumps(document).encode()
        args["specification"] = replace(args["specification"], protocol_sha256=sha256(args["candidate_bytes"]).hexdigest())
    elif damage == "candidate-physical-key":
        document = json.loads(args["candidate_bytes"])
        document["population"]["nominal_coordinate"]["full_physical_key"][0] = "7"
        args["candidate_bytes"] = json.dumps(document).encode()
        args["specification"] = replace(args["specification"], protocol_sha256=sha256(args["candidate_bytes"]).hexdigest())
    elif damage == "coordinate":
        args["nominal"] = replace(args["nominal"], coordinate_id="coordinate.changed")
    elif damage == "raw-source":
        args["normalization_source_bytes"] += b"\n"
    elif damage == "scalar-owner":
        rule = args["prefix_policy"].factor_rule
        scalar = replace(rule.scalar_closure, normalization_owner=replace(rule.scalar_closure.normalization_owner, sha256="f" * 64))
        args["prefix_policy"] = replace(args["prefix_policy"], factor_rule=replace(rule, scalar_closure=scalar))
    else:
        args["original_factor_rule"] = replace(args["original_factor_rule"], spec_id="rule.foreign")
    with pytest.raises(ValueError):
        protocol_owner.project_protected_e3_protocol(**args)


def test_response_references_join_actual_sources_and_every_declared_member(case):
    selection, protocols, panels = response_fixture(case)
    validate_responses(case, selection, protocols, panels)
    assert len(protocols) == 28 and len(panels) == 56
    assert decode_canonical_bytes(selection.canonical_bytes(), type(selection), maximum_bytes=None) == selection
    assert "streams" not in json.loads(selection.canonical_bytes())["value"]
    assert not hasattr(selection, "allocation") and not hasattr(selection, "protocols")


@pytest.mark.parametrize("damage", ("protocol", "panel"))
def test_response_member_ids_cannot_alias_across_roots_or_groups(case, damage):
    selection, _, _ = response_fixture(case)
    with pytest.raises(ValueError, match="aliases"):
        if damage == "protocol":
            first, second = selection.root_protocols[:2]
            changed = (second[0], replace(second[1], object_id=first[1].object_id))
            replace(selection, root_protocols=(first, changed, *selection.root_protocols[2:]))
        else:
            first, second = selection.group_panels[:2]
            changed = (second[0], (replace(second[1][0], object_id=first[1][0].object_id), second[1][1]))
            replace(selection, group_panels=(first, changed, *selection.group_panels[2:]))


@pytest.mark.parametrize("damage", ("missing-protocol", "extra-panel", "foreign-public-source", "reserved-future-stream", "common-stream", "changed-actuator", "extra-template"))
def test_response_census_source_stream_and_actuator_adversaries(case, damage):
    selection, protocols, panels = response_fixture(case)
    if damage == "missing-protocol":
        protocols = protocols[:-1]
    elif damage == "extra-panel":
        panels = (*panels, panels[0])
    elif damage == "foreign-public-source":
        public = replace(protocols[0].public_source, source=replace(protocols[0].public_source.source, object_id="source.foreign"))
        arrays = replace(protocols[0].templates, source=public.source, producers=(public.source,))
        protocols = (replace(protocols[0], public_source=public, templates=arrays), *protocols[1:])
        selection = replace(selection, root_protocols=tuple((p.public_source.root.root_id, ObjectIdentity.from_record(p.protocol_id, p)) for p in protocols))
    elif damage in ("reserved-future-stream", "common-stream"):
        index = next(i for i, p in enumerate(panels) if p.role == ("INDEPENDENT_FUTURE" if damage == "reserved-future-stream" else "COMMON_NOISE_PANEL"))
        replacement = case.sources[-1].root.streams
        panels = tuple(replace(p, streams=replacement) if i == index else p for i, p in enumerate(panels))
        selection = replace(selection, group_panels=tuple((group, tuple(ObjectIdentity.from_record(p.panel_id, p) for p in panels if p.independent_group_id == group))
            for group, _ in selection.group_panels))
    elif damage == "changed-actuator":
        protocols = (replace(protocols[0], actions=tuple(replace(a, force_norm=D(2)) for a in protocols[0].actions)), *protocols[1:])
        selection = replace(selection, root_protocols=tuple((p.public_source.root.root_id, ObjectIdentity.from_record(p.protocol_id, p)) for p in protocols))
    else:
        publication = publish(case.plane, case.manifest.scalar_definition, "zz.literal.unselected-template")
        selection = replace(selection, template_publications=(*selection.template_publications, publication))
    with pytest.raises((TypeError, ValueError)):
        validate_responses(case, selection, protocols, panels)


def test_scalar_projection_has_independent_literal_q2_residual_and_tiny_fallback(case):
    fields = np.zeros((3, 4, 4), dtype="<c16")
    fields[0] = np.diag([1, -1, 2, -2])
    fields[1, 0, 1] = fields[1, 1, 0] = 1
    fields[2, 2, 3], fields[2, 3, 2] = 1j, -1j
    for alpha in (0.75, 3.0):
        residuals = []
        for a, b, c in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
            residuals.append(float(np.linalg.norm(fields[b] @ fields[c] - fields[c] @ fields[b]
                - 1j * (2.0 * (alpha / 2.0) / 3.0) * fields[a])))
        radius = float(np.trace(sum(value @ value for value in fields)).real / 4)
        denominator = max(abs(alpha / 3) * np.sqrt(4 * max(radius, 0) / 3), np.finfo(float).tiny)
        assert independent_scalar_closure_ratio(fields, alpha) == D(str(float(max(residuals) / denominator)))
    assert independent_scalar_closure_ratio(np.zeros_like(fields), 0.0) == 0
    assert case.projection.meaning == protocol_owner.PROJECTION_MEANING
    assert not hasattr(case.projection, "qualified") and not hasattr(case.projection, "equivalent")
