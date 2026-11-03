# SPDX-License-Identifier: MPL-2.0
"""Original RC/thermal authority, ports and callback contracts after consolidation."""

import pytest

from empirical_lawhood.adapters.methods.battery_thermal_inquiry import (
    operation_bindings as thermal, recursive_translation as inquiry,
)
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquirySource, BatteryInquirySupply, BatteryInquiryInstance,
)
from empirical_lawhood.adapters.methods.rc_prerequisite_chain import (
    operation_bindings as rc, operation_contracts as records, operations,
)
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.contracts import RCChainSummary, RCChainUnitResult
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage


# Exact implementation digests from the preserved 4abe82a3 handwritten owners.
# Permissions, ports and native callbacks are pinned separately below.
EXPECTED_IMPLEMENTATIONS = {
    'rc-prerequisite-chain.phases.source': '2bb858eb782b5573d1ccb9920d5e9cb8482479af793f93637789d6fe0136b0ca',
    'rc-prerequisite-chain.phases.observations': '948bc6f5277a60ccac079d80447f807aedd6c88345786b97bb495f04ebc39bb9',
    'rc-prerequisite-chain.phases.admit': 'c20c208f05570151a161d2753809df8f0f57e8f10b715144e30ce445bb607b8c',
    'rc-prerequisite-chain.phases.commit': 'fb47d0a284533d18726ec92a31be62b053251c6a3ebb46cb61b046cd3240ec3d',
    'rc-prerequisite-chain.phases.deliver': '2a293ab21a93f8893343848b92d4231076ca5586dcaa26bcebf6d66956d38b6d',
    'rc-prerequisite-chain.phases.measure': 'a338c6b7e3a45a58f99124749f10e51c21059d4adcb8786bc132997aab316cd4',
    'rc-prerequisite-chain.phases.support': '9a3d5c34bf7f53f166e4687d4b89fb9072dd2a9c2be5c63554c1c1360eed2ecc',
    'rc-prerequisite-chain.phases.joined': 'ad140fdf6524b872804a2b5b61688c373f52b0750e2b313f28aa273feb307fa3',
    'rc-prerequisite-chain.phases.reduce': '6b61ee55b6ccfb84c68ba766b6c7da5788f355b29b2ffedcea6bcd6ba1b7c083',
    'rc-prerequisite-chain.phases.summary': '51c3abd226dbce3dd8a250f207cdd23688e132880b6fd8b514e5b16a3f514f55',
    'battery-thermal-inquiry.reuse': 'fb7bd4fecd3b73790875478b78e3ead1b2a3c13da2f44db4cc152e853144d869',
    'battery-thermal-inquiry.supply': 'c2c34bce21e706a05c97b12ef69ab5c6a337eca70311d3098d4c5fcc864b1937',
    'battery-thermal-inquiry.use': '6c00bcfa78b84effc3a2d4eb263d2a5dd97760b283c32f698453c1119205889e',
}


def by_role(owner):
    rows = owner.operation_declarations()
    result = {row.capability_key.rsplit('.', 1)[-1]: row for row in rows}
    assert len(result) == len(rows)
    return result


@pytest.mark.parametrize('owner,count,version', ((rc, 10, '1.0.0'), (thermal, 3, '1.1.0')))
def test_original_rosters_versions_and_implementation_digests(owner, count, version):
    rows = by_role(owner)
    expected = {key: value for key, value in EXPECTED_IMPLEMENTATIONS.items() if key.startswith(owner.NAMESPACE + '.')}
    assert len(rows) == count
    assert {row.capability_key: row.manifest().implementation_sha256 for row in rows.values()} == expected
    assert all(row.capability_version == version for row in rows.values())


