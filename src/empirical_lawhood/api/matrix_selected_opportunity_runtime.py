# SPDX-License-Identifier: MPL-2.0
"""Selected opportunity parent custody through genuine development owners.

Development work uses authored packets and ordinary receipts. Only the original
E3 products retain their separate issued/reveal readers; no development record
is coerced into an issue, execution grant or outcome-reveal authority.
"""

from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustodySupplier
from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity as science
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_opportunity_bindings as owner
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_opportunity_workers import SelectedOpportunityWorker
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixSelectedOpportunityEvidenceV2, MatrixSelectedOpportunityRootConfigV2
from .recursive_qualified_parents import MAX_PARENT_BYTES
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile


def reconstruct_opportunity_programme(programme, calibration):
    from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import MatrixSelectedPointDesign
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPointPayload

    if type(programme) is not science.MatrixSelectedOpportunityPublicProgramme:
        raise TypeError("selected opportunity parent requires its exact public programme projection")
    public_design, public_package = programme.point_design, programme.point_design.package
    family = selected_e3_product_family(public_package.specification)
    MatrixSelectedPublicPackage = family.public_type
    from .matrix_selected_runtime import reconstruct_selected_package
    package = reconstruct_selected_package(public_package, calibration)
    design = MatrixSelectedPointDesign(public_design.original_design.object_id, package, public_design.phase, public_design.expected_groups,
        public_design.arms, public_design.sources, public_design.interpretations)
    original = science.MatrixSelectedOpportunityProgramme(programme.original_programme.object_id, programme.sources, programme.reservation,
        design, programme.assay, programme.panels, programme.criterion, programme.minimum_recoverable_groups, programme.tie_policy)
    if (package.identity != public_package.original_package or MatrixSelectedPublicPackage.from_package(package) != public_package
            or design.identity != public_design.original_design or MatrixSelectedPointPayload.from_design(design) != public_design
            or original.identity != programme.original_programme or science.public_programme(original) != programme):
        raise PermissionError("selected opportunity projection substitutes its original package, design or scientific programme")
    return original


def _authenticate_original_products(writer, programme, evidence, codecs, *, source_scan_bytes,current_access=None):
    from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
    from .matrix_sampling_runtime import _original_products
    from empirical_lawhood.api.matrix_selected_producer_scope import selected_original_producer_scope

    from .matrix_prepared_original_commitments import authenticate_prepared_original_commitments
    authenticate_prepared_original_commitments(writer=writer, programme=programme, evidence=evidence, source_scan_bytes=source_scan_bytes,
        **({} if current_access is None else {"current_access":current_access}))
    science.validate_opportunity_evidence(evidence, programme)
    package, calibration = programme.point_design.package, None
    family = selected_e3_product_family(package.specification)
    originals = {science.identity(record): record for record in (package.models, package.model_freeze, package.calibrated_freeze)}
    from .selected_prepared_access import _selected
    selected_originals=_selected(evidence.upstream_products,current_access)
    payloads = _original_products(writer, tuple((product, product.record) for product in selected_originals),
        codecs, scope_validator=selected_original_producer_scope(programme))
    for product, raw in zip(selected_originals, payloads, strict=True):
        if product.record == package.calibration:
            calibration = decode_canonical_bytes(raw, family.calibration_type, maximum_bytes=MAX_PARENT_BYTES)
            if science.identity(calibration) != package.calibration or calibration.canonical_bytes() != raw:
                raise PermissionError("selected opportunity changes its actual original sealed calibration")
        elif raw != originals[product.record].canonical_bytes():
            raise PermissionError("selected opportunity changes actual original fitted/frozen product bytes")
    return reconstruct_opportunity_programme(programme, calibration)


def _design_task(plan):
    rows = tuple(task for task in plan.tasks if task.capability.capability_key == owner.COMMITTED_DESIGN_KEY)
    if len(rows) != 1:
        raise PermissionError("selected opportunity requires one actual installed design task")
    return rows[0]


