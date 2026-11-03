# SPDX-License-Identifier: MPL-2.0
"""Complete exposed durable receipt joins; never actual molecular admission."""

from dataclasses import fields, replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import preparation_integrity
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus, DurableUnitReturn
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import (
    DurableCallLedger, complete_unit,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import definitions, freeze
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_reuse import GeometryReuseSupply
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_contracts as c, control_science
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_preparation_admission import (
    SerializedDurableChemicalForcePlan, SerializedDurableGeometrySupply, decode_plan, validate_operands,
)
from empirical_lawhood.infrastructure.prepared_native_invocation import (
    NativeInputPublication, prepare_native_invocation, validate_prepared_native_invocation,
)
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests import test_rubisco_reused_geometry_chemical_admission as reuse_fixture
from tests import test_rubisco_chemical_force_controls as force_fixture
from tests.test_rubisco_geometry_reuse import original as original


@pytest.fixture(scope="module")
def reuse_admitted(original):
    return reuse_fixture.admitted.__wrapped__(original, force_fixture.plan.__wrapped__())


@pytest.fixture(scope="module")
def durable_admitted(reuse_admitted, tmp_path_factory):
    """Real exposed primary manifests/receipts, with disclosed non-molecular text."""
    admitted = reuse_admitted
    tmp_path = tmp_path_factory.mktemp("serialized-durable-chemical-custody")
    parent = admitted.parent
    selected = admitted.plan.selected_assets[0][0]
    preparation_plan = replace(parent.plan, attempted_model_ids=(selected,))
    source = parent.source
    asset = replace(admitted.assets[0], source=p.identity(source))
    models = tuple(replace(row, assets=p.identity(asset)) if row.model_id == selected else row
        for row in admitted.preparation.models)
    preparation = replace(admitted.preparation, source=p.identity(source), models=models)
    integrity = replace(admitted.integrity, source=p.identity(source), preparation=p.identity(preparation))
    geometry = replace(admitted.geometry, source=p.identity(source), preparation=p.identity(preparation),
        assignment_integrity=p.identity(integrity), models=tuple(
            replace(row, assets=p.identity(asset)) if row.model_id == selected else row
            for row in admitted.geometry.models))
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        preparation_plan.dependency_lock_sha256, preparation_plan.code_sources,
        sha256(canonical_json_bytes(preparation_plan.code_sources)).hexdigest(), "6" * 40, False)
    plane = _plane(tmp_path / "primary-custody")
    records = (source, preparation_plan, parent.nomination, parent.inventory, parent.coordinates)
    bundle = prepare_native_invocation(plane, visibility=VisibilityCeiling.DEVELOPMENT_ONLY,
        access=OutcomeAccess.DEVELOPMENT_VISIBLE, publications=tuple(
            NativeInputPublication((row.identity if hasattr(row, "identity") else p.identity(row)).object_id, row) for row in records)
            + (NativeInputPublication(provenance.identity.object_id, provenance),))
    actual_parent = replace(parent.supply.definition.parent_contact,
        run_id="exposed.durable-chemical", attempt_id="exposed.durable-chemical.native.parent.attempt-001",
        input_materialization_ids=bundle.input_materialization_ids)
    selected_definitions = definitions(preparation_plan, actual_parent,
        sources=(preparation_plan.source, preparation_plan.nomination, preparation_plan.inventory,
            preparation_plan.coordinates, provenance.identity),
        input_materialization_ids=bundle.input_materialization_ids)
    validate_prepared_native_invocation(plane, bundle, selected_definitions,
        visibility=VisibilityCeiling.DEVELOPMENT_ONLY, access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    store = _store(plane, actual_parent, bundle.manifests)
    store.parent_contacts.begin(actual_parent)
    freeze(store, selected_definitions)
    root = tmp_path / "returned-native-fixture"
    root.mkdir()
    geometry_definition = next(row for row in selected_definitions
        if row.subwork_id == preparation_plan.attempted_geometry_ids[0])
    entry = store.begin(geometry_definition, bundle.manifests)
    store.contact(entry)
    directory = root / geometry_definition.subwork_id
    directory.mkdir()
    for name, raw in parent.files.items():
        (directory / name).write_bytes(raw)
    complete_unit(store, preparation_plan, entry, root, directory,
        DurableCallLedger(store, preparation_plan, root, entry, directory), succeeded=True)
    inspection = store.recover(geometry_definition)
    prefix = inspection.receipt.task_id
    archive_root = "runs/" + actual_parent.run_id + "/native-subwork/" + prefix.removeprefix("native-subwork.")
    def manifest(name):
        return decode_artifact_manifest(plane.root.resolve(archive_root + "/" + name + ".manifest.json",
            for_write=False).read_bytes())
    def output(definition, name, kind):
        raw = b"".join(store.iter_completed_output(definition, name))
        return decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    supply = SerializedDurableGeometrySupply("supply.exposed.completed-durable", source, preparation_plan,
        geometry_definition, inspection.begin, inspection.contact, inspection.completion, inspection.receipt,
        output(geometry_definition, "unit.return", DurableUnitReturn),
        output(geometry_definition, "files.census", DurableRawFileCensus),
        tuple(manifest(name + ".json") for name in ("definition", "begin", "contact")),
        tuple(manifest("outputs/" + name) for name in ("files.census", "files.raw", "unit.return")),
        manifest("completion.json"), p.identity(integrity))
    model_definition = next(row for row in selected_definitions if row.subwork_id == selected)
    model_entry = store.begin(model_definition, bundle.manifests)
    store.contact(model_entry)
    model_directory = root / selected
    model_directory.mkdir()
    for row in asset.files:
        (model_directory / Path(row.evidence.relative_path).name).write_bytes(row.raw_utf8.encode())
    complete_unit(store, preparation_plan, model_entry, root, model_directory,
        DurableCallLedger(store, preparation_plan, root, model_entry, model_directory), succeeded=True,
        geometry=geometry_definition.identity, geometry_receipt=supply.geometry_receipt)
    model_inspection = store.recover(model_definition)
    returned = output(model_definition, "unit.return", DurableUnitReturn)
    completion_identity = ObjectIdentity.from_record(model_inspection.receipt.task_id + ".completion",
        model_inspection.completion)
    return_identity = ObjectIdentity.from_record(model_inspection.receipt.task_id + ".output.unit.return", returned)
    custody = ((selected, model_definition, completion_identity, model_inspection.completion,
        return_identity, returned),)
    kwargs = {field.name: getattr(admitted.plan, field.name) for field in fields(c.ChemicalForcePlan)}
    kwargs.update(source=p.identity(source), preparation=p.identity(preparation), assignment_integrity=p.identity(integrity),
        engine_inventory_sha256=source.engine_inventory_sha256,
        mathematical_geometry=p.identity(geometry), selected_assets=((selected, p.identity(asset)),),
        preparation_custody=((selected, model_definition.identity, completion_identity, return_identity),))
    plan = SerializedDurableChemicalForcePlan(**kwargs, preparation_plan=preparation_plan,
        geometry_supplies=(supply,), geometry_inputs=((supply.identity, admitted.parent_files),))
    yield SimpleNamespace(plan=plan, source=source, preparation=preparation, integrity=integrity,
        geometry=geometry, assets=(asset,), custody=custody, supply=supply, store=store, bundle=bundle,
        parent_files=admitted.parent_files, selected_definitions=selected_definitions)
    bundle.close()


def admit(row, **changes):
    operands = {name: getattr(row, name) for name in
        ("plan", "source", "preparation", "integrity", "geometry", "assets", "custody")}
    return validate_operands(**(operands | changes))


def test_complete_durable_receipt_admission_preserves_legacy_math_and_denominators(durable_admitted):
    row = durable_admitted
    old_globals = dict(control_science.validate_operands.__globals__)
    supplier_globals = dict(GeometryReuseSupply.__post_init__.__globals__)
    assert admit(row) == row.plan
    assert decode_plan(row.plan.canonical_bytes().decode()) == row.plan
    assert decode_canonical_bytes(row.supply.canonical_bytes(), SerializedDurableGeometrySupply,
        maximum_bytes=None) == row.supply
    assert control_science.validate_operands.__globals__ == old_globals
    assert GeometryReuseSupply.__post_init__.__globals__ == supplier_globals
    assert len(row.selected_definitions) == 37
    assert len(row.integrity.model_dispositions) == len(row.geometry.models) == 24
    assert len(row.plan.model_census) == 24 and len(row.plan.nve_census) == 96
    assert row.integrity.kinetic_disposition is row.geometry.force_adequacy is A.UNEVALUABLE


@pytest.mark.parametrize("change", ("configuration", "code", "lock", "source", "geometry", "receipt", "completion", "unknown", "return"))
def test_changed_complete_native_model_custody_refuses(durable_admitted, change):
    row = durable_admitted
    name, definition, ci, completion, ri, returned = row.custody[0]
    if change == "configuration": definition = replace(definition, configuration=replace(definition.configuration, object_fingerprint="9" * 64))
    if change == "code": definition = replace(definition, code_sources_sha256="9" * 64)
    if change == "lock": definition = replace(definition, dependency_lock_sha256="9" * 64)
    if change == "source": definition = replace(definition, sources=tuple(value for value in definition.sources if value != row.plan.preparation_plan.inventory))
    if change == "geometry": returned = replace(returned, geometry=replace(returned.geometry, object_fingerprint="9" * 64))
    if change == "receipt": returned = replace(returned, geometry_receipt=replace(returned.geometry_receipt, object_fingerprint="9" * 64))
    if change == "completion": completion = replace(completion, definition=replace(completion.definition, object_fingerprint="9" * 64))
    if change == "unknown": completion = replace(completion, unknown_streams=(row.plan.source,))
    if change == "return": returned = replace(returned, preparation_succeeded=False, reason_codes=("EXPOSED_NEGATIVE",))
    with pytest.raises(ValueError): admit(row, custody=((name, definition, ci, completion, ri, returned),))


@pytest.mark.parametrize("change", ("configuration", "code", "lock", "source"))
def test_self_consistently_rehashed_model_custody_keeps_selected_source_joins(durable_admitted, change):
    row = durable_admitted
    name, definition, ci, completion, ri, returned = row.custody[0]
    if change == "configuration": definition = replace(definition, configuration=replace(definition.configuration, object_fingerprint="9" * 64))
    if change == "code": definition = replace(definition, code_sources_sha256="9" * 64)
    if change == "lock": definition = replace(definition, dependency_lock_sha256="9" * 64)
    if change == "source": definition = replace(definition, sources=tuple(value for value in definition.sources if value != row.plan.preparation_plan.inventory))
    completion = replace(completion, definition=definition.identity)
    returned = replace(returned, plan=definition.configuration)
    ci = ObjectIdentity.from_record(ci.object_id, completion)
    ri = ObjectIdentity.from_record(ri.object_id, returned)
    plan = replace(row.plan, preparation_custody=((name, definition.identity, ci, ri),))
    with pytest.raises(ValueError, match="model/source/geometry"):
        admit(row, plan=plan, custody=((name, definition, ci, completion, ri, returned),))


@pytest.mark.parametrize("change", ("receipt-input", "contact", "completion", "census", "control-order", "output-order", "assignment-parent", "revision", "archive-path"))
def test_changed_complete_geometry_supplier_refuses(durable_admitted, change):
    row = durable_admitted
    supply = row.supply
    changes = {}
    if change == "receipt-input": changes["receipt"] = replace(supply.receipt, input_materialization_ids=supply.receipt.input_materialization_ids[:-1])
    if change == "contact": changes["contact"] = replace(supply.contact, begin=replace(supply.contact.begin, object_fingerprint="9" * 64))
    if change == "completion": changes["completion"] = replace(supply.completion, definition=replace(supply.definition.identity, object_fingerprint="9" * 64))
    if change == "census": changes["census"] = replace(supply.census, files=supply.census.files[:-1])
    if change == "control-order": changes["control_manifests"] = tuple(reversed(supply.control_manifests))
    if change == "output-order": changes["output_manifests"] = tuple(reversed(supply.output_manifests))
    if change == "assignment-parent": changes["independent_integrity"] = replace(supply.independent_integrity, object_fingerprint="9" * 64)
    if change == "revision": changes["independent_integrity"] = replace(supply.independent_integrity, object_version="1.0.0")
    if change == "archive-path":
        value = supply.output_manifests[1]
        changes["output_manifests"] = (supply.output_manifests[0], replace(value, publication=None,
            materialization=replace(value.materialization, relative_path="foreign/archive")), supply.output_manifests[2])
    with pytest.raises(ValueError):
        changed = replace(supply, **changes)
        admit(row, plan=replace(row.plan, geometry_supplies=(changed,),
            geometry_inputs=((changed.identity, row.parent_files),)))


@pytest.mark.parametrize("change", ("missing-supplier", "missing-origin", "wrong-origin", "wrong-heavy", "wrong-source", "legacy-revision", "geometry-negative"))
def test_missing_operands_or_scientific_negative_refuse(durable_admitted, change):
    row = durable_admitted
    kwargs = {}
    with pytest.raises(ValueError):
        if change == "missing-supplier": kwargs["plan"] = replace(row.plan, geometry_supplies=())
        elif change == "missing-origin": kwargs["plan"] = replace(row.plan, geometry_inputs=((row.supply.identity, row.parent_files[1:]),))
        elif change in ("wrong-origin", "wrong-heavy"):
            index = 0 if change == "wrong-origin" else 1
            values = list(row.parent_files)
            target = values[index]
            raw = target.raw_utf8 + "EXPOSED_CHANGED"
            values[index] = p.NativeTextFile(replace(target.evidence, byte_count=len(raw.encode()), sha256=sha256(raw.encode()).hexdigest()), raw)
            kwargs["plan"] = replace(row.plan, geometry_inputs=((row.supply.identity, tuple(values)),))
        elif change == "wrong-source": kwargs["source"] = replace(row.source, selection_id="source.exposed.substitute")
        elif change == "legacy-revision": kwargs["plan"] = replace(row.plan, assignment_integrity=replace(row.plan.assignment_integrity, object_version="1.0.0"))
        else:
            geometry = replace(row.geometry, models=tuple(replace(value, diagnostic_disposition=A.FALSIFIED, diagnostic=None)
                if value.model_id == row.plan.selected_assets[0][0] else value for value in row.geometry.models))
            kwargs.update(geometry=geometry, plan=replace(row.plan, mathematical_geometry=p.identity(geometry)))
        admit(row, **kwargs)


@pytest.mark.parametrize("disposition", (A.FALSIFIED, A.UNEVALUABLE, A.REFUSED, A.NOT_ATTEMPTED))
def test_consistently_rebound_independent_assignment_negative_stays_unadmitted(durable_admitted, disposition):
    row = durable_admitted
    selected = row.plan.selected_assets[0][0]
    model_dispositions = tuple((name, disposition if name == selected else value, reasons)
        for name, value, reasons in row.integrity.model_dispositions)
    counts, overall = preparation_integrity.disposition_census(model_dispositions)
    integrity = replace(row.integrity, model_dispositions=model_dispositions,
        disposition_counts=counts, assignment_disposition=overall, raw_topologies=())
    geometry = replace(row.geometry, assignment_integrity=p.identity(integrity))
    supply = replace(row.supply, independent_integrity=p.identity(integrity))
    plan = replace(row.plan, assignment_integrity=p.identity(integrity), mathematical_geometry=p.identity(geometry),
        geometry_supplies=(supply,), geometry_inputs=((supply.identity, row.parent_files),))
    with pytest.raises(ValueError, match="independent assignment"):
        admit(row, plan=plan, integrity=integrity, geometry=geometry)
