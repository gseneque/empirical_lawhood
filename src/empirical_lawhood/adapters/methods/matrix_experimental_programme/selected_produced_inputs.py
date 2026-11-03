# SPDX-License-Identifier: MPL-2.0
"""Pure inherited access for actual selected scientific product parents.

The API independently authenticates the exact parent census. These helpers
only preserve its immutable labels in cold graphs; they authorize no access.
"""
from dataclasses import fields, is_dataclass, replace

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, derived_outcome_access, lineage_parent_sort_key


def validate_produced_input_parents(parents):
    if (type(parents) is not tuple or not parents or any(type(value) is not ArtifactLineageParent
            or type(value.identity) is not ObjectIdentity or type(value.visibility_ceiling) is not VisibilityCeiling
            or type(value.outcome_access) is not OutcomeAccess for value in parents)
            or parents != tuple(sorted(set(parents), key=lineage_parent_sort_key))
            or len({value.identity for value in parents}) != len(parents)):
        raise ValueError('selected inputs require the exact sorted original produced-parent census')
    for value in parents:
        value.identity.__post_init__()


def produced_record_parents(record, parents):
    """Identify exact retained product bodies or pins, without name heuristics."""
    if not parents:
        return ()
    validate_produced_input_parents(parents)
    pins = {value.identity for value in parents}
    fingerprints = {(pin.object_schema, pin.object_fingerprint) for pin in pins}
    schemas = {schema for schema, _ in fingerprints}
    visited = set()

    def contains(value):
        if type(value) is ObjectIdentity:
            return value in pins
        if id(value) in visited:
            return False
        visited.add(id(value))
        if isinstance(value, CanonicalRecord) and value.SCHEMA in schemas:
            if (value.SCHEMA, value.fingerprint()) in fingerprints:
                return True
        if is_dataclass(value) and not isinstance(value, type):
            return any(contains(getattr(value, field.name)) for field in fields(value))
        if type(value) in (tuple, list):
            return any(contains(item) for item in value)
        if type(value) is dict:
            return any(contains(item) for item in value.values())
        return False

    return parents if contains(record) else ()


def produced_access(*, declared_access, declared_visibility, parents):
    access = derived_outcome_access(declared_access, *(value.outcome_access for value in parents))
    return access, inherited_visibility((declared_visibility, *(value.visibility_ceiling for value in parents)), access)


def inherit_external_inputs(external, records, parents, *, retained_history=False):
    """Inherit custody labels; selected-prepared owners choose HISTORY explicitly."""
    by_input = dict(records)
    result = []
    for item in external:
        selected = produced_record_parents(by_input.get(item.input_id), parents)
        if selected:
            access, visibility = produced_access(declared_access=item.outcome_access,
                declared_visibility=item.visibility_ceiling, parents=selected)
            item = replace(item, scientific_role="HISTORY" if retained_history else item.scientific_role,
                outcome_access=access, visibility_ceiling=visibility)
        result.append(item)
    return tuple(result)


def inherit_external_links(links, external):
    """Keep each external edge at the exact role of its selected operand."""
    roles = {value.input_id: value.scientific_role for value in external}
    return tuple(replace(link, scientific_role=roles[link.external_input_id])
        if link.external_input_id is not None else link for link in links)


def produced_history_parents(external, record, parents):
    """Validate a code-owned retained canonical input; grant no actual access."""
    selected = produced_record_parents(record, parents)
    if bool(selected) != (external.scientific_role == "HISTORY"):
        raise ValueError("selected produced canonical inputs require their exact retained HISTORY role")
    if not selected:
        return ()
    if (not isinstance(record, CanonicalRecord) or external.media_type != "application/json"
            or (record.SCHEMA, record.fingerprint(), len(record.canonical_bytes())) != (
                external.payload_schema, external.expected_content_sha256, external.maximum_size_bytes)
            or produced_access(declared_access=external.outcome_access,
                declared_visibility=external.visibility_ceiling, parents=selected) != (
                    external.outcome_access, external.visibility_ceiling)):
        raise ValueError("selected retained HISTORY changes exact canonical bytes or inherited custody")
    return selected