class SelectedOpportunityRuntimeInputSupplier(CurrentIssuedTaskCustodySupplier):
    def __init__(self, supplier, *, writer, directory, plan, output_codecs, payloads=None, read_access=None):
        self.supplier, self.writer, self.output_codecs = supplier, writer, dict(output_codecs)
        if payloads is None:
            from .recursive_authoring import load_authored_wave
            _,_,_,payloads=load_authored_wave(directory=directory,artifact_writer=writer,lazy_payloads=True,read_access=read_access)
        self.original_input_access=getattr(payloads,'original_input_access',None)
        if self.original_input_access is None:raise PermissionError("prepared DEV lacks its actual original-parent bootstrap")
        self.original_input_access.require_current()
        self.current_access=read_access
        self.custody = CurrentDevelopmentTaskCustody(writer=writer, directory=directory, plan=plan,
            payloads=payloads,original_input_access=self.original_input_access,read_access=read_access)
        task = _design_task(plan)
        value = self.custody.inputs.get(task.capability.config.artifact_id)
        if value is None:
            raise PermissionError("selected opportunity omits its actual authored design configuration")
        manifest = self.custody._manifest(value.materialization.relative_path,
            expected=ArtifactManifest(value.logical, value.materialization))
        kind = MatrixSelectedOpportunityRootConfigV2
        config = self.custody.control_record(manifest, kind, manifest.materialization.size_bytes)
        if config.phase != "design" or config.fingerprint() != task.capability.config.content_sha256:
            raise PermissionError("selected opportunity substitutes its exact authored design selection")
        self.design_config, self.design_task = config, task

    def resolve(self, logical_artifact_ids):
        return self.supplier.resolve(logical_artifact_ids)

    def require_original_input_access(self,task,value):
        return self.custody.require_original_input_access(task,value)

    def require_native_entry(self,context,runner,*,prepared_contract):
        return self.custody.require_native_entry(context,runner,prepared_contract=prepared_contract)

    def prepare_selected_opportunity(self, context, runner):
        if type(runner) is not SelectedOpportunityWorker or runner.prepared_scope is not None:
            raise PermissionError("selected opportunity requires its exact installed unprepared worker")
        self.original_input_access.require_current()
        current = self.custody.current_task(context, runner)
        _, plan, task = current
        receipts, controls = self.custody.task_inputs(context, task)
        kinds = {row.config_record_type.SCHEMA: row.config_record_type for row in owner.operation_declarations()}
        manifest = controls.get(context.config.artifact_id)
        kind = None if manifest is None else kinds.get(manifest.logical.payload_schema)
        if kind is None:
            raise PermissionError("selected opportunity substitutes its actual registered configuration owner")
        config = self.custody.control_record(manifest, kind, manifest.materialization.size_bytes)
        if config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id:
            raise PermissionError("selected opportunity changes its actual current configuration bytes")
        if runner.phase == "design":
            if task != self.design_task or config != self.design_config:
                raise PermissionError("selected opportunity changes its actual whole-programme design task")
            evidence_kind = MatrixSelectedOpportunityEvidenceV2
            values = tuple(value for value in controls.values() if value.logical.payload_schema == evidence_kind.SCHEMA)
            if len(values) != 1:
                raise PermissionError("selected opportunity omits its exact original-product evidence input")
            evidence = self.custody.control_record(values[0], evidence_kind, values[0].materialization.size_bytes)
            if evidence.identity != config.evidence or len(evidence.canonical_bytes()) != config.evidence_size_bytes:
                raise PermissionError("selected opportunity substitutes its original evidence identity or byte bound")
            _authenticate_original_products(self.writer, config.programme, evidence, self.output_codecs,
                source_scan_bytes=context.resource_budget.source_scan_bytes,current_access=self.current_access)
            from .domain_composition.matrix_selected_declarative.derivation import require_evidence_produced_input_parents
            require_evidence_produced_input_parents(self.writer, config.produced_input_parents, evidence,read_access=self.current_access)
        else:
            with self.writer.verification_scope() as writer:
                receipt = receipts.get(self.design_task.task_id)
                if self.design_task.task_id not in task.dependency_task_ids or receipt is None:
                    raise PermissionError("selected opportunity leaf lacks its actual successful design dependency")
                logicals = tuple(value for value in receipt.output_logical_artifacts if value.payload_schema == science.MatrixSelectedOpportunitySeal.SCHEMA)
                from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
                expected_access, expected_visibility = produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                    declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY,
                    parents=self.design_config.produced_input_parents)
                if len(logicals) != 1 or (logicals[0].outcome_access, logicals[0].visibility_ceiling, logicals[0].profile) != (
                        expected_access, expected_visibility, ArtifactProfile.CANONICAL_JSON):
                    raise PermissionError("selected opportunity changes its original complete development seal")
                from .selected_prepared_access import guarded_output_payload
                raw = guarded_output_payload(writer,receipt,logicals[0],MAX_PARENT_BYTES,self.original_input_access)
                seal = decode_canonical_bytes(raw, science.MatrixSelectedOpportunitySeal, maximum_bytes=MAX_PARENT_BYTES)
                if seal != science.opportunity_seal(self.design_config.programme) or seal.canonical_bytes() != raw:
                    raise PermissionError("selected opportunity replaces its actual original design-selected package/census")
                programme_pin = config.programme.identity if type(config) is owner.MatrixSelectedOpportunityRootConfig else getattr(config, "programme", None)
                source = getattr(config, "source", getattr(config, "public_source", None))
                if ((programme_pin is not None and programme_pin != seal.programme)
                        or source is not None and (source.source_id if hasattr(source, "source_id") else source.source.object_id) not in seal.source_ids
                        or hasattr(config, "frozen_package") and (config.point_design, config.frozen_package) != (seal.point_design, seal.package)):
                    raise PermissionError("selected opportunity leaf changes its original programme, source or selected point package")
                writer.require_verification_snapshot()
        if self.custody.current_task(context, runner) != current:
            raise PermissionError("selected opportunity authored custody changed during current preparation")
        self.original_input_access.require_current()
        return runner.with_prepared_scope((context.run_id, context.task_id, context.input_materialization_ids,
            ObjectIdentity.from_record(plan.execution_plan_id, plan)))


