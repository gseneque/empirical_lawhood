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

from .protected_adjudication import ProtectedE3AdjudicationConfig, adjudication_declaration, adjudication_task_id
from .protected_feature_bindings import FEATURE_ARRAY_INPUTS, FEATURE_RECORD_INPUTS, ProtectedE3FeatureConfig, feature_declaration, feature_task_id
from .protected_original_publications import ORIGINAL_PUBLICATION_REQUIREMENT
from .protected_prefix_bindings import PREFIX_INPUTS, prefix_declarations
from .protected_prefix_workers import prefix_worker_phase
from .protected_response_bindings import _arrays, _records, response_declarations
from .protected_response_preparation import response_task_id
from .protected_response_records import ProtectedE3PhysicalForecastConfig, ProtectedE3ResponseConfig
from .protected_source_records import NAMESPACE, ProtectedE3SourceConfig, ProtectedE3SourcePhase, source_task_id
from .protected_statistical_bindings import ProtectedE3FitConfig, ProtectedE3StatisticalConfig, statistical_declarations, statistical_task_id


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
    return tuple(sorted((replace(declaration,
        scientific_hooks=replace(declaration.scientific_hooks, scientific_root_validator=scientific_root_validator),
        publication_requirements=(ORIGINAL_PUBLICATION_REQUIREMENT,)) for declaration in declarations),
        key=lambda row: row.capability_key))


def _task(config):
    # Task identity has one lowering owner. Import only at invocation, after
    # static declaration discovery has finished.
    from .protected_lowering import task_id
    return task_id(config)


def _phase(config):
    if type(config) is ProtectedE3SourceConfig:
        return config.phase.value
    if type(config) is ProtectedE3FeatureConfig:
        return "feature"
    if type(config) is ProtectedE3PhysicalForecastConfig:
        return "physical-forecast"
    if type(config) is ProtectedE3AdjudicationConfig:
        return "adjudicate"
    return config.mode + "-freeze" if config.operation == "freeze" else config.operation


@dataclass(frozen=True, slots=True)
class _CurrentConfigs:
    fit: ProtectedE3FitConfig
    by_task: object
    roots: object
    query_roots: object
    declarations: object
    unit_censuses: object


# Config rows and scientific contexts contain immutable records. Retain only
# one tuple by identity so every node in a compile shares its already checked
# census; another frozen wave, even with equal bytes, is independently checked.
_config_cache = None
_root_cache = None


