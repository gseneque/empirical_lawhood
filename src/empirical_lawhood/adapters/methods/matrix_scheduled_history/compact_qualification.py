# SPDX-License-Identifier: MPL-2.0
"""Compact prospective source readiness, complete roots and causal edge checks.

These are candidate checks over supplied ordinary qualification records. They
do not sign credentials, audit scientific truth or authorize execution/reveal.
"""

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import MaterializationQualificationReceipt, SourceAccessDisposition, StudyDraft

from .compact_records import (
    NAMESPACE, ScheduledCompactCommitmentConfig,
    ScheduledCompactConfig, ScheduledCompactForecastConfig,
    ScheduledCompactPhysicalForecastConfig, ScheduledCompactResponseConfig,
    ScheduledCompactCalibrationConfig,
)

from .forecast import CALIBRATED_QUERY, ScheduledPublicSource
from .source_index import ScheduledSourceIndex

COMMIT_KEY = NAMESPACE+'.commit'
CALIBRATE_KEY, QUALIFY_KEY = NAMESPACE+'.calibrate', NAMESPACE+'.calibration-qualify'


def selected_sources(commitment, *, index=None):
    from .qualification import selected_sources as resolve_selected
    return resolve_selected(commitment, index=index)


def cutoffs(commitment, *, sources=None):
    if sources is None:
        sources = selected_sources(commitment)
    return tuple(sorted((InformationCutoff('cutoff.'+s.root_id, s.coordinate.clock_id, CausalPhase.PRE_ACTION,
        s.coordinate.physical_time(s.policy.cutoff_tick)) for s in sources), key=lambda c: c.cutoff_id))


def _qualification(root, context, logical_id, schema, fingerprint, access, visibility, version='1.0.0'):
    refs = tuple(r for r in root.source_materializations if r.source_id == 'external.'+logical_id)
    if len(refs) != 1:
        raise ValueError('scheduled actual source/audit/corpus publication lacks ordinary qualified materialization')
    ref = refs[0]
    quals = tuple(q for q in context.qualifications if type(q) is MaterializationQualificationReceipt
        and q.source_id == ref.source_id)
    expected = ObjectIdentity(logical_id, schema, version, fingerprint)
    if len(quals) != 1:
        raise ValueError('scheduled actual source lacks exact supplied qualification receipt')
    q = quals[0]
    if (ref.materialization != expected or ref.content_sha256 != fingerprint or q.materialization != expected
            or q.content_sha256 != fingerprint or ref.qualification_receipt != ObjectIdentity.from_record(q.receipt_id, q)
            or ref.access_disposition is not SourceAccessDisposition.VERIFIED_ACCESS
            or q.access_disposition is not SourceAccessDisposition.VERIFIED_ACCESS
            or q.evidence_world_id != root.system.world.world_id or ref.evidence_world_id != q.evidence_world_id
            or q.observation_operator != ref.observation_operator or q.numerical_view_ids != ref.numerical_view_ids
            or q.numerical_view_ids != tuple(v.view_id for v in root.system.numerical_views)
            or q.native_unit_ids != tuple(sorted({v.native_unit for v in root.system.quantities}))
            or q.frame_ids != tuple(sorted({v.coordinate_frame for v in root.system.quantities}))
            or q.clock_ids != tuple(v.clock_id for v in root.system.clocks)
            or q.receiver_semantics_id != root.system.relation.relation_id
            or q.validity_contract_id != root.experiment.obligations.validity.validity_id
            or q.uncertainty_contract_id != root.experiment.obligations.uncertainty.uncertainty_id
            or q.outcome_access is not access or q.visibility_ceiling is not visibility):
        raise ValueError('scheduled source/audit/corpus qualification changes exact experiment-specific scope')


# Keep a bounded number of completed pure joins. Each key retains the exact
# immutable compiler inputs, so a new root, credential, link or config tuple
# always receives its own complete validation. No custody or authority effect
# is cached, and per-operation stage/port checks still run for every context.
_BANK_CONTEXTS = []


