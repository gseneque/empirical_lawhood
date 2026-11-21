# SPDX-License-Identifier: MPL-2.0
"""Disclosed, unpublished receipt fixtures for software revision conformance only.

These invented receipt controls are not original-result acceptance or scientific
qualification. The separate installed exercise reads actual retained custody.
"""

from dataclasses import replace
from decimal import Decimal

from empirical_lawhood.methods.mass_balance_starter import design as original_design, science as original_science
from empirical_lawhood.methods.mass_balance_starter.bindings import operation_declarations as original_operations
from empirical_lawhood.methods.mass_balance_starter.examples import example_evidence
from empirical_lawhood.methods.mass_balance_starter.records import MassSpecification
from empirical_lawhood.methods.mass_balance_revision import design, science
from empirical_lawhood.methods.mass_balance_revision.bindings import operation_declarations
from empirical_lawhood.methods.mass_balance_revision.extension import EXTENSION as _extension_owner_1
EXPERIMENT_PROTOCOL_DECLARATIONS = _extension_owner_1.protocols
from empirical_lawhood.methods.mass_balance_revision.records import ForecastUpgradeSource, ForecastUpgradeSpecification
from empirical_lawhood.api.domain_composition.mass_balance_revision.experiment_binding import EXPERIMENT_RUNTIME_BINDING
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, CanonicalTaskReceipt, LogicalArtifactIdentity, ReceiptCheck
from empirical_lawhood.execution.extension_conformance import ConformanceCall, ConformanceCase, ConformanceProfile, ExtensionConformanceSelection
from empirical_lawhood.execution.plans import DevelopmentExecutionPlan
from empirical_lawhood.execution.recursive_handoff import AuthoredRecursiveWave, RecursiveImplementationBinding


def disclosed_source(case='adverse'):
    evidence = example_evidence(case)
    specification = MassSpecification('disclosed.unpublished.mass.' + case, evidence.identity,
        evidence.scope, evidence.independent_unit_ids, Decimal('.01'))
    config = original_design.config_for(specification, evidence)
    predictors, outcomes = original_design.inputs_for(evidence)
    forecast = original_science.predict(original_science.prediction_config(config), predictors)
    assessment = original_science.assess(config, forecast, outcomes)
    receipts = []
    for product in (forecast, assessment):
        key = 'disclosed.unpublished.' + product.config.phase
        logical = LogicalArtifactIdentity('artifact.' + key, product.fingerprint(), product.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', VisibilityCeiling.DEVELOPMENT_ONLY, (),
            OutcomeAccess.DEVELOPMENT_VISIBLE, ArtifactGenericValidation('validator.disclosed-not-published',
                '1.0.0', 'a'*64, product.SCHEMA, ArtifactProfile.CANONICAL_JSON))
        physical = ArtifactMaterialization('materialization.' + key, logical.logical_artifact_id,
            'storage.disclosed-not-published', key + '.json', product.fingerprint(), product.canonical_size_bytes(), 'none')
        receipts.append(CanonicalTaskReceipt('receipt.' + key, 'run.disclosed-not-executed', product.config.node_id,
            'attempt.' + key, 'a'*40, (), (physical,), (logical,),
            (ReceiptCheck('disclosed-unpublished-software-control', True, ()),), OperationalStatus.SUCCEEDED, ()))
    def pointer(kind):
        return ObjectIdentity('disclosed.not-published.' + kind.__name__.lower(), kind.SCHEMA, kind.VERSION, 'b'*64)
    return ForecastUpgradeSource('disclosed.upgrade-source.' + case, forecast, assessment,
        tuple(sorted(receipts, key=lambda value:value.receipt_id)), pointer(AuthoredRecursiveWave),
        pointer(DevelopmentExecutionPlan), pointer(RecursiveImplementationBinding))


source = disclosed_source()
specification = ForecastUpgradeSpecification('disclosed.upgrade-specification', source.identity,
    source.forecast.config.scope, source.forecast.config.independent_unit_ids)
converted = science.convert(design.config_for(specification), source)
operations = (*original_operations(), *operation_declarations())
old_producer = next(row.registration().selection for row in operations if row.capability_key == 'mass-balance.predict')
new_producer = operations[-1].registration().selection
cases = tuple(ConformanceCase('mass-balance.revision-' + record.VERSION, ConformanceCall.OUTPUT_RECORD_DECODE,
    {'operations':operations, 'producer':producer, 'payload_schema':record.SCHEMA, 'payload':record.canonical_bytes()}, record)
    for producer, record in ((old_producer, source.forecast), (new_producer, converted)))
CONFORMANCE_SELECTION = ExtensionConformanceSelection(namespace='mass-balance', schema_prefix='empirical-lawhood/mass-balance/',
    operations=operations, protocols=EXPERIMENT_PROTOCOL_DECLARATIONS, bindings=(EXPERIMENT_RUNTIME_BINDING,),
    profile=ConformanceProfile.RECORD_REVISIONS, cases=(*cases,
        ConformanceCase('mass-balance.unsupported-producer', ConformanceCall.OUTPUT_RECORD_DECODE,
            {'operations':operations, 'producer':replace(new_producer, capability_version='9.0.0'),
                'payload_schema':converted.SCHEMA, 'payload':converted.canonical_bytes()},
            'UnsupportedRecordRevision', 'original compatible reader')))
