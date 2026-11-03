# SPDX-License-Identifier: MPL-2.0
"""Closed current E3 declarations and their prospective scientific-root guard.

The source and original-publication owners authenticate science and custody.
This pure composition joins their frozen references to the complete current
operation graph. It grants no qualification, issue, execution or reveal.
"""

from dataclasses import dataclass, replace
from functools import lru_cache
from types import MappingProxyType

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.runtime.recursive_compiler import RecursiveConfigInput, RecursiveScientificRootContext

from .configured_protected_adjudication import ConfiguredProtectedE3AdjudicationConfig, adjudication_declaration, adjudication_task_id
from .configured_protected_feature_bindings import FEATURE_ARRAY_INPUTS, FEATURE_RECORD_INPUTS, ConfiguredProtectedE3FeatureConfig, feature_declaration, feature_task_id, feature_producer_task
from .configured_protected_originals import ORIGINAL_PUBLICATION_REQUIREMENT
from .configured_protected_prefix_bindings import PREFIX_INPUTS, prefix_declarations
from .configured_protected_prefix_workers import prefix_worker_phase
from .configured_protected_response_bindings import _arrays, _records, response_declarations
from .configured_protected_response_preparation import response_task_id
from .configured_protected_response_records import ConfiguredProtectedE3PhysicalForecastConfig, ConfiguredProtectedE3ResponseConfig
from .configured_protected_source_records import NAMESPACE, ConfiguredProtectedE3SourceConfig, ProtectedE3SourcePhase, source_task_id
from .configured_protected_statistical_bindings import ConfiguredProtectedE3FitConfig, ConfiguredProtectedE3StatisticalConfig, statistical_declarations, statistical_task_id


def outcome_task_id(root_id):
    """The actual independent paired-outcome output owner, never a callback."""
    return response_task_id(root_id, "response-score")


@lru_cache(maxsize=1)
def operation_declarations():
    """Install sixteen current owners with the same mandatory root hook."""
    declarations = (*prefix_declarations(), feature_declaration(),
        *response_declarations(publication_requirement=ORIGINAL_PUBLICATION_REQUIREMENT,
            scientific_root_validator=scientific_root_validator),
        *statistical_declarations(publication_requirement=ORIGINAL_PUBLICATION_REQUIREMENT,
            scientific_root_validator=scientific_root_validator, outcome_task_id=outcome_task_id),
        adjudication_declaration(scientific_root_validator=scientific_root_validator))
    from .configured_retained_bindings import retained_declaration
    from .configured_retained_execution import RETAINED_PHASES
    retained = tuple(retained_declaration(row, scientific_root_validator=scientific_root_validator)
        for row in declarations if row.capability_key.removeprefix(NAMESPACE + '.').replace('native-fit', 'fit') in RETAINED_PHASES)
    continued = (*response_declarations(publication_requirement=ORIGINAL_PUBLICATION_REQUIREMENT,
        scientific_root_validator=scientific_root_validator, continued=True), feature_declaration(continued=True))
    from .configured_closeout_bindings import missing_outcome_declaration
    closeout = missing_outcome_declaration(publication_requirement=ORIGINAL_PUBLICATION_REQUIREMENT,
        scientific_root_validator=scientific_root_validator)
    return tuple(sorted((replace(declaration,
        scientific_hooks=replace(declaration.scientific_hooks, scientific_root_validator=scientific_root_validator),
        publication_requirements=(ORIGINAL_PUBLICATION_REQUIREMENT,)) for declaration in (*declarations, *retained, *continued, closeout)),
        key=lambda row: row.capability_key))


def _task(config):
    # Task identity has one lowering owner. Import only at invocation, after
    # static declaration discovery has finished.
    from .configured_protected_lowering import task_id
    return task_id(config)


