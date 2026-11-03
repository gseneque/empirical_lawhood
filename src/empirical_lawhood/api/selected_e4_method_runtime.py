# SPDX-License-Identifier: MPL-2.0
"""Actual original DEV acquisition and current selected E4 method custody."""

from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustodySupplier

from hashlib import sha256
from fractions import Fraction

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as acquisition_owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as owner
from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from .recursive_execution import read_recursive_wave
from .recursive_qualified_parents import MAX_PARENT_BYTES, _output_payload
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactManifest
from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import ScheduledRevisionTarget


def _read_control(writer, manifest, kind):
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    if (manifest.logical.payload_schema != kind.SCHEMA or manifest.logical.media_type != "application/json"
            or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise PermissionError("selected DEV method changes original authenticated external input lane")
    writer.verify_manifest(manifest)
    raw = read_bounded_bytes(writer.root.resolve(manifest.materialization.relative_path, for_write=False),
        maximum_bytes=manifest.materialization.size_bytes)
    value = decode_canonical_bytes(raw, kind, maximum_bytes=manifest.materialization.size_bytes)
    if (value.canonical_bytes() != raw or len(raw) != manifest.materialization.size_bytes
            or sha256(raw).hexdigest() != manifest.logical.content_sha256
            or sha256(raw).hexdigest() != manifest.materialization.physical_sha256):
        raise PermissionError("selected DEV method changes actual original canonical input bytes")
    return value


def _external_record(writer, task, controls, schema, kind):
    rows = tuple(controls.get(value.logical_artifact_id) for value in task.external_inputs
        if value.expected_payload_schema == schema)
    if len(rows) != 1 or rows[0] is None:
        raise PermissionError("selected DEV method omits one actual original external operand")
    return _read_control(writer, rows[0], kind)


def original_development_products(*, writer, locator, programme, bank, data_id, _secondary_readout=None,
        _observe_original_access=None):
    """Stream authentic score records; retain bounded paired projections only."""
    from empirical_lawhood.api.matrix_selected_e3_e4_read import _read_selected_e3_e4_development
    if type(locator) is not owner.SelectedE4DevelopmentAcquisition:
        raise TypeError("selected revision needs the actual original DEV acquisition locator")
    if _observe_original_access is not None and not callable(_observe_original_access):
        raise TypeError('original DEV access observer must be callable')
    locator.__post_init__()
    r.validate_development_bank(programme, bank)
    directory = writer.root.resolve(locator.authored_directory, for_write=False)
    authored = {}
    def validate_authored(*, packet, draft, run, plan):
        plan_pin = ObjectIdentity.from_record(plan.execution_plan_id, plan)
        if run.run_plan_id != locator.run_id or plan_pin != locator.execution_plan:
            raise PermissionError("selected revision substitutes original DEV native run or retained plan")
        declarations = {row.capability_key: row for row in acquisition_owner.operation_declarations()}
        entries = tuple(row for row in draft.operations if row.selection.capability_key == acquisition_owner.NAMESPACE + ".entry")
        if len(entries) != 1 or draft.development_study is None or draft.prospective_draft is not None:
            raise PermissionError("selected revision source is not an actual truthful native DEV programme")
        operation, = entries
        entry = decode_recursive_config_input(operation, declarations[operation.selection.capability_key].registration()).record
        if _secondary_readout is not None and entry.secondary_readout != _secondary_readout:
            raise PermissionError('selected E4 later phase changes the target sealed by the original DEV entry')
        if entry.programme != programme or entry.bank != bank:
            raise PermissionError("selected revision source changes actual native DEV full programme or bank")
        authored.update(packet=packet, draft=draft, run=run, plan=plan, operation=operation)
    # The installed reader retains failed/unknown/unentered cases and the full
    # denominator. It starts no native work and reads no original E3 CAL bank.
    authenticated = {}
    def consume(*, products, plan, draft, entry, bank, run_id, original_input_access=None, **_):
        if (entry.programme, bank, run_id) != (programme, selected_bank, locator.run_id):
            raise PermissionError("selected revision actual DEV reader substitutes its original programme/bank/run")
        authenticated.update(products=products, plan=plan, draft=draft, original_input_access=original_input_access)
        if _observe_original_access is not None and original_input_access is not None:
            _observe_original_access(original_input_access)
    selected_bank = bank
    readout = _read_selected_e3_e4_development(directory=directory, artifact_writer=writer,
        allow_partial=locator.allow_partial, _consume_original=None if locator.allow_partial else consume,
        _validate_authored=validate_authored)
    packet, draft, run, plan, operation = (authored[name] for name in ("packet", "draft", "run", "plan", "operation"))
    reduction = decode_canonical_record(readout["reduction"], r.SelectedE3E4DevelopmentReduction)
    if locator.allow_partial:
        # Partial projections deliberately do not hand scientific consumers a
        # complete reader context; preserve their separate custody replay.
        report, products, actual_draft, actual_plan = read_recursive_wave(directory=directory, artifact_writer=writer,
            include_products=True, terminal_product_format="compact", allow_partial=True)
    else:
        products, actual_draft, actual_plan = (authenticated[name] for name in ("products", "draft", "plan"))
        report = readout
    return _original_development_observations(writer=writer, locator=locator, programme=programme, bank=bank,
        data_id=data_id, packet=packet, draft=draft, plan=plan, operation=operation, reduction=reduction,
        report=report, products=products, actual_draft=actual_draft, actual_plan=actual_plan,
        original_input_access=authenticated.get('original_input_access'))


def _original_development_observations(*, writer, locator, programme, bank, data_id, packet, draft, plan,
        operation, reduction, report, products, actual_draft, actual_plan, original_input_access=None):
    """Finish one already authenticated original DEV read; no later-call authority."""
    from empirical_lawhood.api.matrix_selected_e3_e4_read import _record
    from .matrix_read_indexes import product_record_index
    from functools import partial
    product_lookup = product_record_index(products)
    record = partial(_record, original_input_access=original_input_access, product_lookup=product_lookup)
    if (actual_draft, actual_plan, report["packet_sha256"], report["run_id"]) != (draft, plan, packet.fingerprint(), locator.run_id):
        raise PermissionError("selected revision original DEV custody changed during exact source replay")
    receipt = products["receipts"].get(operation.node_id)
    if receipt is None or ObjectIdentity.from_record(receipt.receipt_id, receipt) != locator.entry_receipt:
        raise PermissionError("selected revision lacks the actual successful original four-product source entry")
    seal = record(writer, products, operation.node_id, r.SelectedE3E4EntrySeal)
    if seal is None or seal.programme != programme.identity or seal.bank != bank.identity or seal.forecast_design != programme.forecast_design:
        raise PermissionError("selected revision substitutes actual original complete native DEV entry")
    cases = []
    index=bank.source_index()
    matched = getattr(bank.forecast_design.package.specification.measurement, 'is_matched', False)
    from .selected_e4_case_projection import original_score_projections
    projections = original_score_projections(writer=writer, products=products, programme=programme, bank=bank,
        original_input_access=original_input_access, product_lookup=product_lookup)
    for case, result, projection in zip(programme.cases, reduction.cases, projections, strict=True):
        prefix = record(writer, products, acquisition_owner.local_node(case.root_id, "project"), r.SelectedE3E4CausalPrefix)
        # Actual DEV acquisition owner calls the causal operation project.
        source = bank.source(case.root_id,index=index)
        protocol, panels = bank.response_selection.validate_source(source)
        feature = None
        if matched:
            account = record(writer, products, acquisition_owner.local_node(case.root_id, 'account'), r.SelectedE3E4AccountSeal)
            if (account is None) != (result.forecast is None):
                raise PermissionError('matched E4 DEV observations omit the actual original sealed account')
            if account is not None:
                physical = record(writer, products, acquisition_owner.local_node(case.root_id, 'mechanical'), r.SelectedE3E4MechanicalForecast)
                witness = record(writer, products, acquisition_owner.local_node(case.root_id, 'measure'), r.SelectedE3E4Witness)
                if any(value is None for value in (prefix, physical, witness)):
                    raise PermissionError('matched E4 DEV observations omit the original causal/mechanical evidence')
                from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_science import (
                    validate_selected_account, validate_selected_account_lineage,
                )
                from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
                validate_selected_account_lineage(account, bank.forecast_design, protocol.public_source, prefix, witness,
                    protocol=protocol, physical=physical, physical_kind=r.SelectedE3E4MechanicalForecast)
                if scientific_reconstruction_enabled():
                    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
                    arrays = []
                    for phase, operand in (('project', prefix.arrays), ('measure', witness.arrays), ('mechanical', physical.arrays)):
                        raw = _original_array(writer, products, plan, acquisition_owner.local_node(case.root_id, phase), operand,
                            original_input_access=original_input_access)
                        arrays.append(decode_matrix_arrays(raw, operand))
                    validate_selected_account(account, bank.forecast_design, protocol.public_source, prefix, witness,
                        arrays[0], arrays[1], protocol=protocol, physical=physical, frozen_arrays=arrays[2], physical_kind=r.SelectedE3E4MechanicalForecast)
                feature = p.SelectedE4CausalFeatureProjection.from_account(account)
        cases.append(p.SelectedE4ObservedCase(case.root_id, case.source, case.independent_group_id, source.coordinate,
            None if prefix is None else p.SelectedE4PrefixProjection.from_record(prefix, record_id="projection." + case.root_id),
            projection, result.disposition, result.numerical_disposition, result.forecast, None, result.original_log_points,
            result.target_contract, feature))
    observed = p.SelectedE4ObservedData(data_id, programme.identity, r.pin(reduction), tuple(cases))
    # All original joins are independently replayed before any fitting.
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import validate_observed_data
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import E4MatchedRelationTarget
    target = E4MatchedRelationTarget('target.source-replay', programme.criterion) if matched else ScheduledRevisionTarget("target.source-replay",
        programme.criterion, bank.forecast_design.package.specification.measurement.horizons, ("PRIMARY", "FINE"),
        "CUMULATIVE_LOG1P_NORMALIZED_RESPONSE_ERROR_ALL15")
    validate_observed_data(programme, bank, reduction, observed, target, allow_absent=False)
    if original_input_access is not None:
        original_input_access.require_current()
    return reduction, observed


def _original_array(writer, products, plan, task_id, operand, *, original_input_access=None):
    """Reuse the existing exact receipt/publication array boundary for DEV replay."""
    from empirical_lawhood.api.matrix_full_factor_custody import _output
    actual = _output(writer, products, plan, task_id, 'arrays', original_input_access=original_input_access)
    if actual is None:
        raise PermissionError('matched E4 causal replay lacks a successful original array output')
    _, publication = actual
    artifact = operand.array_artifact
    if ((publication.logical.logical_artifact_id, publication.logical.payload_schema, publication.logical.content_sha256,
            publication.logical.media_type, publication.materialization.physical_sha256, publication.materialization.size_bytes) !=
            (artifact.artifact_id, artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.sha256, artifact.size_bytes)):
        raise PermissionError('matched E4 causal replay substitutes the original named array archive')
    if original_input_access is not None:
        original_input_access.require_current()
    raw = read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path, for_write=False), maximum_bytes=artifact.size_bytes)
    if original_input_access is not None:
        original_input_access.require_current()
    return raw


