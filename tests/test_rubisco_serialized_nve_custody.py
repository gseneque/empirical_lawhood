# SPDX-License-Identifier: MPL-2.0
"""Real-shaped same-ID custody, never native chemical or NVE qualification."""

from dataclasses import fields, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_contracts as c, control_roster, nve_contracts, nve_roster, nve_science
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.nve_preparation_admission import SerializedPreparationNVEControlPlan, decode_plan
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.serialized_nve_custody import ChemicalForceCustodySupply, SerializedCustodyNVEControlPlan
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.status import OperationalStatus
from tests.test_rubisco_nve_durable_controls import full_state, full_system, native_text
from tests.test_rubisco_serialized_durable_chemical_admission import durable_admitted as durable_admitted, reuse_admitted as reuse_admitted, original as original


@pytest.fixture(scope="module")
def admitted(durable_admitted):
    """Disclosed serializer-shaped originals, with genuine canonical ID rules."""
    old = durable_admitted
    controls = old.plan
    name, asset = controls.selected_assets[0]
    sources = {controls.source, controls.preparation, controls.assignment_integrity, controls.mathematical_geometry,
        asset, p.identity(controls.hardware), *(identity for row in controls.preparation_custody for identity in row[1:])}
    parent = old.custody[0][1].parent_contact
    definition = next(row for row in control_roster.definitions(controls, parent,
        sources=tuple(sorted(sources, key=lambda row: row.object_id)), input_materialization_ids=parent.input_materialization_ids)
        if row.subwork_id == "control.chemical-force."+name)
    completion = replace(old.custody[0][3], definition=definition.identity,
        output_ids=tuple(sorted(row.output_id for row in definition.outputs)), operational_status=OperationalStatus.SUCCEEDED)
    ci = ObjectIdentity.from_record("exposed.chemical-primary.completion", completion)
    files = {name: b"EXPOSED SOFTWARE FIXTURE ONLY\n" for name in ("minimizer-termination.json", "minimizer-progress.jsonl",
        "declared-system-constraints.json", "minimizer-apparatus.json", "apparatus-cuda.json", "apparatus-cpu.json",
        "controlled-integrator-00.xml", "cpu-force-reference.xml")}
    files.update({"controlled-system-00.xml": full_system(), "minimized.xml": full_state()})
    texts = tuple(native_text("exposed-chemical/"+name, raw) for name, raw in sorted(files.items()))
    returned = c.ChemicalForceReturn(definition.subwork_id, controls.identity, asset, True, 2,
        "exposed-chemical/minimized.xml", tuple(row.evidence for row in texts), (definition.identity,))
    assessment = c.ChemicalForceAssessment("assessment.exposed.original-chemical", controls.identity, returned.identity,
        A.SATISFIED, A.SATISFIED, Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), ("EXPOSED_TYPED_CUSTODY_ONLY",))
    ai = p.identity(assessment)
    supply = nve_contracts.RelaxedModelSupply("product.exposed.relaxed", old.assets[0], returned.identity, ai,
        next(row for row in texts if Path(row.evidence.relative_path).name == "controlled-system-00.xml"),
        next(row for row in texts if Path(row.evidence.relative_path).name == "minimized.xml"))
    key = next(row for row in p.model_roster() if c.model_id(row) == name)
    previous = SerializedPreparationNVEControlPlan("config.exposed.original-serialized-nve", controls,
        ((name, supply.identity, definition.identity, ci, returned.identity, ai),), ((*key, "ensemble-01", "primary"),),
        p.NATIVE_WORK_ROOT+"/exposed-custody-nve-unentered", controls.code_sources, controls.dependency_lock_sha256)
    envelope = ChemicalForceCustodySupply("product.exposed.assessed-chemical-custody", definition, ci, completion, returned, assessment)
    kwargs = {field.name: getattr(previous, field.name) for field in fields(previous)}
    plan = SerializedCustodyNVEControlPlan(**kwargs, chemical_custody_supplies=(envelope,))
    return SimpleNamespace(plan=plan, previous=previous, envelope=envelope, source=old.source,
        relaxed=supply, custody=(envelope.original_custody,), parent=parent)