def _phase(config):
    from .configured_retained_execution import ConfiguredE3RetainedTaskConfig
    from .configured_continued_response import ConfiguredE3ContinuedFeatureConfig, ConfiguredE3ContinuedResponseConfig
    from .configured_closeout_execution import ConfiguredE3MissingOutcomeConfig
    if type(config) is ConfiguredE3MissingOutcomeConfig:
        return 'missing-response-score'
    if type(config) is ConfiguredE3RetainedTaskConfig:
        return 'retained-' + _phase(config.original_config)
    if type(config) is ConfiguredE3ContinuedResponseConfig:
        return 'continued-' + config.operation
    if type(config) is ConfiguredE3ContinuedFeatureConfig:
        return 'continued-feature'
    if type(config) is ConfiguredProtectedE3SourceConfig:
        return config.phase.value
    if type(config) is ConfiguredProtectedE3FeatureConfig:
        return "feature"
    if type(config) is ConfiguredProtectedE3PhysicalForecastConfig:
        return "physical-forecast"
    if type(config) is ConfiguredProtectedE3AdjudicationConfig:
        return "adjudicate"
    return config.mode + "-freeze" if config.operation == "freeze" else config.operation


def _declaration_key(config):
    if type(config) is ConfiguredProtectedE3FitConfig:
        return NAMESPACE + ".native-fit"
    return NAMESPACE + "." + _phase(config)


@dataclass(frozen=True, slots=True)
class _CurrentConfigs:
    fit: ConfiguredProtectedE3FitConfig
    by_task: object
    roots: object
    query_roots: object
    declarations: object
    unit_censuses: object
    original_inputs: object = None
    original: object = None
    continuation: object = None
    completed_task_ids: tuple[str, ...] = ()
    closeout: object = None


# Config rows and scientific contexts contain immutable records. Retain only
# one tuple by identity so every node in a compile shares its already checked
# census; another frozen wave, even with equal bytes, is independently checked.
_config_cache = None
_root_cache = None
_unfinished_config_cache = None


def unfinished_configs(config_inputs, declared_config_inputs):
    """Validate the whole authored science and its explicitly selected suffix."""
    global _unfinished_config_cache
    key = config_inputs, declared_config_inputs
    if _unfinished_config_cache is not None and all(a is b for a, b in zip(key, _unfinished_config_cache[:2], strict=True)):
        return _unfinished_config_cache[2]
    complete = validate_current_configs(declared_config_inputs)
    if complete.original is None:
        raise ValueError('unfinished E3 requires an explicit retained original execution')
    selected = {row.node_id: row.record for row in config_inputs}
    from .configured_closeout_execution import ConfiguredE3MissingOutcomeConfig
    missing = {node: config for node, config in complete.by_task.items() if type(config) is ConfiguredE3MissingOutcomeConfig}
    excluded = {response_task_id(config.source.root_id, 'responses') for config in missing.values()}
    closeouts = {config.closeout for config in missing.values()}
    if missing and (not set(missing) <= set(selected) or excluded & set(selected) or len(closeouts) != 1):
        raise ValueError('CAL closeout must assess every missing root and exclude every uncertain native call')
    if (any(complete.by_task.get(node) != config for node, config in selected.items())
            or any(_phase(config) not in ('continued-responses', 'continued-response-score', 'forecast',
                'calibrate', 'calibration-freeze', 'assess', 'adjudicate', 'missing-response-score') for config in selected.values())):
        raise ValueError('unfinished E3 selects completed science or a different configuration')
    done = tuple(sorted(set(complete.by_task) - set(selected) - excluded))
    if not done:
        raise ValueError('unfinished E3 requires actual retained predecessor operations')
    def allowed_completed(config):
        if missing and _phase(config) in ('continued-responses', 'continued-response-score'):
            return config.source.root.root.role.value == 'CALIBRATION'
        return _phase(config) in ('retained-prefix', 'retained-numerical', 'retained-measure',
            'retained-check', 'retained-project', 'retained-feature', 'retained-physical-forecast', 'retained-fit',
            'retained-model-freeze', 'retained-forecast', 'continued-feature', 'forecast')
    if any(not allowed_completed(complete.by_task[node]) for node in done):
        raise ValueError('unfinished E3 cannot omit future responses or their assessment')
    units = {}
    for config in selected.values():
        declaration = complete.declarations[_declaration_key(config)]
        units.setdefault(_phase(config), set()).update(declaration.scientific_hooks.scientific_unit_ids(config))
    result = replace(complete, by_task=MappingProxyType(selected), completed_task_ids=done,
        unit_censuses=MappingProxyType({phase: tuple(sorted(values)) for phase, values in units.items()}),
        closeout=next(iter(closeouts)) if closeouts else None)
    _unfinished_config_cache = *key, result
    return result


