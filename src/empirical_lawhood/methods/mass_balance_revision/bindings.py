# SPDX-License-Identifier: MPL-2.0
"""Version-2 output through the ordinary stateless recursive operation owner."""

from dataclasses import replace
from functools import partial

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks

from empirical_lawhood.methods.mass_balance_revision import design, science
from empirical_lawhood.methods.mass_balance_revision.records import MAX_BYTES, ForecastUpgradeConfig, ForecastUpgradeSource, ForecastUpgradeSpecification, MassForecastV2


def unit_ids(config):
    return config.specification.independent_unit_ids


def operands(config):
    return (config.specification.source.object_fingerprint,)


def root_validator(config, context):
    if (tuple(row.record for row in context.config_inputs) != (config,)
            or context.node_id != config.node_id or context.root != design.root_for(config)
            or context.requirements or context.connections or context.links != (design.link_for(config),)
            or context.external_inputs != (design.external_for(config),)
            or context.unit_ids != unit_ids(config) or context.selected_unit_ids != unit_ids(config)
            or context.stage is not ScientificStage.TRANSFORM or context.complete_unit_census
            or context.outcome_access is not design.ACCESS or context.visibility_ceiling is not design.VISIBILITY):
        raise ValueError('forecast upgrade changes its complete original input, unit census or exposure')


class Runner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def execute(self, context):
        try:
            expected = {kind.SCHEMA:kind for kind in (ForecastUpgradeConfig, ForecastUpgradeSource)}
            records = {}
            for port in context.input_ports:
                kind = expected.get(port.payload_schema)
                if kind is None or kind in records or port.media_type != 'application/json':
                    raise ValueError('forecast upgrade changes its exact source/configuration input census')
                records[kind] = decode_canonical_bytes(port.read(), kind, maximum_bytes=MAX_BYTES)
            if set(records) != set(expected.values()):
                raise ValueError('forecast upgrade omits an original selected operand')
            config = records[ForecastUpgradeConfig]
            if (config.node_id != context.task_id or config.config_id != context.config.config_id
                    or config.fingerprint() != context.config.content_sha256 or context.resource_budget != design.BUDGET
                    or context.permissions != design.PERMISSIONS or context.outcome_access is not design.ACCESS
                    or tuple(port.output_id for port in context.output_ports) != (context.task_id + '.product',)):
                raise ValueError('forecast upgrade changes its separately admitted operation contract')
            result = science.convert(config, records[ForecastUpgradeSource])
            return RunnerResult((TaskOutputPayload(context.task_id + '.product', result.canonical_bytes()),),
                (ReceiptCheck('mass-balance-independent-unit-conversion', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    declaration = RecursiveOperationDeclaration(capability_key='mass-balance.upgrade-forecast', capability_version='2.0.0',
        implementation_id='mass-balance.upgrade-forecast.exact-grams-v2', kind=CapabilityKind.TRANSFORM,
        config_record_type=ForecastUpgradeConfig, stage=ScientificStage.TRANSFORM,
        input_ports=(RecursivePortContract('original', ForecastUpgradeSource.SCHEMA, 'application/json', MAX_BYTES),),
        outputs=(OutputTemplate('product', MassForecastV2.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=design.PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=design.ACCESS, visibility_ceiling=design.VISIBILITY, resources=design.BUDGET,
        conformance_check_ids=('mass-balance-exact-revision-selection', 'mass-balance-original-custody', 'mass-balance-unit-conversion'),
        runner_factory=Runner,
        record_codecs={kind.SCHEMA:kind for kind in (ForecastUpgradeConfig, ForecastUpgradeSource,
            ForecastUpgradeSpecification, MassForecastV2)},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=operands,
            scientific_unit_ids=unit_ids, scientific_root_validator=root_validator))
    return (replace(declaration, runner_factory=partial(Runner, manifest=declaration.manifest())),)