def test_original_ID_collision_preserved_with_legitimate_supplier_and_full97(admitted):
    row = admitted
    original_bytes = tuple(record.canonical_bytes() for record in row.envelope.original_custody[1:])
    assert row.envelope.definition.identity.object_id == row.envelope.returned.identity.object_id
    assert row.envelope.definition.identity.object_schema != row.envelope.returned.identity.object_schema
    assert row.envelope.identity.object_id not in {row.envelope.definition.identity.object_id, row.envelope.returned.identity.object_id}
    with pytest.raises(ValueError):
        nve_roster.definitions(row.previous, row.parent,
            sources=(row.previous.chemical_controls.identity, row.previous.chemical_controls.source,
                *(identity for parent in row.previous.admitted_parents for identity in parent[1:])),
            input_materialization_ids=row.parent.input_materialization_ids)
    definitions = nve_roster.definitions(row.plan, row.parent, sources=row.plan.custody_source_identities,
        input_materialization_ids=row.parent.input_materialization_ids)
    assert len(definitions) == 97 and len(row.plan.full_census) == 96
    assert nve_science.validate_operands(row.plan, row.source, (row.relaxed,), row.custody) == row.plan
    assert tuple(record.canonical_bytes() for record in row.envelope.original_custody[1:]) == original_bytes
    assert decode_plan(row.plan.canonical_bytes().decode()) == row.plan
    assert decode_canonical_bytes(row.envelope.canonical_bytes(), ChemicalForceCustodySupply, maximum_bytes=None) == row.envelope
    assert decode_plan(row.previous.canonical_bytes().decode()) == row.previous
    assert row.plan.numerical_window_picosecond == Decimal("100")
    assert row.plan.receiver_contract == "ALL_ELEVEN_FULL_STATES_AND_OPAQUE_CHECKPOINTS"


@pytest.mark.parametrize("field", ("definition", "completion_identity", "completion", "returned", "assessment"))
def test_missing_complete_original_member_refuses(admitted, field):
    with pytest.raises(ValueError):
        replace(admitted.envelope, **{field: None})


@pytest.mark.parametrize("changed", ("configuration", "completion", "returned", "assessment"))
def test_substituted_original_member_refuses(admitted, changed):
    row = admitted.envelope
    if changed == "configuration":
        value = replace(row.definition, configuration=replace(row.definition.configuration, object_fingerprint="1"*64))
        field = "definition"
    elif changed == "completion":
        value = replace(row.completion, definition=replace(row.completion.definition, object_fingerprint="1"*64))
        field = changed
    elif changed == "returned":
        value = replace(row.returned, assets=replace(row.returned.assets, object_fingerprint="1"*64))
        field = changed
    else:
        value = replace(row.assessment, returned=replace(row.assessment.returned, object_fingerprint="1"*64))
        field = changed
    with pytest.raises(ValueError):
        replace(row, **{field: value})


@pytest.mark.parametrize("changed", ("missing-envelope", "direct-original", "negative-assessment", "unknown-completion", "source", "parent-return"))
def test_independent_or_unknown_admission_refuses_before_contact(admitted, changed):
    row = admitted
    plan, source, custody = row.plan, row.source, row.custody
    with pytest.raises(ValueError):
        if changed == "missing-envelope":
            replace(plan, chemical_custody_supplies=())
        elif changed == "direct-original":
            custody = (custody[0][:-1]+(replace(row.envelope.assessment, force_agreement_disposition=A.FALSIFIED),),)
        elif changed == "negative-assessment":
            negative = replace(row.envelope.assessment, force_agreement_disposition=A.FALSIFIED)
            envelope = replace(row.envelope, assessment=negative)
            parent = plan.admitted_parents[0][:-1]+(p.identity(negative),)
            plan = replace(plan, chemical_custody_supplies=(envelope,), admitted_parents=(parent,))
            custody = (envelope.original_custody,)
        elif changed == "unknown-completion":
            completion = replace(row.envelope.completion, unknown_streams=(plan.chemical_controls.source,))
            ci = ObjectIdentity.from_record(row.envelope.completion_identity.object_id, completion)
            envelope = replace(row.envelope, completion=completion, completion_identity=ci)
            old = plan.admitted_parents[0]
            plan = replace(plan, chemical_custody_supplies=(envelope,), admitted_parents=((old[0], old[1], old[2], ci, old[4], old[5]),))
            custody = (envelope.original_custody,)
        elif changed == "source":
            source = replace(source, engine_inventory_sha256="1"*64)
        else:
            old = plan.admitted_parents[0]
            replace(plan, admitted_parents=((old[0], old[1], old[2], old[3], replace(old[4], object_fingerprint="1"*64), old[5]),))
        nve_science.validate_operands(plan, source, (row.relaxed,), custody)


def test_preserved_accepted_legacy_record_and_numerical_owners():
    root = Path(__file__).resolve().parents[1]/"src/empirical_lawhood/adapters/methods/rubisco_insilico_sampling"
    assert sha256((root/"nve_contracts.py").read_bytes()).hexdigest() == "56d98187056b49a1b56a591e1183460c472b7b40339620655df5b3b166fc2114"
