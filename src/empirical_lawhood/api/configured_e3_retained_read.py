# SPDX-License-Identifier: MPL-2.0
"""Authenticate retained E3 copies through their original partial execution."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import ConfiguredE3RetainedExecution, ConfiguredE3RetainedTaskConfig
from empirical_lawhood.kernel.status import OperationalStatus

from .configured_e3_retained_custody import _active_original_reads, read_original_partial_e3
from .matrix_selected_runtime import _published_input


_active_reads = ContextVar('configured_e3_retained_product_reads', default=())
_active_unfinished_plan_reads = ContextVar('configured_e3_unfinished_plan_reads', default=())


@dataclass(frozen=True, slots=True)
class RetainedE3Read:
    retention: object
    original: object
    tasks: object
    unfinished: object = None
    predecessor: object = None

    def require_config(self, config, task, run_id):
        self.original.require_access()
        config.validate_retention(self.retention)
        if (run_id != self.retention.continued_run_id
                or self.tasks.get(task.task_id) != config
                or task.capability.config.config_schema != config.SCHEMA
                or task.capability.config.content_sha256 != config.fingerprint()):
            raise PermissionError('retained E3 product changes its exact original configuration or current adoption')

    def require_receipt(self, config, task, receipt):
        self.require_config(config, task, receipt.run_id)
        if (receipt.task_id != task.task_id or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or receipt.implementation_commit != self.retention.response_provenance.observed_git_head):
            raise PermissionError('retained E3 product lacks its actual continued successful copy receipt')
        original = {row.logical_artifact_id: row for row in config.original_receipt.output_logical_artifacts}
        old_physical = {row.logical_artifact_id: row for row in config.original_receipt.output_materializations}
        outputs = {row.output_id: row for row in task.outputs}
        logicals = {row.logical_artifact_id: row for row in receipt.output_logical_artifacts}
        physicals = {row.logical_artifact_id: row for row in receipt.output_materializations}
        if (set(outputs) != {row.output_id for row in config.original_task.outputs}
                or set(logicals) != {row.logical_artifact_id for row in task.outputs}
                or set(physicals) != set(logicals)):
            raise PermissionError('retained E3 product changes its complete copied output census')
        for output in config.original_task.outputs:
            old, before = original[output.logical_artifact_id], old_physical[output.logical_artifact_id]
            current = outputs[output.output_id]
            actual, physical = logicals[current.logical_artifact_id], physicals[current.logical_artifact_id]
            if ((actual.payload_schema, actual.profile, actual.media_type, actual.content_sha256,
                    actual.outcome_access, actual.visibility_ceiling, physical.physical_sha256, physical.size_bytes) !=
                    (old.payload_schema, old.profile, old.media_type, old.content_sha256,
                        old.outcome_access, old.visibility_ceiling, before.physical_sha256, before.size_bytes)):
                raise PermissionError('retained E3 product changes original receipt-bound bytes or access')
        self.original.require_access()


def task_retention(writer, run_id, task):
    specs = tuple(row for row in task.external_inputs
        if row.expected_payload_schema == ConfiguredE3RetainedExecution.SCHEMA)
    if len(specs) != 1:
        raise PermissionError('retained E3 product omits its exact published continuation')
    return _published_input(writer, run_id, specs[0], ConfiguredE3RetainedExecution)


@contextmanager
def retained_execution_read(*, writer, retention):
    """Reuse immutable proof only inside its still-open original access scope."""
    if type(retention) is not ConfiguredE3RetainedExecution:
        raise TypeError('retained E3 read requires its exact continuation record')
    for read in _active_reads.get():
        if read.original.writer.root is writer.root and read.retention == retention:
            read.original.require_access()
            yield read
            read.original.require_access()
            return

    @contextmanager
    def original_scope():
        rows = tuple(row for row in _active_original_reads.get() if row.writer.root is writer.root
            and row.directory == retention.original_authoring_directory
            and row.package.run_plan_id == retention.original_run_id)
        if len(rows) > 1:
            raise PermissionError('retained E3 read has ambiguous original custody lifetimes')
        if rows:
            rows[0].require_access()
            yield rows[0]
        else:
            with read_original_partial_e3(artifact_writer=writer, directory=retention.original_authoring_directory,
                    run_id=retention.original_run_id,
                    reveal_authority_id=retention.original_reveal_authority.object_id) as original:
                yield original

    with original_scope() as original:
        expected, tasks = original.continuation(record_id=retention.record_id,
            continued_run_id=retention.continued_run_id, response_provenance=retention.response_provenance)
        if expected != retention:
            raise PermissionError('retained E3 read substitutes its actual original partial execution')
        read = RetainedE3Read(retention, original, {row.original_task.task_id: row for row in tasks})
        token = _active_reads.set((*_active_reads.get(), read))
        try:
            yield read
            original.require_access()
        finally:
            _active_reads.reset(token)


@contextmanager
def continued_plan_read(*, writer, plan, receipts=None):
    """Keep original custody live across one complete continued-product read."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import ConfiguredE3UnfinishedExecution
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import ConfiguredE3ClosedExecution
    closed = tuple(spec for task in plan.tasks for spec in task.external_inputs
        if spec.expected_payload_schema == ConfiguredE3ClosedExecution.SCHEMA)
    if closed:
        with unfinished_plan_read(writer=writer, plan=plan, specs=closed, closed=True) as read:
            yield read
        return
    unfinished = tuple(spec for task in plan.tasks for spec in task.external_inputs
        if spec.expected_payload_schema == ConfiguredE3UnfinishedExecution.SCHEMA)
    if unfinished:
        with unfinished_plan_read(writer=writer, plan=plan, specs=unfinished) as read:
            yield read
        return
    tasks = tuple(task for task in plan.tasks if task.capability.config.config_schema == ConfiguredE3RetainedTaskConfig.SCHEMA)
    if not tasks:
        yield None
        return
    run_id = plan.source_plan.object_id
    retention = task_retention(writer, run_id, tasks[0])
    def retention_metadata(spec):
        return (spec.logical_artifact_id, spec.expected_payload_schema, spec.expected_content_sha256,
            spec.expected_size_bytes, spec.expected_media_type, spec.expected_outcome_access, spec.expected_visibility_ceiling)
    shared, = (row for row in tasks[0].external_inputs if row.expected_payload_schema == ConfiguredE3RetainedExecution.SCHEMA)
    with retained_execution_read(writer=writer, retention=retention) as read:
        if ({task.task_id for task in plan.tasks} != {task.task_id for task in read.original.plan.tasks}
                or {task.task_id for task in tasks} != set(read.tasks)):
            raise PermissionError('retained E3 read changes its original graph or complete adoption census')
        for task in tasks:
            specs = tuple(row for row in task.external_inputs if row.logical_artifact_id == task.capability.config.artifact_id)
            pins = tuple(row for row in task.external_inputs
                if row.expected_payload_schema == ConfiguredE3RetainedExecution.SCHEMA)
            if len(specs) != 1 or len(pins) != 1 or retention_metadata(pins[0]) != retention_metadata(shared):
                raise PermissionError('retained E3 read changes an adopted task continuation')
            config = _published_input(writer, run_id, specs[0], ConfiguredE3RetainedTaskConfig)
            read.require_config(config, task, run_id)
            if receipts is not None:
                if task.task_id not in receipts:
                    raise PermissionError('retained E3 read omits a required successful adoption')
                read.require_receipt(config, task, receipts[task.task_id])
        yield read