def validate_current_configs(config_inputs):
    """Check one closed fit/freezes/CAL/CONF census without scientific I/O."""
    global _config_cache
    if _config_cache is not None and _config_cache[0] is config_inputs:
        return _config_cache[1]
    from .configured_continued_response import ConfiguredE3ContinuedFeatureConfig, ConfiguredE3ContinuedResponseConfig
    from .configured_retained_execution import ConfiguredE3RetainedTaskConfig
    from .configured_closeout_execution import ConfiguredE3MissingOutcomeConfig
    continued_kinds = (ConfiguredE3RetainedTaskConfig, ConfiguredE3ContinuedFeatureConfig, ConfiguredE3ContinuedResponseConfig, ConfiguredE3MissingOutcomeConfig)
    if type(config_inputs) is tuple and any(type(row) is RecursiveConfigInput and type(row.record) in continued_kinds
            for row in config_inputs):
        result = _continued_configs(config_inputs, continued_kinds)
        _config_cache = config_inputs, result
        return result
    kinds = (ConfiguredProtectedE3SourceConfig, ConfiguredProtectedE3FeatureConfig, ConfiguredProtectedE3PhysicalForecastConfig,
        ConfiguredProtectedE3ResponseConfig, ConfiguredProtectedE3FitConfig, ConfiguredProtectedE3StatisticalConfig, ConfiguredProtectedE3AdjudicationConfig)
    if (type(config_inputs) is not tuple or not config_inputs
            or any(type(row) is not RecursiveConfigInput or type(row.record) not in kinds for row in config_inputs)):
        raise ValueError("protected E3 wave mixes another configuration or lifecycle")
    by_task, roots = {}, {}
    for row in config_inputs:
        config = row.record
        config.__post_init__()
        node = _task(config)
        if row.node_id != node or node in by_task:
            raise ValueError("protected E3 wave duplicates or substitutes a derived task identity")
        by_task[node] = config
        if type(config) is ConfiguredProtectedE3SourceConfig and config.phase is ProtectedE3SourcePhase.PREFIX:
            roots[config.source.root_id] = config.source
    fits = tuple(config for config in by_task.values() if type(config) is ConfiguredProtectedE3FitConfig)
    if len(fits) != 1 or fits[0].original_publications is None:
        raise ValueError("protected E3 wave needs one fit with its original-publication custody")
    fit, = fits
    originals = {key: publication.logical.content_sha256 for key, publication, _ in fit.publications}
    if len({source.identity for source in roots.values()}) != len(roots):
        raise ValueError("protected E3 wave aliases original source identities across whole roots")
    if len({source.specification for source in roots.values()}) != 1:
        raise ValueError("protected E3 wave mixes original native specifications")
    expected = {_task(fit)}
    globals_ = (("freeze", "model"), ("calibrate", ""), ("freeze", "calibration"), ("assess", ""))
    for operation, mode in globals_:
        node = statistical_task_id(fit.specification, fit.allocation, operation, mode=mode)
        expected.add(node)
        config = by_task.get(node)
        if type(config) is not ConfiguredProtectedE3StatisticalConfig or config.root is not None:
            raise ValueError("protected E3 wave omits fit, separate model/calibration freezes or final assessment")
    terminal = adjudication_task_id(fit.specification, fit.allocation)
    expected.add(terminal)
    if type(by_task.get(terminal)) is not ConfiguredProtectedE3AdjudicationConfig:
        raise ValueError("protected E3 wave omits its final authority-bound scientific adjudication")
    query_roots = {"calibration": [], "evaluation": []}
    for root_id, source in roots.items():
        root = source.root.root
        if root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION):
            raise ValueError("protected E3 wave enters reserved or unrelated source work")
        if (source.allocation.object_fingerprint, source.reservation.object_fingerprint, source.selection.object_fingerprint) != (
                originals["allocation"], originals["reservation"], originals["native-selection"]):
            raise ValueError("protected E3 wave substitutes its reserved original source/allocation/selection bytes")
        role = "calibration" if root.role is MatrixProgrammeRole.CALIBRATION else "evaluation"
        query_roots[role].append(root)
        for phase in ProtectedE3SourcePhase:
            node = source_task_id(root_id, phase)
            expected.add(node)
            config = by_task.get(node)
            if (type(config) is not ConfiguredProtectedE3SourceConfig or config.phase is not phase or config.source != source
                    or config.source_manifest != fit.source_manifest):
                raise ValueError("protected E3 wave changes a whole root or source manifest across prefix phases")
        feature = by_task.get(feature_task_id(root_id))
        physical = by_task.get(response_task_id(root_id, "physical-forecast"))
        forecast = by_task.get(statistical_task_id(fit.specification, fit.allocation, "forecast", mode=role, root=root))
        if (type(feature) is not ConfiguredProtectedE3FeatureConfig or feature.root != root or feature.allocation != fit.allocation
                or type(physical) is not ConfiguredProtectedE3PhysicalForecastConfig
                or type(forecast) is not ConfiguredProtectedE3StatisticalConfig or forecast.root != root or forecast.mode != role):
            raise ValueError("protected E3 wave omits its actual seedless feature and pre-future forecasts")
        expected.update((_task(feature), _task(physical), _task(forecast)))
        pair = []
        for operation in ("responses", "response-score"):
            node = response_task_id(root_id, operation)
            expected.add(node)
            config = by_task.get(node)
            if (type(config) is not ConfiguredProtectedE3ResponseConfig or config.operation != operation or config.source != source
                    or config.source_manifest != fit.source_manifest or config.protocol != physical.protocol
                    or config.numerical_profile != physical.numerical_profile):
                raise ValueError("protected E3 wave changes its actual source/protocol/profile across responses")
            pair.append(config)
        if pair[0].response_selection != pair[1].response_selection:
            raise ValueError("protected E3 wave changes original paired response selection before assessment")
    if set(by_task) != expected:
        raise ValueError("protected E3 wave changes the complete selected current task census")
    for role, count in fit.query_census:
        selected = query_roots[role]
        if len(selected) != count or len({root.independent_group_id for root in selected}) != count:
            raise ValueError("protected E3 wave drops complete independent CAL/CONF roots or enlarges nested units")
    groups = tuple(root.independent_group_id for selected in query_roots.values() for root in selected)
    if len(set(groups)) != len(groups):
        raise ValueError("protected E3 wave reuses an independent unit across CAL and CONF")
    if len({config.response_selection for config in by_task.values() if type(config) is ConfiguredProtectedE3ResponseConfig}) != 1:
        raise ValueError("protected E3 wave mixes original paired response selections")
    for config in by_task.values():
        if (config.specification != fit.specification
                or type(config) in (ConfiguredProtectedE3FitConfig, ConfiguredProtectedE3StatisticalConfig, ConfiguredProtectedE3FeatureConfig, ConfiguredProtectedE3AdjudicationConfig)
                    and config.allocation != fit.allocation
                or type(config) in (ConfiguredProtectedE3FitConfig, ConfiguredProtectedE3StatisticalConfig) and config.query_census != fit.query_census):
            raise ValueError("protected E3 wave changes its frozen specification/allocation or selected population")
    declarations = {row.capability_key: row for row in operation_declarations()}
    unit_censuses = {}
    for config in by_task.values():
        phase = _phase(config)
        declaration = declarations[_declaration_key(config)]
        unit_censuses.setdefault(phase, set()).update(declaration.scientific_hooks.scientific_unit_ids(config))
    result = _CurrentConfigs(fit, MappingProxyType(by_task), MappingProxyType(roots),
        MappingProxyType({role: tuple(sorted(selected, key=lambda root: root.root_id)) for role, selected in query_roots.items()}),
        MappingProxyType(declarations), MappingProxyType({phase: tuple(sorted(units)) for phase, units in unit_censuses.items()}))
    _config_cache = config_inputs, result
    return result


