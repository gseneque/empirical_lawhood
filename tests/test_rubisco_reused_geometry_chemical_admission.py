# SPDX-License-Identifier: MPL-2.0
"""Exposed complete supplier/admission joins; no actual molecular assessment."""

from dataclasses import fields, replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import preparation_integrity as legacy
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import physical_preparation_geometry as legacy_geometry
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import serialized_preparation_assessment as serialized
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import definitions
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_contracts as c, control_science
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_preparation_admission import (
    ReusedGeometryChemicalForcePlan, decode_assessments, decode_plan, validate_operands,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_invocation import build_invocation
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_roster import definitions as control_definitions
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_rubisco_geometry_reuse import fresh, original as original
from tests import test_rubisco_chemical_force_controls as chemical_controls
from tests.test_rubisco_physical_preparation_geometry import diagnostic
from tests.test_rubisco_preparation_integrity import exposed_preparation


@pytest.fixture
def oldplan():
    return chemical_controls.plan.__wrapped__()


@pytest.fixture
def admitted(original, oldplan):
    """Typed admission control only; its fixture text is explicitly not a molecule."""
    source, preparation_plan = fresh(original)
    _, old_product, old_assets = exposed_preparation(A.NOT_ATTEMPTED)
    selected = preparation_plan.attempted_model_ids[0]
    roster_index = tuple(row.model_id for row in old_product.models).index(selected)
    parent_files = tuple(p.NativeTextFile(evidence, original.files[Path(evidence.relative_path).name].decode())
        for evidence in (original.assessment.origin_file, original.assessment.heavy_file))
    origin = json.loads(parent_files[0].raw_utf8) | {"amber_realization": {"fixture": "exposed only"}}
    raw_files = {
        "complete-heavy.pdb": parent_files[1].raw_utf8,
        "atom-origin-provenance.json": json.dumps(origin, sort_keys=True),
        "model.prmtop": "EXPOSED TOPOLOGY NOT A MOLECULE\n",
        "model.inpcrd": "EXPOSED COORDINATES NOT A MOLECULE\n",
        "complete-assigned-parameters.json": '{"scope":"exposed fixture"}\n',
    }
    files = tuple(p.NativeTextFile(p.FileEvidence(selected + "/" + name, len(raw.encode()),
        sha256(raw.encode()).hexdigest()), raw) for name, raw in sorted(raw_files.items()))
    asset = replace(old_assets[roster_index], source=p.identity(source), files=files)
    assets = tuple(asset if index == roster_index else replace(row, source=p.identity(source))
        for index, row in enumerate(old_assets))
    call = p.NativeCall("call.exposed.typed-only", None, selected, "EXPOSED", "{}", "{}",
        oldplan.temperature_kelvin * 0, oldplan.temperature_kelvin * 0, "COMPLETED", None, ())
    model = replace(old_product.models[roster_index], disposition=A.SATISFIED,
        reason_codes=("EXPOSED_TYPED_ADMISSION_FIXTURE_ONLY",), files=tuple(row.evidence for row in files),
        assets=p.identity(asset), atom_count=4, complete_parameter_census=(("atoms", 4),),
        provenance_manifest_path=selected + "/atom-origin-provenance.json", native_call_ids=(call.call_id,))
    models = tuple(model if index == roster_index else replace(row, assets=p.identity(assets[index]))
        for index, row in enumerate(old_product.models))
    preparation = replace(old_product, source=p.identity(source), structural_inventory=source.structural_inventory,
        structural_coordinates=source.structural_coordinates, nomination=source.nomination, models=models,
        native_calls=(call,), files=tuple(row.evidence for row in files))
    dispositions = tuple((row.model_id, row.disposition, row.reason_codes) for row in models)
    counts, overall = legacy.disposition_census(dispositions)
    integrity = serialized.SerializedPreparationIntegrity("assessment.exposed.assignment", p.identity(source),
        p.identity(preparation), serialized.ASSIGNMENT_METHOD, dispositions, counts, overall, 1,
        ((selected, next(row.evidence for row in files if row.evidence.relative_path.endswith("model.prmtop"))),))
    mathematical_models = tuple(legacy_geometry.ModelGeometry(row.model_id, row.assets, row.disposition,
        A.SATISFIED if row.model_id == selected else A.NOT_ATTEMPTED,
        ("EXPOSED_TYPED_ADMISSION_FIXTURE_ONLY",),
        tuple(value.evidence for value in files if Path(value.evidence.relative_path).name != "complete-assigned-parameters.json")
            if row.model_id == selected else (), diagnostic() if row.model_id == selected else None)
        for row in models)
    geometry = serialized.SerializedPreparationGeometry("assessment.exposed.geometry", p.identity(source),
        p.identity(preparation), p.identity(integrity), mathematical_models)
    selected_definitions = definitions(preparation_plan, original.supply.definition.parent_contact,
        sources=(preparation_plan.source, preparation_plan.nomination, preparation_plan.inventory,
            preparation_plan.coordinates, original.supply.identity, original.supply.independent_integrity),
        input_materialization_ids=original.supply.definition.parent_contact.input_materialization_ids)
    definition = next(row for row in selected_definitions if row.subwork_id == selected)
    completion = replace(original.supply.completion, definition=definition.identity,
        output_ids=tuple(sorted(row.output_id for row in definition.outputs)))
    returned = replace(original.supply.returned, unit_id=selected, plan=preparation_plan.identity,
        geometry=original.supply.definition.identity, geometry_receipt=original.supply.geometry_receipt,
        files=tuple(row.evidence for row in files))
    custody = ((selected, definition, ObjectIdentity.from_record("completion.exposed.model", completion), completion,
        ObjectIdentity.from_record("return.exposed.model", returned), returned),)
    kwargs = {field.name: getattr(oldplan, field.name) for field in fields(c.ChemicalForcePlan)}
    kwargs.update(source=p.identity(source), preparation=p.identity(preparation), assignment_integrity=p.identity(integrity),
        mathematical_geometry=p.identity(geometry), selected_assets=((selected, p.identity(asset)),),
        preparation_custody=((selected, definition.identity, custody[0][2], custody[0][4]),))
    plan = ReusedGeometryChemicalForcePlan(**kwargs, preparation_plan=preparation_plan,
        geometry_supplies=(original.supply,), geometry_assessments=(original.assessment,),
        geometry_inputs=((original.supply.identity, parent_files),))
    return SimpleNamespace(plan=plan, source=source, preparation=preparation, integrity=integrity,
        geometry=geometry, assets=(asset,), custody=custody, parent=original, parent_files=parent_files)


def admit(row, **changes):
    operands = {name: getattr(row, name) for name in ("plan", "source", "preparation", "integrity", "geometry", "assets", "custody")}
    return validate_operands(**(operands | changes))


def test_complete_typed_supplier_admission_and_roundtrip_preserve_old_math(admitted):
    globals_before = dict(control_science.validate_operands.__globals__)
    assert admit(admitted) == admitted.plan
    assert decode_plan(admitted.plan.canonical_bytes().decode()) == admitted.plan
    assert decode_assessments(admitted.integrity.canonical_bytes().decode(),
        admitted.geometry.canonical_bytes().decode()) == (admitted.integrity, admitted.geometry)
    assert control_science.validate_operands.__globals__ == globals_before
    assert len(admitted.integrity.model_dispositions) == len(admitted.geometry.models) == 24
    assert len(admitted.plan.model_census) == 24 and len(admitted.plan.nve_census) == 96
    assert admitted.integrity.kinetic_disposition is admitted.geometry.force_adequacy is A.UNEVALUABLE


@pytest.mark.parametrize("change", ("configuration", "code", "lock", "supplier-source", "assessment-source", "geometry", "receipt"))
def test_changed_complete_model_native_custody_is_refused(admitted, change):
    name, definition, ci, completion, ri, returned = admitted.custody[0]
    if change == "configuration":
        definition = replace(definition, configuration=admitted.parent.plan.identity)
    if change == "code":
        definition = replace(definition, code_sources_sha256="9" * 64)
    if change == "lock":
        definition = replace(definition, dependency_lock_sha256="9" * 64)
    if change in ("supplier-source", "assessment-source"):
        removed = admitted.parent.supply.identity if change == "supplier-source" else admitted.parent.supply.independent_integrity
        definition = replace(definition, sources=tuple(row for row in definition.sources if row != removed))
    if change == "geometry":
        returned = replace(returned, geometry=replace(returned.geometry, object_fingerprint="9" * 64))
    if change == "receipt":
        returned = replace(returned, geometry_receipt=replace(returned.geometry_receipt, object_fingerprint="9" * 64))
    with pytest.raises(ValueError):
        admit(admitted, custody=((name, definition, ci, completion, ri, returned),))


@pytest.mark.parametrize("change", ("heavy", "origin", "no-realization", "wrong-source", "assignment-negative", "geometry-negative"))
def test_changed_materialized_operands_or_independent_negative_refuse(admitted, change):
    kwargs = {}
    if change in ("heavy", "origin", "no-realization"):
        name = "complete-heavy.pdb" if change == "heavy" else "atom-origin-provenance.json"
        asset = admitted.assets[0]
        target = next(row for row in asset.files if row.evidence.relative_path.endswith(name))
        raw = "EXPOSED SUBSTITUTED\n" if change == "heavy" else target.raw_utf8
        if change != "heavy":
            document = json.loads(raw)
            if change == "origin": document["exposed"] = "changed original source"
            else: document.pop("amber_realization")
            raw = json.dumps(document, sort_keys=True)
        changed = p.NativeTextFile(replace(target.evidence, byte_count=len(raw.encode()), sha256=sha256(raw.encode()).hexdigest()), raw)
        kwargs["assets"] = (replace(asset, files=tuple(changed if row == target else row for row in asset.files)),)
    elif change == "wrong-source":
        kwargs["source"] = replace(admitted.source, selection_id="source.exposed.substituted")
    elif change == "assignment-negative":
        rows = tuple((name, A.FALSIFIED if value is A.SATISFIED else value, reasons)
            for name, value, reasons in admitted.integrity.model_dispositions)
        counts, overall = legacy.disposition_census(rows)
        integrity = replace(admitted.integrity, model_dispositions=rows, disposition_counts=counts,
            assignment_disposition=overall, raw_topologies=())
        geometry = replace(admitted.geometry, assignment_integrity=p.identity(integrity))
        kwargs.update(integrity=integrity, geometry=geometry,
            plan=replace(admitted.plan, assignment_integrity=p.identity(integrity), mathematical_geometry=p.identity(geometry)))
    else:
        rows = tuple(replace(row, diagnostic_disposition=A.FALSIFIED, diagnostic=None)
            if row.model_id == admitted.plan.selected_assets[0][0] else row for row in admitted.geometry.models)
        geometry = replace(admitted.geometry, models=rows)
        kwargs.update(geometry=geometry, plan=replace(admitted.plan, mathematical_geometry=p.identity(geometry)))
    with pytest.raises(ValueError):
        admit(admitted, **kwargs)


@pytest.mark.parametrize("change", ("missing-supplier", "missing-assessment", "wrong-assessment", "missing-origin", "wrong-parent-bytes", "original-revision"))
def test_successor_plan_requires_complete_exact_supplier_operands(admitted, change):
    changes = {}
    if change == "missing-supplier": changes["geometry_supplies"] = ()
    if change == "missing-assessment": changes["geometry_assessments"] = ()
    if change == "wrong-assessment": changes["geometry_assessments"] = (replace(admitted.parent.assessment, product_id="assessment.changed"),)
    if change == "missing-origin": changes["geometry_inputs"] = ((admitted.parent.supply.identity, admitted.parent_files[1:]),)
    if change == "wrong-parent-bytes":
        row = admitted.parent_files[1]
        raw = row.raw_utf8 + "SUBSTITUTED\n"
        changed = p.NativeTextFile(replace(row.evidence, byte_count=len(raw.encode()), sha256=sha256(raw.encode()).hexdigest()), raw)
        changes["geometry_inputs"] = ((admitted.parent.supply.identity, (admitted.parent_files[0], changed)),)
    if change == "original-revision": changes["assignment_integrity"] = replace(admitted.plan.assignment_integrity, object_version="1.0.0")
    with pytest.raises(ValueError):
        admit(admitted, plan=replace(admitted.plan, **changes))


def test_original_revision_decodes_without_silent_successor_selection(oldplan):
    source, preparation, assets = exposed_preparation(A.NOT_ATTEMPTED)
    integrity = legacy.assess(source, preparation, assets, (), (), {})
    geometry = legacy_geometry.assess_geometry(source, preparation, assets, integrity)
    old_bytes = oldplan.canonical_bytes()
    assert type(decode_plan(old_bytes.decode())) is c.ChemicalForcePlan
    assert decode_assessments(integrity.canonical_bytes().decode(), geometry.canonical_bytes().decode()) == (integrity, geometry)
    assert oldplan.canonical_bytes() == old_bytes
    successor = serialized.assess(source, preparation, assets, (), (), {})
    with pytest.raises(ValueError):
        decode_assessments(successor.canonical_bytes().decode(), geometry.canonical_bytes().decode())


def test_invocation_preserves_whole_control_roster_and_explicit_new_revision(admitted):
    plan = admitted.plan
    parent = admitted.parent.supply.definition.parent_contact
    sources = (plan.source, plan.preparation, plan.assignment_integrity, plan.mathematical_geometry,
        *(row[1] for row in plan.selected_assets), *(identity for row in plan.preparation_custody for identity in row[1:]))
    selected = control_definitions(plan, parent, sources=sources, input_materialization_ids=parent.input_materialization_ids)
    raw = build_invocation(plan, admitted.source, admitted.preparation, admitted.integrity, admitted.geometry,
        admitted.assets, admitted.custody, selected, source_root="/tmp/exposed-caller-source")
    document = json.loads(raw)
    assert len(document["definitions"]) == 121
    assert decode_plan(document["plan"]) == plan
    assert json.loads(document["plan"])["version"] == "1.1.0"
    assert sha256(canonical_json_bytes(plan.preparation_plan.code_sources)).hexdigest() == admitted.custody[0][1].code_sources_sha256
