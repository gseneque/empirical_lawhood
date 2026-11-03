# SPDX-License-Identifier: MPL-2.0
"""Explicit raw-history/seal graph; no scientific source or authority selection."""

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.planning.study_authoring import StudyDraft

from .commitment import COMMIT_KEY, ScheduledCommitmentConfig
from .forecast import CALIBRATED_QUERY, ScheduledCalibratedForecastConfig, ScheduledForecastConfig, ScheduledPublicSource
from .operation_bindings import BUDGET, NAMESPACE, PHASES, operation_registrations
from .qualification import selected_sources
from .records import ScheduledConfig, identity
from .response_bindings import RESPONSE_PHASES
from .response_selection import ScheduledPhysicalForecastConfig, ScheduledResponseConfig
from .calibration_bindings import CALIBRATION_PHASES, ScheduledCalibrationConfig
from .source_index import ScheduledSourceIndex


def history_draft(*, root, commitment, proof_owners, operational_budgets, draft_id,
        template_bytes=None, calibration_record=None, calibration_requirements=(), calibration_connections=(), calibration_contributions=()):
    """Compose one complete caller-selected bank, preserving its whole groups.

    Stock source qualification, issue/execution/reveal remain external. This
    Response selection additionally supplies actual scheduled pulse branches,
    independent response-error scores and the complete calibration reduction.
    Calibrated queries require callers' original qualified-parent declarations;
    stock authentication replays their actual authority before publication.
    """
    if (type(root) is not StudyDraft or root.campaign is None or root.experiment is None
            or type(commitment) is not ScheduledCommitmentConfig
            or tuple(sorted(set(proof_owners))) != proof_owners):
        raise ValueError('scheduled composition requires actual prospective root, frozen commitment and explicit proof owners')
    index = ScheduledSourceIndex.from_shared(reservation=commitment.reservation,
        specification=commitment.specification, provenances=commitment.provenances)
    index.require_roster(commitment.sources, expected_root_ids=index.root_ids)
    sources = selected_sources(commitment, index=index)
    registrations = {r.selection.capability_key.rsplit('.', 1)[-1]: r for r in operation_registrations()}
    external, records, operations, links = {}, {}, [], []

    def add(record, logical_id=None, publication=None):
        logical_id = publication.logical.logical_artifact_id if publication else logical_id
        if logical_id is None:
            logical_id = record.identity.object_id if type(record) is NumericalProducingProvenance else record.coordinate_id if hasattr(record, 'coordinate_id') else identity(record).object_id
        name = 'external.'+logical_id
        value = RecursiveExternalInput(name, logical_id, record.SCHEMA, 'application/json', None,
            OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, record.fingerprint(), 'SOURCE')
        if external.setdefault(name, value) != value or records.setdefault(logical_id, record) != record:
            raise ValueError('scheduled composition aliases distinct shared source bytes')
        return name

    def node(config, role):
        name = COMMIT_KEY if role == 'commit' else NAMESPACE+'.'+role if type(config) is ScheduledCalibrationConfig else NAMESPACE+'.'+(config.root_id if hasattr(config, 'root_id') else config.source.root_id)+'.'+role
        obligations = tuple(o for o, n in proof_owners if n == name)
        budget = operational_budgets.get(name)
        if not obligations or budget is None or not BUDGET.contains(budget):
            raise ValueError('scheduled composition omits explicit proof owners or contained operational budget')
        operations.append(RecursiveOperationSpec.from_config(node_id=name, selection=registrations[role].selection,
            config_id=config.config_id, config=config, obligation_ids=obligations, resource_budget=budget))
        return name

    def edge(name, port, *, external_id=None, owner=None, output='product'):
        links.append(RecursiveInputLink('edge.'+name+'.'+port, name, port, external_input_id=external_id,
            producer_node_id=owner, producer_output_id=output if owner else None,
            scientific_role='SOURCE' if external_id or owner == COMMIT_KEY else 'HISTORY' if owner and owner.endswith('.prefix') else 'OUTCOME'))

    first, design = index.resolve(commitment.sources[0]), commitment.forecast_design
    name = node(commitment, 'commit')
    for port, record, pub in (('allocation', first.allocation, first.reservation.publication),
            ('selection', first.specification.selection, first.specification.publication), ('audit', commitment.audit, commitment.audit_publication),
            ('model', design.model_record, design.model_publication), ('training', design.training_record, design.training_publication),
            ('criterion', design.criterion_record, design.criterion_publication)):
        edge(name, port, external_id=add(record, publication=pub))
    edge(name, 'forecast-design', external_id=add(design))
    if commitment.response_selection is not None:
        edge(name, 'response-selection', external_id=add(commitment.response_selection, publication=commitment.response_selection_publication))
    for record in (commitment.audit.census, *commitment.audit.prior_scheduled_coordinates):
        pub = next(p for p in commitment.audit.prior_corpus if
            (p.logical.payload_schema, p.logical.content_sha256) == (record.SCHEMA, record.fingerprint()))
        port = 'prior-census' if record is commitment.audit.census else 'prior-coordinates.'+record.coordinate_id
        edge(name, port, external_id=add(record, publication=pub))
    for source in commitment.sources:
        edge(name, 'source.'+source.root_id, external_id=add(source))
    for source in sources:
        suffix = '-development' if source.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE' else ''
        forecast_role = 'forecast-calibrated' if dict(design.source_scopes)[source.root_id] == CALIBRATED_QUERY else 'forecast'
        roles = ('prefix', 'numerical', 'measure', 'check', 'project', forecast_role, 'continue'+suffix, 'full-numerical'+suffix)
        for role in roles:
            cls = ScheduledCalibratedForecastConfig if role == 'forecast-calibrated' else ScheduledForecastConfig
            config = cls('config.'+NAMESPACE+'.'+source.root_id+'.'+role, ScheduledPublicSource.from_source(source), design) if role in ('forecast', 'forecast-calibrated') else ScheduledConfig('config.'+NAMESPACE+'.'+source.root_id+'.'+role, role, source.reference, identity(commitment))
            name = node(config, role)
            for port, _ in next(p for p in PHASES if p[0] == role)[1]:
                if port == 'physical-forecast' and commitment.response_selection is None:
                    continue
                if port == 'streams':
                    for stream in source.root.streams:
                        edge(name, port+'.'+stream.purpose, external_id=add(stream, source.root.stream_identity(stream).object_id))
                elif port in ('source', 'commitment-config', 'forecast-design', 'allocation', 'selection', 'coordinate', 'provenance'):
                    record, pub = {'source': (source.reference, None), 'commitment-config': (commitment, None), 'forecast-design': (design, None),
                        'allocation': (source.allocation, source.reservation.publication),
                        'selection': (source.specification.selection, source.specification.publication),
                        'coordinate': (source.coordinate, None), 'provenance': (source.provenance, None)}[port]
                    edge(name, port, external_id=add(record, publication=pub))
                elif port == 'calibration':
                    pub = design.calibration_publication
                    if calibration_record is None or calibration_record.fingerprint() != design.calibration.object_fingerprint:
                        raise ValueError('scheduled query requires actual original sealed calibration value and qualified-parent declarations')
                    input_id = 'external.'+pub.logical.logical_artifact_id
                    value = RecursiveExternalInput(input_id, pub.logical.logical_artifact_id, pub.logical.payload_schema,
                        pub.logical.media_type, pub.materialization.size_bytes, pub.logical.outcome_access, pub.logical.visibility_ceiling,
                        pub.logical.content_sha256, 'HISTORY')
                    external[input_id], records[pub.logical.logical_artifact_id] = value, calibration_record
                    req = tuple(r for r in calibration_requirements if r.consumer_operation_id == name)
                    conn = tuple(c for c in calibration_connections if len(req) == 1 and c.requirement_id == req[0].requirement_id)
                    if len(req) != 1 or len(conn) != 1 or conn[0].external_input_id != input_id or conn[0].consumer_input_id != 'calibration':
                        raise ValueError('scheduled query omits exact actual qualified-parent calibration connection')
                    links.append(RecursiveInputLink('edge.'+name+'.calibration', name, 'calibration', external_input_id=input_id,
                        scientific_role='HISTORY', requirement_id=req[0].requirement_id, connection_id=conn[0].connection_id))
                elif port == 'commitment':
                    edge(name, port, owner=COMMIT_KEY)
                else:
                    owner = 'prefix' if port.startswith('history') or port == 'checkpoint' else 'project' if port.startswith('causal') or port == 'feature' else forecast_role if port == 'forecast' else port.removesuffix('-arrays')
                    edge(name, port, owner=NAMESPACE+'.'+source.root_id+'.'+owner,
                        output='arrays' if port.endswith('-arrays') else 'feature' if port == 'feature' else 'checkpoint' if port == 'checkpoint' else 'product')
        if commitment.response_selection is not None:
            protocol, panels = commitment.response_selection.validate_source(source)
            for role in ('physical-forecast', 'responses'+suffix, 'response-score'+suffix):
                config = ScheduledPhysicalForecastConfig('config.'+NAMESPACE+'.'+source.root_id+'.'+role, protocol) if role == 'physical-forecast' else ScheduledResponseConfig('config.'+NAMESPACE+'.'+source.root_id+'.'+role, role, source.reference, commitment.response_selection.identity, identity(commitment))
                name = node(config, role)
                for port, _ in next(p for p in RESPONSE_PHASES if p[0] == role)[1]:
                    if port == 'templates':
                        artifact = protocol.templates.array_artifact
                        raw = (template_bytes or {}).get(artifact.artifact_id)
                        from hashlib import sha256
                        if raw is None or len(raw) != artifact.size_bytes or sha256(raw).hexdigest() != artifact.sha256:
                            raise ValueError('scheduled composition omits exact original pre-future template bytes')
                        input_id = 'external.'+artifact.artifact_id
                        external[input_id] = RecursiveExternalInput(input_id, artifact.artifact_id, artifact.payload_schema,
                            artifact.media_type, artifact.size_bytes, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE,
                            artifact.sha256, 'SOURCE')
                        records[artifact.artifact_id] = raw
                        edge(name, port, external_id=input_id)
                    elif port == 'streams':
                        for stream in source.root.streams:
                            edge(name, 'streams.'+stream.purpose, external_id=add(stream, source.root.stream_identity(stream).object_id))
                        for panel in panels:
                            if panel.role == 'INDEPENDENT_FUTURE':
                                for stream in panel.streams:
                                    edge(name, 'streams.future.'+stream.purpose, external_id=add(stream, panel.stream_identity(stream).object_id))
                    elif port in ('source', 'commitment-config', 'allocation', 'selection', 'coordinate', 'provenance', 'response-selection'):
                        record, pub = {'source': (source.reference, None), 'commitment-config': (commitment, None), 'allocation': (source.allocation, source.reservation.publication),
                            'selection': (source.specification.selection, source.specification.publication), 'coordinate': (source.coordinate, None),
                            'provenance': (source.provenance, None), 'response-selection': (commitment.response_selection, commitment.response_selection_publication)}[port]
                        edge(name, port, external_id=add(record, publication=pub))
                    elif port == 'commitment':
                        edge(name, port, owner=COMMIT_KEY)
                    else:
                        owner = 'prefix' if port.startswith('history') or port == 'checkpoint' else 'project' if port.startswith('causal') else forecast_role if port == 'error-forecast' else 'responses'+suffix if port.startswith('responses') else port.removesuffix('-arrays')
                        edge(name, port, owner=NAMESPACE+'.'+source.root_id+'.'+owner,
                            output='arrays' if port.endswith('-arrays') else 'checkpoint' if port == 'checkpoint' else 'product')
    if commitment.response_selection is not None and commitment.response_selection.calibration_criterion is not None:
        calibration_id = 'calibration.'+commitment.response_selection.selection_id
        for role in ('calibrate', 'calibration-qualify'):
            config = ScheduledCalibrationConfig('config.'+NAMESPACE+'.'+role, role, identity(commitment), calibration_id, tuple(sorted({s.root.root.independent_group_id for s in sources})))
            name = node(config, role)
            for port, _ in next(p for p in CALIBRATION_PHASES if p[0] == role)[1]:
                if port == 'commitment':
                    edge(name, port, owner=COMMIT_KEY)
                elif port == 'commitment-config':
                    edge(name, port, external_id=add(commitment))
                elif port == 'calibration':
                    edge(name, port, owner=NAMESPACE+'.calibrate')
                else:
                    for source in sources:
                        edge(name, port+'.'+source.root_id, owner=NAMESPACE+'.'+source.root_id+'.'+('response-score' if port == 'scores' else 'forecast'))
    if set(operational_budgets) != {o.node_id for o in operations}:
        raise ValueError('scheduled composition operational request census differs from selected graph')
    draft = RecursiveStudyDraft(draft_id, root.question, root.campaign, calibration_requirements, calibration_connections, (),
        tuple(sorted(operations, key=lambda o: o.node_id)), tuple(sorted(external.values(), key=lambda e: e.input_id)),
        tuple(sorted(links, key=lambda e: e.edge_id)), tuple(sorted(o.node_id for o in operations)), contribution_parents=calibration_contributions, prospective_draft=root)
    return draft, records