def authenticate_selected_e4_development_operands(*, writer, draft, plan, task, config, controls, codecs, receipts=None,
        _secondary_readout=None, _original_development_reader=None):
    """Replay actual native DEV provenance for fit and its original freeze.

    controls is the authenticated full external manifest census of this original
    method packet; receipts is the official successful dependency receipt map.
    No issued package, reveal grant or invented development qualification exists.
    """
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
    if type(plan) is not DevelopmentExecutionPlan or type(config) is not owner.SelectedE4MethodConfig:
        raise PermissionError("selected revision requires its actual authored DEV plan and exact method owner")
    declarations = {row.capability_key: row for row in owner.operation_declarations()}
    fits = tuple(row for row in draft.operations if row.selection.capability_key == owner.NAMESPACE + ".revision-fit")
    freezes = tuple(row for row in draft.operations if row.selection.capability_key == owner.NAMESPACE + ".revision-freeze")
    if len(fits) != 1 or len(freezes) != 1 or len(draft.operations) != 2 or draft.development_study is None:
        raise PermissionError("selected revision original DEV packet changes its exact one-fit/one-freeze source scope")
    fit_operation, = fits
    fit_config = decode_recursive_config_input(fit_operation, declarations[fit_operation.selection.capability_key].registration()).record
    fit_tasks = tuple(row for row in plan.tasks if row.task_id == fit_operation.node_id)
    if len(fit_tasks) != 1 or fit_tasks[0].capability.requested_resources != fit_config.operational_budget:
        raise PermissionError("selected revision original fitting reservation differs from its frozen selection")
    fit_task, = fit_tasks
    records = {name: _external_record(writer, fit_task, controls, kind.SCHEMA, kind)
        for name, kind in owner.input_types("revision-fit").items()}
    if (records["programme"].identity != fit_config.programme or records["programme"].group_ids != fit_config.group_ids
            or any(owner.record_identity(records[name]) != pin for name, pin in fit_config.external_operands)
            or fit_config.programme != config.programme or fit_config.group_ids != config.group_ids
            or task.capability.requested_resources != config.operational_budget):
        raise PermissionError("selected revision original acquisition/science/budget pins do not match actual method operands")
    reader = original_development_products if _original_development_reader is None else _original_development_reader
    actual_reduction, actual_data = reader(writer=writer, locator=records["acquisition"],
        programme=records["programme"], bank=records["bank"], data_id=records["data"].record_id,
        _secondary_readout=_secondary_readout)
    if (records["reduction"], records["data"]) != (actual_reduction, actual_data):
        raise PermissionError("selected revision cannot fit a caller-authored observation companion")
    records["specification"].validate_programme(records["programme"])
    if config.operation == "revision-freeze":
        receipt = None if receipts is None else receipts.get(fit_task.task_id)
        if receipt is None or fit_task.task_id not in task.dependency_task_ids:
            raise PermissionError("selected revision freeze lacks the actual successful original fit dependency")
        logicals = tuple(row for row in receipt.output_logical_artifacts if row.payload_schema == owner.science.SelectedE4RevisionNomination.SCHEMA)
        if len(logicals) != 1:
            raise PermissionError("selected revision freeze substitutes the actual original nomination output")
        raw = _output_payload(writer, receipt, logicals[0], MAX_PARENT_BYTES)
        nomination = decode_canonical_bytes(raw, owner.science.SelectedE4RevisionNomination, maximum_bytes=MAX_PARENT_BYTES)
        if (nomination.specification != records["specification"] or nomination.data != actual_data.identity
                or nomination.canonical_bytes() != raw):
            raise PermissionError("selected revision freeze changes genuine original native-derived fitting inputs")
    elif config.operation != "revision-fit":
        raise PermissionError("selected DEV source authentication cannot admit another method lane")
    return records