# Port order is canonical. Function argument order is independently fixed here:
# using sorted ports as call arguments would change the RC scientific operation.
RC_PHASES = (
    ('source', records.RCSourceOperationConfig, (), (),
        (('evidence', records.RCSourceEvidence), ('observer', records.RCObserverExport)),
        operations.acquire_source, ScientificStage.ACQUIRE),
    ('observations', records.RCObservationOperationConfig, (('observer', records.RCObserverExport),),
        (records.RCObserverExport,), (('reports', records.RCObservationSet),),
        operations.construct_observations, ScientificStage.TRANSFORM),
    ('admit', records.RCAdmissionOperationConfig, (('reports', records.RCObservationSet),),
        (records.RCObservationSet,), (('admissions', records.RCAdmissionSet),),
        operations.admit_observations, ScientificStage.ADMISSION),
    ('commit', records.RCCommitmentOperationConfig,
        (('admissions', records.RCAdmissionSet), ('reports', records.RCObservationSet)),
        (records.RCObservationSet, records.RCAdmissionSet), (('commitments', records.RCCommitmentSet),),
        operations.commit_preparations, ScientificStage.FREEZE),
    ('deliver', records.RCDeliveryOperationConfig, (('commitments', records.RCCommitmentSet),),
        (records.RCCommitmentSet,), (('native', records.RCNativeDeliverySet),),
        operations.deliver_phases, ScientificStage.PREPARE),
    ('measure', records.RCMeasurementOperationConfig,
        (('commitments', records.RCCommitmentSet), ('reports', records.RCObservationSet), ('source', records.RCSourceEvidence)),
        (records.RCSourceEvidence, records.RCObservationSet, records.RCCommitmentSet),
        (('measurements', records.RCMeasurementAssessmentSet),), operations.assess_measurement, ScientificStage.FALSIFY),
    ('support', records.RCSupportOperationConfig,
        (('commitments', records.RCCommitmentSet), ('measurements', records.RCMeasurementAssessmentSet), ('native', records.RCNativeDeliverySet)),
        (records.RCMeasurementAssessmentSet, records.RCCommitmentSet, records.RCNativeDeliverySet),
        (('support', records.RCSupportAssessmentSet),), operations.assess_support, ScientificStage.FALSIFY),
    ('joined', records.RCJoinedOperationConfig,
        (('commitments', records.RCCommitmentSet), ('measurements', records.RCMeasurementAssessmentSet),
         ('native', records.RCNativeDeliverySet), ('support', records.RCSupportAssessmentSet)),
        (records.RCMeasurementAssessmentSet, records.RCCommitmentSet, records.RCNativeDeliverySet, records.RCSupportAssessmentSet),
        (('joined', records.RCJoinedAssessmentSet),), operations.assess_joined, ScientificStage.FALSIFY),
    ('reduce', records.RCUnitReductionConfig,
        (('commitments', records.RCCommitmentSet), ('joined', records.RCJoinedAssessmentSet),
         ('measurements', records.RCMeasurementAssessmentSet), ('reports', records.RCObservationSet),
         ('source', records.RCSourceEvidence), ('support', records.RCSupportAssessmentSet)),
        (records.RCSourceEvidence, records.RCObservationSet, records.RCCommitmentSet,
         records.RCMeasurementAssessmentSet, records.RCSupportAssessmentSet, records.RCJoinedAssessmentSet),
        (('unit', RCChainUnitResult),), operations.reduce_unit, ScientificStage.REPORT),
    ('summary', records.RCSummaryOperationConfig, (('units', RCChainUnitResult),), (RCChainUnitResult,),
        (('summary', RCChainSummary),), operations.summarize_units, ScientificStage.REPORT),
)