def _continued_configs(config_inputs, continued_kinds):
    """Prove the entire original science, then the explicit adoption frontier."""
    from .configured_continued_response import original_config, ConfiguredE3ContinuedFeatureConfig, ConfiguredE3ContinuedResponseConfig
    from .configured_retained_execution import ConfiguredE3RetainedTaskConfig
    from .configured_closeout_execution import ConfiguredE3MissingOutcomeConfig
    if any(type(row) is not RecursiveConfigInput for row in config_inputs):
        raise ValueError('continued E3 changes the exact selected configuration roster')
    original_inputs = tuple(replace(row, record=original_config(row.record),
        record_type=type(original_config(row.record))) for row in config_inputs)
    original = validate_current_configs(original_inputs)
    by_task = {}
    pins = set()
    for row in config_inputs:
        config = row.record
        config.__post_init__()
        node = _task(config)
        if node != row.node_id or node in by_task:
            raise ValueError('continued E3 changes a derived task or duplicates a selected node')
        by_task[node] = config
        if type(config) in continued_kinds:
            pins.add(config.continuation)
        science = original.by_task[node]
        mandatory = type(science) in (ConfiguredProtectedE3SourceConfig, ConfiguredProtectedE3PhysicalForecastConfig,
            ConfiguredProtectedE3FitConfig) or _phase(science) == 'model-freeze'
        if mandatory and type(config) is not ConfiguredE3RetainedTaskConfig:
            raise ValueError('continued E3 must retain every original prefix, physical forecast, fit and model freeze')
        if type(science) is ConfiguredProtectedE3ResponseConfig and type(config) not in (ConfiguredE3ContinuedResponseConfig, ConfiguredE3MissingOutcomeConfig):
            raise ValueError('continued E3 must bind every new response and score to the explicit source continuation')
        if type(science) is ConfiguredProtectedE3FeatureConfig and type(config) not in (
                ConfiguredE3RetainedTaskConfig, ConfiguredE3ContinuedFeatureConfig):
            raise ValueError('continued E3 feature must retain its receipt or bind its original array aliases')
    if len(pins) != 1:
        raise ValueError('continued E3 changes its one exact original execution and source continuation')
    declarations = {row.capability_key: row for row in operation_declarations()}
    unit_censuses = {}
    for config in by_task.values():
        declaration = declarations[_declaration_key(config)]
        unit_censuses.setdefault(_phase(config), set()).update(declaration.scientific_hooks.scientific_unit_ids(config))
    return _CurrentConfigs(original.fit, MappingProxyType(by_task), original.roots, original.query_roots,
        MappingProxyType(declarations), MappingProxyType({phase: tuple(sorted(units)) for phase, units in unit_censuses.items()}),
        original_inputs, original, next(iter(pins)))


