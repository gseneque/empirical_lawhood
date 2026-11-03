# SPDX-License-Identifier: MPL-2.0
"""Pure exposed supply/portable-parent/successor compilation; no worker effects."""
from pathlib import Path
from dataclasses import replace

import pytest
from tests.rubisco_inquiry_source_fixtures import successor_source_operands

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.plans import ScientificInputRole
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave


def portable_parent(supplier):
    """Exact-byte portable metadata conformance, never scientific custody evidence."""
    product = ContributionProduct('product.exposed-compile.design-operand',
        ObjectIdentity.from_record(supplier.product_id, supplier),
        ArtifactIdentity('artifact.exposed-compile.supplier', 'scientific-product', supplier.SCHEMA,
                         supplier.fingerprint(), 'application/json', len(supplier.canonical_bytes())),
        ObjectIdentity('receipt.exposed-compile', 'empirical-lawhood/testing/exposed-compile-receipt', '1.0.0', 'a' * 64),
        ContributionRole.DESIGN_OPERAND, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    assessment = supplier.evaluation if hasattr(supplier, 'evaluation') else supplier.check
    assessment_id = assessment.evaluation_id if hasattr(assessment, 'evaluation_id') else assessment.check_id
    parent = ContributionManifest('contribution.exposed-compile', 'Can exact assessed source bytes compile for a distinct use?',
        'Exposed software metadata fixture; no actual custody or scientific qualification.', supplier.scope, (product,),
        (ObjectIdentity.from_record(assessment_id, assessment),), ())
    return decode_canonical_bytes(parent.canonical_bytes(), ContributionManifest, maximum_bytes=None)


def compile_complete_draft(draft, owner):
    declarations = owner.operation_declarations()
    compilation = compile_recursive_wave(draft=draft,
        registrations=tuple(declaration.registration() for declaration in declarations),
        registry=CapabilityRegistry('registry.exposed-inquiry-compile',
            tuple(sorted((declaration.manifest() for declaration in declarations), key=lambda value: value.registry_id))),
        implementation_commit='1' * 40, output_codecs=owner.output_codecs())
    assert compilation.execution_plan is not None
    assert len(compilation.execution_plan.tasks) == 1
    return compilation


@pytest.mark.parametrize('family', ('rubisco', 'material'))
def test_complete_source_then_portable_parent_and_instance_successor_compiles(family):
    if family == 'rubisco':
        from empirical_lawhood.adapters.methods.rubisco_inquiry import science, operation_bindings as owner, recursive_translation as drafts
        from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import (
            WilsonArticleInputV1, TeParentGenbankInputV1, WILSON_SOURCE_SHA256, GENBANK_SOURCE_SHA256,
        )
        article, genbank = successor_source_operands()
        operands = (WilsonArticleInputV1('input.exposed-compile.article', WILSON_SOURCE_SHA256, article.decode()),
                    TeParentGenbankInputV1('input.exposed-compile.genbank', GENBANK_SOURCE_SHA256, genbank.decode()))
    else:
        from empirical_lawhood.adapters.methods.analytic_material_inquiry import science, operation_bindings as owner, recursive_translation as drafts
        from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.native_quickstart import UniformElectronGasAnalyticReferenceConfig
        operands = (decode_canonical_bytes(Path('programmes/materials/superconductivity/workflows/electron-gas-response/config.json').read_bytes(), UniformElectronGasAnalyticReferenceConfig, maximum_bytes=None),)
    # Exposed pure fixture arithmetic, then real compiler; no operation runner.
    supplier = science.supply(*operands)
    first = drafts.supply_draft(*operands)
    compile_complete_draft(first, owner)
    assert all(value.scientific_role == ScientificInputRole.SOURCE.value for value in first.external_inputs)
    parent = portable_parent(supplier)
    later = drafts.use_draft(supplier, parent=parent)
    from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
    product = parent.products[0]
    origins = RecursiveInputOrigins(tuple(sorted((
        RecursiveInputOrigin(value.input_id, RecursiveInputOriginKind.CONTRIBUTION,
            value.expected_content_sha256, product.role.value, ObjectIdentity.from_record(parent.contribution_id, parent),
            product.product_id, product.producing_receipt) if value.input_id.endswith('.supplier') else
        RecursiveInputOrigin(value.input_id, RecursiveInputOriginKind.SOURCE, value.expected_content_sha256, value.scientific_role)
        for value in later.external_inputs), key=lambda value: value.input_id)))
    origins.validate_draft(later)
    result = compile_complete_draft(later, owner)
    assert later.contribution_parents == (parent,)
    supplier_input = next(value for value in later.external_inputs if value.input_id.endswith('.supplier'))
    instance_input = next(value for value in later.external_inputs if value.input_id.endswith('.instance'))
    assert supplier_input.scientific_role == ScientificInputRole.MODEL.value
    assert instance_input.scientific_role == ScientificInputRole.SOURCE.value
    assert parent.products[0].role is ContributionRole.DESIGN_OPERAND
    assert supplier_input.logical_artifact_id == parent.products[0].artifact.artifact_id
    assert result.selected_scientific_projection.contribution_parents == (ObjectIdentity.from_record(parent.contribution_id, parent),)

    wrong = replace(later, external_inputs=tuple(replace(value, scientific_role='OUTCOME')
        if value.input_id.endswith('.supplier') else value for value in later.external_inputs))
    with pytest.raises(ValueError, match='digest or role'):
        origins.validate_draft(wrong)
    with pytest.raises(ValueError, match='exact external-input contract'):
        compile_complete_draft(wrong, owner)