@contextmanager
def unfinished_plan_read(*, writer, plan, specs, closed=False):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import ConfiguredE3UnfinishedExecution
    from .configured_e3_unfinished_custody import read_unfinished_e3
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import ConfiguredE3ClosedExecution
    from .configured_e3_closeout_custody import read_closed_e3
    run_id = plan.source_plan.object_id
    scope = _published_input(writer, run_id, specs[0], ConfiguredE3ClosedExecution if closed else ConfiguredE3UnfinishedExecution)
    if (any(spec != specs[0] for spec in specs)
            or scope.retention.continued_run_id != run_id
            or {task.task_id for task in plan.tasks} != set(scope.unfinished_task_ids)):
        raise PermissionError('unfinished E3 read changes its exact selected execution boundary')
    reader = read_closed_e3 if closed else read_unfinished_e3
    with reader(artifact_writer=writer, directory=scope.predecessor_authoring_directory,
            run_id=scope.predecessor_run_id, reveal_authority_id=scope.predecessor_reveal_authority.object_id) as predecessor:
        projection = predecessor.closeout if closed else predecessor.unfinished
        if projection(record_id=scope.record_id, retention=scope.retention) != scope:
            raise PermissionError('unfinished E3 read changes its actual preceding receipt and resource history')
        retention, tasks = predecessor.continuation(record_id=scope.retention.record_id,
            continued_run_id=run_id, response_provenance=scope.retention.response_provenance)
        if retention != scope.retention:
            raise PermissionError('unfinished E3 read changes its original scientific retention')
        read = RetainedE3Read(retention, predecessor.original, {row.original_task.task_id: row for row in tasks}, scope, predecessor)
        token = _active_unfinished_plan_reads.set((*_active_unfinished_plan_reads.get(), (writer.root, plan, read)))
        try:
            yield read
            predecessor.require_access()
        finally:
            _active_unfinished_plan_reads.reset(token)


