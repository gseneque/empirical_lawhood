# SPDX-License-Identifier: MPL-2.0
"""Shared graph/source joins with version-specific link and operand contracts."""
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import StudyDraft, SourceAccessDisposition


def validate_protected_root(context, current, *, validate_links, external_fingerprint):
    root = context.root
    if (type(root) is not StudyDraft or root.system is None or root.experiment is None
            or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or root.experiment.system_id != root.system.system_id
            or root.experiment.world_id != root.system.world.world_id):
        raise ValueError("protected E3 requires its actual prospective numerical StudyDraft")
    units = tuple(sorted(source.root.root.independent_group_id for source in current.roots.values()))
    if root.evaluation_unit_ids != units or set(root.development_unit_ids) & set(units):
        raise ValueError("protected E3 root changes its exact independent CAL/CONF population")
    pins = {record.object_identity for record in root.design_inputs
        if record.materialization_sha256 == record.object_identity.object_fingerprint}
    if not {current.fit.specification, current.fit.allocation, current.fit.source_manifest, current.fit.training_allocation}.issubset(pins):
        raise ValueError("protected E3 root loses exact specification/allocation/original-source design references")
    incoming = validate_links(context.config_inputs, context.links)
    externals = {row.input_id: row for row in context.external_inputs}
    sources = {row.source_id: row for row in root.source_materializations}
    qualifications = {ObjectIdentity.from_record(row.receipt_id, row): row for row in context.qualifications}
    used = set()
    for node, by_name in incoming.items():
        config = current.by_task[node]
        for name, link in by_name.items():
            if link.external_input_id is None:
                continue
            used.add(link.external_input_id)
            external = externals.get(link.external_input_id)
            source = sources.get(link.external_input_id)
            qualification = qualifications.get(None if source is None else source.qualification_receipt)
            if external is None or source is None or qualification is None:
                raise ValueError("protected E3 source loses its direct ordinary qualification reference")
            fingerprint = external_fingerprint(config, name, current)
            if (external.parent_substitution or source.access_disposition is not SourceAccessDisposition.VERIFIED_ACCESS
                    or source.source_id != qualification.source_id or source.materialization != qualification.materialization
                    or source.evidence_world_id != root.system.world.world_id or qualification.evidence_world_id != source.evidence_world_id
                    or source.observation_operator != qualification.observation_operator or source.numerical_view_ids != qualification.numerical_view_ids
                    or (source.materialization.object_id, source.materialization.object_schema, source.materialization.object_fingerprint,
                        source.content_sha256, qualification.content_sha256) != (external.logical_artifact_id, external.payload_schema,
                            external.expected_content_sha256, external.expected_content_sha256, external.expected_content_sha256)
                    or (qualification.outcome_access, qualification.visibility_ceiling) != (external.outcome_access, external.visibility_ceiling)
                    or fingerprint is not None and external.expected_content_sha256 != fingerprint):
                raise ValueError("protected E3 source substitutes exact ordinary bytes, qualification or information scope")
    if used != set(externals):
        raise ValueError("protected E3 graph changes the complete selected ordinary external-input census")


def validate_protected_links(config_inputs, links, *, current, declaration_key, expected_producers, role):
    """Refuse missing or bypassed producers before a lowered graph is returned."""
    incoming = {node: {} for node in current.by_task}
    for link in links:
        if link.consumer_node_id not in incoming or link.consumer_input_id in incoming[link.consumer_node_id]:
            raise ValueError("protected E3 graph changes its complete consumer/input census")
        incoming[link.consumer_node_id][link.consumer_input_id] = link
    for node, config in current.by_task.items():
        expected = expected_producers(config, config_inputs)
        actual = incoming[node]
        matched = set()
        declaration = current.declarations[declaration_key(config)]
        for name, producer in expected.items():
            names = tuple(key for key in actual if key.startswith(name[:-1])) if name.endswith(".*") else ((name,) if name in actual else ())
            if name.endswith(".*"):
                port = next(port for port in declaration.input_ports if port.port_id == name.removesuffix(".*"))
            else:
                port = next(port for port in declaration.input_ports if port.matches(name))
            if (not names or len(names) < port.minimum_count or port.maximum_count is not None and len(names) > port.maximum_count):
                raise ValueError("protected E3 graph drops a complete scientific input or original source census")
            for key in names:
                link = actual[key]
                if ((link.producer_node_id, link.producer_output_id) != ((None, None) if producer is None else producer)
                        or (link.external_input_id is not None) != (producer is None)
                        or link.scientific_role != role(config, key, producer)):
                    raise ValueError("protected E3 graph bypasses its exact fit/freeze/forecast-before-future producer")
                matched.add(key)
        if matched != set(actual):
            raise ValueError("protected E3 graph adds an undeclared source or scientific input")
    return incoming

