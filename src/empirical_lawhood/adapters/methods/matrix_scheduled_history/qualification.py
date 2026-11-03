# SPDX-License-Identifier: MPL-2.0
"""Existing prospective source readiness, complete roots and causal edge checks.

These are candidate checks over supplied ordinary qualification records. They
do not sign credentials, audit scientific truth or authorize execution/reveal.
"""

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import MaterializationQualificationReceipt, SourceAccessDisposition, StudyDraft

from .commitment import COMMIT_KEY, ScheduledCommitmentConfig
from .forecast import CALIBRATED_QUERY, ScheduledCalibratedForecastConfig, ScheduledForecastConfig, ScheduledPublicSource
from .records import NAMESPACE, ScheduledConfig
from .response_selection import ScheduledPhysicalForecastConfig, ScheduledResponseConfig
from .calibration_bindings import CALIBRATE_KEY, QUALIFY_KEY, ScheduledCalibrationConfig


def selected_sources(commitment, *, index=None, sources=None):
    from .source_index import ResolvedScheduledSource, ScheduledSourceIndex

    if sources is not None:
        if (type(sources) is not tuple or not sources
                or any(type(source) is not ResolvedScheduledSource for source in sources)
                or tuple(source.root_id for source in sources) != commitment.selected_root_ids
                or tuple(source.reference for source in sources) != tuple(reference for reference in
                    commitment.sources if reference.root_id in commitment.selected_root_ids)
                or any(source.index is not sources[0].index for source in sources)):
            raise ValueError('scheduled source views change the exact selected shared denominator')
        for source in sources:
            source.index.require_shared_source(source.reference, commitment)
        return sources

    if index is None:
        index = ScheduledSourceIndex.from_shared(reservation=commitment.reservation,
            specification=commitment.specification, provenances=commitment.provenances)
    return tuple(index.resolve(s) for s in commitment.sources if s.root_id in commitment.selected_root_ids)


def cutoffs(commitment, *, sources=None, index=None):
    sources = selected_sources(commitment, index=index, sources=sources)
    return tuple(sorted((InformationCutoff('cutoff.'+s.root_id, s.coordinate.clock_id, CausalPhase.PRE_ACTION,
        s.coordinate.physical_time(s.policy.cutoff_tick)) for s in sources), key=lambda c: c.cutoff_id))


def _qualification(root, context, logical_id, schema, fingerprint, access, visibility, *, version='1.0.0'):
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