class SelectedE4DevelopmentMethodRuntimeSupplier(CurrentIssuedTaskCustodySupplier):
    def __init__(self, supplier, *, writer, directory, plan, output_codecs):
        self.supplier, self.writer, self.output_codecs = supplier, writer, dict(output_codecs)
        self.custody = CurrentDevelopmentTaskCustody(writer=writer, directory=directory, plan=plan)

    def resolve(self, logical_artifact_ids):
        return self.supplier.resolve(logical_artifact_ids)

    def prepare_selected_e4_method(self, context, runner):
        if type(runner) is not owner.SelectedE4MethodWorker or runner.prepared_scope is not None:
            raise PermissionError("selected revision needs its exact installed unprepared DEV method runner")
        # Scheduler threads do not inherit the programme caller's read state.
        # Keep the complete original replay in this task's finite custody and
        # authority contexts, including the final current-task check.
        from empirical_lawhood.infrastructure.parallel_verification import canonical_validation_scope
        pool = getattr(getattr(self.writer, '_read_verification', None), 'canonical_pool', None)
        # Share the invocation's process capacity across scheduler threads.
        # The independent custody plane still owns its separate byte census.
        with canonical_validation_scope(min(8, self.writer.maximum_parallel_verifications), shared_pool=pool), self.custody.task_read_scope():
            return self._prepare_selected_e4_method(context, runner)

    def _prepare_selected_e4_method(self, context, runner):
        current = self.custody.current_task(context, runner)
        _, plan, task = current
        receipts, direct = self.custody.task_inputs(context, task)
        config = self.custody.control_record(direct[context.config.artifact_id], owner.SelectedE4MethodConfig,
            direct[context.config.artifact_id].materialization.size_bytes)
        if config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id:
            raise PermissionError("selected revision substitutes the current actual authored method config")
        with self.custody.writer.read_context() as writer:
            controls = {artifact_id: self.custody._manifest(value.materialization.relative_path,
                expected=ArtifactManifest(value.logical, value.materialization))
                for artifact_id, value in self.custody.inputs.items()}
            authenticate_selected_e4_development_operands(writer=writer, draft=self.custody.draft, plan=plan, task=task,
                config=config, controls=controls, codecs=self.output_codecs, receipts=receipts)
            writer.require_verification_snapshot()
        if self.custody.current_task(context, runner) != current:
            raise PermissionError("selected revision current DEV custody changed during source preparation")
        return runner.with_prepared_scope((context.run_id, context.task_id, context.input_materialization_ids,
            ObjectIdentity.from_record(plan.execution_plan_id, plan)))


