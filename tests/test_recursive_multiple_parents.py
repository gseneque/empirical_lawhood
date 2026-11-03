# SPDX-License-Identifier: MPL-2.0
"""Authentic software receipts/relocation; zero native or scientific qualification."""

from dataclasses import dataclass, replace
from pathlib import Path
import shutil
from typing import ClassVar

import pytest

from empirical_lawhood.api import (
    recursive_authoring as author,
    recursive_execution as execution,
)
from empirical_lawhood.api import recursive_contributions as contributions
from empirical_lawhood.adapters.composition.discovery import (
    manifest as capability_manifest,
)
from empirical_lawhood.adapters.methods.battery_recursive_construction.contracts import (
    BatteryProcedureContribution,
    BatteryFurtherProduct,
)
from empirical_lawhood.adapters.methods.battery_recursive_construction.examples import (
    battery_wave_b_draft,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import (
    EvidenceCeiling,
    OutcomeAccess,
    VisibilityCeiling,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import (
    RecursiveOperationSpec,
    RecursiveExternalInput,
    RecursiveInputLink,
)
from empirical_lawhood.planning.recursive_input_origins import (
    RecursiveInputOrigins,
    RecursiveInputOrigin,
    RecursiveInputOriginKind,
    contribution_graph_role,
)
from empirical_lawhood.planning.study_authoring import CapabilitySelection
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import (
    CapabilityKind,
    CapabilityRegistry,
    CapabilityPermission,
)
from empirical_lawhood.runtime.execution import (
    RunnerRegistry,
    RunnerResult,
    TaskOutputPayload,
)
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import (
    RecursiveOperationRegistration,
    RecursivePortContract,
)
from empirical_lawhood.runtime.recursive_handoff import (
    RecursiveParentClosuresBinding,
    recursive_parent_closure_bindings,
)
from tests.test_recursive_contribution_custody import (
    portable_a as portable_a,
    ROOT,
    _publish_fixture_wave,
    _raw_snapshot,
)
from tests.test_recursive_public_service import _plane

NODE = "testing.multiple-parents.read"


@dataclass(frozen=True, slots=True)
class PairConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/multiple-parent-config"
    config_id: str
    procedure: ObjectIdentity
    outcome: ObjectIdentity


@dataclass(frozen=True, slots=True)
class PairRead(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/multiple-parent-byte-join"
    product_id: str
    procedure: ObjectIdentity
    outcome: ObjectIdentity


def identity(record, key):
    return ObjectIdentity.from_record(key, record)


class PairRunner:
    def __init__(self, manifest):
        self.manifest = manifest

    def execute(self, ctx):
        try:
            codecs = {
                r.SCHEMA: r
                for r in (
                    PairConfig,
                    BatteryProcedureContribution,
                    BatteryFurtherProduct,
                )
            }
            records = {
                port.payload_schema: decode_canonical_bytes(
                    port.read(), codecs[port.payload_schema], maximum_bytes=None
                )
                for port in ctx.input_ports
            }
            config, procedure, outcome = (
                records[r.SCHEMA]
                for r in (
                    PairConfig,
                    BatteryProcedureContribution,
                    BatteryFurtherProduct,
                )
            )
            assert config.procedure == identity(procedure, procedure.procedure_id)
            assert config.outcome == identity(outcome, outcome.product_id)
            value = PairRead(
                "product.testing.multiple-parent-byte-join",
                config.procedure,
                config.outcome,
            )
            return RunnerResult(
                (
                    TaskOutputPayload(
                        ctx.output_ports[0].output_id, value.canonical_bytes()
                    ),
                ),
                (
                    ReceiptCheck(
                        "exposed-byte-join-only-no-scientific-admission", True, ()
                    ),
                ),
            )
        finally:
            for port in ctx.input_ports:
                port.close()


def pair_draft(first, second, procedure, outcome):
    base = battery_wave_b_draft(first, procedure)
    config = PairConfig(
        "config." + NODE,
        identity(procedure, procedure.procedure_id),
        identity(outcome, outcome.product_id),
    )
    manifest = capability_manifest(
        "read",
        PairConfig,
        CapabilityKind.ANALYSIS,
        (
            PairConfig.SCHEMA,
            BatteryProcedureContribution.SCHEMA,
            BatteryFurtherProduct.SCHEMA,
        ),
        (PairRead.SCHEMA,),
        EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        None,
        namespace="testing.multiple-parents",
        resources=base.campaign.budget,
        read_permission=CapabilityPermission.READ_DEVELOPMENT,
        implementation_id="exposed-byte-join",
        conformance_ids=("testing.multiple-parent-byte-join",),
    )
    selection = CapabilitySelection(
        manifest.capability_key,
        manifest.capability_version,
        manifest.implementation_sha256,
    )
    registration = RecursiveOperationRegistration(
        selection,
        ScientificStage.FALSIFY,
        PairConfig,
        (
            RecursivePortContract(
                "outcome", BatteryFurtherProduct.SCHEMA, "application/json", None
            ),
            RecursivePortContract(
                "procedure",
                BatteryProcedureContribution.SCHEMA,
                "application/json",
                None,
            ),
        ),
        (
            OutputTemplate(
                "join",
                PairRead.SCHEMA,
                ArtifactProfile.CANONICAL_JSON,
                "application/json",
                ".json",
            ),
        ),
        manifest.permissions,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        base.campaign.budget,
    )
    operation = RecursiveOperationSpec.from_config(
        node_id=NODE,
        selection=selection,
        config_id=config.config_id,
        config=config,
        obligation_ids=("obligation.testing.multiple-parent-byte-join",),
        resource_budget=base.campaign.budget,
    )
    origins, externals, links = [], [], []
    for name, parent, record in (
        ("procedure", first, procedure),
        ("outcome", second, outcome),
    ):
        product = next(
            p
            for p in parent.products
            if p.record.object_fingerprint == record.fingerprint()
        )
        eid = "external.testing.multiple-parents." + name
        role = contribution_graph_role(product.role)
        origins.append(
            RecursiveInputOrigin(
                eid,
                RecursiveInputOriginKind.CONTRIBUTION,
                product.artifact.sha256,
                product.role.value,
                identity(parent, parent.contribution_id),
                product.product_id,
                product.producing_receipt,
            )
        )
        externals.append(
            RecursiveExternalInput(
                eid,
                product.artifact.artifact_id,
                record.SCHEMA,
                "application/json",
                None,
                product.outcome_access,
                product.visibility_ceiling,
                record.fingerprint(),
                role,
            )
        )
        links.append(
            RecursiveInputLink(
                "edge." + eid, NODE, name, external_input_id=eid, scientific_role=role
            )
        )
    draft = replace(
        base,
        draft_id="testing.multiple-parent-byte-join",
        question="Exposed byte custody joins only.",
        requirements=(),
        connections=(),
        operations=(operation,),
        external_inputs=tuple(sorted(externals, key=lambda r: r.input_id)),
        links=tuple(sorted(links, key=lambda r: r.edge_id)),
        selected_operation_ids=(NODE,),
        contribution_parents=tuple(
            sorted((first, second), key=lambda r: r.contribution_id)
        ),
    )
    return (
        draft,
        RecursiveInputOrigins(tuple(sorted(origins, key=lambda r: r.input_id))),
        manifest,
        registration,
    )


def test_multiple_exact_receipt_parents_author_run_export_and_relocate(
    portable_a, monkeypatch, tmp_path
):
    _, _, _, _, plane, first_dir, _ = portable_a
    _, _, first, _, first_products, _ = (
        contributions.authenticate_recursive_contribution(
            directory=first_dir, artifact_writer=plane
        )
    )
    procedure = next(
        r
        for rows in first_products["records"].values()
        for r in rows.values()
        if type(r) is BatteryProcedureContribution
    )
    b = Path(plane.root.contract.canonical_path) / "authored-b"
    _publish_fixture_wave(
        monkeypatch,
        plane,
        b,
        battery_wave_b_draft(first, procedure),
        manifest=first,
        procedure=procedure,
        parent=first_dir,
    )
    second_dir = b.parent / "exported-b"
    contributions.export_recursive_contribution(
        directory=b, output_dir=second_dir, project_root=ROOT, artifact_writer=plane
    )
    _, _, second, _, second_products, _ = (
        contributions.authenticate_recursive_contribution(
            directory=second_dir, artifact_writer=plane
        )
    )
    outcome = next(
        r
        for rows in second_products["records"].values()
        for r in rows.values()
        if type(r) is BatteryFurtherProduct
    )
    assert first.scope != second.scope
    draft, origins, manifest, registration = pair_draft(
        first, second, procedure, outcome
    )
    directories = (
        second_dir,
        first_dir,
    )  # Caller order never rewrites canonical parent order.
    original = _raw_snapshot(first_dir), _raw_snapshot(second_dir)
    codecs = {
        r.SCHEMA: r
        for r in (
            PairConfig,
            PairRead,
            BatteryProcedureContribution,
            BatteryFurtherProduct,
        )
    }
    old_registrations, old_registry, old_codecs = author.operation_catalog()
    codecs = {**old_codecs, **codecs}
    registry = CapabilityRegistry(
        "registry.testing.multiple-parent-byte-join",
        tuple(
            sorted((*old_registry.capabilities, manifest), key=lambda r: r.registry_id)
        ),
    )
    catalog = lambda: ((*old_registrations, registration), registry, codecs)
    monkeypatch.setattr(author, "operation_catalog", catalog)
    monkeypatch.setattr(execution, "operation_catalog", catalog)
    monkeypatch.setattr(
        execution,
        "operation_runners",
        lambda **kwargs: RunnerRegistry(
            (PairRunner(manifest),), registry_sha256=registry.fingerprint()
        ),
    )
    destination = b.parent / "authored-pair"
    authored = author.author_recursive_wave(
        draft=draft,
        project_root=ROOT,
        artifact_writer=plane,
        output_dir=destination,
        contribution_dirs=directories,
        origins=origins,
    )
    _, retained, _, payloads = author.load_authored_wave(
        directory=destination, artifact_writer=plane
    )
    assert retained == draft and "parent-closure.json" not in payloads
    closure = decode_canonical_bytes(
        payloads["parent-closures.json"],
        RecursiveParentClosuresBinding,
        maximum_bytes=None,
    )
    assert tuple(r.contribution for r in closure.bindings) == tuple(
        identity(p, p.contribution_id) for p in draft.contribution_parents
    )
    from empirical_lawhood.api.recursive_inquiry import _inquiry_parent_depth

    # The first wave is both direct and an ancestor of the second; depth is max,
    # not the sum of overlapping branches.
    assert (
        _inquiry_parent_depth(payloads=payloads, draft=draft, artifact_writer=plane)
        == 3
    )
    result = execution.run_recursive_wave(
        directory=destination, project_root=ROOT, artifact_writer=plane
    )
    assert (
        result["status"] == "SUCCEEDED"
        and result["new_native_contact_count"] == 0
        and authored["task_count"] == 1
    )
    result, products, _, _ = execution.read_recursive_wave(
        directory=destination, artifact_writer=plane, include_products=True
    )
    record = products["records"][NODE][NODE + ".join"]
    assert record.procedure == identity(
        procedure, procedure.procedure_id
    ) and record.outcome == identity(outcome, outcome.product_id)

    # Complete ancestry export, including the common first parent, creates no new producing receipt.
    def described(d, p):
        from empirical_lawhood.kernel.references import ArtifactIdentity
        from empirical_lawhood.kernel.scientific_contributions import (
            ContributionProduct,
        )

        receipt = p["receipts"][NODE]
        artifact = next(iter(p["outputs"].values()))
        product = ContributionProduct(
            "product.testing.multiple-parent-byte-join",
            identity(record, record.product_id),
            ArtifactIdentity(
                artifact.logical.logical_artifact_id,
                "scientific-product",
                record.SCHEMA,
                record.fingerprint(),
                "application/json",
                artifact.materialization.size_bytes,
            ),
            identity(receipt, receipt.receipt_id),
            ContributionRole.RETAINED_ANALYSIS_INPUT,
            EvidenceCeiling.NON_PROMOTABLE,
            OutcomeAccess.DEVELOPMENT_VISIBLE,
            VisibilityCeiling.DEVELOPMENT_ONLY,
        )
        return ContributionManifest(
            "contribution.testing.multiple-parent-byte-join",
            d.question,
            "Exposed byte conformance only.",
            first.scope,
            (product,),
            (identity(record, record.product_id),),
            (),
            tuple(identity(p, p.contribution_id) for p in d.contribution_parents),
        )

    original_description = contributions._described
    monkeypatch.setattr(
        contributions,
        "_described",
        lambda d, p: (
            described(d, p)
            if d.draft_id == draft.draft_id
            else original_description(d, p)
        ),
    )
    original_callbacks = contributions._callbacks
    monkeypatch.setattr(
        contributions,
        "_callbacks",
        lambda d, p, name: (
            () if d.draft_id == draft.draft_id else original_callbacks(d, p, name)
        ),
    )
    exported = b.parent / "exported-pair"
    contributions.export_recursive_contribution(
        directory=destination,
        output_dir=exported,
        project_root=ROOT,
        artifact_writer=plane,
    )
    third = _plane(tmp_path / "third-selected")
    copied = Path(third.root.contract.canonical_path) / "imported-pair"
    shutil.copytree(exported, copied)
    transport = decode_canonical_bytes(
        (copied / "transport.json").read_bytes(),
        contributions.PortableRecursiveContribution,
        maximum_bytes=None,
    )
    assert transport.parent_closure_relative_paths == tuple(
        sorted((first_dir.name, second_dir.name))
    )
    assert len({m.relative_path for m in transport.members}) == len(transport.members)
    snapshot = _raw_snapshot(copied)
    inspected = contributions.inspect_recursive_contribution(
        directory=copied, artifact_writer=third
    )
    assert (
        inspected["producing_run_id"] == result["run_id"]
        and _raw_snapshot(copied) == snapshot
    )
    assert (_raw_snapshot(first_dir), _raw_snapshot(second_dir)) == original

    assert recursive_parent_closure_bindings(payloads) == closure.bindings
    first_origin = origins.inputs[0]
    other_parent = next(
        identity(parent, parent.contribution_id)
        for parent in draft.contribution_parents
        if identity(parent, parent.contribution_id) != first_origin.parent
    )
    swapped = replace(
        origins,
        inputs=(replace(first_origin, parent=other_parent), *origins.inputs[1:]),
    )
    with pytest.raises(ValueError, match="product"):
        swapped.validate_draft(draft)
    for dirs in ((first_dir,), (first_dir, first_dir)):
        with pytest.raises(ValueError):
            contributions.contribution_input_bindings(
                directories=dirs, draft=draft, artifact_writer=plane, origins=origins
            )
    with pytest.raises(ValueError, match="exact input origins"):
        contributions.contribution_input_bindings(
            directories=directories, draft=draft, artifact_writer=plane
        )
    with pytest.raises(ValueError, match="exact authenticated"):
        substituted = replace(
            draft,
            contribution_parents=tuple(
                sorted(
                    (replace(first, scope=second.scope), second),
                    key=lambda r: r.contribution_id,
                )
            ),
        )
        contributions.contribution_input_bindings(
            directories=directories,
            draft=substituted,
            artifact_writer=plane,
            origins=origins,
        )
    with pytest.raises(ValueError, match="two different"):
        recursive_parent_closure_bindings(
            {**payloads, "parent-closure.json": closure.bindings[0].canonical_bytes()}
        )
    with pytest.raises(ValueError, match="sorted unique"):
        RecursiveParentClosuresBinding((closure.bindings[0], closure.bindings[0]))
    # Source disguise remains forbidden across the union of direct and ancestral outputs.
    disguised = origins.inputs[0]
    changed = replace(
        disguised,
        kind=RecursiveInputOriginKind.SOURCE,
        scientific_role="SOURCE",
        parent=None,
        product_id=None,
        producing_receipt=None,
    )
    changed_origins = replace(origins, inputs=(changed, *origins.inputs[1:]))
    changed_draft = replace(
        draft,
        external_inputs=tuple(
            replace(r, scientific_role="SOURCE")
            if r.input_id == changed.input_id
            else r
            for r in draft.external_inputs
        ),
    )
    with pytest.raises(ValueError, match="disguises"):
        contributions.contribution_input_bindings(
            directories=directories,
            draft=changed_draft,
            artifact_writer=plane,
            origins=changed_origins,
        )
    # Every parent's full closure remains required even when the child's authored bytes are unchanged.
    artifact = next(
        a
        for a in first_products["outputs"].values()
        if a.logical.content_sha256 == procedure.fingerprint()
    )
    path = first_dir / "custody" / artifact.materialization.relative_path
    old = path.read_bytes()
    try:
        path.write_bytes(b"{}")
        with pytest.raises(ValueError):
            author.load_authored_wave(directory=destination, artifact_writer=plane)
        with pytest.raises(ValueError):
            execution.read_recursive_wave(directory=destination, artifact_writer=plane)
    finally:
        path.write_bytes(old)


def test_parent_collection_is_complete_canonical_census_without_two_parent_limit():
    from empirical_lawhood.runtime.recursive_handoff import (
        RecursiveParentClosureBinding,
        PortableRecursiveContribution,
    )

    values = tuple(
        RecursiveParentClosureBinding(
            "portable-" + key,
            ObjectIdentity(
                "portable." + key,
                PortableRecursiveContribution.SCHEMA,
                "1.0.0",
                key * 64,
            ),
            ObjectIdentity(
                "contribution." + key, ContributionManifest.SCHEMA, "1.0.0", key * 64
            ),
        )
        for key in ("a", "b", "c")
    )
    collection = RecursiveParentClosuresBinding(values)
    assert (
        decode_canonical_bytes(
            collection.canonical_bytes(),
            RecursiveParentClosuresBinding,
            maximum_bytes=None,
        ).bindings
        == values
    )
    assert (
        recursive_parent_closure_bindings(
            {"parent-closures.json": collection.canonical_bytes()}
        )
        == values
    )
    assert (
        recursive_parent_closure_bindings(
            {"parent-closure.json": values[0].canonical_bytes()}
        )
        == values[:1]
    )
    for bad in ((), values[::-1], (values[0], values[0])):
        with pytest.raises(ValueError):
            RecursiveParentClosuresBinding(bad)
    with pytest.raises(ValueError, match="repeat a portable directory"):
        RecursiveParentClosuresBinding(
            (values[0], replace(values[1], relative_path=values[0].relative_path))
        )
