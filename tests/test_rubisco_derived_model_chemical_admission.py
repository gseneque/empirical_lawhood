# SPDX-License-Identifier: MPL-2.0
"""Complete exposed derived-supplier conformance; zero molecular acquisition.

Every native-shaped object/call here is a disclosed software fixture. The full
5048-residue genotype and two reordered waters test the actual producer/readers,
not chemical completeness, qualification, or a new physical independent unit.
"""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import parameter_audit as producer
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import preparation_integrity as legacy
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import physical_preparation_geometry as geometry
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import serialized_preparation_assessment as historical
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableUnitReturn, geometry_keys
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import definitions as preparation_definitions
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_contracts as c
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_invocation import build_invocation
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_preparation_admission import decode_plan, validate_operands
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_roster import definitions as control_definitions
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.derived_model_admission import (
    DerivedChemicalForcePlan, DerivedModelSupply, INDEPENDENT_OWNERS,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.science import hardware_from_stdout
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from tests.test_rubisco_geometry_reuse import fresh, original as original  # noqa: F401
from tests.test_rubisco_preparation_integrity import amber_text, exposed_preparation
from tests.test_rubisco_serialized_coordinate_assessment import serialized_exposed, topology


PRODUCING_ROOT = Path(p.__file__).resolve().parents[5]


def document(value):
    return json.loads(value.canonical_bytes())


def text_file(root, relative, raw):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw)
    data = path.read_bytes()
    return p.NativeTextFile(p.FileEvidence(relative, len(data), sha256(data).hexdigest()), data.decode())