def bind_selected_e4_development_runtime(*, supplier, writer, directory, plan, output_codecs):
    return SelectedE4DevelopmentMethodRuntimeSupplier(supplier, writer=writer, directory=directory, plan=plan, output_codecs=output_codecs)


def prepare_selected_e4_method(supplier, context, runner):
    """Fresh issued custody and actual successful entry for a protected tail."""
    from .selected_e4_native_runtime import authenticate_selected_e4_parent
    if type(runner) is not owner.SelectedE4MethodWorker or runner.prepared_scope is not None:
        raise PermissionError("selected protected tail needs its exact installed unprepared method worker")
    package, plan, task, receipts, controls, entry_config = authenticate_selected_e4_parent(supplier, context, runner)
    config_manifest = controls.get(context.config.artifact_id)
    if config_manifest is None:
        raise PermissionError("selected protected tail omits its actual current config publication")
    config_specs = tuple(value for value in task.external_inputs if value.logical_artifact_id == context.config.artifact_id)
    if len(config_specs) != 1:
        raise PermissionError("selected protected tail omits its exact current automatic config input")
    with supplier.writer.verification_scope() as writer:
        config = supplier.custody.control_record(config_manifest, owner.SelectedE4MethodConfig,
            config_manifest.materialization.size_bytes, expected_outcome_access=config_specs[0].expected_outcome_access,
            expected_visibility_ceiling=config_specs[0].expected_visibility_ceiling)
        if (config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id
                or config.operational_budget != task.capability.requested_resources
                or config.programme != entry_config.programme_pin or config.group_ids != entry_config.scope_group_ids):
            raise PermissionError("selected protected tail changes current full-programme source or operational reservation")
        writer.require_verification_snapshot()
    if supplier.custody.current_task(context, runner) != (package, plan, task):
        raise PermissionError("selected protected method current issued custody changed during preparation")
    return runner.with_prepared_scope((context.run_id, context.task_id, context.input_materialization_ids,
        ObjectIdentity.from_record(plan.execution_plan_id, plan)))