def bind_selected_opportunity_runtime(*, supplier, writer, directory, plan, output_codecs,payloads=None,read_access=None):
    return SelectedOpportunityRuntimeInputSupplier(supplier, writer=writer, directory=directory, plan=plan, output_codecs=output_codecs,payloads=payloads,read_access=read_access)


def authenticate_selected_development_nomination(writer, binding, *, package, criterion, nomination_pin, expected_groups=None,read_access=None):
    """Read the genuine complete DEV producer before a separate CONF entry.

    The caller first authenticates the original full selected E3 package. This
    reader then checks the actual development packet, complete operational
    receipt closure and unchanged selected endpoint reduction. It creates no
    qualification or protected access authority.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_development_product import MatrixSelectedDevelopmentProduct
    from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    from .recursive_execution import _read_recursive_wave_with_roots
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input

    family = selected_e3_product_family(package.specification)
    if type(binding) is not MatrixSelectedDevelopmentProduct or type(package) is not family.package_type:
        raise TypeError("selected development nomination requires actual development locators and authenticated original full package")
    binding.__post_init__()
    directory = writer.root.resolve(binding.authoring_relative_path, for_write=False)
    def validate_authored(*, packet, draft, source, payloads, run, plan, index):
        nonlocal expected_groups
        if (ObjectIdentity.from_record(packet.packet_id, packet) != binding.authored_wave
                or ObjectIdentity.from_record(run.run_plan_id, run) != binding.run_plan
                or ObjectIdentity.from_record(plan.execution_plan_id, plan) != binding.execution_plan
                or run.run_plan_id != binding.run_id or draft.development_study is None or draft.prospective_draft is not None):
            raise PermissionError("selected development nomination substitutes its actual authored packet/run/plan or exposed lane")
        declaration = next(row for row in owner.operation_declarations() if row.capability_key.endswith(".nominate"))
        operations = tuple(value for value in draft.operations if value.node_id == binding.task_id)
        tasks = tuple(value for value in plan.tasks if value.task_id == binding.task_id)
        if len(operations) != 1 or len(tasks) != 1 or operations[0].selection != declaration.registration().selection:
            raise PermissionError("selected development nomination lacks its exact installed selected opportunity producer")
        config = decode_recursive_config_input(operations[0], declaration.registration()).record
        original = reconstruct_opportunity_programme(config.programme, package.calibration)
        actual_groups = original.point_design.expected_groups
        if expected_groups is None:
            expected_groups = actual_groups
        if type(expected_groups) is not int or expected_groups < 1 or expected_groups != actual_groups:
            raise PermissionError("selected nomination changes its actual authenticated complete group census")
        if (config.phase != "nominate" or original.point_design.package != package or original.criterion != criterion
                or original.point_design.expected_groups != expected_groups or len(original.roster.cases) != 3 * expected_groups
                or draft.development_study != owner.development_root(config.programme, draft.development_study.study_id)
                or binding.record != nomination_pin):
            raise PermissionError("selected development nomination changes actual selected package, complete opportunity scope or frozen criterion")
        return original

    result, roots, original = _read_recursive_wave_with_roots(directory=directory, artifact_writer=writer,
        include_products=True, terminal_product_format="references", validate_authored=validate_authored,read_access=read_access)
    packet, draft, _source, _run, plan, _index = roots
    report, products, actual_draft, actual_plan = result
    receipt = products["receipts"].get(binding.task_id)
    manifest = products["outputs"].get(binding.logical_artifact_id)
    if (actual_draft != draft or actual_plan != plan or report["packet_sha256"] != packet.fingerprint()
            or receipt is None or ObjectIdentity.from_record(receipt.receipt_id, receipt) != binding.receipt
            or manifest is None or manifest.logical != binding.publication.logical or manifest.materialization != binding.publication.materialization):
        raise PermissionError("selected development nomination substitutes its actual complete producing receipt or publication")
    nomination = products["records"].get(binding.task_id, {}).get(binding.task_id + ".product")
    observations = {}
    for source in original.sources.sources:
        names = (("point", "point"), ("mechanical", "mechanical"), ("readout", "response-score"))
        values = []
        for _, phase in names:
            producer = owner.NAMESPACE + "." + source.source_id + "." + phase
            value = products["records"].get(producer, {}).get(producer + ".product")
            if value is None:
                raise PermissionError("selected development nomination drops an actual complete case product")
            values.append(value)
        observations["case." + source.source_id] = tuple(values)
    _, replay = science.nominate_selected_opportunity(original, observations,
        result_id="nomination." + original.identity.object_fingerprint)
    if (nomination != replay or replay.identity != nomination_pin or replay.disposition != "NOMINATED"
            or len(replay.development_unit_ids) != expected_groups):
        raise PermissionError("selected development nomination changes the actual complete endpoint reduction or has no functional headroom")
    authenticate_publication(writer, binding.publication, nomination)
    return nomination, receipt, binding.publication
