# SPDX-License-Identifier: MPL-2.0
"""Exposed software fixtures; these are not biological/structural qualification."""

from decimal import Decimal as D

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_structure import science


def test_cif_lexical_multiline_quotes_and_loop_shape():
    tables = science.cif_tables(
        'data_fixture\n_note.text\n;first\nsecond\n;\nloop_\n_atom.a\n_atom.b\n1 "O5\'"\n2 .\n'
    )
    assert tables["_note"][0]["text"] == "first\nsecond"
    assert tables["_atom"] == [{"a": "1", "b": "O5'"}, {"a": "2", "b": "."}]
    reserved = science.cif_tables(
        'data_fixture\nloop_\n_a.x\n_a.y\n1 "_atom_site.id"\n2 "loop_"\n'
    )
    assert reserved["_a"] == [
        {"x": "1", "y": "_atom_site.id"},
        {"x": "2", "y": "loop_"},
    ]
    for text in (
        "data_fixture\nloop_\n_a.x\n_a.y\n1\n",
        "data_fixture\n_a.x 1\n_a.x 2\n",
        "data_fixture\n_a.x\n;unterminated\n",
    ):
        with pytest.raises(ValueError):
            science.cif_tables(text)


def fixture_tables():
    scheme, atoms = [], []
    for index, (asym, entity) in enumerate(
        zip("ABCDEFGH", ("1", "2") * 4, strict=True), 1
    ):
        length = 493 if entity == "1" else 138
        for position in range(1, length + 1):
            scheme.append(
                dict(
                    asym_id=asym,
                    entity_id=entity,
                    seq_id=str(position),
                    auth_seq_num=str(position + 17),
                    pdb_ins_code=".",
                    mon_id="ILE" if position == 95 else "ALA",
                    pdb_strand_id=asym,
                )
            )
        position = "210" if entity == "1" else "95"
        atoms.append(
            dict(
                id=str(index),
                label_asym_id=asym,
                auth_asym_id=asym,
                label_entity_id=entity,
                label_seq_id=position,
                auth_seq_id=str(int(position) + 17),
                pdbx_PDB_ins_code=".",
                label_comp_id="KCX" if entity == "1" else "ILE",
                label_atom_id="CA",
                type_symbol="C",
                label_alt_id="A",
                occupancy="0.6",
                Cartn_x=str(index),
                Cartn_y="0",
                Cartn_z="0",
                pdbx_PDB_model_num="1",
            )
        )
    operators = []
    for op, sign in (("1", 1), ("2", -1)):
        row = {"id": op}
        row.update(
            {
                f"matrix[{i}][{j}]": str(
                    sign if i == j and i < 3 else 1 if i == j else 0
                )
                for i in range(1, 4)
                for j in range(1, 4)
            }
        )
        row.update({f"vector[{i}]": "0" for i in range(1, 4)})
        operators.append(row)
    return {
        "_pdbx_struct_oper_list": operators,
        "_pdbx_struct_assembly_gen": [
            dict(
                assembly_id="1",
                oper_expression="1,2",
                asym_id_list=",".join("ABCDEFGH"),
            )
        ],
        "_atom_site": atoms,
        "_entity_poly": [
            dict(entity_id="1", pdbx_seq_one_letter_code_can="A" * 493),
            dict(entity_id="2", pdbx_seq_one_letter_code_can="A" * 94 + "I" + "A" * 43),
        ],
        "_pdbx_poly_seq_scheme": scheme,
    }


def test_full_assembly_maps_missing_positions_activation_and_exact_symmetry(
    monkeypatch,
):
    tables = fixture_tables()
    monkeypatch.setattr(science, "cif_tables", lambda _: tables)
    atoms, chains, operators = science.expand("1BWV", "EXPOSED_FIXTURE")
    assert len(atoms) == 16 and len(chains) == 16 and len(operators) == 2
    assert atoms[0].xyz_angstrom == (D(1), D(0), D(0))
    assert atoms[8].xyz_angstrom == (D(-1), D(0), D(0))
    assert atoms[0].component_id == "KCX" and atoms[0].occupancy == D(".6")
    ssu = chains[1]
    assert len(ssu.residues) == 138
    assert ssu.residues[94] == (95, "112", ".", "ILE", ("CA",))
    assert len([r for r in ssu.residues if not r[4]]) == 137
    views = science.neighborhoods(atoms, chains, (D(3), D(5), D(8)))
    assert len(views) == 8
    assert all(v.author_position == "112" for v in views)
    assert all(len(v.other_chain_minima_angstrom) == 15 for v in views)
    assert tuple(shell for shell, _ in views[0].shells) == (D(3), D(5), D(8))
    assert views[0].query_atom_count == 1
    # Every positive alternate is descriptive, not one invented conformer.
    tables["_atom_site"][1]["occupancy"] = "0"
    atoms, chains, _ = science.expand("1BWV", "EXPOSED_FIXTURE")
    views = science.neighborhoods(atoms, chains, (D(3), D(5), D(8)))
    assert views[0].query_atom_count == 0
    assert all(distance is None for _, distance in views[0].other_chain_minima_angstrom)