def validate_selected_e4_calibration_producer(*, binding, package, execution_plan, receipt, logical,
        writer, read_scope, expected_public):
    """Exact selected CAL scope after original issued/reveal/closure admission."""
    from empirical_lawhood.api.matrix_selected_producer_scope import _installed_task, _original_output, _read_config
    from .matrix_selected_runtime import _published_input
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_bindings import operation_declarations as native_declarations

    if type(expected_public) is not p.SelectedE4PublicCalibration:
        raise TypeError("selected CAL producer requires its actual expected public original projection")
    expected_public.__post_init__()
    tasks = tuple(row for row in execution_plan.tasks if row.task_id == binding.task_id)
    if len(tasks) != 1 or (receipt.run_id, receipt.task_id) != (binding.run_id, binding.task_id):
        raise PermissionError("selected CAL producer changes actual original task/receipt")
    task, = tasks
    declaration = next(row for row in owner.operation_declarations() if row.capability_key == owner.NAMESPACE + ".revision-calibrate")
    _installed_task(task, package, declaration)
    _original_output(task, logical, binding, declaration)
    config = _read_config(writer, binding, task, owner.SelectedE4MethodConfig)
    if (config.operation != "revision-calibrate" or config.programme != expected_public.specification.calibration_programme
            or config.group_ids != expected_public.group_ids or config.operational_budget != task.capability.requested_resources):
        raise PermissionError("selected CAL producer changes full independent population or frozen reservation")
    def operand(name, kind):
        links = tuple(row for row in config.links if row.consumer_input_id == name and row.external_input_id is not None)
        if len(links) != 1:
            raise PermissionError("selected CAL producer omits an exact original scientific operand")
        specs = tuple(row for row in task.external_inputs if row.input_id == links[0].external_input_id)
        if len(specs) != 1:
            raise PermissionError("selected CAL producer changes original external scientific custody")
        record = _published_input(writer, binding.run_id, specs[0], kind)
        if owner.record_identity(record) != dict(config.external_operands).get(name):
            raise PermissionError("selected CAL producer substitutes actual original scientific bytes")
        return record
    specification = operand("specification", p.SelectedE4CalibrationSpecification)
    revision = operand("revision", p.SelectedE4RevisionExport)
    programme = operand("programme", p.SelectedE4PhaseProgramme)
    if (specification != expected_public.specification or revision.models is None
            or (revision.decision.development, revision.decision.nomination, revision.decision.frozen) !=
            (specification.development_programme, specification.nomination, specification.frozen_models)
            or (revision.models.revision_model.identity, revision.models.baseline_model.identity, revision.models.target.identity) !=
            (expected_public.revision_model, expected_public.baseline_model, expected_public.target)
            or programme.group_ids != config.group_ids or programme.identity != config.programme
            or Fraction(specification.alpha) != 1 - Fraction(programme.confidence)):
        raise PermissionError("selected CAL producer substitutes exact frozen coefficients, alpha, target or model ancestry")
    entries = tuple(row for row in execution_plan.tasks if row.task_id == config.entry_node_id)
    if len(entries) != 1 or config.entry_node_id not in task.dependency_task_ids:
        raise PermissionError("selected CAL producer omits actual direct full-phase source entry")
    entry, = entries
    candidates = tuple(row for row in native_declarations() if row.capability_key == entry.capability.capability_key
        and any(output.payload_schema == owner.input_types("revision-calibrate")["entry"].SCHEMA for output in row.outputs))
    if len(candidates) != 1:
        raise PermissionError("selected CAL producer entry is not the independently installed scientific owner")
    _installed_task(entry, package, candidates[0])
    entry_config = _read_config(writer, binding, entry, candidates[0].config_record_type)
    if entry_config.programme_pin != config.programme or entry_config.scope_group_ids != config.group_ids:
        raise PermissionError("selected CAL producer changes original full-phase source-entry scope")


def describe_selected_e4_development_acquisition(*, directory, artifact_writer, allow_partial):
    """Derive a locator from original DEV custody; no researcher task-ID roster."""
    from .recursive_execution import _read_recursive_wave_with_roots
    result, roots, _ = _read_recursive_wave_with_roots(directory=directory, artifact_writer=artifact_writer,
        include_products=True, terminal_product_format="compact", allow_partial=allow_partial)
    report, products, actual_draft, actual_plan = result
    packet, draft, _, run, plan, _ = roots
    return _development_acquisition_from_read(directory=directory, artifact_writer=artifact_writer,
        allow_partial=allow_partial, packet=packet, draft=draft, run=run, plan=plan, report=report, products=products,
        actual_draft=actual_draft, actual_plan=actual_plan)