def expected_producers(config, config_inputs, *, _current=None):
    """One guard projection shared by lowering and cold root validation.

    Repeated external records use ``panels.*``/``streams.*``; their exact
    multiplicity and source bytes remain the declaration and qualification's
    contracts. Repeated reduction inputs name every exact selected whole root.
    """
    current = validate_current_configs(config_inputs) if _current is None else _current
    if current.by_task.get(_task(config)) != config:
        raise ValueError("protected E3 graph guard receives another selected configuration")
    from .configured_closeout_execution import ConfiguredE3MissingOutcomeConfig
    if type(config) is ConfiguredE3MissingOutcomeConfig:
        return {'closeout': None, 'products': None}
    if current.original_inputs is not None:
        from .configured_continued_response import original_config
        from .configured_retained_execution import ConfiguredE3RetainedTaskConfig
        result = expected_producers(original_config(config), current.original_inputs, _current=current.original)
        if hasattr(config, 'continuation'):
            result['retention'] = None
        if current.completed_task_ids:
            imported = {key for key, producer in result.items()
                if producer is not None and producer[0] in current.completed_task_ids}
            if imported:
                result.update((key, None) for key in imported)
                result['closeout' if current.closeout is not None else 'unfinished'] = None
        if type(config) is ConfiguredE3RetainedTaskConfig:
            result.update(('retained-' + output.output_id.rsplit('.', 1)[-1], None) for output in config.original_task.outputs)
        return result
    fit, phase = current.fit, _phase(config)
    statistic = lambda operation, mode="", root=None: statistical_task_id(fit.specification, fit.allocation, operation, mode=mode, root=root)
    if type(config) is ConfiguredProtectedE3SourceConfig:
        if config.phase is ProtectedE3SourcePhase.PREFIX:
            return {"streams.*" if name == "streams" else name: None for name, _ in PREFIX_INPUTS}
        selected = prefix_worker_phase(config.phase)
        return {**{name: None if producer is None else (source_task_id(config.source.root_id, producer), "product")
            for name, _, producer in selected.records}, **{name: (source_task_id(config.source.root_id, producer), "arrays")
                for name, producer in selected.arrays}}
    if type(config) is ConfiguredProtectedE3FeatureConfig:
        root_id = config.root.root_id
        return {**{name: None if producer is None else (feature_producer_task(root_id, producer), "product")
            for name, _, producer in FEATURE_RECORD_INPUTS}, **{name: (feature_producer_task(root_id, producer), "arrays")
                for name, producer in FEATURE_ARRAY_INPUTS}}
    if type(config) in (ConfiguredProtectedE3PhysicalForecastConfig, ConfiguredProtectedE3ResponseConfig):
        root_id = config.root_id if type(config) is ConfiguredProtectedE3PhysicalForecastConfig else config.source.root_id
        root = current.roots[root_id].root.root
        confirmation = root.role is MatrixProgrammeRole.CONFIRMATION
        mode = "evaluation" if confirmation else "calibration"
        prefix = source_task_id(root_id, ProtectedE3SourcePhase.PREFIX)
        project = source_task_id(root_id, ProtectedE3SourcePhase.PROJECT)
        producers = {"causal": (project, "product"), "history": (prefix, "product"), "checkpoint": (prefix, "checkpoint"),
            "physical": (response_task_id(root_id, "physical-forecast"), "product"), "models": (statistic("fit"), "product"),
            "frozen": (statistic("freeze", "calibration" if confirmation else "model"), "product"),
            "error": (statistic("forecast", mode, root), "product"), "calibration": (statistic("calibrate"), "product"),
            "model-freeze": (statistic("freeze", "model"), "product"), "responses": (response_task_id(root_id, "responses"), "product")}
        result = {name + ".*" if name in ("panels", "streams") else name: producers.get(name)
            for name, _ in _records(phase) if confirmation or name not in ("calibration", "model-freeze")}
        arrays = {"prefix-arrays": (prefix, "arrays"), "causal-arrays": (project, "arrays"),
            "physical-arrays": (response_task_id(root_id, "physical-forecast"), "arrays"),
            "response-arrays": (response_task_id(root_id, "responses"), "arrays")}
        result.update({name: arrays.get(name) for name in _arrays(phase)})
        return result
    result = {"specification": None, "allocation": None}
    if type(config) is ConfiguredProtectedE3AdjudicationConfig:
        return {**result, "assessment": (statistic("assess"), "product")}
    if phase == "fit":
        return {name: None for name in ("specification", "allocation", "manifest", "training-allocation", "original-allocation",
            "native-selection", "reservation", "features", "outcomes")}
    if phase in ("model-freeze", "calibration-freeze", "forecast", "calibrate"):
        result["models"] = statistic("fit"), "product"
    if phase == "model-freeze":
        result["prefit-join"] = statistic("fit"), "prefit-join"
    elif phase == "calibration-freeze":
        result.update({"model-freeze": (statistic("freeze", "model"), "product"), "calibration": (statistic("calibrate"), "product")})
    else:
        mode = config.mode if phase == "forecast" else "calibration" if phase == "calibrate" else "evaluation"
        result["frozen"] = statistic("freeze", "model" if mode == "calibration" else "calibration"), "product"
        if phase == "forecast":
            result["feature"] = feature_task_id(config.root.root_id), "product"
            if mode == "evaluation":
                result.update({"model-freeze": (statistic("freeze", "model"), "product"), "calibration": (statistic("calibrate"), "product")})
        else:
            for root in current.query_roots[mode]:
                result["forecasts." + root.root_id] = statistic("forecast", mode, root), "product"
                result["outcomes." + root.root_id] = outcome_task_id(root.root_id), "outcome"
    return result


