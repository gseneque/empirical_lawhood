# SPDX-License-Identifier: MPL-2.0
"""Explicit ownership joins; exposed synthetic custody is not scientific evidence."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_input_origins import (
    RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins, contribution_graph_role,
)
from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution, contribution_input_bindings
from tests.test_recursive_contribution_custody import portable_a  # noqa: F401, F811


def _mixed(manifest):
    product = manifest.products[0]
    parent = ObjectIdentity.from_record(manifest.contribution_id, manifest)
    contributed = RecursiveInputOrigin("parent.input", RecursiveInputOriginKind.CONTRIBUTION,
        product.artifact.sha256, product.role.value, parent, product.product_id, product.producing_receipt)
    source = RecursiveInputOrigin("source.input", RecursiveInputOriginKind.SOURCE, "a"*64, "SOURCE")
    origins = RecursiveInputOrigins((contributed, source))
    externals = tuple(SimpleNamespace(input_id=value.input_id, expected_content_sha256=value.expected_content_sha256,
        scientific_role=(value.scientific_role if value.kind is RecursiveInputOriginKind.SOURCE else contribution_graph_role(value.scientific_role)), parent_substitution=False, logical_artifact_id=value.input_id,
        payload_schema=product.artifact.payload_schema, outcome_access=product.outcome_access,
        visibility_ceiling=product.visibility_ceiling) for value in origins.inputs)
    draft = SimpleNamespace(contribution_parents=(manifest,), external_inputs=externals,
        selected_operation_ids=("consumer",), links=tuple(SimpleNamespace(consumer_node_id="consumer", external_input_id=v.input_id) for v in origins.inputs))
    return draft, origins


def test_exact_parent_product_and_new_source_resolve_only_declared_product(portable_a):  # noqa: F811
    _, _, _, _, plane, imported, _ = portable_a
    _, _, manifest, _, _, _ = authenticate_recursive_contribution(directory=imported, artifact_writer=plane)
    draft, origins = _mixed(manifest)
    origins.validate_draft(draft)
    assert decode_canonical_bytes(origins.canonical_bytes(), RecursiveInputOrigins, maximum_bytes=1024**2) == origins
    bindings = contribution_input_bindings(directory=imported, draft=draft, artifact_writer=plane, origins=origins)
    assert tuple(input_id for input_id, _ in bindings) == ("parent.input",)
    assert bindings[0][1].read_bytes()


@pytest.mark.parametrize("change", ["parent", "product", "receipt", "digest", "role", "source", "missing", "duplicate"])
def test_origin_adversarial_joins_refuse(portable_a, change):  # noqa: F811
    _, _, _, _, plane, imported, _ = portable_a
    _, _, manifest, _, _, _ = authenticate_recursive_contribution(directory=imported, artifact_writer=plane)
    draft, origins = _mixed(manifest)
    parent, source = origins.inputs
    with pytest.raises(ValueError):
        if change == "parent":
            parent = replace(parent, parent=replace(parent.parent, object_fingerprint="b"*64))
        elif change == "product":
            parent = replace(parent, product_id="absent.product")
        elif change == "receipt":
            parent = replace(parent, producing_receipt=replace(parent.producing_receipt, object_fingerprint="b"*64))
        elif change == "digest":
            parent = replace(parent, expected_content_sha256="b"*64)
        elif change == "role":
            parent = replace(parent, scientific_role="INSTANCE_PRODUCT" if parent.scientific_role != "INSTANCE_PRODUCT" else "DESIGN_OPERAND")
        elif change == "source":
            parent = replace(parent, kind=RecursiveInputOriginKind.SOURCE, parent=None, product_id=None, producing_receipt=None)
        candidates = (parent,) if change == "missing" else ((parent, parent, source) if change == "duplicate" else (parent, source))
        changed = RecursiveInputOrigins(candidates)
        contribution_input_bindings(directory=imported, draft=draft, artifact_writer=plane, origins=changed)


def test_unexported_parent_checkpoint_cannot_be_source_at_authoring_or_retained_load(portable_a, monkeypatch):  # noqa: F811
    from hashlib import sha256
    from pathlib import Path
    from empirical_lawhood.api import recursive_authoring as author
    from empirical_lawhood.api.recursive_contributions import _publish
    from empirical_lawhood.adapters.methods.battery_recursive_construction.contracts import BatteryProcedureContribution
    from empirical_lawhood.adapters.methods.battery_recursive_construction.examples import battery_wave_b_draft
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveParentClosureBinding, RecursiveWaveMember

    from empirical_lawhood.api import recursive_contributions as contributions
    import shutil

    producer, original_directory, _, _, plane, _, _ = portable_a
    original_describer = contributions._described
    def subset_description(draft, products):
        manifest = original_describer(draft, products)
        return replace(manifest, products=tuple(value for value in manifest.products
            if not value.artifact.payload_schema.endswith("checkpoint")))
    # This exposed software fixture projects only some authentic products into
    # the public contribution. The omitted checkpoint remains in receipt custody.
    monkeypatch.setattr(contributions, "_described", subset_description)
    original_callbacks = contributions._callbacks
    monkeypatch.setattr(contributions, "_callbacks", lambda draft, products, name:
        () if name == "next_wave_builder" else original_callbacks(draft, products, name))
    exported = Path(producer.root.contract.canonical_path) / "subset-export"
    contributions.export_recursive_contribution(directory=original_directory, output_dir=exported,
        project_root=Path(__file__).resolve().parents[1], artifact_writer=producer)
    imported = Path(plane.root.contract.canonical_path) / "subset-import"
    shutil.copytree(exported, imported)
    _, transport, manifest, _, products, view = authenticate_recursive_contribution(directory=imported, artifact_writer=plane)
    exported_digests = {product.artifact.sha256 for product in manifest.products}
    checkpoint_artifact = next(value for value in products["outputs"].values()
        if value.logical.content_sha256 not in exported_digests and value.logical.payload_schema.endswith("checkpoint"))
    checkpoint_path = view.root.resolve(checkpoint_artifact.materialization.relative_path, for_write=False)
    procedure = next(record for values in products["records"].values() for record in values.values()
        if isinstance(record, BatteryProcedureContribution))
    draft = battery_wave_b_draft(manifest, procedure)
    old_source = next(value for value in draft.external_inputs if value.input_id == "battery.parent.manifest")
    source = replace(old_source, expected_content_sha256=checkpoint_artifact.logical.content_sha256,
        payload_schema=checkpoint_artifact.logical.payload_schema, scientific_role="SOURCE")
    draft = replace(draft, external_inputs=tuple(source if value.input_id == source.input_id else value for value in draft.external_inputs))
    product = next(value for value in manifest.products if value.artifact.sha256 == procedure.fingerprint())
    draft = replace(draft, external_inputs=tuple(replace(value, scientific_role=contribution_graph_role(product.role))
        if value.input_id == "battery.parent.procedure" else value for value in draft.external_inputs))
    origins = RecursiveInputOrigins(tuple(sorted((
        RecursiveInputOrigin(source.input_id, RecursiveInputOriginKind.SOURCE, source.expected_content_sha256, "SOURCE"),
        RecursiveInputOrigin("battery.parent.procedure", RecursiveInputOriginKind.CONTRIBUTION,
            product.artifact.sha256, product.role.value, ObjectIdentity.from_record(manifest.contribution_id, manifest),
            product.product_id, product.producing_receipt)), key=lambda value: value.input_id)))
    origins.validate_draft(draft)  # Only actual receipt custody reveals the omitted product.
    with pytest.raises(ValueError, match="authenticated parent-produced output"):
        contribution_input_bindings(directory=imported, draft=draft, artifact_writer=plane, origins=origins)
    root = Path(plane.root.contract.canonical_path)
    with pytest.raises(ValueError, match="authenticated parent-produced output"):
        author.author_recursive_wave(draft=draft, project_root=Path(__file__).resolve().parents[1], artifact_writer=plane,
            output_dir=root / "rejected-author", input_bindings=((source.input_id, checkpoint_path),),
            contribution_dir=imported, origins=origins)
    assert not (root / "rejected-author").exists()
    # Build an otherwise byte-authenticated authored packet to exercise the read
    # boundary independently of the refusing public authoring boundary.
    _, _, implementation, _ = author.load_authored_wave(
        directory=imported / "custody" / transport.authoring_relative_path, artifact_writer=view)
    closure = RecursiveParentClosureBinding(imported.relative_to(root).as_posix(),
        ObjectIdentity.from_record(transport.transport_id, transport), ObjectIdentity.from_record(manifest.contribution_id, manifest))
    records = {"draft.json": draft, "implementation.json": implementation, "origins.json": origins, "parent-closure.json": closure}
    for origin in origins.inputs:
        raw = checkpoint_path.read_bytes() if origin.kind is RecursiveInputOriginKind.SOURCE else procedure.canonical_bytes()
        codec = type(procedure) if origin.kind is RecursiveInputOriginKind.CONTRIBUTION else type(next(record
            for values in products["records"].values() for record in values.values() if record.fingerprint() == origin.expected_content_sha256))
        records["external-" + sha256(origin.input_id.encode()).hexdigest()[:24] + ".json"] = decode_canonical_bytes(raw, codec, maximum_bytes=16*1024**2)
    members = tuple(RecursiveWaveMember(name, ObjectIdentity.from_record(draft.draft_id if name == "draft.json"
        else "recursive-member." + name.removesuffix(".json"), record), len(record.canonical_bytes())) for name, record in sorted(records.items()))
    identities = {member.filename: member.identity for member in members}
    packet = AuthoredRecursiveWave("packet.disguised", identities["draft.json"], identities["implementation.json"], members)
    directory = root / "retained-disguised"
    directory.mkdir()
    for name, record in (*records.items(), ("authored-wave.json", packet)):
        _publish(plane, directory, name, record, packet.packet_id)
    with pytest.raises(ValueError, match="authenticated parent-produced output"):
        author.load_authored_wave(directory=directory, artifact_writer=plane)


def test_portable_roles_project_to_existing_graph_roles_without_changing_origin_bytes():
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    from empirical_lawhood.runtime.plans import ScientificInputRole
    expected = ((ContributionRole.DESIGN_OPERAND, ScientificInputRole.MODEL),
                (ContributionRole.QUALIFIED_EVIDENTIAL_PARENT, ScientificInputRole.QUALIFICATION),
                (ContributionRole.RETAINED_ANALYSIS_INPUT, ScientificInputRole.HISTORY),
                (ContributionRole.INSTANCE_PRODUCT, ScientificInputRole.OUTCOME))
    for role, graph_role in expected:
        assert contribution_graph_role(role) == graph_role.value


def test_graph_role_substitution_refuses_even_with_correct_portable_role(portable_a):  # noqa: F811
    _, _, _, _, plane, imported, _ = portable_a
    _, _, manifest, _, _, _ = authenticate_recursive_contribution(directory=imported, artifact_writer=plane)
    draft, origins = _mixed(manifest)
    before = origins.canonical_bytes()
    origins.validate_draft(draft)
    assert origins.canonical_bytes() == before
    parent_input = draft.external_inputs[0]
    wrong = SimpleNamespace(**{**vars(parent_input), 'scientific_role': 'MODEL' if parent_input.scientific_role != 'MODEL' else 'HISTORY'})
    changed = SimpleNamespace(**{**vars(draft), 'external_inputs': (wrong, *draft.external_inputs[1:])})
    with pytest.raises(ValueError, match='digest or role'):
        origins.validate_draft(changed)