def test_selected_assembly_and_full_denominator_refuse_changes(monkeypatch):
    tables = fixture_tables()
    monkeypatch.setattr(science, "cif_tables", lambda _: tables)
    tables["_pdbx_struct_assembly_gen"][0]["oper_expression"] = "1"
    with pytest.raises(ValueError, match="generation"):
        science.expand("1BWV", "EXPOSED_FIXTURE")
    tables["_pdbx_struct_assembly_gen"][0]["oper_expression"] = "1,2"
    tables["_pdbx_poly_seq_scheme"].pop()
    with pytest.raises(ValueError, match="sequence positions"):
        science.expand("1BWV", "EXPOSED_FIXTURE")


def test_full_fasta_refuses_multimember_and_bad_residue():
    assert science.fasta(">exposed\nMI\n") == "MI"
    for text in ("MI", ">one\nMI\n>two\nMI", ">one\nMX"):
        with pytest.raises(ValueError):
            science.fasta(text)


def test_expanded_cif_preserves_every_atom_column_and_independent_maps(monkeypatch):
    from dataclasses import dataclass, replace
    from hashlib import sha256
    from typing import ClassVar

    from empirical_lawhood.kernel.serialization import CanonicalRecord
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure import (
        contracts as c,
    )

    @dataclass(frozen=True, slots=True)
    class ExposedSourceFixture(CanonicalRecord):
        SCHEMA: ClassVar[str] = "empirical-lawhood/exposed-test/structural-source"
        input_id: str
        source_members: tuple[c.StructuralSourceMember, ...]

        @property
        def nomination(self):
            return c.identity(self)

        @property
        def scope(self):
            return c.scope(self)

    tables = fixture_tables()
    for row in tables["_entity_poly"]:
        row["pdbx_strand_id"] = "A,C,E,G" if row["entity_id"] == "1" else "B,D,F,H"
    tables["_struct_asym"] = [
        dict(id=asym, entity_id=entity)
        for asym, entity in zip("ABCDEFGH", ("1", "2") * 4, strict=True)
    ]
    tables["_pdbx_struct_mod_residue"] = [
        dict(
            id="1",
            label_asym_id="A",
            auth_asym_id="A",
            label_seq_id="210",
            auth_seq_id="227",
            parent_comp_id="LYS",
        )
    ]
    tables["_atom_site"][1]["label_atom_id"] = "O5'"
    for row in tables["_atom_site"]:
        row["B_iso_or_equiv"] = "12.34"
        row["pdbx_formal_charge"] = "?"
    actual_parser = science.cif_tables
    monkeypatch.setattr(science, "cif_tables", lambda _: tables)
    atoms, chains, operators = science.expand("1BWV", "EXPOSED_FIXTURE")
    source = ExposedSourceFixture(
        "source.exposed-structure-fixture",
        tuple(
            c.StructuralSourceMember(
                name,
                "https://example.test/exposed-fixture",
                sha256(b"EXPOSED_FIXTURE").hexdigest(),
                "EXPOSED_FIXTURE",
            )
            for name in ("1bwv.cif", "3zxw.cif")
        ),
    )
    inventory = c.StructuralInventory(
        "product.exposed-structure-fixture",
        c.identity(source),
        c.identity(source),
        atoms + tuple(replace(a, pdb_id="3ZXW") for a in atoms),
        chains + tuple(replace(chain, pdb_id="3ZXW") for chain in chains),
        operators,
        (),
        (),
        (),
    )
    product = science.assembly_coordinates(source, inventory)
    assert product.inventory == c.identity(inventory)
    assert len(product.files) == 2
    for _, digest, text in product.files:
        assert sha256(text.encode()).hexdigest() == digest
        expanded = actual_parser(text)
        assert len(expanded["_atom_site"]) == 16
        assert expanded["_atom_site"][8]["Cartn_x"] == "-1"
        assert expanded["_atom_site"][1]["label_atom_id"] == "O5'"
        assert expanded["_atom_site"][1]["occupancy"] == "0.6"
        assert expanded["_atom_site"][1]["B_iso_or_equiv"] == "12.34"
        assert len(expanded["_pdbx_poly_seq_scheme"]) == 8 * (493 + 138)
        assert expanded["_pdbx_poly_seq_scheme"][0]["asym_id"] == "op1_A"
        assert len(expanded["_pdbx_struct_mod_residue"]) == 2
        assert expanded["_pdbx_struct_mod_residue"][1]["auth_asym_id"] == "op2_A"
    with pytest.raises(ValueError, match="bytes changed"):
        replace(
            product,
            files=(
                ("1bwv-assembly1.cif", product.files[0][1], product.files[0][2] + " "),
                product.files[1],
            ),
        )

    # Exposed callback fixture: canonical values retain geometry, but not the
    # original Decimal spelling used by the observed coordinate export.
    from types import SimpleNamespace
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure import (
        recursive_translation as rt,
    )

    reconstructed = replace(
        inventory,
        atoms=(
            replace(inventory.atoms[0], xyz_angstrom=(D("1.0000"), D("-0.000"), D("0.000"))),
            *inventory.atoms[1:],
        ),
    )
    retained_inventory = decode_canonical_bytes(
        reconstructed.canonical_bytes(), c.StructuralInventory, maximum_bytes=None
    )
    assert retained_inventory == reconstructed
    assert retained_inventory.fingerprint() == reconstructed.fingerprint()
    retained_coordinates = science.assembly_coordinates(source, reconstructed)
    assert science.assembly_coordinates(source, retained_inventory) != retained_coordinates
    node = rt.ANALYZE
    config = SimpleNamespace(source=source)
    external = tuple(
        SimpleNamespace(input_id='external.' + node + '.' + name,
                        expected_content_sha256=source.fingerprint(), scientific_role=role)
        for name, role in (('source', 'SOURCE'), ('nomination', 'OUTCOME'))
    )
    draft = SimpleNamespace(external_inputs=external,
                            development_study=SimpleNamespace(numerical_view_ids=()))
    payloads = {'external-' + sha256(row.input_id.encode()).hexdigest()[:24] + '.json': b'exposed-fixture'
                for row in external}
    records = {node: {node + '.inventory': retained_inventory, node + '.coordinates': retained_coordinates},
               rt.ASSESS: None}
    monkeypatch.setattr(rt, '_configs', lambda _: ({node: config}, config))
    monkeypatch.setattr(rt, '_actual_outputs', lambda *_: (config, records))
    monkeypatch.setattr(rt, 'decode_canonical_bytes', lambda *_args, **_kwargs: source)
    monkeypatch.setattr(science, 'validate_source', lambda *_: None)
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure import independent_assessment as independent

    def fixture_independent_inventory(_source, _dossier, actual):
        if actual != reconstructed:
            raise ValueError('actual inventory fails independent source reconstruction')
        return reconstructed, (), D(0), ()

    monkeypatch.setattr(independent, 'validate_observed_inventory', fixture_independent_inventory)
    monkeypatch.setattr(independent, 'validate_coordinate_export', lambda *_: None)
    monkeypatch.setattr(science, 'analyze', lambda *_: pytest.fail('recovery must not execute producer analysis'))
    assert len(rt.inquiry_evidence_projector(draft, payloads, {})) == 4
    # Exact historical export equality is still mandatory, including harmless
    # changed spelling; the correction does not admit a substituted artifact.
    records[node][node + '.coordinates'] = science.assembly_coordinates(source, retained_inventory)
    with pytest.raises(ValueError, match='coordinate export'):
        rt.inquiry_evidence_projector(draft, payloads, {})
    records[node][node + '.coordinates'] = retained_coordinates
    records[node][node + '.inventory'] = replace(
        retained_inventory,
        atoms=(replace(retained_inventory.atoms[0], xyz_angstrom=(D('2'), D(0), D(0))),
               *retained_inventory.atoms[1:]),
    )
    with pytest.raises(ValueError, match='inventory fails'):
        rt.inquiry_evidence_projector(draft, payloads, {})