def _role(config, name, producer):
    from .configured_continued_response import original_config
    from .configured_retained_execution import ConfiguredE3RetainedTaskConfig
    from .configured_closeout_execution import ConfiguredE3MissingOutcomeConfig
    if type(config) is ConfiguredE3MissingOutcomeConfig and name == 'products':
        return 'HISTORY'
    if type(config) is ConfiguredE3RetainedTaskConfig and name.startswith('retained-'):
        return "HISTORY"
    config = original_config(config)
    if producer is None:
        return "SOURCE"
    if type(config) is ConfiguredProtectedE3ResponseConfig and name in ("models", "frozen", "error", "calibration", "model-freeze"):
        return "MODEL"
    if type(config) is ConfiguredProtectedE3AdjudicationConfig:
        return "OUTCOME"
    if type(config) in (ConfiguredProtectedE3FitConfig, ConfiguredProtectedE3StatisticalConfig):
        return "OUTCOME" if name.startswith("outcomes.") else "HISTORY" if name == "feature" else "MODEL"
    return "HISTORY"


def validate_generated_links(config_inputs, links, *, _current=None):
    from .protected_root_validation import validate_protected_links
    current = validate_current_configs(config_inputs) if _current is None else _current
    def role(config, name, producer):
        if current.completed_task_ids and producer is None:
            from .configured_continued_response import original_config
            original = expected_producers(original_config(config), current.original_inputs, _current=current.original).get(name)
            if original is not None and original[0] in current.completed_task_ids:
                return 'HISTORY'
        return _role(config, name, producer)
    return validate_protected_links(config_inputs, links, current=current,
        declaration_key=_declaration_key,
        expected_producers=lambda config, rows: expected_producers(config, rows, _current=current), role=role)