def _development_acquisition_from_read(*, directory, artifact_writer, allow_partial, packet, draft, run, plan,
        report, products, actual_draft, actual_plan):
    """Derive the original locator from this read's exact roots and entry receipt."""
    from pathlib import Path
    if (actual_draft, actual_plan, report["packet_sha256"]) != (draft, plan, packet.fingerprint()):
        raise PermissionError("selected original DEV declaration changed during locator projection")
    entries = tuple(row for row in plan.tasks if row.capability.capability_key == acquisition_owner.NAMESPACE + ".entry")
    if len(entries) != 1:
        raise PermissionError("selected revision locator needs the actual native DEV entry owner")
    entry, = entries
    receipt = products["receipts"].get(entry.task_id)
    if receipt is None:
        raise PermissionError("selected revision locator cannot invent successful original source entry")
    relative = Path(directory).resolve(strict=True).relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    return owner.SelectedE4DevelopmentAcquisition("acquisition." + plan.fingerprint(), relative, run.run_plan_id,
        ObjectIdentity.from_record(plan.execution_plan_id, plan), ObjectIdentity.from_record(receipt.receipt_id, receipt), allow_partial)


def selected_e4_revision_inputs_from_acquisition(*, directory, artifact_writer, allow_partial):
    """Read actual scientific source inputs for public --sources preparation."""
    if allow_partial is False:
        from .selected_e3_access import original_e3_authority_read_context
        # The retained-product reader and its observation projection must share
        # one complete byte census instead of reopening publications per case.
        with original_e3_authority_read_context(artifact_writer), artifact_writer.read_context() as reading:
            return _complete_selected_e4_revision_inputs_from_acquisition(directory=directory, artifact_writer=reading)
    locator = describe_selected_e4_development_acquisition(directory=directory, artifact_writer=artifact_writer, allow_partial=allow_partial)
    _, draft, _, _ = load_authored_wave(directory=directory, artifact_writer=artifact_writer, lazy_payloads=True)
    declarations = {row.capability_key: row for row in acquisition_owner.operation_declarations()}
    entry, = tuple(row for row in draft.operations if row.selection.capability_key == acquisition_owner.NAMESPACE + ".entry")
    config = decode_recursive_config_input(entry, declarations[entry.selection.capability_key].registration()).record
    reduction, data = original_development_products(writer=artifact_writer, locator=locator, programme=config.programme,
        bank=config.bank, data_id="observed." + config.programme.programme_id)
    return {"programme": config.programme, "bank": config.bank, "acquisition": locator, "reduction": reduction, "data": data}


def _complete_selected_e4_revision_inputs_from_acquisition(*, directory, artifact_writer):
    """Derive complete inputs through one original reader and its actual callback.

    Decoded roots and authenticated products remain local to this invocation.
    The explicitly partial route retains its separate original custody replay.
    """
    from empirical_lawhood.api.matrix_selected_e3_e4_read import _read_selected_e3_e4_development
    authored, authenticated = {}, {}
    def validate_authored(*, packet, draft, run, plan):
        declarations = {row.capability_key: row for row in acquisition_owner.operation_declarations()}
        entries = tuple(row for row in draft.operations if row.selection.capability_key == acquisition_owner.NAMESPACE + ".entry")
        if len(entries) != 1 or draft.development_study is None or draft.prospective_draft is not None:
            raise PermissionError("selected E4 read requires original complete truthful DEV declaration")
        entry, = entries
        config = decode_recursive_config_input(entry, declarations[entry.selection.capability_key].registration()).record
        if type(config) is not acquisition_owner.SelectedE3E4EntryConfig:
            raise PermissionError("selected E4 read changes original entry owner")
        r.validate_development_bank(config.programme, config.bank)
        authored.update(packet=packet, draft=draft, run=run, plan=plan, operation=entry, config=config)
    def consume(*, products, plan, draft, entry, bank, run_id, original_input_access=None, **_):
        config = authored["config"]
        if (draft, plan, entry, bank, run_id) != (authored["draft"], authored["plan"], config,
                config.bank, authored["run"].run_plan_id):
            raise PermissionError("selected revision complete derivation changes its original source/read callback")
        authenticated.update(products=products, draft=draft, plan=plan, original_input_access=original_input_access)
    readout = _read_selected_e3_e4_development(directory=directory, artifact_writer=artifact_writer,
        allow_partial=False, _validate_authored=validate_authored, _consume_original=consume)
    packet, draft, run, plan, operation, config = (authored[name]
        for name in ("packet", "draft", "run", "plan", "operation", "config"))
    products, actual_draft, actual_plan = (authenticated[name] for name in ("products", "draft", "plan"))
    locator = _development_acquisition_from_read(directory=directory, artifact_writer=artifact_writer,
        allow_partial=False, packet=packet, draft=draft, run=run, plan=plan, report=readout, products=products,
        actual_draft=actual_draft, actual_plan=actual_plan)
    reduction = decode_canonical_record(readout["reduction"], r.SelectedE3E4DevelopmentReduction)
    reduction, data = _original_development_observations(writer=artifact_writer, locator=locator,
        programme=config.programme, bank=config.bank, data_id="observed." + config.programme.programme_id,
        packet=packet, draft=draft, plan=plan, operation=operation, reduction=reduction, report=readout,
        products=products, actual_draft=actual_draft, actual_plan=actual_plan,
        original_input_access=authenticated.get('original_input_access'))
    return {"programme": config.programme, "bank": config.bank, "acquisition": locator, "reduction": reduction, "data": data}