def producing_custody(writer, plan, task_id):
    """Return the actual old producer within the current live continuation read."""
    matches = tuple(read for root, current, read in _active_unfinished_plan_reads.get()
        if root is writer.root and current is plan)
    if len(matches) > 1:
        raise PermissionError('E3 product has ambiguous original custody lifetimes')
    if not matches or task_id not in matches[0].predecessor.receipts:
        return None
    previous = matches[0].predecessor
    previous.require_access()
    return previous.product_source(task_id) if hasattr(previous, 'product_source') else previous


def consumed_parent(*, writer, plan, receipts, task, edge):
    """Authenticate the materialization actually consumed, retaining its producer."""
    if edge is None:
        raise PermissionError('E3 read omits its consumed scientific parent')
    producer = edge.producer_task_id
    source_writer = writer
    if producer is None:
        from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
        matches = tuple(read for root, current, read in _active_unfinished_plan_reads.get()
            if root is writer.root and current is plan)
        if len(matches) != 1:
            raise PermissionError('E3 external parent lacks its authenticated unfinished execution lifetime')
        read, = matches
        read.predecessor.require_access()
        imported = tuple(row for row in read.unfinished.imported_outputs
            if row.logical.logical_artifact_id == edge.operational_logical_artifact_id)
        if len(imported) != 1:
            raise PermissionError('E3 external parent is not an original receipted output')
        original, = imported
        producer = original.task_id
        receipt = read.predecessor.receipts[producer]
        logical, physical = original.logical, original.materialization
        relative, _, _ = provider_input_location(writer, plan.source_plan.object_id, logical.logical_artifact_id)
        manifest = writer.read_manifest(relative)
        writer.verify_manifest(manifest)
        if (manifest.logical.content_sha256, manifest.logical.payload_schema, manifest.logical.profile,
                manifest.logical.media_type, manifest.logical.outcome_access, manifest.logical.visibility_ceiling,
                manifest.materialization.physical_sha256, manifest.materialization.size_bytes) != (
                logical.content_sha256, logical.payload_schema, logical.profile, logical.media_type,
                logical.outcome_access, logical.visibility_ceiling, physical.physical_sha256, physical.size_bytes):
            raise PermissionError('E3 external parent changes original receipt bytes or access')
        consumed = manifest.materialization
        owner = producing_custody(writer, plan, producer)
        if owner is None:
            raise PermissionError('E3 external parent loses its actual producing custody')
        source_writer = owner.writer
    else:
        receipt = receipts.get(producer)
        if receipt is None:
            raise PermissionError('E3 consumed parent lacks its original successful receipt')
        logicals = tuple(row for row in receipt.output_logical_artifacts
            if row.logical_artifact_id == edge.operational_logical_artifact_id)
        materials = tuple(row for row in receipt.output_materializations
            if row.logical_artifact_id == edge.operational_logical_artifact_id)
        if len(logicals) != 1 or len(materials) != 1:
            raise PermissionError('E3 read changes its consumed typed output')
        logical, consumed = logicals[0], materials[0]
    if logical.payload_schema != edge.payload_schema:
        raise PermissionError('E3 read changes its consumed typed output')
    consumer = receipts.get(task.task_id)
    if consumer is None or consumed.materialization_id not in consumer.input_materialization_ids:
        raise PermissionError('E3 read changes its consumed parent materialization')
    return producer, receipt, logical, source_writer


def authenticated_original_config(*, writer, run_id, task, config):
    """Unwrap scientific operands only after authenticating their real producer."""
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
    if not scientific_reconstruction_enabled():
        from .retained_e3_evidence import retained_e3_evidence_context
        with retained_e3_evidence_context(writer) as read:
            return read.original_config(task_retention(writer, run_id, task), task, config)
    with retained_execution_read(writer=writer, retention=task_retention(writer, run_id, task)) as read:
        read.require_config(config, task, run_id)
        return config.original_config