def json_file(root, relative, value):
    return text_file(root, relative, json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def binding(root, row):
    return dict(path=str(root / row.evidence.relative_path), bytes=row.evidence.byte_count, sha256=row.evidence.sha256)


class ExposedAtom:
    """Hashable native-shaped scalar object; no imported backend or model."""


def native_shape(census, rows):
    atoms, residues = [], []
    for index, (name, atom_name, number) in enumerate(zip(census["residue_names"],
            census["atom_names"], census["atomic_numbers"], strict=True)):
        residue = SimpleNamespace(idx=index, name=name, number=index, chain="", atoms=[])
        atom = ExposedAtom()
        atom.idx, atom.name, atom.atomic_number, atom.residue = index, atom_name, number, residue
        atom.type, atom.charge, atom.mass, atom.rmin, atom.epsilon = "C", 0., 12., 0., 0.
        residue.atoms.append(atom)
        residues.append(residue)
        atoms.append(atom)
    def term(indices, coefficients, **flags):
        return SimpleNamespace(**{f"atom{index+1}": atoms[value] for index, value in enumerate(indices)},
            type=SimpleNamespace(**coefficients), **flags)
    return SimpleNamespace(atoms=atoms, residues=residues,
        bonds=[term((0, 1), dict(k=0., req=1.379)), term((2, 3), dict(k=0., req=1.379))],
        angles=[term((0, 1, 2), dict(k=66., theteq=0.))],
        dihedrals=[term((0, 1, 2, 3), dict(phi_k=-1.7, phase=0., per=2., scee=0., scnb=0.),
            ignore_end=True, improper=True)], parm_data=rows)


COLD_READER = r'''
import importlib.abc,json,sys
from dataclasses import asdict
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace
class NoProducer(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in ('numpy','scipy','openmm','parmed','pdbfixer') or fullname.endswith('.parameter_audit'):
            raise AssertionError('producer/backend entered independent reader: '+fullname)
sys.meta_path.insert(0,NoProducer())
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import amber_parameters as a,serialized_coordinate_assessment as s,contracts as p
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
root=Path(sys.argv[1]); selected=json.loads((root/'reader-input.json').read_bytes())
model=decode_canonical_bytes(selected['model'].encode(),p.PreparedModel,maximum_bytes=None)
atoms=tuple(SimpleNamespace(**(row|{'occupancy':D(row['occupancy']),'xyz_angstrom':tuple(D(x) for x in row['xyz_angstrom'])})) for row in selected['atoms'])
chains=tuple(SimpleNamespace(**row) for row in selected['chains'])
raw=(root/'raw/model.prmtop').read_text(); restart=(root/'raw/model.inpcrd').read_text(); heavy=(root/'raw/complete-heavy.pdb').read_text()
origin=json.loads((root/'derived/atom-origin-provenance.json').read_bytes()); audit=json.loads((root/'derived/complete-assigned-parameters.json').read_bytes())
census=a.validate_assignment_supported_inactive14(raw,audit)
proof=s.validate_origins_from_coordinates(model,census,origin,heavy,restart,atoms,chains,set())
result=s.diagnose_geometry_supported_inactive14(raw,restart,heavy,origin)
(root/'geometry-diagnostic.json').write_bytes(result.diagnostic.canonical_bytes())
(root/'independent-result.json').write_text(json.dumps(dict(complete_parameter_term_census=census['term_census'],inactive14_support=asdict(census['inactive14_support']),coordinate_origin_validation=asdict(proof),geometry_method=json.loads(result.method.canonical_bytes())),sort_keys=True))
assert not any(name.split('.')[0] in ('numpy','scipy','openmm','parmed','pdbfixer') or name.endswith('.parameter_audit') for name in sys.modules)
'''


COLD_CONSUMER = r'''
import importlib.abc,json,sys
from pathlib import Path
from types import SimpleNamespace
class NoBackend(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in ('numpy','scipy','openmm','parmed','pdbfixer') or fullname.endswith('.parameter_audit'):
            raise AssertionError('native producer/backend entered consumer proof: '+fullname)
sys.meta_path.insert(0,NoBackend())
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_native_entry as entry,control_preparation_admission as admission
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import science as preparation_science
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
root=Path(sys.argv[1]);data=json.loads((root/'consumer-invocation.json').read_bytes())
first=decode_canonical_bytes(data['definitions'][0].encode(),NativeSubworkDefinition,maximum_bytes=None)
observed={'admission_count':0,'roster_count':0}
original=admission.validate_operands
def validate(*args):
    result=original(*args);observed['admission_count']+=1
    assert args[-1][0][-1].preparation_succeeded is False
    return result
admission.validate_operands=validate
def stop_before_stock(*args):
    raise RuntimeError('EXPOSED_STOP_AFTER_ACTUAL_CHILD_ADMISSION')
preparation_science.validate_stock=stop_before_stock
def freeze(roster,*,definitions):
    observed['roster_count']=len(definitions)
progress=SimpleNamespace(parent_contact=first.parent_contact,freeze_roster=freeze)
try:
    entry._authenticated_child(progress,data)
except RuntimeError as error:
    assert str(error)=='EXPOSED_STOP_AFTER_ACTUAL_CHILD_ADMISSION'
else:
    raise AssertionError('consumer unexpectedly entered stock/backend')
assert observed=={'admission_count':1,'roster_count':0}
assert not any(name.split('.')[0] in ('numpy','scipy','openmm','parmed','pdbfixer') or name.endswith('.parameter_audit') for name in sys.modules)
(root/'consumer-admission.json').write_text(json.dumps(observed,sort_keys=True))
'''


@pytest.fixture(scope="module")
def derived(original, tmp_path_factory):
    root = tmp_path_factory.mktemp("complete-derived-chemical-exposed")
    args = serialized_exposed()
    rows = topology(args[1])
    # Zero-LJ native-shaped fixture removes no atoms, terms, or source rows.
    # It supplies no physical potential: the check is protocol/data conformance.
    rows["LENNARD_JONES_ACOEF"] = [D(0)] * len(rows["LENNARD_JONES_ACOEF"])
    rows["LENNARD_JONES_BCOEF"] = [D(0)] * len(rows["LENNARD_JONES_BCOEF"])
    shape = native_shape(args[1], rows)
    origin = deepcopy(args[2])
    origin.pop("amber_realization")
    old_origin = json_file(root, "raw/atom-origin-provenance.json", origin)
    raw = {"model.prmtop": text_file(root, "raw/model.prmtop", amber_text(rows)),
        "model.inpcrd": text_file(root, "raw/model.inpcrd", args[4]),
        "complete-heavy.pdb": text_file(root, "raw/complete-heavy.pdb", args[3]),
        "atom-origin-provenance.json": old_origin}
    origin["amber_realization"] = producer.realized_atom_origins_from_coordinates(shape, origin, args[3], args[4])
    derived_origin = json_file(root, "derived/atom-origin-provenance.json", origin)
    audit = json_file(root, "derived/complete-assigned-parameters.json", producer.assigned_parameter_inventory(shape))
    json_file(root, "reader-input.json", dict(model=args[0].canonical_bytes().decode(),
        atoms=[{key: [str(x) for x in value] if key == "xyz_angstrom" else str(value) if isinstance(value, D) else value
            for key, value in vars(atom).items()} for atom in args[5]], chains=[vars(chain) for chain in args[6]]))
    environment = dict(os.environ, PYTHONPATH=str(PRODUCING_ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    cold = subprocess.run([sys.executable, "-c", COLD_READER, str(root)], env=environment, capture_output=True, text=True)
    assert cold.returncode == 0, cold.stderr
    result = json.loads((root / "independent-result.json").read_bytes())
    diagnostic_text = text_file(root, "retained/geometry-diagnostic.json", (root / "geometry-diagnostic.json").read_text())
    diagnostic = decode_canonical_bytes(diagnostic_text.raw_utf8.encode(), geometry.GeometryDiagnostic, maximum_bytes=None)
    assert diagnostic.atom_count == diagnostic.heavy_atom_count == 5050
    assert result["coordinate_origin_validation"]["chemical_residue_map"] == [["Z", 1, 5049], ["Z", 2, 5048]]
    source, recipe = fresh(original)
    selected = "model.gp.wt.m1.joint-01.scoped-kcx-aliases"
    recipe = replace(recipe, attempted_model_ids=(selected,))
    _, old_product, old_assets = exposed_preparation(A.NOT_ATTEMPTED)
    ordinal = tuple(row.model_id for row in old_product.models).index(selected)
    original_files = tuple(sorted(raw.values(), key=lambda file: file.evidence.relative_path))
    old_asset = replace(old_assets[ordinal], source=p.identity(source), files=original_files)
    asset = replace(old_asset, product_id="product.exposed.derived-assets", files=tuple(sorted(
        (raw["model.prmtop"], raw["model.inpcrd"], raw["complete-heavy.pdb"], derived_origin, audit),
        key=lambda file: file.evidence.relative_path)))
    parent = original.supply.definition.parent_contact
    definitions = preparation_definitions(recipe, parent, sources=(recipe.source, recipe.nomination,
        recipe.inventory, recipe.coordinates, original.supply.identity, original.supply.independent_integrity),
        input_materialization_ids=parent.input_materialization_ids)
    definition = next(row for row in definitions if row.subwork_id == selected)
    call_ids = tuple(selected + ".call." + str(index).zfill(6) for index in (1, 2))
    call_definitions = tuple(replace(definition, subwork_id=name) for name in call_ids)
    calls = tuple(p.NativeCall(name, None, selected, "EXPOSED_SOFTWARE_NATIVE_SHAPE_ONLY", "{}", "{}",
        D(0), D(0), "COMPLETED", None, ()) for name in call_ids)
    model = replace(old_product.models[ordinal], disposition=A.UNEVALUABLE,
        reason_codes=("EXPOSED_ORIGINAL_POSITIONAL_POSTPROCESS_FAILURE",), assets=p.identity(old_asset),
        files=tuple(file.evidence for file in original_files), native_call_ids=call_ids)
    preparation = replace(old_product, source=p.identity(source), structural_inventory=source.structural_inventory,
        structural_coordinates=source.structural_coordinates, nomination=source.nomination,
        models=tuple(model if index == ordinal else value for index, value in enumerate(old_product.models)),
        native_calls=calls, files=model.files)
    dispositions = tuple((value.model_id, value.disposition, value.reason_codes) for value in preparation.models)
    counts, overall = legacy.disposition_census(dispositions)
    integrity = historical.SerializedPreparationIntegrity("assessment.exposed.original.assignment", p.identity(source),
        p.identity(preparation), historical.ASSIGNMENT_METHOD, dispositions, counts, overall, 2, ())
    geometry_rows = tuple(geometry.ModelGeometry(value.model_id, value.assets, value.disposition,
        A.REFUSED if value.model_id == selected else A.NOT_ATTEMPTED, ("EXPOSED_HISTORICAL_READER_FAILURE",), (), None)
        for value in preparation.models)
    historical_geometry = historical.SerializedPreparationGeometry("assessment.exposed.original.geometry",
        p.identity(source), p.identity(preparation), p.identity(integrity), geometry_rows)
    completion = replace(original.supply.completion, definition=definition.identity,
        operational_status=OperationalStatus.FAILED, reason_codes=("EXPOSED_POSTPROCESS_FAILURE",),
        output_ids=tuple(sorted(value.output_id for value in definition.outputs)))
    returned = DurableUnitReturn(selected, recipe.identity, original.supply.definition.identity,
        original.supply.geometry_receipt, True, False, ("EXPOSED_POSITIONAL_FAILURE",), model.files,
        tuple(value.identity for value in call_definitions), "exposed original positional origin error")
    ci, ri = ObjectIdentity.from_record("completion.exposed.original", completion), ObjectIdentity.from_record("return.exposed.original", returned)
    custody = ((selected, definition, ci, completion, ri, returned),)
    history = dict(assignment_dispositions=[[name, value.value, list(reasons)] for name, value, reasons in dispositions],
        full36states={name: NativeSubworkState.COMPLETED.value if name == selected else NativeSubworkState.NOT_ENTERED.value
            for name in sorted((*["geometry." + ".".join(key) for key in geometry_keys()], *[c.model_id(key) for key in p.model_roster()]))},
        actual_selected_model_custody=[dict(model_id=selected, state="COMPLETED", definition=document(definition), completion_identity=document(ci),
            completion=document(completion), return_identity=document(ri), returned=document(returned))], assessment_products={})
    for name, value in (("preparation-projection", preparation), ("assignment-integrity", integrity), ("physical-geometry", historical_geometry)):
        history["assessment_products"][name] = binding(root, text_file(root, "historical/" + name + ".json", value.canonical_bytes().decode()))
    historical_text = json_file(root, "retained/historical-readout.json", history)
    prefix = PRODUCING_ROOT
    source_rows = [dict(relative_path=name, frozen=dict(path=str(prefix / name), bytes=(prefix / name).stat().st_size,
        sha256=sha256((prefix / name).read_bytes()).hexdigest())) for name in INDEPENDENT_OWNERS]
    producer_manifest = json_file(root, "retained/producer-source.json", dict(schema="el.rubisco.scoped-wt.additive-postprocessing-source.v1",
        members=[dict(relative_path="parameter_audit.py", sha256=sha256(Path(producer.__file__).read_bytes()).hexdigest())]))
    independent_manifest = json_file(root, "retained/independent-source.json", dict(schema="el.rubisco.scoped-wt.independent-composition-source.v1",
        members=source_rows, derived_producer_source_manifest=binding(root, producer_manifest)))
    histories = dict(original_full24_assignment_dispositions=history["assignment_dispositions"], original_full36_unit_states=history["full36states"])
    produced = json_file(root, "retained/postprocessing.json", dict(schema="el.rubisco.scoped-wt.derived-postprocessing.v1",
        derived_postprocessing="PRODUCTS_PRODUCED", error=None, new_postprocess_load_count=1,
        molecular_acquisition_count=0, native_solver_count=0, tleap_count=0,
        historical_original_unit_preparation_success=False, historical_original_assignment_disposition="UNEVALUABLE",
        historical_original_known_model_native_call_count=2, historical_original_unit_operational_status="FAILED",
        original_readout=binding(root, historical_text), source_manifest=binding(root, producer_manifest),
        original_raw_operands={name: binding(root, value) for name, value in raw.items()},
        derived_origin=binding(root, derived_origin), derived_parameter_audit=binding(root, audit), **histories))
    common = dict(schema="el.rubisco.scoped-wt.derived-independent-phase.v1", phase_state="COMPLETED", assessment_error=None,
        native_calls=0, producer_reexecution=False, physical_independent_units=0, qualification=False, matched_I95M_admission=False,
        original_unit_preparation_success=False, original_readout=binding(root, historical_text),
        derived_products=binding(root, produced), source_manifest=binding(root, independent_manifest),
        historical_producer_source_manifest=binding(root, producer_manifest),
        original_raw_operands={name: binding(root, value) for name, value in raw.items()},
        derived_origin=binding(root, derived_origin), derived_parameter_audit=binding(root, audit), **histories)
    assignment = json_file(root, "retained/assignment.json", common | dict(phase="assignment-origin", result={
        name: result[name] for name in ("complete_parameter_term_census", "inactive14_support", "coordinate_origin_validation")}))
    geometry_readout = json_file(root, "retained/geometry.json", common | dict(phase="geometry", result=dict(
        method=result["geometry_method"], diagnostic=binding(root, diagnostic_text), independent_assignment_origin_parent=binding(root, assignment),
        hard_geometry_disposition=diagnostic.hard_geometry_disposition.value, pair_counts=[list(value) for value in diagnostic.pair_counts],
        bonded_counts=[list(value) for value in diagnostic.bonded_counts])))
    supply = DerivedModelSupply("supply.exposed.derived", selected, p.identity(asset), historical_text, produced, assignment,
        geometry_readout, producer_manifest, independent_manifest, diagnostic_text)
    plan = DerivedChemicalForcePlan(plan_id="config.exposed.derived-chemical", source=p.identity(source),
        preparation=p.identity(preparation), assignment_integrity=p.identity(integrity), mathematical_geometry=p.identity(historical_geometry),
        selected_assets=((selected, p.identity(asset)),), preparation_custody=((selected, definition.identity, ci, ri),),
        hardware=hardware_from_stdout(b"GPU-exposed, Exposed device, 0, 0000:00:00.0, 1, 0\n"),
        workdir=p.NATIVE_WORK_ROOT + "/exposed-derived-chemical-never-entered", interpreter_path=sys.executable, interpreter_sha256="1" * 64,
        engine_inventory_sha256=source.engine_inventory_sha256, hardware_inspector_path="/tmp/exposed-hardware", hardware_inspector_sha256="2" * 64,
        code_sources=tuple(sorted((row["relative_path"], row["frozen"]["sha256"]) for row in source_rows)), dependency_lock_sha256="3" * 64,
        preparation_plan=recipe, derived_supplies=(supply,))
    return SimpleNamespace(root=root, plan=plan, supply=supply, source=source, preparation=preparation, integrity=integrity,
        geometry=historical_geometry, assets=(asset,), custody=custody, parent=parent, diagnostic=diagnostic)


def admit(row, **changes):
    return validate_operands(**({name: getattr(row, name) for name in
        ("plan", "source", "preparation", "integrity", "geometry", "assets", "custody")} | changes))


def test_complete_producer_cold_readback_actual_consumer_preserves_original_failure(derived):
    row = derived
    if os.environ.get("EL_DERIVED_TEST_SOURCE_ROOT"):
        assert PRODUCING_ROOT == Path(os.environ["EL_DERIVED_TEST_SOURCE_ROOT"]).resolve()
    before = tuple(value.canonical_bytes() for value in (row.preparation, row.integrity, row.geometry, row.custody[0][-1]))
    assert admit(row) == row.plan
    assert decode_plan(row.plan.canonical_bytes().decode()) == row.plan
    sources = (row.plan.source, row.plan.preparation, row.plan.assignment_integrity, row.plan.mathematical_geometry,
        row.plan.preparation_plan.identity, row.supply.identity, *(value[1] for value in row.plan.selected_assets),
        *(identity for value in row.plan.preparation_custody for identity in value[1:]))
    selected = control_definitions(row.plan, row.parent, sources=sources, input_materialization_ids=row.parent.input_materialization_ids)
    raw = build_invocation(row.plan, row.source, row.preparation, row.integrity, row.geometry, row.assets, row.custody,
        selected, source_root=str(PRODUCING_ROOT))
    parsed = json.loads(raw)
    text_file(row.root, "consumer-invocation.json", raw.decode())
    environment = dict(os.environ, PYTHONPATH=str(PRODUCING_ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    cold = subprocess.run([sys.executable, "-c", COLD_CONSUMER, str(row.root)], env=environment, capture_output=True, text=True)
    assert cold.returncode == 0, cold.stderr
    assert json.loads((row.root / "consumer-admission.json").read_bytes()) == dict(admission_count=1, roster_count=0)
    assert decode_plan(parsed["plan"]) == row.plan and len(parsed["definitions"]) == 121
    assert row.custody[0][-1].preparation_succeeded is False
    assert before == tuple(value.canonical_bytes() for value in (row.preparation, row.integrity, row.geometry, row.custody[0][-1]))
    assert len(row.preparation.models) == len(row.integrity.model_dispositions) == 24
    assert len(json.loads(row.supply.historical_readout.raw_utf8)["full36states"]) == 36
    assert len(row.plan.nve_census) == 96 and row.plan.physical_independent_units == 0
    assert row.diagnostic.geometry_adequacy is row.diagnostic.force_adequacy is A.UNEVALUABLE


@pytest.mark.parametrize("change", ("missing-phase", "negative-phase", "wrong-source", "wrong-parent", "thin-history", "wrong-method"))
def test_derived_supplier_missing_negative_and_rehashed_source_evidence_refuses(derived, change):
    supply = derived.supply
    data = json.loads(supply.assignment_readout.raw_utf8)
    if change == "missing-phase": data.pop("result")
    if change == "negative-phase": data.update(phase_state="KNOWN_ADVERSE_RETURN", assessment_error="exposed failure")
    if change == "wrong-source": data["source_manifest"]["sha256"] = "9" * 64
    if change == "wrong-parent": data["historical_producer_source_manifest"]["sha256"] = "9" * 64
    if change == "thin-history": data["original_full24_assignment_dispositions"].pop()
    if change == "wrong-method": data["result"]["coordinate_origin_validation"]["method"]["object_version"] = "1.0.0"
    changed = json_file(derived.root, "negative/" + change + ".json", data)
    with pytest.raises((ValueError, KeyError)):
        replace(supply, assignment_readout=changed)


@pytest.mark.parametrize("change", ("missing-asset", "rehashed-raw", "relabel-original", "missing-supplier", "wrong-code", "wrong-return"))
def test_actual_derived_consumer_preserves_full_raw_original_and_source_guards(derived, change):
    row = derived
    changes = {}
    if change == "missing-asset": changes["assets"] = (replace(row.assets[0], files=row.assets[0].files[:-1]),)
    if change == "rehashed-raw":
        asset = row.assets[0]
        old = next(value for value in asset.files if value.evidence.relative_path.endswith("model.inpcrd"))
        modified = text_file(row.root, "negative/changed/model.inpcrd", old.raw_utf8 + "REHASHED SUBSTITUTION\n")
        changes["assets"] = (replace(asset, files=tuple(sorted((modified if value == old else value for value in asset.files), key=lambda value: value.evidence.relative_path))),)
    if change == "relabel-original":
        changes["preparation"] = replace(row.preparation, product_id="product.exposed.relabelled")
    if change == "missing-supplier":
        with pytest.raises(ValueError): replace(row.plan, derived_supplies=())
        return
    if change == "wrong-code":
        with pytest.raises(ValueError): replace(row.plan, code_sources=tuple((name, "9" * 64) for name, _ in row.plan.code_sources))
        return
    if change == "wrong-return":
        name, definition, ci, completion, ri, returned = row.custody[0]
        changed = replace(returned, preparation_succeeded=True, error_text=None)
        changes["custody"] = ((name, definition, ci, completion, ObjectIdentity.from_record(ri.object_id, changed), changed),)
    with pytest.raises(ValueError): admit(row, **changes)


def test_complete_negative_geometry_remains_valid_evidence_and_refuses_chemical_entry(derived):
    row = derived
    negative = replace(row.diagnostic, coincident_unwrapped_pair_count=1, hard_geometry_disposition=A.FALSIFIED)
    diagnostic = text_file(row.root, "negative/geometry-diagnostic.json", negative.canonical_bytes().decode())
    value = json.loads(row.supply.geometry_readout.raw_utf8)
    value["result"].update(diagnostic=binding(row.root, diagnostic), hard_geometry_disposition="FALSIFIED")
    phase = json_file(row.root, "negative/geometry-result.json", value)
    supply = replace(row.supply, geometry_diagnostic=diagnostic, geometry_readout=phase)
    plan = replace(row.plan, derived_supplies=(supply,))
    assert supply.geometry_diagnostic == diagnostic
    with pytest.raises(ValueError, match="adverse independent hard geometry"):
        admit(row, plan=plan)
    assert row.custody[0][-1].preparation_succeeded is False


@pytest.mark.parametrize("omitted", ("derived", "original-recipe"))
def test_actual_roster_requires_derived_and_original_recipe_as_ordinary_inputs(derived, omitted):
    row = derived
    sources = (row.plan.source, row.plan.preparation, row.plan.assignment_integrity, row.plan.mathematical_geometry,
        row.plan.preparation_plan.identity, row.supply.identity, *(value[1] for value in row.plan.selected_assets),
        *(identity for value in row.plan.preparation_custody for identity in value[1:]))
    missing = row.supply.identity if omitted == "derived" else row.plan.preparation_plan.identity
    with pytest.raises(ValueError, match="omits genuine selected"):
        control_definitions(row.plan, row.parent, sources=tuple(value for value in sources if value != missing),
            input_materialization_ids=row.parent.input_materialization_ids)