def read_selected_e4_revision(*, directory, artifact_writer, allow_partial=False):
    """Read original DEV selection and complete adverse state without refitting."""
    from empirical_lawhood.api.matrix_selected_e3_e4_read import _record
    report, products, draft, plan = read_recursive_wave(directory=directory, artifact_writer=artifact_writer,
        include_products=True, terminal_product_format="compact", allow_partial=allow_partial)
    operations = {row.selection.capability_key: row for row in draft.operations}
    fit = operations.get(owner.NAMESPACE + ".revision-fit")
    freeze = operations.get(owner.NAMESPACE + ".revision-freeze")
    if len(operations) != 2 or fit is None or freeze is None or draft.development_study is None:
        raise PermissionError("selected E4 scientific read changes its actual fit/freeze development scope")
    nomination = _record(artifact_writer, products, fit.node_id, owner.science.SelectedE4RevisionNomination)
    frozen = _record(artifact_writer, products, freeze.node_id, owner.science.SelectedE4FrozenRevision)
    return {**report, "assigned_groups": len(draft.development_study.assigned_unit_ids),
        "scientific_disposition": None if nomination is None else nomination.trigger_disposition,
        "endpoint_fit_calls": None if nomination is None else nomination.endpoint_fit_calls,
        "missing_groups": None if nomination is None else list(nomination.missing_groups),
        "joint_freeze": None if frozen is None else frozen.to_document(),
        "qualification": "NOT_ESTABLISHED", "downstream_authority": "NONE", "new_native_contact_count": 0}


def validate_selected_e4_downstream_producer(*, binding, package, execution_plan, receipt, logical,
        writer, read_scope, expected_revision, expected_calibration, expected_e3_package):
    """Authenticate the genuine original CONF nomination's complete source scope."""
    from empirical_lawhood.api.matrix_selected_producer_scope import _installed_task, _original_output, _read_config
    from .matrix_selected_runtime import _published_input
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_bindings import operation_declarations as native_declarations

    if type(expected_revision) is not p.SelectedE4RevisionExport:
        raise TypeError("selected downstream producer needs its actual public original DEV decision/models")
    expected_revision.__post_init__()
    if expected_calibration is not None:
        if type(expected_calibration) is not p.SelectedE4PublicCalibration:
            raise TypeError("selected downstream producer needs the actual public original CAL projection")
        expected_calibration.__post_init__()
    if type(expected_e3_package) is not ObjectIdentity:
        raise TypeError("selected downstream producer needs its exact original E3 package pin")
    tasks = tuple(row for row in execution_plan.tasks if row.task_id == binding.task_id)
    if len(tasks) != 1 or (receipt.run_id, receipt.task_id) != (binding.run_id, binding.task_id):
        raise PermissionError("selected downstream producer changes original CONF task or receipt")
    task, = tasks
    declaration = next(row for row in owner.operation_declarations() if row.capability_key == owner.NAMESPACE + ".downstream-nominate")
    _installed_task(task, package, declaration)
    _original_output(task, logical, binding, declaration)
    config = _read_config(writer, binding, task, owner.SelectedE4MethodConfig)
    scope_links = tuple(row for row in config.links if row.consumer_input_id == "scope" and row.external_input_id is not None)
    scope_specs = tuple(row for row in task.external_inputs if len(scope_links) == 1 and row.input_id == scope_links[0].external_input_id)
    if len(scope_specs) != 1:
        raise PermissionError("selected downstream producer omits its actual pre-outcome scientific scope")
    scope = _published_input(writer, binding.run_id, scope_specs[0], owner.SelectedE4ConfirmationScope)
    if (scope.identity != dict(config.external_operands).get("scope")
            or scope.revision != expected_revision or scope.calibration != expected_calibration
            or scope.specification.original_e3_package != expected_e3_package
            or config.programme != scope.specification.confirmation
            or len(config.group_ids) != scope.specification.nomination_rule.confirmation_group_count
            or config.operational_budget != task.capability.requested_resources):
        raise PermissionError("selected downstream producer substitutes full CONF scope, frozen models/CAL or decision rule")
    confirmation_links = tuple(row for row in config.links if row.consumer_input_id == "confirmation")
    if len(confirmation_links) != 1 or confirmation_links[0].producer_output_id != "product":
        raise PermissionError("selected downstream producer lacks the actual complete CONF assessment")
    confirmation_tasks = tuple(row for row in execution_plan.tasks if row.task_id == confirmation_links[0].producer_node_id)
    if len(confirmation_tasks) != 1 or confirmation_tasks[0].task_id not in task.dependency_task_ids:
        raise PermissionError("selected downstream producer bypasses actual complete CONF receipt closure")
    confirmation_task, = confirmation_tasks
    confirmation_declaration = next(row for row in owner.operation_declarations()
        if row.capability_key == owner.NAMESPACE + ".confirmation-assess")
    _installed_task(confirmation_task, package, confirmation_declaration)
    confirmation_config = _read_config(writer, binding, confirmation_task, owner.SelectedE4MethodConfig)
    if (confirmation_config.programme, confirmation_config.group_ids, dict(confirmation_config.external_operands).get("scope")) != (
            config.programme, config.group_ids, scope.identity):
        raise PermissionError("selected downstream producer changes actual CONF population or frozen scientific choices")
    entries = tuple(row for row in execution_plan.tasks if row.task_id == config.entry_node_id)
    if len(entries) != 1 or config.entry_node_id not in task.dependency_task_ids:
        raise PermissionError("selected downstream producer omits actual direct fullphase entry")
    entry, = entries
    entry_declarations = tuple(row for row in native_declarations() if row.capability_key == entry.capability.capability_key
        and any(output.payload_schema == owner.input_types("downstream-nominate")["entry"].SCHEMA for output in row.outputs))
    if len(entry_declarations) != 1:
        raise PermissionError("selected downstream producer changes original installed fullphase entry owner")
    _installed_task(entry, package, entry_declarations[0])
    entry_config = _read_config(writer, binding, entry, entry_declarations[0].config_record_type)
    if entry_config.programme_pin != config.programme or entry_config.scope_group_ids != config.group_ids:
        raise PermissionError("selected downstream producer changes original full CONF source-entry census")

