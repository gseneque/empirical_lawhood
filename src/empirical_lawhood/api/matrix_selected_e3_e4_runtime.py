# SPDX-License-Identifier: MPL-2.0
"""Genuine authored DEV custody and original issued E3 product authentication."""

from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustodySupplier

from functools import partial

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner, selected_e3_e4_records as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_workers import SelectedE3E4Worker
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody
from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
from .recursive_qualified_parents import MAX_PARENT_BYTES, _output_payload
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile


def _authenticate_selected_projection(*, frozen, criterion, policies, preparation,
        binding, package, execution_plan, writer, assay=None, fit_config=None, downstream_coordinates=()):
    """One original fit plus distinct producer-pinned projections per parent read."""
    family = selected_e3_product_family(frozen.specification)
    preparation_types = (family.preparation_type,)
    if family.configured:
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import configured_preparation_types
        preparation_types = configured_preparation_types()
    ProtectedE3ProtocolProjection = family.projection_type
    ProtectedE3ResponseNumericalProfile = family.numerical_type
    _selected_protocol = family.selected_protocol
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import ProtectedE3NativeSourceManifest
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
    from empirical_lawhood.api.matrix_selected_producer_scope import _installed_task, _read_config
    from .matrix_selected_runtime import _published_input

    task, = (value for value in execution_plan.tasks if value.task_id == binding.task_id)
    declarations = {value.capability_key: value for value in family.operation_declarations()}
    kind = declarations[task.capability.capability_key].config_record_type
    config = _read_config(writer, binding, task, kind)
    if fit_config is not None and fit_config != config:
        raise PermissionError("selected original projection substitutes its already authenticated fit configuration")
    if assay is not None:
        if type(assay) is not MatrixPreparedAssayMethod:
            raise TypeError("selected original assay requires its exact complete method owner")
        assay.__post_init__()
    specs = tuple(value for value in task.external_inputs if value.expected_payload_schema == ProtectedE3NativeSourceManifest.SCHEMA)
    if len(specs) != 1:
        raise PermissionError("selected E4 original fit omits its actual preparation manifest")
    manifest = _published_input(writer, binding.run_id, specs[0], ProtectedE3NativeSourceManifest)
    if (science.pin(manifest) != config.source_manifest
            or science.identity(manifest.reservation.allocation) != frozen.prefit.original_allocation
            or science.identity(manifest.reservation) != frozen.prefit.reservation
            or science.identity(manifest.native_specification) != frozen.prefit.native_specification):
        raise PermissionError("selected E4 substitutes actual original fit preparation")
    if downstream_coordinates:
        science.require_e4_reserved_physical_exclusion(downstream_coordinates, manifest.reservation)
    original_policies = {science.identity(value): value for value in manifest.native_specification.selection.prefix_policies}
    if policies is None:
        policies = manifest.native_specification.selection.prefix_policies
    selected_policies = {science.identity(value): value for value in policies}
    if any(original_policies.get(pin) != policy for pin, policy in selected_policies.items()):
        raise PermissionError("selected E4 substitutes an original prepared prefix policy")
    if preparation is not None:
        if (type(preparation) not in preparation_types or preparation.manifest != manifest
                or preparation.mathematical_protocol != criterion):
            raise PermissionError("selected E4 preparation differs from actual original producer inputs")
    remaining = set(selected_policies)
    seen = set()
    physical_keys = {family.namespace + '.physical-forecast'}
    if family.configured:
        physical_keys.add(family.namespace + '.retained-physical-forecast')
    criterion_kind = MatrixResponseFrontierProtocol if criterion is None else type(criterion)
    for physical in execution_plan.tasks:
        if physical.capability.capability_key not in physical_keys:
            continue
        declaration = declarations[physical.capability.capability_key]
        projection_specs = tuple(value for value in physical.external_inputs
            if value.expected_payload_schema == ProtectedE3ProtocolProjection.SCHEMA)
        if len(projection_specs) != 1:
            raise PermissionError("selected E4 original physical producer omits its exact projection")
        spec, = projection_specs
        key = (spec.logical_artifact_id, spec.expected_content_sha256)
        if key in seen:
            continue
        seen.add(key)
        _installed_task(physical, package, declaration)
        projection = _published_input(writer, binding.run_id, spec, ProtectedE3ProtocolProjection)
        if projection.prefix_policy not in remaining:
            continue
        actual = {}
        for kind in (criterion_kind, ScheduledResponseProtocol, ProtectedE3ResponseNumericalProfile):
            inputs = tuple(value for value in physical.external_inputs if value.expected_payload_schema == kind.SCHEMA)
            if len(inputs) != 1:
                raise PermissionError("selected E4 original physical producer loses its complete prepared inputs")
            actual[kind] = _published_input(writer, binding.run_id, inputs[0], kind)
        if criterion is None:
            criterion = actual[criterion_kind]
        protocol = actual[ScheduledResponseProtocol]
        physical_config = _read_config(writer, binding, physical, declaration.config_record_type)
        policy = selected_policies[projection.prefix_policy]
        full = science.selected_original_factor_rule(criterion)
        scalar = manifest.scalar_definition
        if (actual[type(criterion)] != criterion or physical_config.specification != frozen.specification.identity
                or physical_config.root_id != protocol.public_source.root.root_id
                or physical_config.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or physical_config.numerical_profile != science.pin(actual[ProtectedE3ResponseNumericalProfile])
                or projection.original_factor_rule != criterion.factor_rule
                or projection.prefix_rule != policy.factor_rule.identity
                or projection.scalar_definition != ObjectIdentity.from_record(scalar.definition_id, scalar)
                or projection.typed_normalization != policy.factor_rule.scalar_closure.normalization_owner
                or projection.original_normalization != full.scalar_closure.normalization_owner
                or projection.cutoff_tick != frozen.specification.measurement.origin_tick
                or protocol.public_source.policy != policy
                or preparation is not None and projection not in preparation.projections):
            raise PermissionError("selected E4 substitutes authentic original prepared protocol projection")
        _selected_protocol(frozen.specification, protocol, actual[ProtectedE3ResponseNumericalProfile], projection, criterion)
        science.validate_selected_prefix_projection(criterion, policy, projection.cutoff_tick)
        if assay is not None:
            try:
                assay.validate_protocol(protocol)
            except ValueError as error:
                raise PermissionError("selected assay differs from the exact original producer-pinned complete method") from error
        remaining.remove(projection.prefix_policy)
        if not remaining:
            break
    if remaining:
        raise PermissionError("selected E4 has no actual original physical producer for its prefix projection")


