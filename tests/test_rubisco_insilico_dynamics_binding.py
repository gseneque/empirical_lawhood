# SPDX-License-Identifier: MPL-2.0
"""Exposed software conformance only, no native models or scientific admission."""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace as N
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import (
    contracts as c,
    science,
    preparation,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import (
    operation_bindings as ob,
    recursive_translation as rt,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_structure import (
    contracts as sc,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import (
    EvidenceCeiling,
    OutcomeAccess,
    VisibilityCeiling,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole
from empirical_lawhood.kernel.scientific_contributions import (
    ContributionManifest,
    ContributionProduct,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import (
    WorkerInputKind,
    WorkerOutputPort,
    DependencyReceiptBinding,
)
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_battery_refined_inquiry_binding import Port
from tests.test_rubisco_nomination_preparation import parent
from tests.rubisco_nomination_fixture import nominee


@pytest.fixture
def exposed(monkeypatch, tmp_path):
    _, dossier = nominee()
    # Relocate only this explicit software stock's selected scratch root.
    monkeypatch.setattr(c, "NATIVE_WORK_ROOT", str(tmp_path))
    original = ObjectIdentity(
        "input.exposed-structure", sc.StructuralSource.SCHEMA, "1.0.0", "a" * 64
    )
    inventory = sc.StructuralInventory(
        "product.exposed.inventory",
        original,
        c.identity(dossier),
        (),
        (),
        (),
        (),
        (),
        (),
    )
    coordinates = sc.AssemblyCoordinates(
        "product.exposed.coordinates",
        c.identity(inventory),
        tuple(
            (name, sha256(b"Exposed coordinates").hexdigest(), "Exposed coordinates")
            for name in ("1bwv-assembly1.cif", "3zxw-assembly1.cif")
        ),
    )
    constructs = preparation.controlled_constructs(
        gp_lsu="A" * 493,
        gp_ssu_m1="M" + "A" * 93 + "I" + "A" * 43,
        gp_ssu_v1="V" + "A" * 93 + "I" + "A" * 43,
        te_lsu="A" * 414 + "P" + "A" * 60,
        te_ssu="A" * 97 + "V" + "A" * 20,
    )
    raw = "Exposed software stock, never scientific intake."
    source = c.PreparationSelection(
        "input.exposed.preparation",
        c.identity(inventory),
        c.identity(coordinates),
        c.identity(dossier),
        str(tmp_path / "exposed-models"),
        c.ENGINE_INVENTORY_SHA256,
        constructs,
        (
            c.SourceMember(
                "source.exposed",
                "https://example.invalid/exposed",
                sha256(raw.encode()).hexdigest(),
                raw,
            ),
        ),
    )
    # Isolate only domain source validity: this test cannot enter authentic stock or native science.
    monkeypatch.setattr(science, "validate_source", lambda *args: source)
    monkeypatch.setattr(science, "validate_inputs", lambda *args: source)
    nominal = parent(dossier)
    receipt = ObjectIdentity(
        "receipt.exposed-structure",
        "empirical-lawhood/testing/exposed-receipt",
        "1.0.0",
        "b" * 64,
    )
    products = tuple(
        sorted(
            (
                ContributionProduct(
                    "product.exposed." + name,
                    c.identity(record),
                    ArtifactIdentity(
                        "artifact.exposed." + name,
                        "scientific-product",
                        record.SCHEMA,
                        record.fingerprint(),
                        ob.MEDIA,
                        len(record.canonical_bytes()),
                    ),
                    receipt,
                    ContributionRole.RETAINED_ANALYSIS_INPUT,
                    EvidenceCeiling.NON_PROMOTABLE,
                    OutcomeAccess.DEVELOPMENT_VISIBLE,
                    VisibilityCeiling.DEVELOPMENT_ONLY,
                )
                for name, record in (
                    ("inventory", inventory),
                    ("coordinates", coordinates),
                )
            ),
            key=lambda r: r.product_id,
        )
    )
    structural = ContributionManifest(
        "contribution.exposed.structure",
        c.QUESTION,
        "Exposed unsigned metadata only.",
        sc.scope(
            N(
                input_id=original.object_id,
                fingerprint=lambda: original.object_fingerprint,
            )
        ),
        products,
        (c.identity(inventory),),
        (),
        (),
    )
    return N(
        source=source,
        dossier=dossier,
        inventory=inventory,
        coordinates=coordinates,
        nominal=nominal,
        structural=structural,
    )


def draft(e):
    return rt.preparation_draft(
        e.source,
        e.dossier,
        e.inventory,
        e.coordinates,
        nomination_parent=e.nominal,
        structure_parent=e.structural,
    )


def compile(selected):
    return compile_recursive_wave(
        draft=selected,
        registrations=ob.operation_registrations(),
        registry=CapabilityRegistry(
            "registry.exposed-dynamics", ob.operation_manifests()
        ),
        implementation_commit="1" * 40,
        output_codecs=ob.output_codecs(),
    )


def test_cold_descriptors_no_native_tools():
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import importlib.abc,sys
class Refuse(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in ('openmm','pybamm','pdbfixer','parmed'): raise AssertionError(fullname)
sys.meta_path.insert(0,Refuse())
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import extension_bundle,executable_binding
assert {row.binding.capability_key for row in executable_binding.EXECUTABLE_BINDING_FACTORIES} == {
 'rubisco-insilico-dynamics.assess-preparation','rubisco-insilico-dynamics.prepare',
 'rubisco-durable-preparation.prepare','rubisco-durable-preparation.reuse-geometry'}
""",
        ],
        check=True,
    )


def test_compile_exact_two_parent_roles_native24_and_nomination_world(exposed):
    selected = draft(exposed)
    compiled = compile(selected)
    assert len(selected.contribution_parents) == 2
    assert selected.development_study.world_id == exposed.dossier.scope.world_id
    assert selected.development_study.world_id != c.scope(exposed.source).world_id
    assert (
        len(
            ob.native_effect_slot_ids(
                decode_canonical_bytes(
                    selected.operations[1].config_payload.encode(),
                    c.PreparationOperationConfig,
                    maximum_bytes=None,
                )
            )
        )
        == 24
    )
    tasks = {t.task_id: t for t in compiled.execution_plan.tasks}
    assert tasks[rt.ASSESS].dependency_task_ids == (rt.PREPARE,)
    assert len(tasks[rt.PREPARE].outputs) == 25
    assert len(ob.operation_inputs("assess-preparation")) == 29
    assert {r.scientific_role for r in selected.external_inputs} == {
        "SOURCE",
        "HISTORY",
        "OUTCOME",
    }
    rt.inquiry_endpoint_validator(selected, c.scope(exposed.source))
    with pytest.raises(ValueError):
        rt.preparation_draft(
            exposed.source,
            exposed.dossier,
            exposed.inventory,
            exposed.coordinates,
            nomination_parent=exposed.structural,
            structure_parent=exposed.nominal,
        )
    altered = replace(
        exposed.structural,
        scope=replace(exposed.structural.scope, source_config_sha256="c" * 64),
    )
    with pytest.raises(ValueError, match="scope"):
        rt.preparation_draft(
            exposed.source,
            exposed.dossier,
            exposed.inventory,
            exposed.coordinates,
            nomination_parent=exposed.nominal,
            structure_parent=altered,
        )
    links = tuple(
        replace(r, scientific_role="SOURCE")
        if r.consumer_input_id == "inventory"
        else r
        for r in selected.links
    )
    with pytest.raises(ValueError, match="roles"):
        compile(replace(selected, links=links))


def negative_products(e):
    assets = tuple(
        c.ModelAssets(
            "product.exposed.assets." + str(i), c.identity(e.source), *row, ()
        )
        for i, row in enumerate(c.model_roster())
    )
    constructs = {r.construct_id: r for r in e.source.constructs}
    models = tuple(
        c.PreparedModel(
            "model." + ".".join(row),
            constructs[row[0]],
            row[1],
            row[2],
            c.A.UNEVALUABLE,
            ("EXPOSED_UNENTERED_NATIVE_FIXTURE",),
            (),
            c.identity(assets[i]),
            0,
            (),
            None,
            (),
        )
        for i, row in enumerate(c.model_roster())
    )
    product = c.PreparationProduct(
        "product.exposed.preparation",
        c.identity(e.source),
        c.identity(e.inventory),
        c.identity(e.coordinates),
        c.identity(e.dossier),
        models,
        (),
        (),
        1,
    )
    return product, assets


def context(e, operation, prepared, assets):
    node = c.NAMESPACE + "." + operation
    config = c.PreparationOperationConfig(
        "config." + node,
        operation,
        e.source,
        e.dossier.scope,
        tuple(
            sorted(
                (
                    c.identity(e.source),
                    c.identity(e.dossier),
                    c.identity(e.inventory),
                    c.identity(e.coordinates),
                ),
                key=lambda r: r.object_id,
            )
        ),
    )
    inputs = [Port(config.config_id, config, WorkerInputKind.EXTERNAL)]
    inputs.extend(
        Port(
            "external.exposed." + name,
            getattr(e, "dossier" if name == "nomination" else name),
            WorkerInputKind.EXTERNAL,
        )
        for name in ("source", "nomination", "inventory", "coordinates")
    )
    receipts = ()
    if operation == "assess-preparation":
        additional = [
            Port(
                "artifact.run.exposed." + rt.PREPARE + ".preparation",
                prepared,
                WorkerInputKind.DEPENDENCY,
            )
        ]
        additional.extend(
            Port(
                "artifact.run.exposed." + rt.PREPARE + f".assets-{i:02d}",
                asset,
                WorkerInputKind.DEPENDENCY,
            )
            for i, asset in enumerate(assets)
        )
        inputs.extend(additional)
        receipts = (
            DependencyReceiptBinding(
                "receipt.exposed.native",
                rt.PREPARE,
                tuple(sorted(p.materialization_id for p in additional)),
            ),
        )
    return N(
        task_id=node,
        run_id="run.exposed",
        attempt_id="attempt.exposed",
        input_ports=tuple(inputs),
        permissions=ob.PreparationRunner(operation).manifest.permissions,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        resource_budget=ob.BUDGET,
        dependency_receipts=receipts,
        config=N(
            artifact_id=config.config_id,
            config_id=config.config_id,
            content_sha256=config.fingerprint(),
        ),
        output_ports=tuple(
            WorkerOutputPort(
                node + "." + name,
                codec.SCHEMA,
                ArtifactProfile.CANONICAL_JSON,
                ob.MEDIA,
            )
            for name, codec in ob.operation_outputs(operation)
        ),
    )


def test_real_pure_assessor_full24_negative_census_and_dependency_refusals(exposed):
    product, assets = negative_products(exposed)
    ctx = context(exposed, "assess-preparation", product, assets)
    result = ob.PreparationRunner("assess-preparation").execute(ctx)
    assessment = decode_canonical_bytes(
        result.outputs[0].payload, c.PreparationAssessment, maximum_bytes=None
    )
    assert assessment.preparation_disposition is c.A.UNEVALUABLE
    assert assessment.prior_nomination_scope == exposed.dossier.scope
    assert len(assessment.model_dispositions) == 24
    assert all(p.closed for p in ctx.input_ports)
    missing = context(exposed, "assess-preparation", product, assets)
    missing.dependency_receipts = ()
    with pytest.raises(ValueError, match="receipt"):
        ob.PreparationRunner("assess-preparation").execute(missing)
    swapped = context(exposed, "assess-preparation", product, tuple(reversed(assets)))
    with pytest.raises(ValueError, match="custody"):
        ob.PreparationRunner("assess-preparation").execute(swapped)
    omitted = context(exposed, "assess-preparation", product, assets[:-1])
    with pytest.raises(ValueError, match="census"):
        ob.PreparationRunner("assess-preparation").execute(omitted)


def test_exposed_original_input_census_requires_complete_prepared_native_progress(
    exposed, monkeypatch
):
    """Synthetic input checks do not substitute a backend for worker readiness."""
    product, assets = negative_products(exposed)

    def forbidden_prepare(*args, **kwargs):
        raise AssertionError("unprepared synthetic context reached native execution")

    module_name = "empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.native"
    import empirical_lawhood.adapters.methods.rubisco_insilico_dynamics as package
    fixture_native = N(prepare=forbidden_prepare)
    monkeypatch.setitem(sys.modules, module_name, fixture_native)
    monkeypatch.setattr(package, 'native', fixture_native, raising=False)
    ctx = context(exposed, "prepare", product, assets)
    runner = ob.PreparationRunner("prepare")
    config, values = runner.validated_inputs(ctx)
    assert config.source == exposed.source and config.prior_nomination_scope == exposed.dossier.scope
    assert values == {"source": exposed.source, "nomination": exposed.dossier,
        "inventory": exposed.inventory, "coordinates": exposed.coordinates}
    declared = ob.operation_outputs("prepare")
    assert len(declared) == 25 and sum(kind is c.ModelAssets for _, kind in declared) == 24
    with pytest.raises(ValueError, match="SOFTWARE:.*prepared native progress"):
        runner.execute(ctx)
    ctx.prepared_invocation = None
    with pytest.raises(ValueError, match="SOFTWARE:.*specialist preparation"):
        runner.execute_with_native_subwork(ctx, None, None)
    refused = context(exposed, "prepare", product, assets)
    refused.config.content_sha256 = "c" * 64
    with pytest.raises(ValueError, match="substitutes"):
        runner.validated_inputs(refused)
    wrongkind = context(exposed, "prepare", product, assets)
    next(
        p
        for p in wrongkind.input_ports
        if p.payload_schema == sc.StructuralInventory.SCHEMA
    ).kind = WorkerInputKind.DEPENDENCY
    with pytest.raises(ValueError, match="custody"):
        runner.validated_inputs(wrongkind)


def test_callback_refuses_changed_parent_scope_or_historical_source_disguise(exposed):
    selected = draft(exposed)
    rt._configs(selected)
    structural = replace(
        exposed.structural,
        scope=replace(exposed.structural.scope, world_id="world.crossed-structure"),
    )
    parents = tuple(
        sorted((exposed.nominal, structural), key=lambda p: p.contribution_id)
    )
    with pytest.raises(ValueError, match="scope"):
        rt._configs(replace(selected, contribution_parents=parents))
    inputs = tuple(
        replace(r, scientific_role="SOURCE")
        if r.input_id.endswith(".coordinates")
        else r
        for r in selected.external_inputs
    )
    with pytest.raises(ValueError, match="roster"):
        rt._configs(replace(selected, external_inputs=inputs))
    removed = replace(selected, contribution_parents=(exposed.nominal,))
    with pytest.raises(ValueError, match="parents"):
        rt._configs(removed)
