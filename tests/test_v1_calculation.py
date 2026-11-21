# SPDX-License-Identifier: MPL-2.0
"""Public calculation contracts, cold discovery and actual worker adaptation."""
from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import pickle
from typing import ClassVar

import pytest

from empirical_lawhood.science import CanonicalRecord, ResourceBudget, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.methods import Calculation, RecordInput, RecordOutput
from empirical_lawhood.execution.extensions import ExtensionDeclaration, descriptor_projection
from empirical_lawhood.execution.capabilities import CapabilityConfigRef
from empirical_lawhood.execution.execution import TaskContext, WorkerInputBinding, WorkerInputPort, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile


@dataclass(frozen=True, slots=True)
class ScaleConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/calculation-config'
    factor: Decimal


@dataclass(frozen=True, slots=True)
class Observations(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/calculation-observations'
    values: tuple[Decimal, ...]


@dataclass(frozen=True, slots=True)
class Product(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/calculation-product'
    values: tuple[Decimal, ...]


def scale(config, inputs):
    return {'result': Product(tuple(value * config.factor for value in inputs['observations'].values))}


def method(**kwargs):
    values = dict(capability_key='testing.calculation.scale', version='1.0.0', implementation_id='testing.scale.v1',
        config_type=ScaleConfig, inputs=(RecordInput('observations', Observations, 4096),),
        outputs=(RecordOutput('result', Product, 4096),), calculate=scale,
        resources=ResourceBudget(1, 64 * 1024**2, 0, 30, 8192, 4096),
        applicability='Finite exposed dimensionless observations', assumptions=('Exact Decimal inputs.',))
    return Calculation(**(values | kwargs))


class Reader(BytesIO):
    @property
    def bytes_read(self):
        return self.tell()


def worker_context(calculation, config, observations):
    def port(record, artifact):
        raw = record.canonical_bytes()
        binding = WorkerInputBinding(artifact, 'materialization.' + artifact, record.SCHEMA, 'application/json',
            len(raw), VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE, WorkerInputKind.EXTERNAL)
        return WorkerInputPort(binding, Reader(raw))
    ports = (port(config, 'config.scale'), port(observations, 'observations.scale'))
    return TaskContext('run.test', 'task.scale', 'attempt.test', CapabilityConfigRef('config.scale', config.SCHEMA,
        sha256(config.SCHEMA.encode()).hexdigest(), config.fingerprint(), 'config.scale'),
        tuple(port.binding for port in ports), ports,
        (WorkerOutputPort('task.scale.result', Product.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json'),),
        calculation.permissions, calculation.outcome_access, calculation.resources, WorkerIsolationProfile.TRUSTED_LOCAL)


def test_public_independent_calculation_and_original_worker_match():
    calculation = method()
    config, observations = ScaleConfig(Decimal('2')), Observations((Decimal('1.25'), Decimal('-3')))
    expected = Product((Decimal('2.50'), Decimal('-6')))
    assert calculation(config, {'observations': observations}) == {'result': expected}
    context = worker_context(calculation, config, observations)
    result = calculation.operation.runner_factory().execute(context)
    assert result.outputs[0].payload == expected.canonical_bytes()
    assert all(port._reader.closed for port in context.input_ports)
    assert result.checks[0].passed


def test_declaration_and_discovery_do_not_call_calculation():
    def forbidden(*args):
        pytest.fail('cold discovery called science')
    calculation = method(calculate=forbidden)
    extension = ExtensionDeclaration('testing.scale', '1.0.0', (calculation.operation,))
    assert extension.discovery.capability_manifests == (calculation.operation.manifest(),)
    assert extension.executable.bindings == tuple(factory.binding for factory in extension.factories)
    assert calculation.describe()['scientific_execution_performed'] is False
    assert calculation.operation.inquiry_hooks.inquiry_work_projector is None
    assert calculation.operation.execution_properties.native_effect is False


def test_worker_and_declaration_are_reconstructible_across_process_serialization():
    calculation = method()
    runner = pickle.loads(pickle.dumps(calculation.operation.runner_factory()))
    assert runner.manifest == calculation.operation.manifest()
    context = worker_context(calculation, ScaleConfig(Decimal('2')), Observations((Decimal('4'),)))
    assert runner.execute(context).outputs[0].payload == Product((Decimal('8'),)).canonical_bytes()


@pytest.mark.parametrize('bad_inputs', ({}, {'wrong': Observations((Decimal('1'),))},
    {'observations': Product((Decimal('1'),))}))
def test_declared_input_census_and_exact_record_types_are_enforced(bad_inputs):
    with pytest.raises((TypeError, ValueError)):
        method()(ScaleConfig(Decimal('1')), bad_inputs)


@pytest.mark.parametrize('calculation', (
    lambda config, inputs: {},
    lambda config, inputs: {'result': Observations((Decimal('1'),))},
    lambda config, inputs: {'result': Product((Decimal('1'),)), 'extra': Product(())},
))
def test_incomplete_extra_and_substituted_results_refuse(calculation):
    with pytest.raises((TypeError, ValueError)):
        method(calculate=calculation)(ScaleConfig(Decimal('1')), {'observations': Observations((Decimal('1'),))})


def test_failed_calculation_closes_every_original_input_guard():
    def fail(config, inputs):
        raise ArithmeticError('selected scientific failure')
    calculation = method(calculate=fail)
    context = worker_context(calculation, ScaleConfig(Decimal('1')), Observations((Decimal('1'),)))
    with pytest.raises(ArithmeticError, match='selected scientific failure'):
        calculation.operation.runner_factory().execute(context)
    assert all(port._reader.closed for port in context.input_ports)


def test_substituted_config_and_output_contract_refuse_before_science():
    calculation = method()
    context = worker_context(calculation, ScaleConfig(Decimal('1')), Observations((Decimal('1'),)))
    context = replace(context, config=replace(context.config, content_sha256='0' * 64))
    with pytest.raises(ValueError, match='authored bytes'):
        calculation.operation.runner_factory().execute(context)
    context = worker_context(calculation, ScaleConfig(Decimal('1')), Observations((Decimal('1'),)))
    context = replace(context, output_ports=(replace(context.output_ports[0], output_id='task.scale.other'),))
    with pytest.raises(ValueError, match='output'):
        calculation.operation.runner_factory().execute(context)


def test_canonical_byte_limits_apply_to_independent_calls():
    calculation = method(inputs=(RecordInput('observations', Observations, 32),))
    with pytest.raises(ValueError, match='byte bound'):
        calculation(ScaleConfig(Decimal('1')), {'observations': Observations((Decimal('1'),))})


def test_duplicate_schemas_and_declaration_owners_refuse():
    with pytest.raises(ValueError, match='distinct schemas'):
        method(inputs=(RecordInput('one', Observations, 4096), RecordInput('two', Observations, 4096)))
    calculation = method()
    with pytest.raises(ValueError, match='repeat'):
        ExtensionDeclaration('testing.scale', '1.0.0', (calculation.operation, calculation.operation))
    from types import ModuleType
    module = ModuleType('test.extension')
    module.EXTENSION = ExtensionDeclaration('testing.scale', '1.0.0', (calculation.operation,))
    module.EXECUTABLE_BINDING_FACTORIES = ()
    with pytest.raises(ValueError, match='duplicates'):
        descriptor_projection(module, 'EXECUTABLE_BINDING_FACTORIES')


def test_actual_registry_composition_accepts_a_calculation_without_invented_profiles():
    from empirical_lawhood.execution.generated_extension_bundles import EXTENSION_BUNDLE_CONTRIBUTIONS
    from empirical_lawhood.execution.extension_bundles import compose_extension_bundle_aggregate

    def forbidden(*args):
        pytest.fail("registration ran scientific work")

    calculation = method(calculate=forbidden)
    extension = ExtensionDeclaration("testing.scale", "1.0.0", (calculation.operation,))
    aggregate = compose_extension_bundle_aggregate((*EXTENSION_BUNDLE_CONTRIBUTIONS, extension.discovery))
    binding = aggregate.binding(calculation.capability_key, calculation.version)
    assert binding is not None
    assert binding.profile_registrations == ()
    assert binding.bundle_fingerprint == aggregate.bundle.fingerprint()
    assert calculation.operation.manifest() in aggregate.capability_registry.capabilities
    assert aggregate.bundle.profile_registrations  # Existing required aggregate roles remain intact.