def test_cold_registration_rosters_have_no_native_engine():
    import subprocess
    import sys

    probe = """
import importlib.abc
import sys
class RefuseNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pybamm', 'openmm'}:
            raise AssertionError('cold structure registration imports a native engine')
sys.meta_path.insert(0, RefuseNative())
from empirical_lawhood.adapters.methods.rubisco_insilico_structure import (
    executable_binding as eb,
    operation_bindings as ob,
)
assert len(eb.EXECUTABLE_BINDING_FACTORIES) == 2
registrations = tuple(declaration.registration() for declaration in ob.operation_declarations())
assert all(not r.native_effect for r in registrations)
assert tuple(name for name, _ in ob.operation_outputs('analyze')) == (
    'coordinates', 'inventory',
)
assert not {'pybamm', 'openmm'}.intersection(sys.modules)
"""
    subprocess.run([sys.executable, "-c", probe], check=True)


def test_registered_assessment_projects_all_phases_with_sorted_limits():
    from dataclasses import replace
    from types import SimpleNamespace
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.recursive_requirements import AssessmentPhase
    from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure import (
        contracts as c,
        operation_bindings as ob,
        recursive_translation as rt,
    )

    scope = c.scope(
        SimpleNamespace(input_id="source.exposed-fixture", fingerprint=lambda: "0" * 64)
    )
    source = ObjectIdentity(
        "source.exposed-fixture", c.StructuralSource.SCHEMA, "1.0.0", "0" * 64
    )
    inventory = ObjectIdentity(
        "product.exposed-inventory", c.StructuralInventory.SCHEMA, "1.0.0", "1" * 64
    )
    nomination = ObjectIdentity(
        "product.exposed-nomination",
        "empirical-lawhood/rubisco-nomination-preparation/exploratory-dossier",
        "1.0.0",
        "2" * 64,
    )
    parent = ObjectIdentity(
        "contribution.exposed-fixture", ContributionManifest.SCHEMA, "1.0.0", "3" * 64
    )
    requirement, connection = rt.requirement_pair(
        scope, parent, "product.exposed-nomination"
    )
    record = c.StructuralAssessment(
        "product.exposed-assessment",
        source,
        inventory,
        nomination,
        scope,
        (),
        (),
        c.A.SATISFIED,
        c.A.UNEVALUABLE,
        c.A.UNEVALUABLE,
        ("ZERO_NEW_BIOLOGICAL_UNITS", "MUTANT_COMPARISON_PENDING"),
    )
    projected = ob.project_assessments(record, requirement, connection)
    assert tuple(row.phase for row in projected) == tuple(AssessmentPhase)
    assert all(
        row.reason_codes == ("MUTANT_COMPARISON_PENDING", "ZERO_NEW_BIOLOGICAL_UNITS")
        for row in projected
    )
    assert all(row.disposition is c.A.SATISFIED for row in projected)
    with pytest.raises(ValueError, match="exact prior scope"):
        ob.project_assessments(
            record,
            replace(
                requirement, scope=replace(scope, source_id="source.other-fixture")
            ),
            connection,
        )