def scientific_root_validator(config, context):
    from .operation_bindings import PHASES, phase_access, phase_visibility, source_operands, units
    from .response_bindings import RESPONSE_PHASES, units as response_units
    from .calibration_bindings import CALIBRATION_PHASES, units as calibration_units
    configs = tuple(v.record for v in context.config_inputs)
    commits = tuple(c for c in configs if type(c) is ScheduledCommitmentConfig)
    forecast_types = (ScheduledForecastConfig, ScheduledCalibratedForecastConfig)
    response_types = (ScheduledPhysicalForecastConfig, ScheduledResponseConfig)
    if len(commits) != 1 or any(type(c) not in (ScheduledConfig, *forecast_types, ScheduledCommitmentConfig, *response_types, ScheduledCalibrationConfig) for c in configs):
        raise ValueError('scheduled route requires one actual whole-population pre-access commitment')
    commit = commits[0]
    from .source_index import ScheduledSourceIndex
    index = ScheduledSourceIndex.from_shared(reservation=commit.reservation,
        specification=commit.specification, provenances=commit.provenances)
    index.require_roster(commit.sources, expected_root_ids=index.root_ids)
    sources = selected_sources(commit, index=index)
    all_sources = tuple(index.resolve(reference) for reference in commit.sources)
    groups = tuple(sorted({s.root.root.independent_group_id for s in sources}))
    expected = {COMMIT_KEY}
    source_by_root = {s.root_id: s for s in sources}
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
        raise ValueError('scheduled route thins complete selected root/paired history/forecast phases')
    for c in configs:
        if type(c) is ScheduledConfig:
            if (c.source.root_id not in source_by_root or c.source != source_by_root[c.source.root_id].reference
                    or c.commitment_config != ObjectIdentity.from_record(commit.config_id, commit)):
                raise ValueError('scheduled phases substitute native sources within one bank')
        elif type(c) in forecast_types:
            source = source_by_root.get(c.root_id)
            if source is None or c.public_source != ScheduledPublicSource.from_source(source) or c.design != commit.forecast_design:
                raise ValueError('scheduled predictor public source/design differs from original committed closure')
        elif type(c) in response_types:
            source = source_by_root.get(c.root_id)
            if source is None or commit.response_selection is None:
                raise ValueError('scheduled response loses complete committed whole-group selection')
            protocol, _ = commit.response_selection.validate_source(source)
            if type(c) is ScheduledPhysicalForecastConfig and c.protocol != protocol or type(c) is ScheduledResponseConfig and (c.source != source.reference or c.selection != commit.response_selection.identity
                    or c.commitment_config != ObjectIdentity.from_record(commit.config_id, commit)):
                raise ValueError('scheduled pulse phases change exact public/private committed source boundary')
        elif type(c) is ScheduledCalibrationConfig:
            if (c.commitment != ObjectIdentity.from_record(commit.config_id, commit) or c.group_ids != groups
                    or any(source.root.root.role.value != 'CALIBRATION' for source in sources)
                    or commit.response_selection is None or commit.response_selection.calibration_criterion is None):
                raise ValueError('scheduled calibration phases change original complete selected bank')
    root = context.root
    if (type(root) is not StudyDraft or root.system is None or root.experiment is None or root.campaign is None
            or root.unresolved_decisions or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or root.experiment.system_id != root.system.system_id or root.experiment.world_id != root.system.world.world_id
            or tuple(sorted((*root.development_unit_ids, *root.evaluation_unit_ids))) != groups
            or root.development_unit_ids != tuple(sorted({s.root.root.independent_group_id for s in sources if s.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'}))
            or root.experiment.information_cutoffs != cutoffs(commit, sources=sources)
            or not {o for s in all_sources for o in source_operands(s)} <= {i.object_identity for i in root.design_inputs}
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
    for s in commit.sources:
        _qualification(root, context, s.source_id, s.SCHEMA, s.fingerprint(), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, version=s.VERSION)
    if type(config) in (ScheduledConfig, ScheduledResponseConfig, ScheduledCalibrationConfig):
        _qualification(root, context, commit.config_id, commit.SCHEMA, commit.fingerprint(),
            OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, version=commit.VERSION)
    role = 'commit' if type(config) is ScheduledCommitmentConfig else 'forecast-calibrated' if type(config) is ScheduledCalibratedForecastConfig else 'forecast' if type(config) is ScheduledForecastConfig else 'physical-forecast' if type(config) is ScheduledPhysicalForecastConfig else config.operation
    phase = next(p for p in (*PHASES, *RESPONSE_PHASES, *CALIBRATION_PHASES) if p[0] == role)
    node = COMMIT_KEY if role == 'commit' else NAMESPACE+'.'+role if type(config) is ScheduledCalibrationConfig else NAMESPACE+'.'+(config.root_id if type(config) in (*forecast_types, *response_types) else config.source.root_id)+'.'+role
    native = role in ('prefix', 'continue', 'continue-development', 'responses', 'responses-development')
    role_groups = groups if role == 'commit' else tuple(sorted({s.root.root.independent_group_id for s in sources
        if not role.endswith('-development') or s.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'}))
    if role in ('continue', 'full-numerical', 'responses', 'response-score', 'forecast-calibrated'):
        role_groups = tuple(sorted({s.root.root.independent_group_id for s in sources if s.evidence_role != 'EXPOSED_DEVELOPMENT_NONPROMOTABLE'}))
    if (context.node_id != node or context.stage is not phase[3] or context.outcome_access is not phase_access(role)
            or context.visibility_ceiling is not phase_visibility(role) or context.unit_ids != (response_units(config) if type(config) in response_types else calibration_units(config) if type(config) is ScheduledCalibrationConfig else units(config))
            or context.selected_unit_ids != role_groups or context.complete_unit_census != native):
        raise ValueError('scheduled phase changes exact stage, native census, role or outcome scope')
    names = {n for n, _ in phase[1] if n not in ('streams', 'prior-coordinates') and not (role == 'commit' and n == 'source')
        and not (n == 'calibration' and commit.forecast_design.calibration is None and role != 'calibration-qualify')
        and not (n == 'response-selection' and commit.response_selection is None)
        and not (n == 'physical-forecast' and commit.response_selection is None)
        and n not in ('scores', 'forecasts')}
    if role == 'commit':
        names |= {'source.'+s.root_id for s in commit.sources}
        names |= {'prior-coordinates.'+c.coordinate_id for c in commit.audit.prior_scheduled_coordinates}
    elif native:
        names |= {'streams.'+s.purpose for s in config.source.root.streams}
        if role.startswith('responses'):
            _, panels = commit.response_selection.validate_source(source_by_root[config.source.root_id])
            names |= {'streams.future.'+s.purpose for p in panels if p.role == 'INDEPENDENT_FUTURE' for s in p.streams}
    elif role == 'calibrate':
        names |= {'scores.'+s.root_id for s in sources} | {'forecasts.'+s.root_id for s in sources}
    incoming = tuple(l for l in context.links if l.consumer_node_id == node)
    if len(incoming) != len(names) or {l.consumer_input_id for l in incoming} != names:
        raise ValueError('scheduled phase omits complete actual source/dependency port census')
    for link in incoming:
        name = link.consumer_input_id
        if name in ('allocation', 'selection', 'audit', 'prior-census', 'coordinate', 'provenance', 'source', 'forecast-design',
                'model', 'training', 'criterion', 'response-selection', 'templates', 'commitment-config') or name.startswith(('source.', 'streams.', 'prior-coordinates.')):
            if link.external_input_id is None or link.producer_node_id is not None or link.scientific_role != 'SOURCE':
                raise ValueError('scheduled source/audit is not an actual qualified ordinary input')
        elif name == 'calibration' and role == 'forecast-calibrated':
            if link.external_input_id is None or link.requirement_id is None or link.connection_id is None:
                raise ValueError('scheduled calibrated forecast lacks original authenticated sealed parent input')
        else:
            if role == 'calibrate' and name.startswith(('scores.', 'forecasts.')):
                root_id = name.split('.', 1)[1]
                owner = 'response-score' if name.startswith('scores.') else 'forecast'
            else:
                root_id = config.root_id if type(config) in (*forecast_types, *response_types) else config.source.root_id if type(config) is ScheduledConfig else ''
                owner = 'prefix' if name.startswith('history') or name == 'checkpoint' else 'project' if name.startswith('causal') or name == 'feature' else 'commit' if name == 'commitment' else 'forecast-calibrated' if name in ('forecast', 'error-forecast') and dict(commit.forecast_design.source_scopes).get(root_id) == CALIBRATED_QUERY else 'forecast' if name == 'error-forecast' else 'calibrate' if role == 'calibration-qualify' and name == 'calibration' else name.removesuffix('-arrays')
            if owner == 'responses' and source_by_root[config.source.root_id].evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE':
                owner += '-development'
            producer = COMMIT_KEY if owner == 'commit' else CALIBRATE_KEY if owner == 'calibrate' else NAMESPACE+'.'+root_id+'.'+owner
            output = 'arrays' if name.endswith('-arrays') else 'feature' if name == 'feature' else 'checkpoint' if name == 'checkpoint' else 'product'
            if link.producer_node_id != producer or link.producer_output_id != output or link.external_input_id is not None:
                raise ValueError('scheduled phase changes original producer/output before its native contact')
    if native:
        from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
        validate_parameter_ou_domain(source_by_root[config.source.root_id].coordinate)