def _external_fingerprint(config, name, current):
    """Bind directly represented references; qualified owners cover other data."""
    from .configured_closeout_execution import ConfiguredE3MissingOutcomeConfig
    if name == 'closeout':
        pin = config.closeout if type(config) is ConfiguredE3MissingOutcomeConfig else current.closeout
        return None if pin is None else pin.object_fingerprint
    if type(config) is ConfiguredE3MissingOutcomeConfig and name == 'products':
        return config.products.object_fingerprint
    if current.original is not None:
        from .configured_continued_response import original_config, ConfiguredE3ContinuedResponseConfig
        from .configured_retained_execution import ConfiguredE3RetainedTaskConfig
        if name == 'retention':
            return current.continuation.object_fingerprint
        if type(config) is ConfiguredE3ContinuedResponseConfig and name == 'provenance':
            # The config pins the retention record, which owns the continued
            # producer. Preparation and worker custody check that exact member;
            # the original prefix source is not this direct operand's producer.
            return None
        if type(config) is ConfiguredE3RetainedTaskConfig and name.startswith('retained-'):
            output, = (output for output in config.original_task.outputs
                if output.output_id.rsplit('.', 1)[-1] == name.removeprefix('retained-'))
            logical, = (row for row in config.original_receipt.output_logical_artifacts
                if row.logical_artifact_id == output.logical_artifact_id)
            return logical.content_sha256
        if name == 'native-config':
            return current.by_task[response_task_id(config.source.root_id, 'responses')].fingerprint()
        return _external_fingerprint(original_config(config), name, current.original)
    if name == "specification":
        return current.fit.specification.object_fingerprint
    if name == "allocation":
        return current.fit.allocation.object_fingerprint
    if name == "manifest":
        return current.fit.source_manifest.object_fingerprint
    if type(config) is ConfiguredProtectedE3FitConfig:
        if name == "training-allocation":
            return config.training_allocation.object_fingerprint
        keys = {"original-allocation": "allocation", "native-selection": "native-selection", "reservation": "reservation"}
        if name in keys:
            return next(publication.logical.content_sha256 for key, publication, _ in config.publications if key == keys[name])
    if type(config) is ConfiguredProtectedE3FeatureConfig:
        return {"public-source": config.public_source.object_fingerprint,
            "numerical-design": config.numerical_design.object_fingerprint}.get(name)
    if type(config) in (ConfiguredProtectedE3PhysicalForecastConfig, ConfiguredProtectedE3ResponseConfig):
        if name in ("protocol", "numerical-profile"):
            return getattr(config, name.replace("-", "_")).object_fingerprint
    if type(config) in (ConfiguredProtectedE3SourceConfig, ConfiguredProtectedE3ResponseConfig):
        source = config.source
        root_id = source.root_id
        direct = {"source": source.fingerprint(), "coordinate": source.coordinate.object_fingerprint,
            "provenance": source.provenance.object_fingerprint,
            "prefix-config": current.by_task[source_task_id(root_id, ProtectedE3SourcePhase.PREFIX)].fingerprint()}
        if type(config) is ConfiguredProtectedE3ResponseConfig:
            direct.update({"selection": config.response_selection.object_fingerprint,
                "physical-config": current.by_task[response_task_id(root_id, "physical-forecast")].fingerprint(),
                "native-config": current.by_task[response_task_id(root_id, "responses")].fingerprint()})
        if name.startswith("streams."):
            stream = next((stream for stream in source.root.streams
                if name in ("streams." + stream.purpose, "streams." + source.root.stream_identity(stream).object_id)), None)
            return None if stream is None else stream.fingerprint()
        return direct.get(name)
    return None