def test_exposed_two_pure_compile_joins_actual_prerequisite_world_and_source_endpoint():
    """Compile only: authentic already exposed bytes plus explicit metadata fixture.

    No native/structural science, scheduler, fake parent admission or actual
    qualification. The compiler and owner validators remain unmocked.
    """
    from dataclasses import replace
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure import (
        contracts as c,
        operation_bindings as ob,
        recursive_translation as rt,
    )
    from tests.test_rubisco_nomination_preparation import parent
    from tests.rubisco_nomination_fixture import nominee, structural_source

    source = structural_source()
    _, dossier = nominee()
    draft = rt.source_mapping_draft(source, dossier, parent=parent(dossier))
    assert draft.development_study.world_id == dossier.scope.world_id
    assert draft.development_study.system.object_id == dossier.scope.system_id
    assert draft.development_study.claims[0].world_id == dossier.scope.world_id
    assert draft.development_study.world_id != c.scope(source).world_id
    rt.inquiry_endpoint_validator(draft, c.scope(source))
    registry = CapabilityRegistry(
        "registry.exposed-structure", tuple(declaration.manifest() for declaration in ob.operation_declarations())
    )

    def compile(selected):
        return compile_recursive_wave(
            draft=selected,
            registrations=tuple(declaration.registration() for declaration in ob.operation_declarations()),
            registry=registry,
            implementation_commit="1" * 40,
            output_codecs=ob.output_codecs(),
        )

    compiled = compile(draft)
    assert len(compiled.execution_plan.tasks) == 2
    assert {task.task_id for task in compiled.execution_plan.tasks} == {
        rt.ANALYZE,
        rt.ASSESS,
    }
    assert compiled.execution_plan.tasks[1].dependency_task_ids == (rt.ANALYZE,)
    # A superficially consistent same-graph claim must not cross world scope.
    wrong_root = replace(
        draft.development_study,
        world_id=c.scope(source).world_id,
        claims=(
            replace(
                draft.development_study.claims[0], world_id=c.scope(source).world_id
            ),
        ),
    )
    with pytest.raises(ValueError):
        compile(replace(draft, development_study=wrong_root))
    # The second selected config is authenticated too, not just its consumer.
    operation = draft.operations[1]
    config = decode_canonical_bytes(
        operation.config_payload.encode(),
        c.StructureOperationConfig,
        maximum_bytes=None,
    )
    altered = replace(
        config,
        nomination_scope=replace(
            config.nomination_scope, receiver_id="receiver.exposed-substitution"
        ),
    )
    from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec

    changed = RecursiveOperationSpec.from_config(
        node_id=operation.node_id,
        selection=operation.selection,
        config_id=altered.config_id,
        config=altered,
        obligation_ids=operation.obligation_ids,
        resource_budget=operation.resource_budget,
    )
    with pytest.raises(ValueError, match="scientific root"):
        compile(replace(draft, operations=(draft.operations[0], changed)))