@pytest.mark.parametrize('role,config,ports,arguments,products,operation,stage', RC_PHASES)
def test_rc_exact_port_census_argument_order_assessors_and_native_preparation(
        role, config, ports, arguments, products, operation, stage):
    row = by_role(rc)[role]
    assert row.config_record_type is config
    assert row.stage is stage
    assert tuple((port.port_id, port.payload_schema, port.media_type, port.maximum_size_bytes,
        port.minimum_count, port.maximum_count) for port in row.input_ports) == tuple(
        (name, record.SCHEMA, 'application/json', 16 * 1024**2, 1, 32 if role == 'summary' else 1)
        for name, record in ports)
    assert tuple((out.output_id, out.payload_schema, out.profile, out.media_type, out.filename_suffix) for out in row.outputs) == tuple(
        (name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json') for name, record in products)
    native = role in ('source', 'deliver')
    assert row.kind is {
        'source': CapabilityKind.SIMULATOR, 'observations': CapabilityKind.OBSERVATION_OPERATOR,
        'admit': CapabilityKind.ADMISSION_EVALUATOR, 'commit': CapabilityKind.TRANSFORM,
        'deliver': CapabilityKind.NATIVE_DELIVERY, 'measure': CapabilityKind.FALSIFIER,
        'support': CapabilityKind.FALSIFIER, 'joined': CapabilityKind.FALSIFIER,
        'reduce': CapabilityKind.REPORTER, 'summary': CapabilityKind.REPORTER,
    }[role]
    assert row.execution_properties.native_effect is native
    assert row.execution_properties.complete_unit_census is native
    assert row.execution_properties.native_work_preparer is (rc.prepare_native_work if native else None)
    assert row.execution_properties.barrier is (BarrierKind.FREEZE if role == 'commit' else BarrierKind.NONE)
    assert row.scientific_hooks.assessment_projector is (rc.assessment_projector if role in ('measure', 'support', 'joined') else None)
    assert row.scientific_hooks.native_effect_slot_ids is (rc.native_effect_slot_ids if native else None)
    runner = row.runner_factory()
    assert type(runner) is operations.RCPhaseRunner
    assert runner.manifest == row.manifest()
    assert runner.config_type is config and runner.operation is operation
    assert runner.input_types == arguments
    assert runner.output_types == tuple(record for _, record in products)


@pytest.mark.parametrize('role,ports,product', (
    ('reuse', (('instance', BatteryInquiryInstance), ('supplier', thermal.BatteryInquiryAssessedInstance)), thermal.BatteryInquiryAssessedInstance),
    ('supply', (('source', BatteryInquirySource),), BatteryInquirySupply),
    ('use', (('instance', BatteryInquiryInstance), ('supplier', BatteryInquirySupply)), thermal.BatteryInquiryAssessedInstance),
))
def test_thermal_exact_inputs_native_census_and_current_phase_runner(role, ports, product):
    row = by_role(thermal)[role]
    assert row.config_record_type is thermal.BatteryInquiryOperationConfig
    assert row.stage is ScientificStage.ACQUIRE
    assert tuple((port.port_id, port.payload_schema, port.media_type, port.maximum_size_bytes,
        port.minimum_count, port.maximum_count) for port in row.input_ports) == tuple(
        (name, record.SCHEMA, 'application/json', None, 1, 1) for name, record in ports)
    assert tuple((out.output_id, out.payload_schema, out.profile, out.media_type, out.filename_suffix) for out in row.outputs) == (
        ('native-census', thermal.BatteryInquiryNativeCensus.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),
        ('product', product.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'))
    assert row.execution_properties.native_effect is True
    assert row.kind is CapabilityKind.SIMULATOR
    assert row.execution_properties.native_work_preparer is None
    assert row.execution_properties.complete_unit_census is True
    assert row.execution_properties.barrier is BarrierKind.NONE
    assert row.scientific_hooks.native_effect_slot_ids is thermal.native_effect_slot_ids
    assert row.scientific_hooks.assessment_projector is (None if role == 'supply' else thermal.project_battery_assessments)
    runner = row.runner_factory()
    assert type(runner) is thermal.BatteryInquiryRunner
    assert runner.role == role and runner.manifest == row.manifest()


@pytest.mark.parametrize('owner,budget', (
    (rc, ResourceBudget(1, 1024**3, 0, 600, 16 * 1024**2, 16 * 1024**2)),
    (thermal, ResourceBudget(1, None, 0, None, None, None)),
))
def test_exact_original_nonpromotable_development_authority_and_budget(owner, budget):
    permissions = tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT)))
    for row in owner.operation_declarations():
        registration, manifest = row.registration(), row.manifest()
        assert row.permissions == manifest.permissions == registration.required_permissions == permissions
        assert row.resources == manifest.resource_ceiling == registration.resource_ceiling == budget
        assert row.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
        assert row.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
        assert row.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
        assert row.conformance_check_ids == (('complete-phase-ports', 'truth-isolated-policy') if owner is rc else (
            'complete-native-subsolve-and-transition-census', 'independent-source-bound-assessment', 'nonpromotable-numerical-family'))
        assert row.scientific_hooks.scientific_operand_sha256s is owner.scientific_operand_sha256s
        assert row.scientific_hooks.scientific_unit_ids is owner.scientific_unit_ids
        assert row.scientific_hooks.scientific_root_validator is owner.scientific_root_validator


@pytest.mark.parametrize('owner', (rc, thermal))
def test_declaration_construction_and_projections_never_construct_or_execute_runners(owner, monkeypatch):
    def refused(*args, **kwargs):
        pytest.fail('metadata projection entered a scientific runner or validator')

    if owner is rc:
        monkeypatch.setattr(operations, 'RCPhaseRunner', refused)
    else:
        monkeypatch.setattr(thermal, 'BatteryInquiryRunner', refused)
        monkeypatch.setattr(thermal.science, 'supply', refused)
        monkeypatch.setattr(thermal.science, 'assess', refused)
    monkeypatch.setattr(owner, 'scientific_root_validator', refused)
    for row in owner.operation_declarations():
        factory = row.provider_factory()
        assert factory.manifest == row.manifest()
        assert factory.registration == row.registration()
        assert callable(factory.runner_factory)


@pytest.mark.parametrize('family', ('rc', 'thermal'))
def test_actual_discovery_and_executable_descriptors_share_the_authoritative_roster(family):
    if family == 'rc':
        from empirical_lawhood.adapters.methods.rc_prerequisite_chain import extension_bundle as cold, executable_binding as live
    else:
        from empirical_lawhood.adapters.methods.battery_thermal_inquiry import extension_bundle as cold, executable_binding as live
    declarations = {row.capability_key: row for row in cold.OPERATION_DECLARATIONS}
    factories = {row.manifest.capability_key: row for row in live.EXECUTABLE_BINDING_FACTORIES}
    assert set(declarations) == set(factories)
    assert tuple(sorted((row.manifest() for row in declarations.values()), key=lambda row: row.registry_id)) == cold.EXTENSION_BUNDLE_CONTRIBUTION.capability_manifests
    assert tuple(row.binding for row in live.EXECUTABLE_BINDING_FACTORIES) == live.EXECUTABLE_BINDING_CONTRIBUTION.bindings
    for key, row in declarations.items():
        assert factories[key].manifest == row.manifest()
        assert factories[key].registration == row.registration()
        assert factories[key].output_codecs == row.record_codecs


def test_thermal_all_six_inquiry_hooks_remain_the_current_owning_callbacks():
    expected = {
        'contribution_describer': inquiry.describe_contributions,
        'next_wave_builder': inquiry.next_wave_builder,
        'inquiry_outcome_projector': inquiry.inquiry_outcome_projector,
        'inquiry_evidence_projector': inquiry.inquiry_evidence_projector,
        'inquiry_endpoint_validator': inquiry.inquiry_endpoint_validator,
        'inquiry_record_identity': thermal.inquiry_record_identity,
    }
    for row in thermal.operation_declarations():
        factory = row.provider_factory()
        for name, callback in expected.items():
            assert getattr(row.inquiry_hooks, name) is callback
            assert getattr(factory, name) is callback


def test_thermal_identity_preserves_native_census_and_scientific_record_branches():
    # Pure current source/nonentry metadata; no acquired trace or authority.
    source = BatteryInquirySource()
    source_pin = thermal.science.identity(source)
    census = thermal.BatteryInquiryNativeCensus('native-census.battery-thermal-inquiry.use', source_pin, 'use', (), 0, 0)
    assert thermal.inquiry_record_identity(census) == ObjectIdentity.from_record(census.census_id, census)
    assert thermal.inquiry_record_identity(source) == source_pin
