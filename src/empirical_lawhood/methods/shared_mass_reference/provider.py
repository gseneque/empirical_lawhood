# SPDX-License-Identifier: MPL-2.0
"""Retain ordinary provider ownership while sharing only an immutable reference."""

from dataclasses import dataclass

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_stable_id
from empirical_lawhood.execution.plans import ExternalInputSpec
from empirical_lawhood.execution.providers import CampaignRuntimeProvider
from empirical_lawhood.execution.recursive_provider import RecursiveInputSupplier, RecursiveOperationProvider, require_recursive_input_supplier

from empirical_lawhood.methods.shared_mass_reference.service import MassScopeService, ScopeServiceSelection


@dataclass(frozen=True, slots=True)
class OperationInputHandle:
    """An exact finite input view, not permission to inspect a sibling's inputs."""

    capability_key: str
    execution_plan: ObjectIdentity
    allowed_specs: tuple[ExternalInputSpec, ...]
    supplier: RecursiveInputSupplier

    def __post_init__(self):
        validate_stable_id(self.capability_key)
        if type(self.execution_plan) is not ObjectIdentity or type(self.allowed_specs) is not tuple:
            raise TypeError('operation input handle requires its frozen plan and finite exact inputs')
        self.execution_plan.__post_init__()
        require_recursive_input_supplier(self.supplier)
        if any(type(spec) is not ExternalInputSpec for spec in self.allowed_specs):
            raise TypeError('operation input handle requires exact immutable external input specifications')
        for spec in self.allowed_specs:
            spec.__post_init__()
        if len(self.allowed_specs) > 16 or len(set(self.allowed_specs)) != len(self.allowed_specs):
            raise ValueError('mass reference input handle exceeds its distinct finite input census')

    def resolve_input(self, spec):
        if type(spec) is not ExternalInputSpec or spec not in self.allowed_specs:
            raise PermissionError('operation input handle refuses another owner or changed frozen input')
        return self.supplier.resolve_input(spec)


class ScopeBoundProvider(CampaignRuntimeProvider):
    """A domain wrapper; the existing composite still owns runner and port joins."""

    CAPABILITY = None

    def __init__(self, *, delegate, service, selection, execution_plan):
        if (type(delegate) is not RecursiveOperationProvider or type(service) is not MassScopeService
                or type(selection) is not ScopeServiceSelection
                or type(execution_plan) is not ObjectIdentity):
            raise TypeError('mass reference provider requires exact code-owned immutable composition products')
        if (delegate.manifest.capability_key != self.CAPABILITY
                or type(delegate.supplier) is not OperationInputHandle
                or delegate.supplier.capability_key != self.CAPABILITY
                or delegate.supplier.execution_plan != execution_plan
                or delegate.registration.native_effect):
            raise ValueError('mass reference provider changes its separate pure operation or input ownership')
        service.resolve(selection)
        self.delegate = delegate
        self.service = service
        self.selection = selection
        self.execution_plan = execution_plan
        self.registry_sha256 = delegate.registry_sha256
        self.capability_count = 1
        self.issued_source_schema_ids = ()

    def _require(self, plan=None):
        self.service.resolve(self.selection)
        if plan is not None and self.execution_plan != ObjectIdentity.from_record(plan.execution_plan_id, plan):
            raise ValueError('mass reference composition refuses another frozen execution plan')

    def worker_preparations(self, registry, execution_plan=None):
        self._require(execution_plan)
        return self.delegate.worker_preparations(registry, execution_plan)

    def runners(self, registry, source_records=()):
        self._require()
        return self.delegate.runners(registry, source_records)

    def external_inputs(self, plan, source_records=()):
        self._require(plan)
        return self.delegate.external_inputs(plan, source_records)

    def output_semantic_contracts(self, registry, execution_plan=None):
        self._require(execution_plan)
        return self.delegate.output_semantic_contracts(registry, execution_plan)

    def scientific_adjudication_contract(self, registry, execution_plan=None):
        self._require(execution_plan)
        return self.delegate.scientific_adjudication_contract(registry, execution_plan)