def authenticate_selected_e3_public_package(*, writer, public, upstream_products, codecs, summary_record_id=None,
        response_criterion=None, prefix_policies=(), original_preparation=None, downstream_coordinates=()):
    """Replay all four actual original producers before any downstream publication."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
    family = selected_e3_product_family(public.specification)
    ProtectedE3Calibration = family.calibration_type
    MatrixSelectedPublicPackage = family.public_type
    MatrixSelectedFrozenPackage = family.package_type
    from .matrix_sampling_runtime import _original_products
    from empirical_lawhood.api.matrix_selected_producer_scope import validate_selected_e3_original_product

    if summary_record_id is not None:
        from empirical_lawhood.kernel.serialization import validate_stable_id
        validate_stable_id(summary_record_id)
    if type(public) is not MatrixSelectedPublicPackage:
        raise TypeError("selected E4 requires its exact original public E3 projection")
    public.__post_init__()
    expected = {science.identity(public.models), science.identity(public.model_freeze),
        public.calibration, science.identity(public.calibrated_freeze)}
    if (type(upstream_products) is not tuple or len(upstream_products) != 4
            or any(type(value) is not MatrixSelectedOriginalProduct for value in upstream_products)
            or tuple(value.record.object_id for value in upstream_products) != tuple(sorted({value.record.object_id for value in upstream_products}))
            or {value.record for value in upstream_products} != expected):
        raise PermissionError("selected E4 omits or substitutes its exact four original producer locators")
    for value in upstream_products:
        value.__post_init__()
    originals = {science.identity(value): value for value in (public.models, public.model_freeze, public.calibrated_freeze)}
    calibration = None
    if (response_criterion is None) != (not prefix_policies):
        raise ValueError("selected E4 projection needs both its original criterion and exact prefix policies")
    if response_criterion is None and original_preparation is not None:
        raise ValueError("selected E4 original preparation needs its actual selected protocol scope")
    if downstream_coordinates and response_criterion is None:
        raise ValueError("selected E4 physical exclusion needs its actual original protocol scope")
    producer = partial(validate_selected_e3_original_product, frozen=public)
    if response_criterion is not None:
        def producer(**kwargs):
            validate_selected_e3_original_product(frozen=public, **kwargs)
            if kwargs["binding"].record == science.identity(public.models):
                _authenticate_selected_projection(frozen=public, criterion=response_criterion,
                    policies=prefix_policies, preparation=original_preparation,
                    downstream_coordinates=downstream_coordinates,
                    **{key: kwargs[key] for key in ("binding", "package", "execution_plan", "writer")})
    payloads = _original_products(writer, tuple((value, value.record) for value in upstream_products),
        codecs, scope_validator=producer)
    for product, raw in zip(upstream_products, payloads, strict=True):
        if product.record == public.calibration:
            calibration = decode_canonical_bytes(raw, ProtectedE3Calibration, maximum_bytes=MAX_PARENT_BYTES)
            if science.identity(calibration) != public.calibration or calibration.canonical_bytes() != raw:
                raise PermissionError("selected E4 changes actual original sealed E3 calibration")
        elif raw != originals[product.record].canonical_bytes():
            raise PermissionError("selected E4 changes actual original E3 model/freeze bytes")
    package = MatrixSelectedFrozenPackage(public.original_package.object_id, public.specification, public.allocation, public.prefit,
        public.models, public.model_freeze, calibration, public.calibrated_freeze, public.selection_unit_ids)
    if package.identity != public.original_package or MatrixSelectedPublicPackage.from_package(package) != public:
        raise PermissionError("selected E4 public package differs from exact original scientific package")
    # Original CAL scores stay in this parent stack frame. Only the bounded
    # original radius/rank/scope projection may leave this read owner.
    if summary_record_id is not None:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4OriginalCalibrationSummary
        return SelectedE4OriginalCalibrationSummary.from_package(package, record_id=summary_record_id)
    return None


def authenticate_original_products(writer, programme, bank, evidence, codecs, *, current_access=None):
    from .domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
    from .selected_e3_access import selected_e3_originals
    originals = selected_e3_originals(evidence.upstream_products, current_access)
    if selected_produced_input_parents(writer,originals=originals)!=evidence.produced_input_parents:
        raise PermissionError("selected E4 DEV substitutes its exact actual produced-parent census")
    science.validate_evidence(evidence, programme, bank)
    authenticate_selected_e3_public_package(writer=writer, public=bank.forecast_design.package,
        upstream_products=originals, codecs=codecs,
        response_criterion=bank.forecast_design.criterion_record,
        prefix_policies=bank.specification.selection.prefix_policies,
        downstream_coordinates=bank.reservation.allocation.coordinates)
    for record, publication in ((bank.reservation.allocation, bank.reservation.publication),
            (bank.specification.selection, bank.specification.publication), (bank.audit, bank.audit_publication),
            (bank.response_selection, bank.response_selection_publication),
            (bank.forecast_design.criterion_record, bank.forecast_design.criterion_publication)):
        authenticate_publication(writer, publication, record)
    for publication in (*bank.audit.prior_corpus, *bank.response_selection.template_publications):
        authenticate_publication(writer, publication)


class SelectedE3E4DevelopmentRuntimeInputSupplier(CurrentIssuedTaskCustodySupplier):
    def __init__(self, supplier, *, writer, directory, plan, output_codecs, payloads=None, read_access=None):
        from .recursive_authoring import load_authored_wave
        from .selected_e3_access import SelectedE3OriginalInputAccess

        self.supplier, self.writer, self.output_codecs = supplier, writer, dict(output_codecs)
        self.read_access = read_access
        if payloads is None:
            _, _, _, payloads = load_authored_wave(directory=directory, artifact_writer=writer,
                lazy_payloads=True, read_access=read_access)
        self.original_input_access = getattr(payloads, 'original_input_access', None)
        if type(self.original_input_access) is not SelectedE3OriginalInputAccess:
            raise PermissionError('selected E4 development lacks its exact current original E3 access bootstrap')
        self.original_input_access.require_current()
        self.custody = CurrentDevelopmentTaskCustody(writer=writer, directory=directory, plan=plan,
            original_input_access=self.original_input_access, read_access=read_access, payloads=payloads)
        tasks = tuple(value for value in plan.tasks if value.capability.capability_key == owner.NAMESPACE + ".entry")
        if len(tasks) != 1:
            raise PermissionError("selected E4 development requires one actual complete entry task")
        self.entry_task, = tasks
        value = self.custody.inputs.get(self.entry_task.capability.config.artifact_id)
        if value is None:
            raise PermissionError("selected E4 development omits its actual authored entry configuration")
        manifest = self.custody._manifest(value.materialization.relative_path,
            expected=ArtifactManifest(value.logical, value.materialization))
        self.entry = self.custody.control_record(manifest, owner.SelectedE3E4EntryConfig, manifest.materialization.size_bytes)
        if self.entry.fingerprint() != self.entry_task.capability.config.content_sha256:
            raise PermissionError("selected E4 substitutes exact authored entry configuration")
        self.configs = dict(owner.contracts(self.entry.programme, self.entry.bank, self.entry.evidence, self.entry.evidence_size_bytes,
            produced_input_parents=self.entry.produced_input_parents,secondary_readout=self.entry.secondary_readout)[0])

    def resolve(self, logical_artifact_ids):
        return self.supplier.resolve(logical_artifact_ids)

    def require_original_input_access(self, task, value):
        return self.custody.require_original_input_access(task, value)

    def require_native_entry(self, context, runner, *, prepared_contract):
        return self.custody.require_native_entry(context, runner, prepared_contract=prepared_contract)

    def prepare_selected_e3_e4_development(self, context, runner):
        if type(runner) is not SelectedE3E4Worker or runner.prepared_scope is not None:
            raise PermissionError("selected E4 requires its exact installed unprepared DEV worker")
        self.original_input_access.require_current()
        current = self.custody.current_task(context, runner)
        _, plan, task = current
        receipts, controls = self.custody.task_inputs(context, task)
        kinds = {value.config_record_type.SCHEMA: value.config_record_type for value in owner.operation_declarations()}
        manifest = controls.get(context.config.artifact_id)
        kind = None if manifest is None else kinds.get(manifest.logical.payload_schema)
        if kind is None:
            raise PermissionError("selected E4 substitutes the registered configuration owner")
        config = self.custody.control_record(manifest, kind, manifest.materialization.size_bytes)
        if (config != self.configs.get(context.task_id) or config.fingerprint() != context.config.content_sha256
                or config.config_id != context.config.config_id):
            raise PermissionError("selected E4 leaf substitutes exact parent-derived full-bank source/phase selection")
        if type(config) is owner.SelectedE3E4CompactConfig:
            from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
            from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_native_source import bind_selected_native_source
            rows = tuple(value for value in controls.values() if value.logical.payload_schema == NumericalProducingProvenance.SCHEMA)
            if len(rows) != 1:
                raise PermissionError("selected E4 leaf loses one exact standalone original provenance input")
            provenance = self.custody.control_record(rows[0], NumericalProducingProvenance, rows[0].materialization.size_bytes)
            original = next(value for value in self.entry.bank.provenances if value.identity == config.source.provenance)
            if provenance != original:
                raise PermissionError("selected E4 leaf substitutes full original producing provenance")
            bind_selected_native_source(config.source, provenance)
        if runner.phase == "entry":
            if task != self.entry_task or config != self.entry:
                raise PermissionError("selected E4 changes its exact authored whole-programme entry")
            values = tuple(value for value in controls.values() if value.logical.payload_schema == science.SelectedE3E4Evidence.SCHEMA)
            if len(values) != 1:
                raise PermissionError("selected E4 omits actual original four-product evidence")
            evidence = self.custody.control_record(values[0], science.SelectedE3E4Evidence, values[0].materialization.size_bytes)
            if evidence.identity != config.evidence or len(evidence.canonical_bytes()) != config.evidence_size_bytes:
                raise PermissionError("selected E4 substitutes original evidence identity or byte bound")
            if evidence.produced_input_parents!=config.produced_input_parents:
                raise PermissionError("selected E4 DEV entry changes its exact original produced-parent census")
            from .matrix_full_factor_secondary import authenticate_e4_secondary_target
            authenticate_e4_secondary_target(writer=self.writer, selection=config.secondary_readout, bank=config.bank)
            authenticate_original_products(self.writer, config.programme, config.bank, evidence,
                self.output_codecs, current_access=self.read_access)
        else:
            with self.writer.verification_scope() as writer:
                receipt = receipts.get(self.entry_task.task_id)
                if self.entry_task.task_id not in task.dependency_task_ids or receipt is None:
                    raise PermissionError("selected E4 leaf omits actual successful whole-programme entry")
                logicals = tuple(value for value in receipt.output_logical_artifacts if value.payload_schema == science.SelectedE3E4EntrySeal.SCHEMA)
                expected = tuple(value for value in self.entry_task.outputs
                    if value.payload_schema == science.SelectedE3E4EntrySeal.SCHEMA)
                if (len(logicals) != 1 or len(expected) != 1
                        or (logicals[0].outcome_access, logicals[0].visibility_ceiling, logicals[0].profile) != (
                            expected[0].outcome_access, expected[0].visibility_ceiling, ArtifactProfile.CANONICAL_JSON)):
                    raise PermissionError("selected E4 substitutes actual original development entry seal")
                self.original_input_access.require_current()
                raw = _output_payload(writer, receipt, logicals[0], MAX_PARENT_BYTES)
                seal = decode_canonical_bytes(raw, science.SelectedE3E4EntrySeal, maximum_bytes=MAX_PARENT_BYTES)
                # Exact expected seal follows immutable actual entry evidence,
                # without reopening original CAL bytes in each child.
                if (seal.programme != self.entry.programme.identity or seal.bank != self.entry.programme.bank
                        or seal.forecast_design != self.entry.programme.forecast_design or seal.evidence != self.entry.evidence
                        or seal.design != self.entry.programme.design or seal.secondary_readout != self.entry.secondary_readout.identity
                        or seal.groups != self.entry.programme.group_ids
                        or seal.sources != tuple(case.source for case in self.entry.programme.cases) or seal.canonical_bytes() != raw):
                    raise PermissionError("selected E4 replaces original whole32x9 entry census")
                writer.require_verification_snapshot()
                self.original_input_access.require_current()
        if self.custody.current_task(context, runner) != current:
            raise PermissionError("selected E4 current authored custody changed during preparation")
        self.original_input_access.require_current()
        return runner.with_prepared_scope((context.run_id, context.task_id, context.input_materialization_ids,
            ObjectIdentity.from_record(plan.execution_plan_id, plan)))


def bind_selected_e3_e4_development_runtime(*, supplier, writer, directory, plan, output_codecs,
        payloads=None, read_access=None):
    return SelectedE3E4DevelopmentRuntimeInputSupplier(supplier, writer=writer, directory=directory,
        plan=plan, output_codecs=output_codecs, payloads=payloads, read_access=read_access)


def authenticate_selected_e3_assay(*, public, upstream_products, assay, assay_publication,
        template_publication, criterion, writer):
    """Join the assay/template to its real installed original E3 task inputs."""
    from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
    from .current_result_custody import authenticate_current_execution_plan
    from empirical_lawhood.api.matrix_selected_producer_scope import _installed_task, _read_config
    from .matrix_selected_runtime import _published_input
    from .recursive_qualified_parents import _actual_package, _replay_parent_authority
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location

    selected, = (value for value in upstream_products if value.record == science.identity(public.models))
    binding = selected.prior_execution
    from .retained_e3_evidence import current_e3_evidence
    evidence = current_e3_evidence(writer)
    reader = None if evidence is None else evidence.reader
    if evidence is None:
        package = _actual_package(writer, binding.run_id)
        issued, _ = _replay_parent_authority(selected, package, writer)
    else:
        package, issued, _, _, _, _ = evidence.product_metadata(selected, selected.record)
    if ObjectIdentity.from_record(package.package_id, package) != binding.package:
        raise PermissionError("selected E4 assay changes its actual original issued package")
    plan = (reader.authenticate_execution_plan(package=package, issued=issued, run_id=binding.run_id)
        if reader is not None else authenticate_current_execution_plan(
            package=package, issued=issued, run_id=binding.run_id, writer=writer))
    if ObjectIdentity.from_record(plan.execution_plan_id, plan) != binding.execution_plan:
        raise PermissionError("selected E4 assay changes its actual original execution plan")
    family = selected_e3_product_family(public.specification)
    declarations = {value.capability_key: value for value in family.operation_declarations()}
    physical_keys = {family.namespace + '.physical-forecast'}
    if family.configured:
        physical_keys.add(family.namespace + '.retained-physical-forecast')
    rows = tuple(value for value in plan.tasks if value.capability.capability_key in physical_keys
        and any(spec.expected_payload_schema == assay.SCHEMA
            and spec.expected_content_sha256 == assay.fingerprint() for spec in value.external_inputs))
    if len(rows) != 1:
        raise PermissionError("selected E4 assay is not one exact installed original forecast task")
    task, = rows
    declaration = declarations[task.capability.capability_key]
    _installed_task(task, package, declaration)
    config = _read_config(writer, binding, task, declaration.config_record_type)
    if (config.root_id != assay.public_source.root.root_id
            or config.specification != public.specification.identity
            or config.protocol != ObjectIdentity.from_record(assay.protocol_id, assay)):
        raise PermissionError("selected E4 assay substitutes original configured scientific scope")
    criteria = tuple(value for value in task.external_inputs
        if value.expected_payload_schema == criterion.SCHEMA
        and value.expected_content_sha256 == criterion.fingerprint())
    if len(criteria) != 1:
        raise PermissionError("selected E4 assay loses its exact original mathematical criterion")
    relative, _, _ = provider_input_location(writer, binding.run_id, criteria[0].logical_artifact_id)
    from .selected_e4_bank_recipe import _publication_from_manifest
    criterion_publication = _publication_from_manifest(writer, writer.read_manifest(relative))
    for publication, kind in ((assay_publication, assay), (template_publication, None),
            (criterion_publication, criterion)):
        specs = tuple(value for value in task.external_inputs
            if value.logical_artifact_id == publication.logical.logical_artifact_id)
        if len(specs) != 1:
            raise PermissionError("selected E4 assay/template publication is not an actual original input")
        spec, = specs
        expected = (spec.expected_payload_schema, spec.expected_content_sha256,
            spec.expected_media_type, spec.expected_outcome_access, spec.expected_visibility_ceiling)
        actual = (publication.logical.payload_schema, publication.logical.content_sha256,
            publication.logical.media_type, publication.logical.outcome_access, publication.logical.visibility_ceiling)
        edges = tuple(value for value in task.scientific_inputs if value.operational_logical_artifact_id == spec.logical_artifact_id)
        relative, _, _ = provider_input_location(writer, binding.run_id, spec.logical_artifact_id)
        if (any(value is None for value in expected) or expected != actual or relative != publication.materialization.relative_path
                or spec.expected_size_bytes not in (None, publication.materialization.size_bytes) or len(edges) != 1
                or publication.materialization.size_bytes > edges[0].maximum_size_bytes):
            raise PermissionError("selected E4 assay/template changes its exact original input publication scope")
        if kind is not None and _published_input(writer, binding.run_id, spec, type(kind)) != kind:
            raise PermissionError("selected E4 assay changes its actual original canonical instrument")

    return criterion_publication


def authenticate_selected_e3_training_banks(*, public, upstream_products, training_specification,
        training_request, writer):
    """Join the original fit's actual native inputs to this exact TRAIN act.

    The caller separately authenticates all four E3 producers and the native
    TRAIN controls. This join prevents substitution of another completed TRAIN
    acquisition that happened to use the same scientific protocol.
    """
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
    from .current_result_custody import authenticate_current_execution_plan
    from .matrix_selected_runtime import _published_input
    from .recursive_qualified_parents import _actual_package, _replay_parent_authority

    native.validate_request(training_specification, training_request)
    selected, = (value for value in upstream_products if value.record == science.identity(public.models))
    binding = selected.prior_execution
    from .retained_e3_evidence import current_e3_evidence
    evidence = current_e3_evidence(writer)
    if evidence is None:
        package = _actual_package(writer, binding.run_id)
        issued, _ = _replay_parent_authority(selected, package, writer)
        plan = authenticate_current_execution_plan(package=package, issued=issued, run_id=binding.run_id, writer=writer)
    else:
        package, issued, _, _, _, _ = evidence.product_metadata(selected, selected.record)
        plan = evidence.reader.authenticate_execution_plan(package=package, issued=issued, run_id=binding.run_id)
    if ObjectIdentity.from_record(package.package_id, package) != binding.package:
        raise PermissionError("programme E4 fit changes its actual original issued package")
    if ObjectIdentity.from_record(plan.execution_plan_id, plan) != binding.execution_plan:
        raise PermissionError("programme E4 fit changes its actual original execution plan")
    task, = (value for value in plan.tasks if value.task_id == binding.task_id)
    acquisition = native.acquisition_seal(training_specification, training_request)
    if public.prefit.training_allocation != acquisition.allocation:
        raise PermissionError("programme E4 original E3 fit consumes another TRAIN allocation")
    for pin, kind in ((public.models.training_features, native.NativeTrainingFeatureBank),
            (public.models.training_outcomes, native.NativeTrainingOutcomeBank)):
        specs = tuple(value for value in task.external_inputs if value.expected_payload_schema == kind.SCHEMA
            and value.expected_content_sha256 == pin.object_fingerprint)
        if len(specs) != 1:
            raise PermissionError("programme E4 fit loses its exact original native TRAIN bank input")
        record = _published_input(writer, binding.run_id, specs[0], kind)
        if (science.identity(record) != pin or record.acquisition != acquisition.identity
                or record.allocation != acquisition.allocation):
            raise PermissionError("programme E4 original E3 fit substitutes its actual TRAIN acquisition")