def validate_current_configs(config_inputs):
    """Check one closed fit/freezes/CAL/CONF census without scientific I/O."""
    global _config_cache
    if _config_cache is not None and _config_cache[0] is config_inputs:
        return _config_cache[1]
    kinds = (ProtectedE3SourceConfig, ProtectedE3FeatureConfig, ProtectedE3PhysicalForecastConfig,
        ProtectedE3ResponseConfig, ProtectedE3FitConfig, ProtectedE3StatisticalConfig, ProtectedE3AdjudicationConfig)
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
        if type(config) is ProtectedE3SourceConfig and config.phase is ProtectedE3SourcePhase.PREFIX:
            roots[config.source.root_id] = config.source
    fits = tuple(config for config in by_task.values() if type(config) is ProtectedE3FitConfig)
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
        if type(config) is not ProtectedE3StatisticalConfig or config.root is not None:
            raise ValueError("protected E3 wave omits fit, separate model/calibration freezes or final assessment")
    terminal = adjudication_task_id(fit.specification, fit.allocation)
    expected.add(terminal)
    if type(by_task.get(terminal)) is not ProtectedE3AdjudicationConfig:
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
            if (type(config) is not ProtectedE3SourceConfig or config.phase is not phase or config.source != source
                    or config.source_manifest != fit.source_manifest):
                raise ValueError("protected E3 wave changes a whole root or source manifest across prefix phases")
        feature = by_task.get(feature_task_id(root_id))
        physical = by_task.get(response_task_id(root_id, "physical-forecast"))
        forecast = by_task.get(statistical_task_id(fit.specification, fit.allocation, "forecast", mode=role, root=root))
        if (type(feature) is not ProtectedE3FeatureConfig or feature.root != root or feature.allocation != fit.allocation
                or type(physical) is not ProtectedE3PhysicalForecastConfig
                or type(forecast) is not ProtectedE3StatisticalConfig or forecast.root != root or forecast.mode != role):
            raise ValueError("protected E3 wave omits its actual seedless feature and pre-future forecasts")
        expected.update((_task(feature), _task(physical), _task(forecast)))
        pair = []
        for operation in ("responses", "response-score"):
            node = response_task_id(root_id, operation)
            expected.add(node)
            config = by_task.get(node)
            if (type(config) is not ProtectedE3ResponseConfig or config.operation != operation or config.source != source
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
    if len({config.response_selection for config in by_task.values() if type(config) is ProtectedE3ResponseConfig}) != 1:
        raise ValueError("protected E3 wave mixes original paired response selections")
    for config in by_task.values():
        if (config.specification != fit.specification
                or type(config) in (ProtectedE3FitConfig, ProtectedE3StatisticalConfig, ProtectedE3FeatureConfig, ProtectedE3AdjudicationConfig)
                    and config.allocation != fit.allocation
                or type(config) in (ProtectedE3FitConfig, ProtectedE3StatisticalConfig) and config.query_census != fit.query_census):
            raise ValueError("protected E3 wave changes its frozen specification/allocation or selected population")
    declarations = {row.capability_key: row for row in operation_declarations()}
    unit_censuses = {}
    for config in by_task.values():
        phase = _phase(config)
        declaration = declarations[NAMESPACE + "." + phase]
        unit_censuses.setdefault(phase, set()).update(declaration.scientific_hooks.scientific_unit_ids(config))
    result = _CurrentConfigs(fit, MappingProxyType(by_task), MappingProxyType(roots),
        MappingProxyType({role: tuple(sorted(selected, key=lambda root: root.root_id)) for role, selected in query_roots.items()}),
        MappingProxyType(declarations), MappingProxyType({phase: tuple(sorted(units)) for phase, units in unit_censuses.items()}))
    _config_cache = config_inputs, result
    return result


def expected_producers(config, config_inputs):
    """One guard projection shared by lowering and cold root validation.

    Repeated external records use ``panels.*``/``streams.*``; their exact
    multiplicity and source bytes remain the declaration and qualification's
    contracts. Repeated reduction inputs name every exact selected whole root.
    """
    current = validate_current_configs(config_inputs)
    if current.by_task.get(_task(config)) != config:
        raise ValueError("protected E3 graph guard receives another selected configuration")
    fit, phase = current.fit, _phase(config)
    statistic = lambda operation, mode="", root=None: statistical_task_id(fit.specification, fit.allocation, operation, mode=mode, root=root)
    if type(config) is ProtectedE3SourceConfig:
        if config.phase is ProtectedE3SourcePhase.PREFIX:
            return {"streams.*" if name == "streams" else name: None for name, _ in PREFIX_INPUTS}
        selected = prefix_worker_phase(config.phase)
        return {**{name: None if producer is None else (source_task_id(config.source.root_id, producer), "product")
            for name, _, producer in selected.records}, **{name: (source_task_id(config.source.root_id, producer), "arrays")
                for name, producer in selected.arrays}}
    if type(config) is ProtectedE3FeatureConfig:
        root_id = config.root.root_id
        return {**{name: None if producer is None else (source_task_id(root_id, producer), "product")
            for name, _, producer in FEATURE_RECORD_INPUTS}, **{name: (source_task_id(root_id, producer), "arrays")
                for name, producer in FEATURE_ARRAY_INPUTS}}
    if type(config) in (ProtectedE3PhysicalForecastConfig, ProtectedE3ResponseConfig):
        root_id = config.root_id if type(config) is ProtectedE3PhysicalForecastConfig else config.source.root_id
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
    if type(config) is ProtectedE3AdjudicationConfig:
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
    if producer is None:
        return "SOURCE"
    if type(config) is ProtectedE3ResponseConfig and name in ("models", "frozen", "error", "calibration", "model-freeze"):
        return "MODEL"
    if type(config) is ProtectedE3AdjudicationConfig:
        return "OUTCOME"
    if type(config) in (ProtectedE3FitConfig, ProtectedE3StatisticalConfig):
        return "OUTCOME" if name.startswith("outcomes.") else "HISTORY" if name == "feature" else "MODEL"
    return "HISTORY"


def validate_generated_links(config_inputs, links):
    from .protected_root_validation import validate_protected_links
    return validate_protected_links(config_inputs, links, current=validate_current_configs(config_inputs),
        declaration_key=lambda config: NAMESPACE + "." + _phase(config), expected_producers=expected_producers, role=_role)


def _external_fingerprint(config, name, current):
    """Bind directly represented references; qualified owners cover other data."""
    if name == "specification":
        return current.fit.specification.object_fingerprint
    if name == "allocation":
        return current.fit.allocation.object_fingerprint
    if name == "manifest":
        return current.fit.source_manifest.object_fingerprint
    if type(config) is ProtectedE3FitConfig:
        if name == "training-allocation":
            return config.training_allocation.object_fingerprint
        keys = {"original-allocation": "allocation", "native-selection": "native-selection", "reservation": "reservation"}
        if name in keys:
            return next(publication.logical.content_sha256 for key, publication, _ in config.publications if key == keys[name])
    if type(config) is ProtectedE3FeatureConfig:
        return {"public-source": config.public_source.object_fingerprint,
            "numerical-design": config.numerical_design.object_fingerprint}.get(name)
    if type(config) in (ProtectedE3PhysicalForecastConfig, ProtectedE3ResponseConfig):
        if name in ("protocol", "numerical-profile"):
            return getattr(config, name.replace("-", "_")).object_fingerprint
    if type(config) in (ProtectedE3SourceConfig, ProtectedE3ResponseConfig):
        source = config.source
        root_id = source.root_id
        direct = {"source": source.fingerprint(), "coordinate": source.coordinate.object_fingerprint,
            "provenance": source.provenance.object_fingerprint,
            "prefix-config": current.by_task[source_task_id(root_id, ProtectedE3SourcePhase.PREFIX)].fingerprint()}
        if type(config) is ProtectedE3ResponseConfig:
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
    cache_key = (context.config_inputs, context.root, context.links, context.qualifications, context.known_design_inputs, context.external_inputs)
    if _root_cache is not None and all(a is b for a, b in zip(_root_cache, cache_key, strict=True)):
        return
    from .protected_root_validation import validate_protected_root
    validate_protected_root(context, current, validate_links=validate_generated_links, external_fingerprint=_external_fingerprint)
    _root_cache = cache_key


def scientific_root_validator(config, context):
    """One installed pure guard over the exact current scientific composition."""
    if type(context) is not RecursiveScientificRootContext:
        raise TypeError("protected E3 requires its actual compiler scientific-root context")
    current = validate_current_configs(context.config_inputs)
    node, phase = _task(config), _phase(config)
    if current.by_task.get(node) != config:
        raise ValueError("protected E3 root receives an unselected scientific configuration")
    declaration = current.declarations[NAMESPACE + "." + phase]
    hooks = declaration.scientific_hooks
    if (context.node_id != node or context.stage is not declaration.stage
            or context.outcome_access is not declaration.outcome_access or context.visibility_ceiling is not declaration.visibility_ceiling
            or context.unit_ids != hooks.scientific_unit_ids(config) or context.selected_unit_ids != current.unit_censuses[phase]
            or context.complete_unit_census is not declaration.execution_properties.complete_unit_census
            or context.requirements or context.connections):
        raise ValueError("protected E3 root changes its declared phase, complete unit census, access or lifecycle")
    _validate_root(context, current)