def export_selected_e4_revision_inputs_from_acquisition(*, directory, artifact_writer, output_directory,
        campaign, resources, allow_partial, expected_specification=None, expected_allocation=None):
    """Publish a ready public --sources selection from authenticated DEV alone."""
    from pathlib import Path
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_revision_preparation as public
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.serialization import validate_relative_locator
    from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest

    records = {**selected_e4_revision_inputs_from_acquisition(directory=directory, artifact_writer=artifact_writer,
        allow_partial=allow_partial), "campaign": campaign, "resources": resources}
    # Validate every supplied role and declared scientific join before
    # publishing any derived companion.
    public.SelectedE4RevisionInputs(**records).__post_init__()
    if expected_specification is not None:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import derive_revision_specification
        derive_revision_specification(expected_specification, records["programme"])
    if expected_allocation is not None:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import allocation
        if expected_allocation != allocation(records["programme"]):
            raise PermissionError("selected revision export changes its actual original native DEV allocation")
    destination = Path(output_directory)
    root = Path(artifact_writer.root.contract.canonical_path)
    if not destination.is_absolute() or any(value.is_symlink() for value in (destination, *destination.parents)):
        raise ValueError("selected revision export requires an absolute guarded real output directory")
    relative = destination.relative_to(root).as_posix()
    validate_relative_locator(relative)
    bindings, payloads = [], []
    for name, record in sorted(records.items()):
        raw = record.canonical_bytes()
        filename = name + "." + record.fingerprint() + ".json"
        identity = ObjectIdentity.from_record(getattr(record, public.ID_FIELDS[name]), record)
        bindings.append(ExperimentInputBinding(name, identity, filename, len(raw)))
        payloads.append((filename, record, raw))
    scope = "export.selected-e4-revision." + sha256(b"".join(row.canonical_bytes() for row in bindings)).hexdigest()
    selection = ExperimentInputSelection(scope, public.PROTOCOL_ID, tuple(bindings))
    payloads.append(("sources.json", selection, selection.canonical_bytes()))
    requests = tuple(ArtifactWriteRequest(scope + "." + filename.removesuffix(".json"), relative + "/" + filename,
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", scope, relative, raw,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
        for filename, record, raw in payloads)
    publications = artifact_writer.write_batch(requests)
    if len(publications) != len(requests):
        raise RuntimeError("selected revision export did not publish its exact complete source selection")
    return {"sources_path": str(destination / "sources.json"), "selection": selection,
        "records": records, "publications": publications, "native_contact": "none",
        "qualification": "NOT_ESTABLISHED"}
