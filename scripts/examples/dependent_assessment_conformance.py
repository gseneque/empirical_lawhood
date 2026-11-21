# SPDX-License-Identifier: MPL-2.0
"""Disclosed finite contracts/projectors, without execution receipts or admission."""

from dataclasses import fields, replace

from empirical_lawhood.methods.assigned_opportunity_assessment import bindings, design, science
from empirical_lawhood.methods.assigned_opportunity_assessment.examples import example_inputs
from empirical_lawhood.methods.assigned_opportunity_assessment.records import NAMESPACE
from empirical_lawhood.design.inquiry_methods import InquiryEvidenceRole
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.extension_conformance import ConformanceCall as Call, ConformanceCase as Case, ConformanceProfile as Profile, ExtensionConformanceSelection
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave


operations = bindings.operation_declarations()
registrations = tuple(row.registration() for row in operations)
actor, outcomes = example_inputs('unevaluable')
draft, sources = design.lower(actor, outcomes)
config = design.make_config(actor, outcomes)
procedure = science.author(design.author_config(config), actor)
assessment = science.assess(config, procedure, outcomes)
evidence = config.author.inputs[0]
contract = config.assessment
contract_arguments = {field.name: getattr(contract, field.name) for field in fields(contract)}
compiler = dict(draft=draft, registrations=registrations,
    registry=CapabilityRegistry('disclosed.opportunity.registry', tuple(row.manifest() for row in operations)),
    implementation_commit='a' * 40, output_codecs=bindings.record_codecs())
outputs = {(NAMESPACE + '.author', NAMESPACE + '.author.product'): procedure,
    (NAMESPACE + '.assess', NAMESPACE + '.assess.product'): assessment}
projection = dict(draft=draft, registrations=registrations, outputs=outputs)
expected = bindings.assessment_projector(assessment, *design.scientific_contract(config.source))
assert {row.phase.value: row.disposition.value for row in expected} == {
    'PROCEDURE': 'SATISFIED', 'INSTANCE': 'SATISFIED', 'ADMISSION': 'SATISFIED', 'JOINED': 'UNEVALUABLE'}
CONFORMANCE_SELECTION = ExtensionConformanceSelection(NAMESPACE, 'empirical-lawhood/' + NAMESPACE + '/', operations,
    imported_record_types=tuple(kind for kind in bindings.record_codecs().values()
                                if not kind.SCHEMA.startswith('empirical-lawhood/' + NAMESPACE + '/')),
    profile=Profile.DEPENDENT_ASSESSMENT_CONTRACTS,
    cases=(Case('inquiry.actor-input', Call.ACTOR_EVIDENCE, dict(evidence=evidence, cutoff=config.author.cutoff), None),
        Case('inquiry.no-evaluator-input', Call.ACTOR_EVIDENCE,
            dict(evidence=replace(evidence, role=InquiryEvidenceRole.EVALUATOR_DIAGNOSTIC), cutoff=config.author.cutoff),
            'ValueError', 'actor role'),
        Case('inquiry.complete-assignment', Call.ASSESSMENT_CONTRACT, contract_arguments, contract),
        Case('inquiry.missing-assignment', Call.ASSESSMENT_CONTRACT,
            {**contract_arguments, 'opportunities': contract.opportunities[:-1]}, 'ValueError', 'every assigned opportunity'),
        Case('inquiry.compile', Call.COMPILE, compiler, compile_recursive_wave(**compiler)),
        Case('inquiry.no-connection', Call.COMPILE, {**compiler, 'draft': replace(draft, connections=())}, 'ValueError', 'connection'),
        Case('inquiry.unevaluable-projection', Call.ASSESS, projection, tuple(sorted(expected, key=lambda row: row.assessment_id))),
        Case('inquiry.missing-producing-evidence', Call.ASSESS,
            {**projection, 'outputs': {key: value for key, value in outputs.items() if value is assessment}},
            'ValueError', 'unavailable producing evidence')))