def _bank_state(context):
    key = (context.root, context.config_inputs, context.qualifications, context.requirements,
        context.connections, context.links, context.known_design_inputs)
    for previous, result in _BANK_CONTEXTS:
        if all(left is right for left, right in zip(previous, key, strict=True)):
            return result
    from .operation_bindings import source_operands
    configs = tuple(v.record for v in context.config_inputs)
    commits = tuple(c for c in configs if type(c) is ScheduledCompactCommitmentConfig)
    allowed = (ScheduledCompactConfig, ScheduledCompactForecastConfig, ScheduledCompactCommitmentConfig,
        ScheduledCompactPhysicalForecastConfig, ScheduledCompactResponseConfig, ScheduledCompactCalibrationConfig)
    if len(commits) != 1 or any(type(c) not in allowed for c in configs):
        raise ValueError('compact scheduled route requires one actual whole-population pre-access bank')
    compact_commit, = commits
    bank = compact_commit.bank
    bank_identity = ObjectIdentity.from_record(bank.bank_id, bank)
    commit = bank.commitment_config()
    index = ScheduledSourceIndex.from_shared(reservation=bank.reservation,
        specification=bank.specification, provenances=bank.provenances)
    sources = selected_sources(commit, index=index)
    complete_sources = tuple(index.resolve(reference) for reference in commit.sources)
    groups = tuple(sorted({s.root.root.independent_group_id for s in sources}))
    descriptors = {s.root_id: s for s in bank.sources}
    source_by_root = {s.root_id: s for s in sources}
    expected = {COMMIT_KEY}
    for s in sources:
        suffix = '-development' if s.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE' else ''
        forecast_role = 'forecast-calibrated' if dict(commit.forecast_design.source_scopes)[s.root_id] == CALIBRATED_QUERY else 'forecast'
        expected |= {NAMESPACE+'.'+s.root_id+'.'+r for r in ('prefix', 'numerical', 'measure', 'check', 'project', forecast_role,
            'continue'+suffix, 'full-numerical'+suffix)}
        if commit.response_selection is not None:
            expected |= {NAMESPACE+'.'+s.root_id+'.'+r for r in ('physical-forecast', 'responses'+suffix, 'response-score'+suffix)}
    if commit.response_selection is not None and commit.response_selection.calibration_criterion is not None:
        expected |= {CALIBRATE_KEY, QUALIFY_KEY}
    if {r.node_id for r in context.config_inputs} != expected or len(configs) != len(expected):
        raise ValueError('compact scheduled route thins complete selected root/paired history/forecast phases')
    for c in configs:
        if type(c) in (ScheduledCompactConfig, ScheduledCompactResponseConfig):
            if c.source != descriptors.get(c.root_id) or c.root_id not in source_by_root or c.bank != bank_identity:
                raise ValueError('compact scheduled phases substitute native source descriptors within one bank')
            if type(c) is ScheduledCompactResponseConfig and (commit.response_selection is None
                    or c.selection != commit.response_selection.identity):
                raise ValueError('compact scheduled pulse phases change original private selection')
        elif type(c) is ScheduledCompactForecastConfig:
            source = source_by_root.get(c.root_id)
            if (source is None or c.public_source != ScheduledPublicSource.from_source(source)
                    or c.design != ObjectIdentity.from_record(commit.forecast_design.design_id, commit.forecast_design)
                    or c.calibrated != (dict(commit.forecast_design.source_scopes)[c.root_id] == CALIBRATED_QUERY)):
                raise ValueError('compact scheduled predictor changes original committed public closure')
        elif type(c) is ScheduledCompactPhysicalForecastConfig:
            source = source_by_root.get(c.root_id)
            if source is None or commit.response_selection is None:
                raise ValueError('compact scheduled response loses complete committed whole-group selection')
            protocol, _ = commit.response_selection.validate_source(source)
            if c.protocol != protocol:
                raise ValueError('compact scheduled physical predictor changes exact public source boundary')
        elif type(c) is ScheduledCompactCalibrationConfig:
            if (c.bank != bank_identity or commit.response_selection is None
                    or commit.response_selection.calibration_criterion is None
                    or c.calibration_id != 'calibration.'+commit.response_selection.selection_id
                    or c.group_ids != groups):
                raise ValueError('compact scheduled calibration changes complete selected original bank')
    root = context.root
    if (type(root) is not StudyDraft or root.system is None or root.experiment is None or root.campaign is None
            or root.unresolved_decisions or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or root.experiment.system_id != root.system.system_id or root.experiment.world_id != root.system.world.world_id
            or tuple(sorted((*root.development_unit_ids, *root.evaluation_unit_ids))) != groups
            or root.development_unit_ids != tuple(sorted({s.root.root.independent_group_id for s in sources if s.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'}))
            or root.experiment.information_cutoffs != cutoffs(commit, sources=sources)
            or not {o for s in complete_sources for o in source_operands(s)} <= {i.object_identity for i in root.design_inputs}
            or not {v.view_id for s in sources for v in (s.coordinate.primary_view, s.coordinate.fine_view)} <= {v.view_id for v in root.system.numerical_views}):
        raise ValueError('scheduled route lacks genuine prospective experiment, original source views or complete group/cutoff scope')
    publications = (commit.reservation.publication, commit.specification.publication,
        commit.audit_publication, *commit.audit.prior_corpus, commit.forecast_design.model_publication,
        commit.forecast_design.training_publication, commit.forecast_design.criterion_publication)
    if commit.forecast_design.calibration_publication is not None:
        # Original sealed score authority is authenticated through the stock
        # qualified-parent connection, separately from source qualification.
        from empirical_lawhood.kernel.recursive_requirements import ContributionRole, ConditionRole
        for source in sources:
            if dict(commit.forecast_design.source_scopes)[source.root_id] != CALIBRATED_QUERY:
                continue
            node = NAMESPACE+'.'+source.root_id+'.forecast-calibrated'
            requirements = tuple(r for r in context.requirements if r.consumer_operation_id == node and r.condition_role is ConditionRole.EVIDENTIAL)
            if len(requirements) != 1:
                raise ValueError('scheduled sealed calibration query lacks exact original qualified-parent requirement')
            req = requirements[0]
            connections = tuple(c for c in context.connections if c.requirement_id == req.requirement_id)
            if (len(connections) != 1 or connections[0].consumer_input_id != 'calibration'
                    or connections[0].evidence_role is not ContributionRole.QUALIFIED_EVIDENTIAL_PARENT
                    or req.scope is None or req.scope.source_config_sha256 != commit.forecast_design.calibration.object_fingerprint
                    or req.scope.population_id != commit.forecast_design.calibration.object_id):
                raise ValueError('scheduled query relabels unqualified/exposed/revealed calibration lineage')
    if commit.response_selection is not None:
        publications += (commit.response_selection_publication, *commit.response_selection.template_publications)
    for pub in publications:
        _qualification(root, context, pub.logical.logical_artifact_id, pub.logical.payload_schema, pub.logical.content_sha256,
            pub.logical.outcome_access, pub.logical.visibility_ceiling,
            version=(commit.audit.census.VERSION if pub.logical.payload_schema == commit.audit.census.SCHEMA else
                commit.response_selection.VERSION if commit.response_selection is not None
                and pub.logical.payload_schema == commit.response_selection.SCHEMA else '1.0.0'))
    _qualification(root, context, bank.bank_id, bank.SCHEMA, bank.fingerprint(), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, bank.VERSION)
    for s in commit.sources:
        descriptor = descriptors[s.root_id]
        if index.resolve(descriptor).reference != s:
            raise ValueError('scheduled source changes its exact shared-parent and root binding')
        _qualification(root, context, descriptor.source_id, descriptor.SCHEMA, descriptor.fingerprint(),
            OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, descriptor.VERSION)
    result = bank, bank_identity, commit, sources, groups, descriptors, source_by_root
    _BANK_CONTEXTS.append((key, result))
    del _BANK_CONTEXTS[:-4]
    return result


def scientific_root_validator(config, context):
    """Validate actual compact configs, source qualifications and causal ports.

    One pure index resolves bounded sources against the exact shared parents.
    This validator checks their complete scientific and executable associations.
    """
    from .operation_bindings import PHASES, phase_access, phase_visibility
    from .response_bindings import RESPONSE_PHASES
    from .calibration_bindings import CALIBRATION_PHASES
    bank, _, commit, sources, groups, descriptors, source_by_root = _bank_state(context)
    role = 'commit' if type(config) is ScheduledCompactCommitmentConfig else 'physical-forecast' if type(config) is ScheduledCompactPhysicalForecastConfig else config.operation
    phase = next(p for p in (*PHASES, *RESPONSE_PHASES, *CALIBRATION_PHASES) if p[0] == role)
    node = COMMIT_KEY if role == 'commit' else NAMESPACE+'.'+role if type(config) is ScheduledCompactCalibrationConfig else NAMESPACE+'.'+config.root_id+'.'+role
    source = source_by_root.get(getattr(config, 'root_id', None))
    config_units = groups if type(config) in (ScheduledCompactCommitmentConfig, ScheduledCompactCalibrationConfig) else (source.root.root.independent_group_id,)
    native = role in ('prefix', 'continue', 'continue-development', 'responses', 'responses-development')
    role_groups = groups if role == 'commit' else tuple(sorted({s.root.root.independent_group_id for s in sources
        if not role.endswith('-development') or s.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'}))
    if role in ('continue', 'full-numerical', 'responses', 'response-score', 'forecast-calibrated'):
        role_groups = tuple(sorted({s.root.root.independent_group_id for s in sources if s.evidence_role != 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'}))
    if (context.node_id != node or context.stage is not phase[3] or context.outcome_access is not phase_access(role)
            or context.visibility_ceiling is not phase_visibility(role) or context.unit_ids != config_units
            or context.selected_unit_ids != role_groups or context.complete_unit_census != native):
        raise ValueError('scheduled phase changes exact stage, native census, role or outcome scope')
    names = {n for n, _ in phase[1] if n not in ('streams', 'prior-coordinates', 'commitment-config') and not (role == 'commit' and n == 'source')
        and not (n == 'calibration' and commit.forecast_design.calibration is None and role != 'calibration-qualify')
        and not (n == 'response-selection' and commit.response_selection is None)
        and not (n == 'physical-forecast' and commit.response_selection is None)
        and n not in ('scores', 'forecasts')}
    if role in ('forecast', 'forecast-calibrated'):
        names.add('forecast-design')
    elif role != 'physical-forecast':
        names.add('bank')
    if role.startswith('response-score'):
        names.add('response-selection')
    if role == 'commit':
        names |= {'source.'+s.root_id for s in commit.sources}
        names |= {'prior-coordinates.'+c.coordinate_id for c in commit.audit.prior_scheduled_coordinates}
    elif native:
        names |= {'streams.'+s.purpose for s in source.root.streams}
        if role.startswith('responses'):
            _, panels = commit.response_selection.validate_source(source)
            names |= {'streams.future.'+s.purpose for p in panels if p.role == 'INDEPENDENT_FUTURE' for s in p.streams}
    elif role == 'calibrate':
        names |= {'scores.'+s.root_id for s in sources} | {'forecasts.'+s.root_id for s in sources}
    elif role == 'calibration-qualify':
        names |= {'full-numericals.'+s.root_id for s in sources}
    incoming = tuple(l for l in context.links if l.consumer_node_id == node)
    if len(incoming) != len(names) or {l.consumer_input_id for l in incoming} != names:
        raise ValueError('scheduled phase omits complete actual source/dependency port census')
    shared = {
        'bank': bank.bank_id,
        'allocation': commit.reservation.publication.logical.logical_artifact_id,
        'selection': commit.specification.publication.logical.logical_artifact_id,
        'audit': commit.audit_publication.logical.logical_artifact_id,
        'forecast-design': commit.forecast_design.design_id,
        'model': commit.forecast_design.model_publication.logical.logical_artifact_id,
        'training': commit.forecast_design.training_publication.logical.logical_artifact_id,
        'criterion': commit.forecast_design.criterion_publication.logical.logical_artifact_id,
    }
    if commit.response_selection is not None:
        shared['response-selection'] = commit.response_selection_publication.logical.logical_artifact_id
    for prior in (commit.audit.census, *commit.audit.prior_scheduled_coordinates):
        pub = next(p for p in commit.audit.prior_corpus if
            (p.logical.payload_schema, p.logical.content_sha256) == (prior.SCHEMA, prior.fingerprint()))
        port = 'prior-census' if prior is commit.audit.census else 'prior-coordinates.'+prior.coordinate_id
        shared[port] = pub.logical.logical_artifact_id
    shared.update({'source.'+s.root_id: descriptors[s.root_id].source_id for s in commit.sources})
    if source is not None:
        shared.update({'source': descriptors[source.root_id].source_id,
            'coordinate': source.coordinate.coordinate_id, 'provenance': source.provenance.identity.object_id})
        shared.update({'streams.'+s.purpose: source.root.stream_identity(s).object_id for s in source.root.streams})
        if role.startswith('responses'):
            _, panels = commit.response_selection.validate_source(source)
            shared.update({'streams.future.'+s.purpose: p.stream_identity(s).object_id
                for p in panels if p.role == 'INDEPENDENT_FUTURE' for s in p.streams})
        if role == 'physical-forecast':
            shared['templates'] = config.protocol.templates.array_artifact.artifact_id
    for link in incoming:
        name = link.consumer_input_id
        if name in ('bank', 'allocation', 'selection', 'audit', 'prior-census', 'coordinate', 'provenance', 'source', 'forecast-design',
                'model', 'training', 'criterion', 'response-selection', 'templates') or name.startswith(('source.', 'streams.', 'prior-coordinates.')):
            if (link.external_input_id != 'external.'+shared[name] or link.producer_node_id is not None
                    or link.scientific_role != 'SOURCE' or link.requirement_id is not None or link.connection_id is not None):
                raise ValueError('scheduled source/audit is not an actual qualified ordinary input')
        elif name == 'calibration' and role == 'forecast-calibrated':
            from empirical_lawhood.kernel.recursive_requirements import ConditionRole
            requirement, = (r for r in context.requirements if r.consumer_operation_id == node
                and r.condition_role is ConditionRole.EVIDENTIAL)
            connection, = (c for c in context.connections if c.requirement_id == requirement.requirement_id)
            if (link.external_input_id != 'external.'+commit.forecast_design.calibration_publication.logical.logical_artifact_id
                    or link.requirement_id != requirement.requirement_id or link.connection_id != connection.connection_id
                    or link.scientific_role != 'HISTORY'):
                raise ValueError('scheduled calibrated forecast lacks original authenticated sealed parent input')
        else:
            if role == 'calibration-qualify' and name.startswith('full-numericals.'):
                root_id = name.split('.', 1)[1]
                owner = 'full-numerical'
            elif role == 'calibrate' and name.startswith(('scores.', 'forecasts.')):
                root_id = name.split('.', 1)[1]
                owner = 'response-score' if name.startswith('scores.') else 'forecast'
            else:
                root_id = getattr(config, 'root_id', '')
                owner = 'prefix' if name.startswith('history') or name == 'checkpoint' else 'project' if name.startswith('causal') or name == 'feature' else 'commit' if name == 'commitment' else 'forecast-calibrated' if name in ('forecast', 'error-forecast') and dict(commit.forecast_design.source_scopes).get(root_id) == CALIBRATED_QUERY else 'forecast' if name == 'error-forecast' else 'calibrate' if role == 'calibration-qualify' and name == 'calibration' else name.removesuffix('-arrays')
            if owner == 'responses' and source.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE':
                owner += '-development'
            producer = COMMIT_KEY if owner == 'commit' else CALIBRATE_KEY if owner == 'calibrate' else NAMESPACE+'.'+root_id+'.'+owner
            output = 'arrays' if name.endswith('-arrays') else 'feature' if name == 'feature' else 'checkpoint' if name == 'checkpoint' else 'product'
            scientific_role = 'SOURCE' if owner == 'commit' else 'HISTORY' if owner == 'prefix' else 'OUTCOME'
            if (link.producer_node_id != producer or link.producer_output_id != output or link.external_input_id is not None
                    or link.scientific_role != scientific_role or link.requirement_id is not None or link.connection_id is not None):
                raise ValueError('scheduled phase changes original producer/output before its native contact')
    if native:
        from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
        validate_parameter_ou_domain(source.coordinate)



def qualified_parent_assessor(*, requirement, connection, contribution, product, parent_evidence):
    """Use the custody assessor over the actual historical or compact plan."""
    from .calibration import qualified_parent_assessor as assess
    return assess(requirement=requirement, connection=connection, contribution=contribution,
        product=product, parent_evidence=parent_evidence)
