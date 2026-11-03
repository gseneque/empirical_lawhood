# SPDX-License-Identifier: MPL-2.0
"""Pure inherited metadata controls; none of these pins grant data access."""
from dataclasses import dataclass, replace
from typing import ClassVar

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_produced_inputs as owner
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, lineage_parent_sort_key


@dataclass(frozen=True, slots=True)
class _ProducedBody(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/tests/selected-produced-body'
    record_id: str
    value: int


@dataclass(frozen=True, slots=True)
class _Consumer(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/tests/selected-produced-consumer'
    record_id: str
    product: ObjectIdentity


def _case():
    body = _ProducedBody('product.original', 7)
    pin = ObjectIdentity.from_record(body.record_id, body)
    receipt = ObjectIdentity('receipt.original', 'empirical-lawhood/runtime/canonical-task-receipt', '1.0.0', 'b' * 64)
    parents = tuple(sorted((ArtifactLineageParent(pin, VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED),
        ArtifactLineageParent(receipt, VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED)),
        key=lineage_parent_sort_key))
    return body, pin, parents


def _external(name, record, *, access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility=VisibilityCeiling.DEVELOPMENT_ONLY):
    return RecursiveExternalInput(name, record.record_id, record.SCHEMA, 'application/json',
        len(record.canonical_bytes()), access, visibility, record.fingerprint(), 'SOURCE')


@pytest.mark.parametrize("retained_history", (False, True))
def test_actual_nested_product_pin_inherits_the_whole_original_product_receipt_census(retained_history):
    body, pin, parents = _case()
    consumer = _Consumer('consumer.model-bearing', pin)
    external = _external('model', consumer)
    inherited, = owner.inherit_external_inputs((external,), (('model', consumer),), parents, retained_history=retained_history)
    assert owner.produced_record_parents(body, parents) == parents
    assert owner.produced_record_parents(consumer, parents) == parents
    assert inherited == replace(external, scientific_role="HISTORY" if retained_history else "SOURCE", outcome_access=OutcomeAccess.EVALUATION_REVEALED,
        visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE)
    if retained_history:
        assert owner.produced_history_parents(inherited, consumer, parents) == parents
    else:
        with pytest.raises(ValueError, match="HISTORY"):
            owner.produced_history_parents(inherited, consumer, parents)


def test_matching_product_id_without_its_exact_digest_does_not_claim_original_ancestry():
    _, pin, parents = _case()
    foreign = _Consumer('consumer.foreign', replace(pin, object_fingerprint='c' * 64))
    external = _external('foreign', foreign)
    assert owner.produced_record_parents(foreign, parents) == ()
    assert owner.inherit_external_inputs((external,), (('foreign', foreign),), parents) == (external,)


def test_independent_future_input_keeps_its_sealed_contract_despite_revealed_originals():
    _, _, parents = _case()
    independent = _ProducedBody('independent.future-input', 9)
    external = _external('future', independent, access=OutcomeAccess.EVALUATION_SEALED,
        visibility=VisibilityCeiling.PROSPECTIVE)
    assert owner.inherit_external_inputs((external,), (('future', independent),), parents) == (external,)


def test_new_sealed_outcome_is_not_relabelled_by_development_parent_but_revealed_parent_cannot_be_resealed():
    _, pin, parents = _case()
    development = (ArtifactLineageParent(pin, VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE),)
    assert owner.produced_access(declared_access=OutcomeAccess.EVALUATION_SEALED,
        declared_visibility=VisibilityCeiling.PROSPECTIVE, parents=development) == (
            OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.DEVELOPMENT_ONLY)
    assert owner.produced_access(declared_access=OutcomeAccess.EVALUATION_SEALED,
        declared_visibility=VisibilityCeiling.PROSPECTIVE, parents=parents) == (
            OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE)


@pytest.mark.parametrize('change', ('missing', 'repeated', 'reordered', 'conflicting-label'))
def test_produced_parent_census_refuses_missing_repeated_reordered_or_conflicting_metadata(change):
    _, _, parents = _case()
    changed = {'missing': (), 'repeated': (*parents, parents[0]), 'reordered': tuple(reversed(parents)),
        'conflicting-label': tuple(sorted((*parents, replace(parents[0],
            outcome_access=OutcomeAccess.OUTCOME_BLIND)), key=lineage_parent_sort_key))}[change]
    with pytest.raises(ValueError, match='exact sorted original produced-parent census'):
        owner.validate_produced_input_parents(changed)


def test_request_parent_declaration_is_compared_with_fresh_independent_actual_metadata(monkeypatch):
    """Instrument the metadata owner only; this does not simulate real custody."""
    from types import SimpleNamespace
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative import derivation
    _, _, parents = _case()
    request = SimpleNamespace(revision=None, original_e3_products=('actual-locators',),
        original_e3_nomination=None, produced_input_parents=parents)
    observed = []
    current = [parents]
    def actual(writer, *, originals, development=()):
        observed.append((writer, originals, development))
        return current[0]
    monkeypatch.setattr(derivation, 'selected_produced_input_parents', actual)
    writer = object()
    derivation.require_produced_input_parents(writer, request)
    current[0] = tuple(replace(value, outcome_access=OutcomeAccess.OUTCOME_BLIND) for value in parents)
    with pytest.raises(PermissionError, match='exact actual produced-input'):
        derivation.require_produced_input_parents(writer, request)
    assert observed == [(writer, request.original_e3_products, ())] * 2


@pytest.mark.parametrize("damage", ("independent-history", "produced-source", "changed-bytes", "lost-custody"))
def test_history_role_requires_exact_canonical_parent_binding_and_custody(damage):
    _, pin, parents = _case()
    record = _Consumer("consumer.retained", pin)
    external, = owner.inherit_external_inputs((_external("model", record),), (("model", record),), parents, retained_history=True)
    if damage == "independent-history":
        record = replace(record, product=replace(pin, object_fingerprint="d" * 64))
        external = replace(_external("model", record), scientific_role="HISTORY")
    elif damage == "produced-source":
        external = replace(external, scientific_role="SOURCE")
    elif damage == "changed-bytes":
        external = replace(external, expected_content_sha256="d" * 64)
    else:
        external = replace(external, outcome_access=OutcomeAccess.OUTCOME_BLIND,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE)
    with pytest.raises(ValueError, match="HISTORY"):
        owner.produced_history_parents(external, record, parents)


def test_retained_history_has_no_ordinary_qualification_but_physical_sources_still_require_it():
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as domain
    _, pin, parents = _case()
    record = _Consumer("consumer.retained", pin)
    history, = owner.inherit_external_inputs((_external("model", record),), (("model", record),), parents, retained_history=True)
    request = SimpleNamespace(produced_input_parents=parents, qualifications=(), source_configs=())
    draft = SimpleNamespace(external_inputs=(history,))
    assert domain.source_dependencies(draft, request, (("model", record),)) == []
    independent = _ProducedBody("independent.physical", 11)
    source = _external("physical", independent)
    draft = SimpleNamespace(external_inputs=(history, source))
    dependencies = domain.source_dependencies(draft, request, (("model", record), ("physical", independent)))
    assert len(dependencies) == 2 and {value.source_key for value in dependencies} == {"physical"}
    request.qualifications = (SimpleNamespace(source_id="model"),)
    with pytest.raises(ValueError, match="foreign source IDs"):
        domain.source_dependencies(SimpleNamespace(external_inputs=(history,)), request, (("model", record),))


def test_external_history_link_projection_keeps_internal_edges_and_exact_source_census():
    from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink
    _, pin, parents = _case()
    record = _Consumer("consumer.retained", pin)
    history, = owner.inherit_external_inputs((_external("model", record),), (("model", record),), parents, retained_history=True)
    source = _external("physical", _ProducedBody("independent.physical", 11))
    links = (RecursiveInputLink("edge.model", "consumer", "model", external_input_id="model", scientific_role="SOURCE"),
        RecursiveInputLink("edge.physical", "consumer", "physical", external_input_id="physical", scientific_role="SOURCE"),
        RecursiveInputLink("edge.internal", "consumer", "history", producer_node_id="producer", producer_output_id="product", scientific_role="HISTORY"))
    projected = owner.inherit_external_links(links, (history, source))
    assert projected == (replace(links[0], scientific_role="HISTORY"), links[1], links[2])
