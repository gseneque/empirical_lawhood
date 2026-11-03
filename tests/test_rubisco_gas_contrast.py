# SPDX-License-Identifier: MPL-2.0
"""Independent gas-contrast arithmetic and authentic public contribution custody."""

from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_assay_bridge import (
    KineticAssayBridgeResult, assess_joint_kinetic_target, execute_kinetic_assay_bridge,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.gas_contrast import (
    BUDGET, CAPABILITY, MEDIA, GasContrastAssessment, GasContrastConfig, GasContrastRunner,
    assess_gas_contrast, operation_declaration,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.gas_contrast_translation import (
    gas_contrast_draft, gas_contrast_input_origins,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.operation_bindings import design, scope
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.recursive_translation import kinetic_join_draft
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_supply import JointKineticSupply, KineticTargetComparison
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A, ContributionRole
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt, ExternalRootContract
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRegistry
from empirical_lawhood.runtime.execution import (
    TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort,
)
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "programmes/biology/photosynthesis/workflows/rubisco-kinetic-join"


def _inputs():
    return tuple(decode_canonical_bytes((EXAMPLE / filename).read_bytes(), record_type, maximum_bytes=None)
        for filename, record_type in (("supply.json", JointKineticSupply), ("query.json", AssayQuery),
            ("comparison.json", KineticTargetComparison)))


def _synthetic_parent(bridge, target, side):
    """Pure arithmetic fixtures have explicit synthetic receipt references."""
    assessment = assess_joint_kinetic_target(bridge.supply, target, assessment_id="assessment.fixture." + side,
        assay_bridge=bridge)
    product = ContributionProduct("product.fixture." + side,
        ObjectIdentity.from_record(bridge.result_id, bridge),
        ArtifactIdentity("artifact.fixture." + side, "exposed-bridge", bridge.SCHEMA, bridge.fingerprint(),
            MEDIA, len(bridge.canonical_bytes())),
        ObjectIdentity("receipt.fixture." + side, CanonicalTaskReceipt.SCHEMA, "1.0.0", sha256(side.encode()).hexdigest()),
        ContributionRole.INSTANCE_PRODUCT, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    science = design(bridge.supply, bridge.query, target, design_id="design.fixture." + side,
        relative_tolerance=bridge.numerical_relative_tolerance)
    return ContributionManifest("contribution.fixture." + side, "Pure exposed arithmetic fixture",
        "Synthetic references supply no authenticated custody or qualification.", scope(science), (product,),
        (ObjectIdentity.from_record(assessment.assessment_id, assessment),), ())


def _pair(tolerance=Decimal("1e-10")):
    source, query, target = _inputs()
    left = execute_kinetic_assay_bridge(source, query, result_id="rubisco-kinetic-join.assay.result", relative_tolerance=tolerance)
    right = execute_kinetic_assay_bridge(source, replace(query, co2_um=query.co2_um * 2),
        result_id="rubisco-kinetic-join.assay.result", relative_tolerance=tolerance)
    parents = tuple(_synthetic_parent(bridge, target, side) for bridge, side in ((left, "left"), (right, "right")))
    draft = gas_contrast_draft(left, right, *parents)
    config = decode_canonical_bytes(draft.operations[0].config_payload.encode(), GasContrastConfig, maximum_bytes=None)
    return config, left, right, parents, draft


def _worker(config, left, right, *, left_artifact_id=None):
    readers, ports = [], []
    values = ((config.config_id, config), (left_artifact_id or config.left_product.artifact.artifact_id, left),
        (config.right_product.artifact.artifact_id, right))
    for artifact_id, record in sorted(values):
        raw = record.canonical_bytes()
        reader = BytesIO(raw)
        readers.append(reader)
        binding = WorkerInputBinding(artifact_id, "material." + artifact_id, record.SCHEMA, MEDIA, len(raw),
            VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE, WorkerInputKind.EXTERNAL)
        ports.append(WorkerInputPort(binding, reader))
    runner = GasContrastRunner()
    ref = CapabilityConfigRef(config.config_id, config.SCHEMA, sha256(config.SCHEMA.encode()).hexdigest(),
        config.fingerprint(), config.config_id)
    context = TaskContext("run.exposed-gas-contrast", CAPABILITY, CAPABILITY + ".attempt-001", ref,
        tuple(port.binding for port in ports), tuple(ports),
        (WorkerOutputPort(CAPABILITY + ".assessment", GasContrastAssessment.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA),),
        runner.manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE, BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, ())
    return runner, context, readers


def test_fraction_falsifier_reproduces_complete_pair_and_adverse_denominator():
    config, left, right, _parents, draft = _pair()
    result = assess_gas_contrast(config, left, right)
    assert len(result.members) == len(left.supply.members) == 3
    assert result.disposition is A.UNEVALUABLE
    assert result.fresh_biological_units == 0 and result.biological_predictive_calibration == "NOT_ESTABLISHED"
    assert gas_contrast_input_origins(draft).inputs[0].producing_receipt == config.left_product.producing_receipt
    supplied = next(member for member in left.supply.members if member.constants is not None)
    constants = supplied.constants
    # This literal rational derivation does not call the method's flux function.
    first_denominator = Fraction(1) + Fraction(left.query.co2_um) / Fraction(constants.kc_um) + Fraction(left.query.o2_um) / Fraction(constants.ko_um)
    second_denominator = Fraction(1) + Fraction(right.query.co2_um) / Fraction(constants.kc_um) + Fraction(right.query.o2_um) / Fraction(constants.ko_um)
    expected_carbon = (Fraction(constants.kcat_c_s_inv) * Fraction(right.query.co2_um) / Fraction(constants.kc_um) / second_denominator
        - Fraction(constants.kcat_c_s_inv) * Fraction(left.query.co2_um) / Fraction(constants.kc_um) / first_denominator)
    expected_oxygen = (Fraction(constants.kcat_o_s_inv) * Fraction(right.query.o2_um) / Fraction(constants.ko_um) / second_denominator
        - Fraction(constants.kcat_o_s_inv) * Fraction(left.query.o2_um) / Fraction(constants.ko_um) / first_denominator)
    row = next(row for row in result.members if row.member_id == supplied.member_id)
    assert tuple(Fraction(*value) for value in row.expected_difference) == (expected_carbon, expected_oxygen)
    assert row.disposition is A.SATISFIED
    assert sum(row.observed_difference is None for row in result.members) == 2


def test_independent_disposition_cannot_hide_failed_assay_members():
    config, left, right, *_ = _pair(Decimal("1e-30"))
    result = assess_gas_contrast(config, left, right)
    assert result.disposition is A.FALSIFIED
    assert len(result.members) == 3
    assert any(row.disposition is A.UNEVALUABLE for row in result.members)


def _compile_contrast(draft):
    declaration = operation_declaration()
    return compile_recursive_wave(draft=draft, registrations=(declaration.registration(),),
        registry=CapabilityRegistry("registry.exposed-gas-contrast", (declaration.manifest(),)),
        implementation_commit="a" * 40, output_codecs=declaration.record_codecs)


@pytest.mark.parametrize("omitted_kind", ["product", "receipt"])
def test_scientific_root_binds_both_actual_products_and_producing_receipts(omitted_kind):
    config, _left, _right, _parents, draft = _pair()
    assert len(_compile_contrast(draft).execution_plan.tasks) == 1
    operands = draft.development_study.scientific_operands
    assert config.left_product.record.object_id == config.right_product.record.object_id
    for product in (config.left_product, config.right_product):
        assert ObjectIdentity(product.artifact.artifact_id, product.record.object_schema,
            product.record.object_version, product.record.object_fingerprint) in operands
        assert product.producing_receipt in operands
    omitted = (config.left_product.artifact.artifact_id if omitted_kind == "product"
        else config.left_product.producing_receipt.object_id)
    changed_root = replace(draft.development_study,
        scientific_operands=tuple(row for row in operands if row.object_id != omitted))
    with pytest.raises(ValueError, match="scientific operands differ"):
        _compile_contrast(replace(draft, development_study=changed_root))


@pytest.mark.parametrize("change", ["material", "query", "parent-scope", "same-product"])
def test_paired_source_query_and_parent_substitutions_refuse(change):
    config, left, right, parents, _draft = _pair()
    with pytest.raises(ValueError):
        if change == "material":
            assess_gas_contrast(config, replace(left, supply=replace(left.supply, supply_id="supply.substituted")), right)
        elif change == "query":
            assess_gas_contrast(config, left, replace(right, query=left.query))
        elif change == "parent-scope":
            parent = replace(parents[0], scope=replace(parents[0].scope, system_id="material.substituted"))
            gas_contrast_draft(left, right, parent, parents[1])
        else:
            replace(config, right_product=config.left_product)


def test_changed_rational_result_refuses_independent_recomputation():
    config, left, right, *_ = _pair()
    result = assess_gas_contrast(config, left, right)
    row = next(row for row in result.members if row.expected_difference is not None)
    wrong = replace(row, expected_difference=((1, 1), row.expected_difference[1]))
    with pytest.raises(ValueError, match="independent arithmetic"):
        replace(result, members=tuple(wrong if value is row else value for value in result.members))


def test_worker_preserves_pair_and_refuses_wrong_producing_artifact():
    config, left, right, *_ = _pair()
    runner, context, readers = _worker(config, left, right)
    result = runner.execute(context)
    assessed = decode_canonical_bytes(result.outputs[0].payload, GasContrastAssessment, maximum_bytes=None)
    assert len(assessed.members) == 3 and all(reader.closed for reader in readers)
    runner, context, readers = _worker(config, left, right, left_artifact_id="artifact.substituted")
    with pytest.raises(ValueError, match="artifact ownership"):
        runner.execute(context)
    assert all(reader.closed for reader in readers)


def _real_plane(path):
    path.mkdir()
    resolved = path.resolve()
    mounted = next(value for value in (resolved, *resolved.parents) if value.is_mount())
    contract = ExternalRootContract("rubisco-gas-contrast-exposed-development", "Declared local software-conformance custody",
        str(resolved), str(mounted), "empirical-lawhood/testing/rubisco-gas-contrast", 1)
    # The actual inspector establishes mount identity, free bytes and write access.
    plane = ExternalArtifactPlane(GuardedExternalRoot(contract))
    assert plane.root.diagnostic().write_ready
    return plane


def _publish_parent(plane, selected_root, side, source, query, target):
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave
    from empirical_lawhood.api.recursive_contributions import export_recursive_contribution
    from empirical_lawhood.api.recursive_execution import read_recursive_wave, run_recursive_wave

    inputs = selected_root / (side + "-inputs")
    inputs.mkdir()
    bindings = []
    for name, record in (("supply", source), ("query", query), ("comparison", target)):
        path = inputs / (name + ".json")
        path.write_bytes(record.canonical_bytes())
        bindings.append(("external.rubisco-kinetic-join." + name, path))
    wave = selected_root / (side + "-wave")
    draft = kinetic_join_draft(source, query, target, relative_tolerance=Decimal("1e-10"),
        draft_id="draft.rubisco.gas-contrast-parent." + side)
    author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane, output_dir=wave, input_bindings=bindings)
    report = run_recursive_wave(directory=wave, project_root=ROOT, artifact_writer=plane)
    assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0
    _, products, _, _ = read_recursive_wave(directory=wave, artifact_writer=plane, include_products=True)
    bridge = next(row for row in products["records"]["rubisco-kinetic-join.assay"].values()
        if type(row) is KineticAssayBridgeResult)
    exported = selected_root / (side + "-contribution")
    export_recursive_contribution(directory=wave, output_dir=exported, project_root=ROOT, artifact_writer=plane)
    parent = decode_canonical_bytes((exported / "contribution.json").read_bytes(), ContributionManifest, maximum_bytes=None)
    return bridge, parent, exported


def test_public_contributor_method_uses_actual_source_receipts_workers_and_recovery(tmp_path, monkeypatch):
    """No source, provenance, catalogue or storage observations are mocked."""
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding
    from empirical_lawhood.api.recursive_execution import read_recursive_wave, run_recursive_wave

    selected_root = tmp_path / "actual-selected-custody"
    plane = _real_plane(selected_root)
    source_binding = implementation_binding(ROOT)
    source, query, target = _inputs()
    left, left_parent, left_dir = _publish_parent(plane, selected_root, "left", source, query, target)
    right, right_parent, right_dir = _publish_parent(plane, selected_root, "right", source,
        replace(query, co2_um=query.co2_um * 2), target)
    draft = gas_contrast_draft(left, right, left_parent, right_parent)
    wave = selected_root / "contrast-wave"
    authored = author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane, output_dir=wave,
        contribution_dirs=(left_dir, right_dir), origins=gas_contrast_input_origins(draft))
    assert authored["task_count"] == 1 and authored["native_contact"] == "none"
    report = run_recursive_wave(directory=wave, project_root=ROOT, artifact_writer=plane)
    assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0
    assert report["producing_code_sha256"] == source_binding.code_sources_sha256
    _, products, _, _ = read_recursive_wave(directory=wave, artifact_writer=plane, include_products=True)
    result = next(row for row in products["records"][CAPABILITY].values() if type(row) is GasContrastAssessment)
    assert result.left == left and result.right == right
    assert len(result.members) == 3 and result.disposition is A.UNEVALUABLE
    assert len(products["receipts"]) == 1

    def forbidden(*args, **kwargs):
        raise AssertionError("completed contributor method reacquired scientific work")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    assert read_recursive_wave(directory=wave, artifact_writer=plane) == report
    assert run_recursive_wave(directory=wave, project_root=ROOT, artifact_writer=plane) == report