def _validate_root(context, current):
    global _root_cache
    cache_key = (context.config_inputs, context.root, context.links, context.qualifications,
        context.known_design_inputs, context.external_inputs, context.declared_config_inputs)
    if _root_cache is not None and all(a is b for a, b in zip(_root_cache, cache_key, strict=True)):
        return
    from .protected_root_validation import validate_protected_root
    if current.completed_task_ids:
        from .configured_unfinished_execution import ConfiguredE3UnfinishedExecution
        from .configured_closeout_execution import ConfiguredE3ClosedExecution
        kind = ConfiguredE3UnfinishedExecution if current.closeout is None else ConfiguredE3ClosedExecution
        scopes = tuple(row for row in context.external_inputs if row.payload_schema == kind.SCHEMA)
        if len(scopes) != 1 or not any(pin.object_identity.object_schema == kind.SCHEMA
                and pin.object_identity.object_fingerprint == scopes[0].expected_content_sha256
                for pin in context.root.design_inputs):
            raise ValueError('unfinished E3 loses its frozen predecessor custody boundary')
    validate_protected_root(context, current,
        validate_links=lambda rows, links: validate_generated_links(rows, links, _current=current),
        external_fingerprint=_external_fingerprint)
    _root_cache = cache_key


def scientific_root_validator(config, context):
    """One installed pure guard over the exact current scientific composition."""
    if type(context) is not RecursiveScientificRootContext:
        raise TypeError("protected E3 requires its actual compiler scientific-root context")
    current = (unfinished_configs(context.config_inputs, context.declared_config_inputs)
        if context.declared_config_inputs else validate_current_configs(context.config_inputs))
    node, phase = _task(config), _phase(config)
    if current.by_task.get(node) != config:
        raise ValueError("protected E3 root receives an unselected scientific configuration")
    declaration = current.declarations[_declaration_key(config)]
    hooks = declaration.scientific_hooks
    if (context.node_id != node or context.stage is not declaration.stage
            or context.outcome_access is not declaration.outcome_access or context.visibility_ceiling is not declaration.visibility_ceiling
            or context.unit_ids != hooks.scientific_unit_ids(config) or context.selected_unit_ids != current.unit_censuses[phase]
            or context.complete_unit_census is not declaration.execution_properties.complete_unit_census
            or context.requirements or context.connections):
        raise ValueError("protected E3 root changes its declared phase, complete unit census, access or lifecycle")
    _validate_root(context, current)
