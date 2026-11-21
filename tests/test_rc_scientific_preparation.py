"""RC whole-census validation has one invocation-local proof and no effects."""

from dataclasses import replace

import pytest

from empirical_lawhood.domains.circuits.rc_prerequisite_chain import operation_bindings as bindings, recursive_translation as translation, scientific_binding as science_binding
from empirical_lawhood.domains.circuits.rc_prerequisite_chain.science import default_chain_config
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave


def compile_draft(draft):
    return compile_recursive_wave(draft=draft, registrations=bindings.operation_registrations(),
        registry=CapabilityRegistry("test.rc.preparation", tuple(sorted(bindings.operation_manifests(),
            key=lambda value: value.registry_id))), implementation_commit="a" * 40,
        output_codecs=bindings.output_codecs())


@pytest.mark.parametrize("units", [1, 2, 4, 8, 11])
def test_one_reference_draft_and_linear_reference_object_census_per_invocation(monkeypatch, units):
    config = default_chain_config()
    draft = translation.rc_recursive_draft(config,
        unit_ids=tuple(unit.unit_id for unit in config.units[:units]), include_summary=False)
    original = translation.rc_recursive_draft
    constructions = []

    def counted(*args, **kwargs):
        result = original(*args, **kwargs)
        constructions.append(len(result.operations))
        return result

    monkeypatch.setattr(translation, "rc_recursive_draft", counted)
    compiled = compile_draft(draft)
    assert len(compiled.execution_plan.tasks) == units * 9
    assert constructions == [units * 9]


def test_equal_or_foreign_context_cannot_reuse_a_prepared_scientific_verdict(monkeypatch):
    config = default_chain_config()
    draft = translation.rc_recursive_draft(config, unit_ids=(config.units[6].unit_id,), include_summary=False)
    contexts = []
    validate = bindings.scientific_root_validator

    def captured(record, context):
        contexts.append((record, context))
        return validate(record, context)

    monkeypatch.setattr(bindings, "scientific_root_validator", captured)
    first = compile_draft(draft)
    second = compile_draft(draft)
    assert first.execution_plan.canonical_bytes() == second.execution_plan.canonical_bytes()
    assert len(contexts) == 18
    record, context = contexts[0]
    prepared = context.scientific_preparation
    assert all(item.scientific_preparation is prepared for _, item in contexts[:9])
    assert contexts[9][1].scientific_preparation is not prepared
    with pytest.raises(TypeError):
        prepared.node_configs[context.node_id] = record
    for changed in (replace(context, root=replace(context.root)),
                    replace(context, links=tuple(list(context.links))),
                    replace(context, scientific_preparation=contexts[9][1].scientific_preparation)):
        with pytest.raises(ValueError, match="exact prepared invocation"):
            science_binding.validate_rc_scientific_binding(record, changed)
    with pytest.raises(ValueError, match="exact prepared invocation"):
        science_binding.validate_rc_scientific_binding(replace(record), context)
