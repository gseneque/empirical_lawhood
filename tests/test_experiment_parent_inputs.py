# SPDX-License-Identifier: MPL-2.0
"""Typed parent/source ownership, without opening or qualifying synthetic evidence."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink
from empirical_lawhood.planning.recursive_input_origins import (
    RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins,
)
from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentInputs
from tests.test_experiment_file_inputs import _prepared
from tests.test_experiment_preparation_public import OtherSource, _other_input_scope


def parent_preparation(tmp_path):
    prepared = _prepared(tmp_path)
    record = OtherSource('fixture.parent.product', (2, 3, 5))
    product = ContributionProduct('fixture.product', ObjectIdentity.from_record(record.source_id, record),
        ArtifactIdentity('fixture.parent-artifact', 'model', record.SCHEMA, record.fingerprint(),
            'application/json', len(record.canonical_bytes())),
        ObjectIdentity('fixture.receipt', 'empirical-lawhood/runtime/canonical-task-receipt', '1.0.0', 'e' * 64),
        ContributionRole.DESIGN_OPERAND, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    manifest = ContributionManifest('fixture.parent', 'Synthetic ownership fixture', 'No qualification',
        prepared.draft.requirements[0].scope, (product,),
        (ObjectIdentity('fixture.assessment', 'empirical-lawhood/testing/assessment', '1.0.0', 'f' * 64),), ())
    external = RecursiveExternalInput('external.parent', product.artifact.artifact_id,
        product.artifact.payload_schema, product.artifact.media_type, product.artifact.size_bytes,
        product.outcome_access, product.visibility_ceiling, product.artifact.sha256, 'MODEL')
    draft = replace(prepared.draft, contribution_parents=(manifest,),
        external_inputs=(*prepared.draft.external_inputs, external),
        links=tuple(sorted((*prepared.draft.links, RecursiveInputLink('edge.parent', 'source', 'parent',
            external_input_id=external.input_id, scientific_role='MODEL')), key=lambda row: row.edge_id)))
    origin = RecursiveInputOrigin(external.input_id, RecursiveInputOriginKind.CONTRIBUTION,
        product.artifact.sha256, product.role.value, ObjectIdentity.from_record(manifest.contribution_id, manifest),
        product.product_id, product.producing_receipt)
    source, = prepared.draft.external_inputs
    origins = RecursiveInputOrigins((RecursiveInputOrigin(source.input_id, RecursiveInputOriginKind.SOURCE,
        source.expected_content_sha256, 'SOURCE'), origin))
    return replace(prepared, draft=draft, origins=origins, contribution_dirs=(tmp_path / 'parent',)), record


def test_preparation_keeps_exact_parent_owned_operand_out_of_source_bindings(tmp_path):
    prepared, _ = parent_preparation(tmp_path)
    assert prepared.executable
    assert len(prepared.draft.external_inputs) == 2
    assert len(prepared.input_files) == 1 and prepared.input_records == ()
    assert not prepared.contribution_dirs[0].exists()
    prepared.origins.validate_draft(prepared.draft)


def test_a_parent_only_consumer_needs_no_duplicate_source_record_or_file(tmp_path):
    prepared, _ = parent_preparation(tmp_path)
    external = next(row for row in prepared.draft.external_inputs if row.input_id == 'external.parent')
    draft = replace(prepared.draft, external_inputs=(external,),
        links=tuple(row for row in prepared.draft.links if row.external_input_id != 'external.original'))
    origins = RecursiveInputOrigins(tuple(row for row in prepared.origins.inputs
        if row.kind is RecursiveInputOriginKind.CONTRIBUTION))
    selected = replace(prepared, draft=draft, origins=origins, input_files=())
    assert selected.executable and not selected.input_records and not selected.input_files


@pytest.mark.parametrize('mutation', ('no-origins', 'no-directory', 'relative-directory', 'duplicate-directory',
    'missing-source', 'duplicate-parent-source', 'extra-source', 'receipt', 'parent', 'role', 'digest', 'missing-origin'))
def test_parent_ownership_and_complete_source_union_refuse_substitutions(tmp_path, mutation):
    prepared, record = parent_preparation(tmp_path)
    with pytest.raises(ValueError):
        if mutation == 'no-origins':
            replace(prepared, origins=None)
        elif mutation == 'no-directory':
            replace(prepared, contribution_dirs=())
        elif mutation == 'relative-directory':
            replace(prepared, contribution_dirs=(Path('relative'),))
        elif mutation == 'duplicate-directory':
            replace(prepared, contribution_dirs=prepared.contribution_dirs * 2)
        elif mutation == 'missing-source':
            replace(prepared, input_files=())
        elif mutation == 'duplicate-parent-source':
            replace(prepared, input_records=(('external.parent', record),))
        elif mutation == 'extra-source':
            replace(prepared, input_records=(('external.foreign', record),))
        else:
            source, parent = prepared.origins.inputs
            if mutation == 'receipt':
                parent = replace(parent, producing_receipt=replace(parent.producing_receipt, object_fingerprint='a' * 64))
            elif mutation == 'parent':
                parent = replace(parent, parent=replace(parent.parent, object_fingerprint='a' * 64))
            elif mutation == 'role':
                parent = replace(parent, scientific_role='INSTANCE_PRODUCT')
            elif mutation == 'digest':
                parent = replace(parent, expected_content_sha256='a' * 64)
            origins = RecursiveInputOrigins((parent,) if mutation == 'missing-origin' else (source, parent))
            replace(prepared, origins=origins)


def test_locations_are_opt_in_authenticated_paths_in_an_immutable_mapping(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    specification, records, selection, path, calls, _ = _other_input_scope(tmp_path, monkeypatch)
    observed = []

    def bind(spec, selected, *, record_paths):
        assert spec == specification and selected == records
        assert record_paths == {selection.bindings[0].key: tmp_path / selection.bindings[0].relative_path}
        with pytest.raises(TypeError):
            record_paths['foreign'] = tmp_path
        observed.append(dict(record_paths))
        return PreparedExperimentInputs({})

    declaration, = generated.EXPERIMENT_PROTOCOL_DECLARATIONS
    monkeypatch.setattr(generated, 'EXPERIMENT_PROTOCOL_DECLARATIONS',
        (replace(declaration, bind_input_locations=True, bind_inputs=bind),))
    load_experiment_inputs(specification, path)
    assert len(observed) == 1 and not calls
    member = next(iter(observed[0].values()))
    member.write_bytes(member.read_bytes().replace(b'5', b'7'))
    with pytest.raises(ValueError, match='selected bytes'):
        load_experiment_inputs(specification, path)
    assert len(observed) == 1


@pytest.mark.parametrize('flag', (None, 0, 1, 'yes'))
def test_input_location_flag_requires_exact_boolean(tmp_path, monkeypatch, flag):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    _other_input_scope(tmp_path, monkeypatch)
    declaration, = generated.EXPERIMENT_PROTOCOL_DECLARATIONS
    with pytest.raises(TypeError, match='input locations'):
        replace(declaration, bind_input_locations=flag)