def authenticate_continued_response_custody(*, writer, plan, receipts, selection, specification,
        allocation, models, model_freeze, calibration, calibrated_freeze, product_reader):
    """Replay original prefix/freeze joins and actual continued native events."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_continued_response import ConfiguredE3ContinuedResponseConfig, ConfiguredE3ContinuedNativeResponse
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import selected_configs, task_id
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_prefix_records import ConfiguredProtectedE3PrefixHistory, ConfiguredProtectedE3CausalPrefix
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_records import ConfiguredProtectedE3PhysicalForecast
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import ConfiguredProtectedE3Forecast
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorNativeBinding
    from .configured_e3_retained_custody import _NativeBinding
    from .recursive_qualified_parents import _prior_native_subwork

    def pin(record, field='record_id'):
        return ObjectIdentity.from_record(getattr(record, field), record)

    tasks = {task.task_id: task for task in plan.tasks}
    configs = {task_id(config): config for config in selected_configs(specification, allocation, selection)}
    closeout = getattr(selection, 'closeout', None)
    if closeout is not None:
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import ConfiguredProtectedE3PairedOutcome
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
        matches = tuple(read for root, current, read in _active_unfinished_plan_reads.get()
            if root is writer.root and current is plan and read.unfinished == closeout)
        if len(matches) != 1:
            raise PermissionError('CAL closeout result lacks its actual original custody lifetime')
        expected = matches[0].predecessor.missing_products(selection.retention.response_provenance)
        for row in closeout.calibration_roots:
            if row.missing_products is not None:
                missing = expected[row.native_task_id]
                score = product_reader(writer, plan, receipts, row.outcome_task_id, ScheduledResponseScore)[0]
                outcome = product_reader(writer, plan, receipts, row.outcome_task_id, ConfiguredProtectedE3PairedOutcome)[0]
                if (score, outcome) != (missing.score, missing.outcome):
                    raise PermissionError('CAL closeout result changes its authenticated missing outcome')
    protocols = {pin(row, 'protocol_id'): row for row in selection.protocols}
    profiles = {pin(row): row for row in selection.numerical_profiles}
    projections = {row.prefix_policy: row for row in selection.projections}
    events = []
    for name, config in configs.items():
        if type(config) is not ConfiguredE3ContinuedResponseConfig or config.operation != 'responses':
            continue
        if closeout is not None and name not in tasks:
            if name not in {row.native_task_id for row in closeout.calibration_roots}:
                raise PermissionError('CAL closeout drops an unclosed response task')
            # The live closeout owner above authenticates every original CAL
            # native return and missing contact under its actual producing plan.
            continue
        task = tasks[name]
        if task.capability.config.content_sha256 != config.fingerprint():
            raise PermissionError('continued E3 read changes the actual issued native response configuration')
        edges = {edge.consumer_input_id: edge for edge in task.scientific_inputs}

        def consumed(port, kind):
            edge = edges.get(port)
            producer, _, logical, _ = consumed_parent(writer=writer, plan=plan, receipts=receipts, task=task, edge=edge)
            if logical.payload_schema != kind.SCHEMA:
                raise PermissionError('continued E3 read changes its exact consumed typed parent')
            return producer, product_reader(writer, plan, receipts, producer, kind)[0]

        prefix_task, history = consumed('history', ConfiguredProtectedE3PrefixHistory)
        _, causal = consumed('causal', ConfiguredProtectedE3CausalPrefix)
        physical_task, physical = consumed('physical', ConfiguredProtectedE3PhysicalForecast)
        _, error = consumed('error', ConfiguredProtectedE3Forecast)
        prefix_config = configs[prefix_task].original_config
        physical_config = configs[physical_task].original_config
        source = history.validate_source(prefix_config, selection.manifest, specification=specification)
        response = product_reader(writer, plan, receipts, name, ConfiguredE3ContinuedNativeResponse)[0]
        protocol = protocols[config.protocol]
        panels = tuple(row for row in selection.panels if row.independent_group_id == source.root.root.independent_group_id)
        confirmation = source.root.root.role.value == 'CONFIRMATION'
        response.validate_source(config, source=source, specification=specification, manifest=selection.manifest,
            selection=selection.response_selection, protocol=protocol, numerical_profile=profiles[config.numerical_profile],
            panels=panels, history=history, causal=causal, physical_config=physical_config, physical=physical,
            error=error, allocation=allocation, models=models, frozen=calibrated_freeze if confirmation else model_freeze,
            calibration=calibration if confirmation else None, model_freeze=model_freeze if confirmation else None,
            mathematical_protocol=selection.mathematical_protocol,
            projection=projections[pin(protocol.public_source.policy, 'policy_id')], retention=selection.retention)
        for evidence in response.native:
            events.append((name, evidence))
    bindings = tuple(RecursivePriorNativeBinding(name, event.definition.identity,
        ObjectIdentity.from_record('completion.' + event.definition.subwork_id, event.completion),
        pin(event.receipt, 'receipt_id')) for name, event in events)
    inspections = _prior_native_subwork(writer, _NativeBinding(bindings, pin(plan, 'execution_plan_id'),
        selection.retention.continued_run_id), plan, receipts)
    actual = {name: event for name, event in events}
    for row in inspections:
        event = actual[row.binding.task_id]
        if ((row.inspection.definition, row.inspection.completion, row.inspection.receipt) !=
                (event.definition, event.completion, event.receipt)):
            raise PermissionError('continued E3 read changes its actual completed response native evidence')
