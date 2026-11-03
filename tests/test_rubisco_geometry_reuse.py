# SPDX-License-Identifier: MPL-2.0
"""Exposed real receipt/archive controls; zero molecular preparation or entry."""

from dataclasses import replace
from hashlib import sha256
import gzip
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as c
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurablePreparationPlan, DurableUnitReturn
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import DurableCallLedger, complete_unit
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import definitions, freeze, census
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_reuse import (
    GeometryReusePlan, GeometryReuseSupply, invocation_bytes, materialize_geometry_inputs, validate_reuse_assessment,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.preamber_geometry_integrity import PreAmberGeometryIntegrity
from empirical_lawhood.infrastructure.native_subwork_ipc import NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from tests.runtime_platform.test_native_subwork import _plane, _store, _process_context
from tests.test_rubisco_preparation_integrity import exposed_preparation
from tests.rubisco_nomination_fixture import nominee


@pytest.fixture(scope="module")
def original(tmp_path_factory):
    """Actual exposed artifact-plane receipt, not a biological/raw-source claim."""
    tmp_path = tmp_path_factory.mktemp("original-geometry-reuse-custody")
    source, _, _ = exposed_preparation()
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure.contracts import StructuralInventory, AssemblyCoordinates
    _, nomination = nominee()
    inventory = StructuralInventory("inventory.exposed", ObjectIdentity("source.exposed.structure",
        "empirical-lawhood/rubisco-insilico-structure/source", "1.0.0", "7" * 64),
        c.identity(nomination), (), (), (), (), (), ())
    coordinates = AssemblyCoordinates("coordinates.exposed", c.identity(inventory),
        tuple((name, sha256(b"EXPOSED").hexdigest(), "EXPOSED")
              for name in ("1bwv-assembly1.cif", "3zxw-assembly1.cif")))
    source = replace(source, structural_inventory=c.identity(inventory),
        structural_coordinates=c.identity(coordinates), nomination=c.identity(nomination))
    root = tmp_path / "working"
    root.mkdir()
    plan = DurablePreparationPlan("plan.exposed.original", c.identity(source), source.nomination,
        source.structural_inventory, source.structural_coordinates, source.native_workdir,
        sys.executable, "1" * 64, sys.executable, "1" * 64, source.engine_inventory_sha256,
        (("src/exposed.py", "2" * 64),), "3" * 64,
        attempted_geometry_ids=("geometry.gp.wt.m1.joint-01",), attempted_model_ids=())
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        plan.dependency_lock_sha256, plan.code_sources, sha256(canonical_json_bytes(plan.code_sources)).hexdigest(), "6" * 40, False)
    plane = _plane(tmp_path / "custody")
    manifests = []
    for record, name in ((source, source.selection_id), (plan, plan.plan_id),
            (nomination, c.identity(nomination).object_id), (inventory, c.identity(inventory).object_id),
            (coordinates, c.identity(coordinates).object_id), (provenance, provenance.identity.object_id)):
        result = plane.write(ArtifactWriteRequest(name, "inputs/" + name + ".json", record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.inputs", "inputs",
            record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(decode_artifact_manifest(plane.root.resolve(
            result.materialization.relative_path + ".manifest.json", for_write=False).read_bytes()))
    parent = NativeEffectContact("exposed.original", "native.parent", "exposed.original.native.parent.attempt-001",
        ObjectIdentity("plan.exposed", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "4" * 64),
        ObjectIdentity("native.parent", "empirical-lawhood/runtime/execution-task", "1.0.0", "5" * 64),
        "6" * 40, tuple(sorted(row.materialization.materialization_id for row in manifests)), ())
    store = _store(plane, parent, tuple(manifests))
    store.parent_contacts.begin(parent)
    selected = definitions(plan, parent,
        sources=(plan.source, plan.nomination, plan.inventory, plan.coordinates, provenance.identity),
        input_materialization_ids=parent.input_materialization_ids)
    context = _process_context(store, selected[0], tuple(manifests))
    service = NativeSubworkPipeService(store, context, tmp_path)
    class Connection:
        def send(self, message):
            if type(message) is NativeSubworkRequest:
                service.handle(message, self)
            else:
                self.reply = message
        def recv(self):
            return self.reply
    progress = PipeNativeSubworkProgress(Connection())
    freeze(progress, selected)
    definition = next(row for row in selected if row.subwork_id == plan.attempted_geometry_ids[0])
    entry = progress.begin(definition)
    progress.contact(entry)
    directory = root / definition.subwork_id
    directory.mkdir()
    files = {"complete-heavy.pdb": b"EXPOSED ORIGINAL PDB, NOT A MOLECULE\n",
        "atom-origin-provenance.json": b'{"exposed":"original source bytes"}\n',
        "z-retained-complete-native.bin": bytes(range(256)) * 8193}
    for name, raw in files.items():
        (directory / name).write_bytes(raw)
    complete_unit(progress, plan, entry, root, directory, DurableCallLedger(progress, plan, root, entry, directory), succeeded=True)
    inspection = progress.recover(definition)
    prefix = inspection.receipt.task_id
    archive_root = "runs/" + parent.run_id + "/native-subwork/" + prefix.removeprefix("native-subwork.")
    def manifest(name):
        return decode_artifact_manifest(plane.root.resolve(archive_root + "/" + name + ".manifest.json", for_write=False).read_bytes())
    def output(name, kind):
        raw = b"".join(progress.iter_completed_output(definition, name))
        return decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
    returned = output("unit.return", DurableUnitReturn)
    retained = output("files.census", DurableRawFileCensus)
    by_name = {Path(row.relative_path).name: row for row in retained.files}
    assessment = PreAmberGeometryIntegrity("assessment.exposed.original", plan.source, definition.identity,
        ObjectIdentity.from_record(prefix + ".completion", inspection.completion),
        ObjectIdentity.from_record(inspection.receipt.receipt_id, inspection.receipt),
        next(row for row in source.constructs if row.construct_id == "gp.wt.m1"), "joint-01",
        by_name["complete-heavy.pdb"], by_name["atom-origin-provenance.json"],
        5048, 5048, 5048, 16, 5032, 16, 0, 0, 0)
    supply = GeometryReuseSupply("supply.exposed.original", source, plan, definition, inspection.begin,
        inspection.contact, inspection.completion, inspection.receipt, returned, retained,
        tuple(manifest(name + ".json") for name in ("definition", "begin", "contact")),
        tuple(manifest("outputs/" + name) for name in ("files.census", "files.raw", "unit.return")),
        manifest("completion.json"), ObjectIdentity.from_record(assessment.product_id, assessment))
    archive = plane.root.resolve(supply.archive_evidence.relative_path, for_write=False)
    yield SimpleNamespace(source=source, plan=plan, selected=selected, progress=progress,
        supply=supply, assessment=assessment, archive=archive, files=files, root=root,
        nomination=nomination, inventory=inventory, coordinates=coordinates)
    for port in context.input_ports:
        port.close()


def fresh(original):
    source = replace(original.source, native_workdir=c.NATIVE_WORK_ROOT + "/exposed-model-successor/native-work")
    plan = GeometryReusePlan(plan_id="plan.exposed.model-successor", source=c.identity(source),
        nomination=source.nomination, inventory=source.structural_inventory, coordinates=source.structural_coordinates,
        workdir=source.native_workdir, interpreter_path=sys.executable, interpreter_sha256="1" * 64,
        tleap_path=sys.executable, tleap_sha256="1" * 64, engine_inventory_sha256=source.engine_inventory_sha256,
        code_sources=original.plan.code_sources, dependency_lock_sha256=original.plan.dependency_lock_sha256,
        attempted_geometry_ids=(), attempted_model_ids=tuple("model.gp.wt.m1.joint-01." + name for name in c.PARAMETER_VIEWS),
        geometry_supplies=(original.supply.identity,), reused_geometry_ids=(original.supply.definition.subwork_id,),
        archive_inputs=((original.supply.identity, str(Path(source.native_workdir).parent / "inputs/original-geometry.archive")),))
    return source, plan


def test_exact_original_receipt_roundtrip_and_full36_new_attempt_denominator(original):
    supply = original.supply
    raw = supply.canonical_bytes()
    assert decode_canonical_bytes(raw, GeometryReuseSupply, maximum_bytes=len(raw)) == supply
    source, plan = fresh(original)
    raw = plan.canonical_bytes()
    assert decode_canonical_bytes(raw, GeometryReusePlan, maximum_bytes=len(raw)) == plan
    validate_reuse_assessment(plan, source, supply, original.assessment)
    assert plan.attempted_geometry_ids == () and len(plan.attempted_model_ids) == 2
    assert len(plan.geometry_census) == 12 and len(plan.model_census) == 24
    assert supply.definition.configuration == original.plan.identity
    assert supply.geometry_receipt.object_id == supply.receipt.receipt_id
    assert len(census(original.progress, original.plan, original.selected).states) == 36


@pytest.mark.parametrize("change", (None, "missing-slot", "wrong-owner", "wrong-code", "wrong-lock", "wrong-input", "missing-assessment"))
def test_full_invocation_exact_roundtrip_and_owner_contracts_before_contact(original, monkeypatch, change):
    import json
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import science
    source, plan = fresh(original)
    monkeypatch.setattr(science, "validate_source", lambda *args: source)
    parent = original.supply.definition.parent_contact
    supplies, assessments = (original.supply,), (original.assessment,)
    sources = (plan.source, plan.nomination, plan.inventory, plan.coordinates,
               original.supply.identity, original.supply.independent_integrity)
    selected = definitions(plan, parent, sources=sources, input_materialization_ids=parent.input_materialization_ids)
    if change == "missing-slot": selected = selected[:-1]
    if change == "wrong-owner": selected = (replace(selected[0], operation_id="foreign.owner"), *selected[1:])
    if change == "wrong-code": selected = (replace(selected[0], code_sources_sha256="9" * 64), *selected[1:])
    if change == "wrong-lock": selected = (replace(selected[0], dependency_lock_sha256="9" * 64), *selected[1:])
    if change == "wrong-input": selected = (replace(selected[0], input_materialization_ids=parent.input_materialization_ids[:-1]), *selected[1:])
    if change == "missing-assessment": assessments = ()
    def invoke():
        return invocation_bytes(plan, source, original.nomination, original.inventory, original.coordinates,
            selected, "/exposed/selected/source", supplies, assessments)
    if change is not None:
        with pytest.raises(ValueError):
            invoke()
    else:
        result = json.loads(invoke())
        assert len(result["definitions"]) == 37 and len(result["supplies"]) == len(result["assessments"]) == 1
        assert result["plan"] == plan.canonical_bytes().decode()
        assert result["supplies"][0] == original.supply.canonical_bytes().decode()


@pytest.mark.parametrize("change", ("receipt-attempt", "receipt-id", "receipt-input", "source", "unit-return", "census", "contact", "completion", "output-order", "control-order", "assessment", "archive-path"))
def test_substituted_original_parents_and_incomplete_custody_refuse(original, change):
    supply = original.supply
    changes = {}
    if change == "receipt-attempt": changes["receipt"] = replace(supply.receipt, attempt_id=supply.receipt.attempt_id + ".changed")
    if change == "receipt-id": changes["receipt"] = replace(supply.receipt, receipt_id=supply.receipt.receipt_id + ".changed")
    if change == "receipt-input": changes["receipt"] = replace(supply.receipt, input_materialization_ids=supply.receipt.input_materialization_ids[:-1])
    if change == "source": changes["original_source"] = replace(supply.original_source, selection_id="source.changed-label")
    if change == "unit-return": changes["returned"] = replace(supply.returned, plan=replace(supply.returned.plan, object_fingerprint="9" * 64))
    if change == "census": changes["census"] = replace(supply.census, files=supply.census.files[:-1])
    if change == "contact": changes["contact"] = replace(supply.contact, begin=replace(supply.contact.begin, object_fingerprint="9" * 64))
    if change == "completion": changes["completion"] = replace(supply.completion, definition=replace(supply.definition.identity, object_fingerprint="9" * 64))
    if change == "output-order": changes["output_manifests"] = tuple(reversed(supply.output_manifests))
    if change == "control-order": changes["control_manifests"] = tuple(reversed(supply.control_manifests))
    if change == "assessment": changes["independent_integrity"] = None
    if change == "archive-path":
        row = supply.output_manifests[1]
        changes["output_manifests"] = (supply.output_manifests[0], replace(row, publication=None,
            materialization=replace(row.materialization, relative_path="foreign/archive")), supply.output_manifests[2])
    with pytest.raises(ValueError):
        replace(supply, **changes)


@pytest.mark.parametrize("field", ("code_sources_sha256", "dependency_lock_sha256"))
def test_consistently_rehashed_original_source_attribution_still_refuses(original, field):
    supply = original.supply
    definition = replace(supply.definition, **{field: "9" * 64})
    prefix = supply.receipt.task_id
    begin = replace(supply.begin, definition=definition.identity)
    contact = replace(supply.contact, begin=ObjectIdentity.from_record(prefix + ".begin", begin))
    completion = replace(supply.completion, definition=definition.identity,
        contact=ObjectIdentity.from_record(prefix + ".contact", contact))
    def rebind(manifest, record):
        return replace(manifest, publication=None,
            logical=replace(manifest.logical, content_sha256=record.fingerprint()),
            materialization=replace(manifest.materialization, physical_sha256=record.fingerprint(),
                size_bytes=len(record.canonical_bytes())))
    controls = tuple(rebind(manifest, record) for manifest, record in zip(
        supply.control_manifests, (definition, begin, contact), strict=True))
    completion_manifest = rebind(supply.completion_manifest, completion)
    outputs = (*supply.output_manifests, completion_manifest)
    receipt = replace(supply.receipt,
        output_materializations=tuple(sorted((row.materialization for row in outputs), key=lambda row: row.materialization_id)),
        output_logical_artifacts=tuple(sorted((row.logical for row in outputs), key=lambda row: row.logical_artifact_id)))
    with pytest.raises(ValueError, match="source/unit/completion/census"):
        replace(supply, definition=definition, begin=begin, contact=contact, completion=completion,
            control_manifests=controls, completion_manifest=completion_manifest, receipt=receipt)


@pytest.mark.parametrize("change", ("geometry-reentered", "missing-supplier", "new-view", "thinned-roster", "archive-outside", "duplicate-archive"))
def test_fresh_model_plan_retains_original_geometry_without_new_completion(original, change):
    _, plan = fresh(original)
    changes = {}
    if change == "geometry-reentered": changes["attempted_geometry_ids"] = plan.reused_geometry_ids
    if change == "missing-supplier": changes["geometry_supplies"] = ()
    if change == "new-view": changes["reused_geometry_ids"] = ("geometry.gp.wt.m1.joint-02",)
    if change == "thinned-roster": changes["model_census"] = plan.model_census[:-1]
    if change == "archive-outside": changes["archive_inputs"] = ((plan.geometry_supplies[0], "/tmp/unselected/archive"),)
    if change == "duplicate-archive": changes["archive_inputs"] = plan.archive_inputs * 2
    with pytest.raises(ValueError):
        replace(plan, **changes)


@pytest.mark.parametrize("change", ("source", "receipt", "file", "identity"))
def test_actual_assessment_parent_and_operand_substitutions_refuse(original, change):
    source, plan = fresh(original)
    result = original.assessment
    if change == "source": result = replace(result, source=replace(result.source, object_fingerprint="9" * 64))
    if change == "receipt": result = replace(result, geometry_receipt=replace(result.geometry_receipt, object_fingerprint="9" * 64))
    if change == "file": result = replace(result, heavy_file=replace(result.heavy_file, sha256="9" * 64))
    if change == "identity": result = replace(result, product_id="assessment.changed-label")
    with pytest.raises(ValueError):
        validate_reuse_assessment(plan, source, original.supply, result)


def test_entire_original_archive_authenticates_before_selective_two_file_supply(original, tmp_path):
    before = sha256(original.archive.read_bytes()).hexdigest()
    destination = tmp_path / "consumer-operands"
    destination.mkdir()
    materialize_geometry_inputs(original.archive, original.supply.definition, original.supply.census,
        original.supply.archive_evidence, destination)
    assert tuple(path.name for path in sorted(destination.iterdir())) == ("atom-origin-provenance.json", "complete-heavy.pdb")
    assert all((destination / name).read_bytes() == original.files[name] for name in ("atom-origin-provenance.json", "complete-heavy.pdb"))
    assert sha256(original.archive.read_bytes()).hexdigest() == before
    with pytest.raises(ValueError, match="existing operand"):
        materialize_geometry_inputs(original.archive, original.supply.definition, original.supply.census,
            original.supply.archive_evidence, destination)


@pytest.mark.parametrize("change", ("unselected-member", "truncated", "extra-gzip-member", "raw-digest", "raw-size"))
def test_any_full_archive_damage_refuses_before_consumer_files_exist(original, tmp_path, change):
    original_raw = original.archive.read_bytes()
    raw = original_raw
    if change == "unselected-member":
        decoded = bytearray(gzip.decompress(raw)); decoded[-1] ^= 1
        raw = gzip.compress(decoded, mtime=0)
    if change == "truncated": raw = raw[:-4]
    if change == "extra-gzip-member": raw += gzip.compress(b"undeclared", mtime=0)
    path = tmp_path / "archive"
    path.write_bytes(raw)
    evidence = replace(original.supply.archive_evidence, byte_count=len(raw), sha256=sha256(raw).hexdigest())
    if change == "raw-digest": evidence = replace(evidence, sha256="9" * 64)
    if change == "raw-size": evidence = replace(evidence, byte_count=evidence.byte_count + 1)
    destination = tmp_path / "operands"
    destination.mkdir()
    with pytest.raises(ValueError):
        materialize_geometry_inputs(path, original.supply.definition, original.supply.census, evidence, destination)
    assert tuple(destination.iterdir()) == ()


def test_domain_entry_stays_cold_without_molecular_imports_or_geometry_builder(tmp_path):
    code = '''
import importlib.abc
import sys
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split('.')[0] in ('numpy','scipy','openmm','pdbfixer','parmed','ash') or name.endswith('.native'):
            raise RuntimeError('native producer entered: '+name)
sys.meta_path.insert(0, Refuse())
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_reuse import GeometryReuseRunner
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import geometry_reuse_native_entry
assert GeometryReuseRunner._entry_target(None)[0].endswith('.geometry_reuse_native_entry')
assert callable(geometry_reuse_native_entry.selected_child)
'''
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"), PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr

