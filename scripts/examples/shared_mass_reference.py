# SPDX-License-Identifier: MPL-2.0
"""Compose one disclosed immutable service; perform no scientific execution."""

from decimal import Decimal
import json

from empirical_lawhood.methods.mass_balance_starter import bindings, design, science
from empirical_lawhood.methods.mass_balance_starter.examples import example_evidence
from empirical_lawhood.methods.mass_balance_starter.records import MassSpecification
from empirical_lawhood.api.shared_mass_composition import compose_mass_reference
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave


class UnopenedInputs:
    def resolve_input(self, spec):
        raise RuntimeError('composition example has no scientific input admission')


def main():
    evidence = example_evidence('positive')
    specification = MassSpecification('example.shared-mass.specification', evidence.identity,
        evidence.scope, evidence.independent_unit_ids, Decimal('0.01'))
    config = design.config_for(specification, evidence)
    draft, _ = design.lower(specification, evidence)
    declarations = bindings.operation_declarations()
    registry = CapabilityRegistry('example.shared-mass.registry', tuple(d.manifest() for d in declarations))
    # This disclosed software-only pin creates no source or execution authority.
    compiled = compile_recursive_wave(draft=draft, registry=registry,
        registrations=tuple(d.registration() for d in declarations), implementation_commit='a' * 40,
        output_codecs={key: codec for d in declarations for key, codec in d.record_codecs.items()})
    runtime = compose_mass_reference(registry=registry, execution_plan=compiled.execution_plan,
        configurations=(config, science.prediction_config(config)), scope_payload=evidence.scope.canonical_bytes(),
        scope_reference=ObjectIdentity.from_record('example.shared-mass.scope', evidence.scope),
        input_suppliers=tuple((d.capability_key, UnopenedInputs()) for d in declarations))
    print(json.dumps({'scope': json.loads(runtime.service.reference.canonical_bytes()),
        'service_key': runtime.service.KEY, 'service_version': runtime.service.VERSION,
        'provider_count': len(runtime.providers),
        'one_shared_object': all(p.service is runtime.service for p in runtime.providers),
        'separate_input_handles': runtime.providers[0].delegate.supplier is not runtime.providers[1].delegate.supplier,
        'scientific_execution': False, 'native_contact_count': 0, 'qualification': 'NOT_ESTABLISHED'}, indent=2))


if __name__ == '__main__':
    main()
