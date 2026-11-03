# SPDX-License-Identifier: MPL-2.0
"""Live access to exact original prepared parents, never a permission record.

Only existing producer locators bootstrap this owner. Fitted requests, derived
selections and revision calibration bodies are never blind locator codecs.
"""
from contextlib import ExitStack
from dataclasses import dataclass, replace
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as domain
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import (
    produced_access, produced_record_parents, validate_produced_input_parents,
)
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactManifest, lineage_parent_sort_key


def _ordered(values):
    if (type(values) is not tuple or any(type(value) is not MatrixSelectedOriginalProduct for value in values)
            or tuple(value.record.object_id for value in values)!=tuple(sorted({value.record.object_id for value in values}))):
        raise ValueError('prepared current access requires sorted exact original producer locators')
    for value in values:value.__post_init__()


@dataclass(frozen=True,slots=True)
class SelectedPreparedCurrentAccess:
    """Operation-local replacement reveals; all original scientific pins stay fixed."""
    originals:tuple[MatrixSelectedOriginalProduct,...]

    def __post_init__(self):
        _ordered(self.originals)
        if len(self.originals)==5:
            from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4Calibration
            calibration=tuple(value for value in self.originals if value.record.object_schema==SelectedE4Calibration.SCHEMA)
            if len(calibration)!=1:
                raise ValueError('protected E4 current access requires its one exact CAL producer')
            _selected_e4_original_roster(tuple(value for value in self.originals if value not in calibration),calibration[0])
        elif len(self.originals) not in (2,4,6):
            raise ValueError('prepared current access requires its actual original and optional DEV-ancestor roster')

    def effective_originals(self,originals):
        _ordered(originals);self.__post_init__()
        by_pin={value.record:value for value in self.originals}
        selected=tuple(by_pin.get(value.record) for value in originals)
        if any(value is None or replace(value,reveal_authority=original.reveal_authority)!=original
                for value,original in zip(selected,originals,strict=True)):
            raise PermissionError('prepared current access changes an original product/package/run/plan/issue/execution')
        return selected

    def development_access(self):
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import (
            SelectedE4Calibration,SelectedE4DownstreamNomination,
        )
        from empirical_lawhood.api.selected_e3_access import SelectedE3CurrentAccess
        e4={SelectedE4Calibration.SCHEMA,SelectedE4DownstreamNomination.SCHEMA}
        values=tuple(value for value in self.originals if value.record.object_schema not in e4)
        return None if not values else SelectedE3CurrentAccess(values)


def select_current_prepared_access(records):
    if type(records) is not tuple:raise TypeError('prepared current access requires exact locator records')
    return SelectedPreparedCurrentAccess(tuple(sorted(records,key=lambda value:value.record.object_id)))


def _selected(originals,current):
    if current is None:return originals
    if type(current) is not SelectedPreparedCurrentAccess:
        raise TypeError('prepared access requires its exact operation-local selection')
    return current.effective_originals(originals)


def _ordinary(writer):
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane,_ScopedArtifactPlane
    return (ExternalArtifactPlane(writer.root,writer.validators,writer.semantic_validations,
        custody_limits=writer.custody_limits, artifact_verification='strict') if type(writer) is _ScopedArtifactPlane else writer)


@dataclass(frozen=True,slots=True)
class SelectedPreparedOriginalInputAccess:
    writer:object
    originals:tuple
    selected_originals:tuple
    development:tuple
    parents:tuple[ArtifactLineageParent,...]
    entries:tuple
    development_scopes:tuple
    current_access:object
    issued_specification:object=None
    issued_directory:Path|None=None
    issued_members:frozenset=frozenset()
    original_members:frozenset=frozenset()
    development_custodies:tuple=()

    def require_current(self,*,artifact_writer=None):
        from empirical_lawhood.api.recursive_qualified_parents import _require_parent_authorities_current
        writer=_ordinary(self.writer if artifact_writer is None else artifact_writer)
        if writer.root.contract!=self.writer.root.contract:
            raise PermissionError('prepared access changes its selected guarded root')
        _require_parent_authorities_current(self.entries,writer)
        for access in self.development_scopes:access.require_current(artifact_writer=writer)

    def record_parents(self,record):
        return () if type(record) in domain.locator_record_types() else produced_record_parents(record,self.parents)

    def require_member(self,manifest):
        if type(manifest) is not ArtifactManifest:
            raise TypeError('prepared access requires an exact authenticated member manifest')
        logical=manifest.logical
        selected=tuple(row for row in logical.lineage_parents if row.identity in {value.identity for value in self.parents})
        if selected:
            expected=produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY,parents=logical.lineage_parents)
            if selected!=self.parents or (logical.outcome_access,logical.visibility_ceiling)!=expected:
                raise PermissionError('prepared member changes its exact complete original ancestry or custody')
        elif (logical.outcome_access,logical.visibility_ceiling) not in (
                (OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY),
                (OutcomeAccess.OUTCOME_BLIND,VisibilityCeiling.PROSPECTIVE)):
            raise PermissionError('protected prepared member omits its actual original ancestry')
        self.require_current()


    def bind_issued_members(self,manifests,*,packet,association,directory=None):
        _require_specification(self.issued_specification,development=False)
        return _bind_issued_members(self,manifests,packet=packet,association=association,directory=directory,
            model_source_schemas=frozenset(kind.SCHEMA for kind in domain.derived_selection_types()),
            locator_schemas=frozenset(kind.SCHEMA for kind in domain.locator_record_types()))

    def bind_source_provenance(self,*,packet,directory):
        """Admit only the two original closure-owned operational disclosures."""
        from empirical_lawhood.api.prospective_experiment import _source_provenance_member_facts
        from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
        if type(packet) is not AuthoredRecursiveWave:
            raise TypeError('prepared source provenance requires its exact already-bound packet')
        if self.issued_directory is None or Path(directory)!=self.issued_directory:
            raise PermissionError('prepared source provenance changes its already-bound original directory')
        relative=(self.issued_directory/'prospective'/'authored-wave.json').relative_to(
            self.writer.root.contract.canonical_path).as_posix()
        owners=tuple((logical,physical) for logical,physical in self.issued_members
            if physical.relative_path==relative)
        if (len(owners)!=1 or (owners[0][0].payload_schema,owners[0][0].content_sha256,
                owners[0][1].physical_sha256,owners[0][1].size_bytes)!=(
                    packet.SCHEMA,packet.fingerprint(),packet.fingerprint(),len(packet.canonical_bytes()))):
            raise PermissionError('prepared source provenance lacks its exact already-bound packet')
        self.require_current()
        facts=_source_provenance_member_facts(writer=self.writer,packet=packet,directory=directory)
        self.require_current()
        return replace(self,issued_members=self.issued_members | facts)

    def require_issued_member(self,manifest):
        """Unknown future outcomes require their own issued receipt/read owner."""
        if type(manifest) is not ArtifactManifest:
            raise TypeError('prepared issued access requires an exact member manifest')
        if (manifest.logical,manifest.materialization) in self.issued_members:
            self.require_current()
            return
        self.require_original_member(manifest)

    def require_original_member(self,manifest):
        """Dispatch to the exact original issued closure or actual DEV owner.

        The DEV custody joins its frozen plan, unique successful receipt and
        complete input lineage before accepting an output's first body hash.
        A matching label or claimed parent tuple is never a dispatch key.
        """
        if type(manifest) is not ArtifactManifest:
            raise TypeError('prepared original access requires an exact member manifest')
        self.require_current()
        fact=manifest.logical,manifest.materialization
        if fact in self.original_members:
            return
        owners=tuple(custody for custody in self.development_custodies
            if fact in custody._original_member_facts or any(
                output.logical_artifact_id==manifest.logical.logical_artifact_id
                for task in custody.plan.tasks for output in task.outputs))
        if len(owners)!=1:
            raise PermissionError('prepared original member is foreign to its actual producing closure')
        custody,=owners
        custody.require_input_member(manifest)
        if fact not in custody._original_member_facts:
            raise PermissionError('prepared DEV ancestor lacks its exact authenticated producer publication')
        self.require_current()


def _bind_issued_members(access,manifests,*,packet,association,directory,model_source_schemas,locator_schemas):
    """Common exact-member/role checks; callers select closed scientific owners."""
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
    from empirical_lawhood.runtime.prospective_experiment import ProspectiveExperimentAssociation,ASSOCIATION_FILENAME
    if type(packet) is not AuthoredRecursiveWave or type(association) is not ProspectiveExperimentAssociation:
        raise TypeError('prepared issued members require their exact closed packet and association')
    packet.__post_init__();association.__post_init__()
    if association.prospective_wave!=ObjectIdentity.from_record(packet.packet_id,packet):
        raise PermissionError('prepared issued association substitutes its exact prospective packet')
    if directory is None:directory=access.issued_directory
    if directory is None:raise PermissionError("prepared issued scope omits its actual selected directory")
    directory=Path(directory)
    if access.issued_directory is not None and directory!=access.issued_directory:
        raise PermissionError("prepared issued scope substitutes its selected directory")
    if not directory.is_absolute() or directory!=directory.resolve(strict=True):
        raise PermissionError('prepared issued members change their actual canonical directory')
    root=Path(access.writer.root.contract.canonical_path)
    prefix=directory.relative_to(root)
    expected={}
    for lane,rows in (('prospective',packet.members),('experiment',association.members)):
        for row in rows:
            path=(prefix/lane/row.filename).as_posix()
            if path in expected:raise PermissionError('prepared issued packet aliases a closed member')
            expected[path]=(row.identity,row.size_bytes,row.filename)
    expected[(prefix/'prospective'/'authored-wave.json').as_posix()]=(ObjectIdentity.from_record(packet.packet_id,packet),len(packet.canonical_bytes()),'authored-wave.json')
    expected[(prefix/'experiment'/ASSOCIATION_FILENAME).as_posix()]=(association.identity,len(association.canonical_bytes()),ASSOCIATION_FILENAME)
    if type(manifests) is not tuple or any(type(row) is not ArtifactManifest for row in manifests):
        raise TypeError('prepared issued member census requires exact manifests')
    if len(manifests)!=len(expected) or {row.materialization.relative_path for row in manifests}!=set(expected):
        raise PermissionError('prepared issued member census omits, repeats or adds a frozen member')
    graph_roles={'draft.json','recursive-prospective.json','authoring.json','scientific-projection.json',
        'template.json','candidate-report.json','candidate.json','preissue-run-plan.json','preissue-execution-plan.json'}
    # These are immutable INPUT publications, not current/future task
    # output permissions. Their owner starts with the seal-preserving DEV input baseline
    # and inherits actual retained-parent custody. Runtime config/output lanes
    # are independently frozen by CurrentIssuedTaskCustody.
    facts=[]
    for manifest in manifests:
        logical,physical=manifest.logical,manifest.materialization
        pin,size,name=expected[physical.relative_path]
        if ((logical.payload_schema,logical.content_sha256,physical.physical_sha256,physical.size_bytes)!=(
                pin.object_schema,pin.object_fingerprint,pin.object_fingerprint,size)
                or physical.storage_root_id!=access.writer.root.contract.storage_root_id
                or logical.profile.value!='CANONICAL_JSON' or logical.media_type!='application/json'
                or physical.compression!='none' or physical.partition_selector is not None):
            raise PermissionError('prepared issued member substitutes its exact frozen metadata')
        selected=tuple(row for row in logical.lineage_parents if row.identity in {value.identity for value in access.parents})
        if selected:
            if selected!=access.parents:raise PermissionError('prepared issued member changes complete original ancestry')
            model_source=logical.payload_schema in model_source_schemas
            if name not in graph_roles and not model_source:
                raise PermissionError('prepared issued member lacks an exact model-bearing input role')
            expected_pair=produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY,parents=logical.lineage_parents)
            if (logical.outcome_access,logical.visibility_ceiling)!=expected_pair:
                raise PermissionError('prepared issued member changes its exact inherited input publication custody')
        else:
            model_source=logical.payload_schema in model_source_schemas
            if name in graph_roles or model_source:
                raise PermissionError('prepared issued protected member omits its complete original ancestry')
            controls={'authored-wave.json','experiment-association.json','implementation.json','source-closure.json',
                'registry.json','resources.json','decoder.json','experiment-specification.json',
                'experiment-allocation.json','experiment-instance.json'}
            locator=(name.startswith('experiment-source-') and logical.payload_schema in locator_schemas)
            if (name not in controls and not locator or (logical.outcome_access,logical.visibility_ceiling) not in (
                    (OutcomeAccess.OUTCOME_BLIND,VisibilityCeiling.PROSPECTIVE),
                    (OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY))):
                raise PermissionError('prepared issued member lacks an exact intrinsic locator/control role')
        facts.append((logical,physical))
    access.require_current()
    return replace(access,issued_members=frozenset(facts))


def _require_specification(specification,*,development):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import (
        SelectedPreparedDevelopmentSpecification,SelectedPreparedProtectedSpecification,
    )
    kind=SelectedPreparedDevelopmentSpecification if development is True else SelectedPreparedProtectedSpecification
    if development is None:
        kinds=(SelectedPreparedDevelopmentSpecification,SelectedPreparedProtectedSpecification)
    else:kinds=(kind,)
    if type(specification) not in kinds:
        raise TypeError('prepared bootstrap requires its exact current scientific specification')
    specification.__post_init__()


def _require_account(specification,rows):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import (
        SelectedE4Calibration,SelectedE4DownstreamNomination,
    )
    originals=tuple(value for key,value in rows if key.startswith('original.'))
    e4={SelectedE4Calibration.SCHEMA,SelectedE4DownstreamNomination.SCHEMA}
    if specification.account=='REVISION':
        if len(originals)!=2 or {value.record.object_schema for value in originals}!=e4:
            raise PermissionError('prepared revision bootstrap changes its actual CAL/CONF producer roster')
    elif len(originals)!=4 or any(value.record.object_schema in e4 for value in originals):
        raise PermissionError('prepared ORIGINAL_E3 bootstrap changes its four actual producer roster')


def _development_metadata(writer,value,current):
    """Authenticate DEV packet/receipt/publication without claiming a nominee."""
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody
    from empirical_lawhood.api.recursive_execution import _retained_plans
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.kernel.status import OperationalStatus
    writer=_ordinary(writer)
    directory=writer.root.resolve(getattr(value,'authored_directory',getattr(value,'authoring_relative_path',None)),for_write=False)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4DevelopmentProduct
    access_selection=(None if current is None else current.development_access()) if type(value) is SelectedE4DevelopmentProduct else current
    packet,draft,_,payloads=load_authored_wave(directory=directory,artifact_writer=writer,lazy_payloads=True,
        read_access=access_selection)
    access=getattr(payloads,'original_input_access',None)
    if access is None:raise PermissionError('prepared DEV parent lacks its actual original access bootstrap')
    access.require_current()
    run,plan,_=_retained_plans(payloads,draft)
    if (run.run_plan_id!=value.run_id or ObjectIdentity.from_record(plan.execution_plan_id,plan)!=value.execution_plan
            or getattr(value,'authored_wave',ObjectIdentity.from_record(packet.packet_id,packet))!=ObjectIdentity.from_record(packet.packet_id,packet)
            or getattr(value,'run_plan',ObjectIdentity.from_record(run.run_plan_id,run))!=ObjectIdentity.from_record(run.run_plan_id,run)
            or draft.development_study is None or draft.prospective_draft is not None):
        raise PermissionError('prepared DEV locator substitutes its actual authored plan or lifecycle')
    custody=CurrentDevelopmentTaskCustody(writer=writer,directory=directory,plan=plan,
        original_input_access=access,payloads=payloads,read_access=access_selection)
    tasks=tuple(row for row in plan.tasks if row.task_id==value.task_id)
    if len(tasks)!=1:raise PermissionError('prepared DEV locator omits its actual producer task')
    attempt=value.receipt.object_id.removeprefix('receipt.')
    store=ExternalTaskReceiptStore(writer);selected=store._read_envelope(value.run_id,value.task_id,attempt)
    if selected is None:raise PermissionError('prepared DEV original receipt is missing')
    path,manifest=selected
    access.require_current()
    receipt=store._read_body(value.run_id,value.task_id,attempt,path,manifest)
    publication=value.publication
    if (receipt.operational_status is not OperationalStatus.SUCCEEDED
            or ObjectIdentity.from_record(receipt.receipt_id,receipt)!=value.receipt
            or publication.logical not in receipt.output_logical_artifacts
            or publication.materialization not in receipt.output_materializations
            or publication.logical.content_sha256!=value.record.object_fingerprint
            or publication.logical.payload_schema!=value.record.object_schema):
        raise PermissionError('prepared DEV original changes its successful producer/publication')
    # The existing actual DEV owner proves the full frozen output census and
    # recursive input lineage before any outcome publication is hashed.
    outputs=custody._receipt_outputs(value.task_id,receipt,_metadata_only=True)
    if not any((row.logical,row.materialization)==(publication.logical,publication.materialization) for row in outputs):
        raise PermissionError("prepared DEV parent changes its exact current producer output")
    custody.require_input_member(ArtifactManifest(publication.logical,publication.materialization))
    # Retain exact control envelopes for the reachable producing DEV graph.
    # Every scientific output is still admitted by that actual DEV custody's
    # successful receipt/full-input-lineage check, never by this control census.
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    tasks_by_id={row.task_id:row for row in plan.tasks}
    pending=[value.task_id];seen=set();receipt_facts=set()
    while pending:
        task_id=pending.pop()
        if task_id in seen:continue
        seen.add(task_id);task=tasks_by_id[task_id]
        retained=[]
        for candidate in custody.index.task(task_id).attempts:
            envelope=store._read_envelope(value.run_id,task_id,candidate.attempt_id)
            if envelope is None:continue
            path,header=envelope
            access.require_current()
            def control_guard(member,expected=header):
                if (member.logical,member.materialization)!=(expected.logical,expected.materialization):
                    raise PermissionError('prepared DEV receipt control includes a foreign publication sibling')
                access.require_current()
            writer.verify_manifest(header,before_member=control_guard)
            access.require_current()
            actual_receipt=store._read_body(value.run_id,task_id,candidate.attempt_id,path,header)
            ExternalRunRecoveryStore._validate_receipt_static(custody.index,task,candidate,actual_receipt)
            if actual_receipt.operational_status is OperationalStatus.SUCCEEDED:
                retained.append((actual_receipt,header))
        if len(retained)!=1:
            raise PermissionError('prepared DEV ancestor lacks its unique actual successful receipt')
        _,header=retained[0]
        receipt_facts.add((header.logical,header.materialization))
        pending.extend(task.dependency_task_ids)
    # Actual scientific readers still own full endpoint and nomination replay.
    logicals={row.logical_artifact_id:row for row in receipt.output_logical_artifacts}
    facts={(manifest.logical,manifest.materialization),*receipt_facts}
    facts.update((logicals[row.logical_artifact_id],row) for row in receipt.output_materializations if row.logical_artifact_id in logicals)
    def guard(member):
        if (member.logical,member.materialization) not in facts:
            raise PermissionError("prepared DEV parent publication includes a foreign receipt sibling")
        access.require_current()
    writer.verify_manifest(manifest,before_member=guard)
    actual=writer.read_manifest(publication.materialization.relative_path)
    if (actual.logical,actual.materialization)!=(publication.logical,publication.materialization):
        raise PermissionError('prepared DEV publication differs from its actual producing receipt')
    writer.verify_manifest(actual,before_member=guard)
    access.require_current()
    return access,custody,frozenset(facts)


def original_input_access(*,artifact_writer,locators,read_access=None):
    originals=tuple(value for key,value in locators if key.startswith('original.'))
    development=tuple(value for key,value in locators if key.startswith('development.'))
    _ordered(originals)
    if len(originals) not in (2,4):raise ValueError('prepared originals require exactly four E3 or two E4 producers')
    return _authenticate_original_input_access(artifact_writer=artifact_writer,originals=originals,
        development=development,read_access=read_access)


def original_input_parents(*, artifact_writer, locators, read_access=None):
    """Return exact lineage facts without constructing future member access.

    Four configured E3 products have a recorded producer/import owner. Its
    current grants, actual plans and successful receipts suffice for these
    parent identities. Consumers of other original members still require
    original_input_access and its complete member census.
    """
    from .retained_e3_evidence import recorded_product_kinds
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
    originals = tuple(value for key, value in locators if key.startswith('original.'))
    development = tuple(value for key, value in locators if key.startswith('development.'))
    _ordered(originals)
    model, freeze, calibration = recorded_product_kinds()
    expected = sorted((kind.SCHEMA, kind.VERSION) for kind in (model, freeze, calibration, freeze))
    if (scientific_reconstruction_enabled() or development
            or sorted((value.record.object_schema, value.record.object_version) for value in originals) != expected):
        return original_input_access(artifact_writer=artifact_writer, locators=locators, read_access=read_access).parents
    selected = _selected(originals, read_access)
    if read_access is not None and any(value.record not in {original.record for original in originals}
            for value in read_access.originals):
        raise PermissionError('prepared current access adds a foreign unused original producer')
    from .recorded_e3_products import recorded_original_product_custody
    parents = []
    with recorded_original_product_custody(artifact_writer,
            tuple((value, value.record) for value in selected)) as (products, scope):
        for value in products:
            value.require_access()
            plan = scope.plan_reader.authenticate(package=value.package, issued=value.package.issued_study,
                receipt=value.receipt, logical=value.logical, capability_prefixes=value.prefixes)
            if ObjectIdentity.from_record(plan.execution_plan_id, plan) != value.original.prior_execution.execution_plan:
                raise PermissionError('prepared original substitutes its producing plan')
            parents.extend(ArtifactLineageParent(pin, value.logical.visibility_ceiling, value.logical.outcome_access)
                for pin in (value.original.record, value.original.prior_execution.receipt))
            value.require_access()
    result = tuple(sorted(set(parents), key=lineage_parent_sort_key))
    validate_produced_input_parents(result)
    return result


def _selected_e4_original_roster(upstream_products,calibration_product):
    """Recognize the two supported E3 editions and a distinct optional E4 CAL."""
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as e3
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as configured
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4Calibration
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_preparation import validate_component_original_products

    validate_component_original_products(upstream_products,calibration_product)
    editions=((e3.ProtectedE3ModelSet,e3.ProtectedE3FrozenProducts,e3.ProtectedE3Calibration,e3.ProtectedE3FrozenProducts),
        (configured.ConfiguredProtectedE3ModelSet,configured.ConfiguredProtectedE3FrozenProducts,
            configured.ConfiguredProtectedE3Calibration,configured.ConfiguredProtectedE3FrozenProducts))
    actual=tuple(sorted((value.record.object_schema,value.record.object_version) for value in upstream_products))
    if actual not in tuple(tuple(sorted((kind.SCHEMA,kind.VERSION) for kind in edition)) for edition in editions):
        raise ValueError('protected E4 requires four original E3 model, freeze, calibration and calibrated-freeze producers')
    if calibration_product is not None:
        pin=calibration_product.record
        if ((pin.object_schema,pin.object_version)!=(SelectedE4Calibration.SCHEMA,SelectedE4Calibration.VERSION)
                or pin in {value.record for value in upstream_products}):
            raise ValueError('protected E4 requires its distinct original E4 CAL producer')


def selected_e4_original_input_access(*,artifact_writer,upstream_products,calibration_product,
        development=(),read_access=None):
    """Authenticate the protected E4 roster without widening prepared accounts."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4DevelopmentProduct
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4RevisionNomination,SelectedE4FrozenRevision

    _selected_e4_original_roster(upstream_products,calibration_product)
    if development:
        if (type(development) is not tuple or len(development)!=2
                or any(type(value) is not SelectedE4DevelopmentProduct for value in development)
                or tuple((value.record.object_schema,value.record.object_version) for value in development)!=
                    tuple((kind.SCHEMA,kind.VERSION) for kind in (SelectedE4RevisionNomination,SelectedE4FrozenRevision))):
            raise ValueError('protected E4 requires its exact DEV nomination and freeze roles')
        for value in development:value.__post_init__()
        if len({(value.authored_directory,value.run_id,value.execution_plan) for value in development})!=1:
            raise PermissionError('protected E4 combines different original DEV nomination and freeze populations')
    elif type(development) is not tuple:
        raise TypeError('protected E4 DEV roles require an exact tuple')
    originals=tuple(sorted((*upstream_products,*(() if calibration_product is None else (calibration_product,))),
        key=lambda value:value.record.object_id))
    _ordered(originals)
    return _authenticate_original_input_access(artifact_writer=artifact_writer,originals=originals,
        development=development,read_access=read_access)


def _receipt_closure_members(writer,closure):
    """Collect exact publication and receipt envelopes without outcome reads."""
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore

    members={(row.logical,row.materialization) for row in closure.manifests}
    store=ExternalTaskReceiptStore(writer)
    for producing in closure.by_task.values():
        envelope=store._read_envelope(producing.run_id,producing.task_id,producing.attempt_id)
        if envelope is None:raise PermissionError('prepared original closure loses an actual receipt envelope')
        _,member=envelope
        if (member.logical.content_sha256!=producing.fingerprint()
                or member.materialization.physical_sha256!=producing.fingerprint()):
            raise PermissionError('prepared original receipt envelope changes its actual bytes')
        members.add((member.logical,member.materialization))
    return members


def _imported_original_members(writer,originals):
    """Join partial E3 producers only through their authenticated continuation."""
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as e3
    from .configured_e3_imported_products import imported_e3_product_custody
    from .recursive_operations import operation_catalog
    from .recursive_qualified_parents import _collect_receipt_closure

    schemas={e3.ConfiguredProtectedE3ModelSet.SCHEMA,e3.ConfiguredProtectedE3FrozenProducts.SCHEMA,
        e3.ConfiguredProtectedE3Calibration.SCHEMA}
    selected=tuple(value for value in originals if value.record.object_schema in schemas)
    def key(value):
        return (value.prior_execution.run_id,value.issued_study,value.execution_authority,value.reveal_authority)
    if len(selected)!=4 or len({key(value) for value in selected})==1:
        return set(),set()
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
    if not scientific_reconstruction_enabled():
        from .recorded_e3_products import recorded_original_members
        return recorded_original_members(writer, selected)
    members=set();completed=set()
    with imported_e3_product_custody(writer,tuple((value,value.record) for value in selected),
            operation_catalog()[2]) as (products,scope):
        for value in products:
            owner=value.producer
            value.require_access()
            current=key(value.original)
            if current in completed:continue
            closure=_collect_receipt_closure(value.package,value.plan,owner.writer,value.reveal,value.prefixes,
                control_reader=scope.plan_reader,allow_partial=value.imported)
            tasks={task.task_id for task in value.plan.tasks}
            if closure.by_task!={node:receipt for node,receipt in owner.receipts.items() if node in tasks}:
                raise PermissionError('prepared imported E3 closure changes its authenticated producing receipts')
            members.update(_receipt_closure_members(owner.writer,closure))
            completed.add(current)
            value.require_access()
    return members,completed


def _authenticate_original_input_access(*,artifact_writer,originals,development,read_access):
    from empirical_lawhood.api.matrix_sampling_runtime import _original_product_metadata
    from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader

    selected=_selected(originals,read_access)
    parents=[];entries={};scopes=[];development_custodies=[]
    from .retained_e3_evidence import retained_e3_evidence_context, recorded_product_kinds
    from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
    kinds={(kind.SCHEMA,kind.VERSION) for kind in recorded_product_kinds()}
    with ExitStack() as lifetime:
        if not scientific_reconstruction_enabled() and any(
                (value.record.object_schema,value.record.object_version) in kinds for value in selected):
            evidence=lifetime.enter_context(retained_e3_evidence_context(artifact_writer))
            writer,reader=evidence.writer,evidence.reader
        else:
            writer=lifetime.enter_context(artifact_writer.verification_scope())
            reader=CurrentResultPlanReader(writer)
        original_members,closures=_imported_original_members(writer,selected)
        for value in selected:
            package,issued,reveal,receipt,logical,prefixes=_original_product_metadata(writer,value,value.record,_control_reader=reader)
            plan=reader.authenticate(package=package,issued=issued,receipt=receipt,logical=logical,capability_prefixes=prefixes)
            if ObjectIdentity.from_record(plan.execution_plan_id,plan)!=value.prior_execution.execution_plan:
                raise PermissionError('prepared original substitutes its producing plan')
            key=(value.prior_execution.run_id,value.issued_study,value.execution_authority,value.reveal_authority)
            old=entries.setdefault(key,(value,package))
            if old[1]!=package:raise PermissionError('prepared originals combine different producing packages')
            if key not in closures:
                from .recursive_qualified_parents import _collect_receipt_closure
                # This owner collects only manifests and actual receipts; it
                # does not verify/hash scientific outcome or array bodies.
                closure=_collect_receipt_closure(package,plan,writer,reveal,prefixes,control_reader=reader)
                closures.add(key)
                original_members.update(_receipt_closure_members(writer,closure))
            parents.extend(ArtifactLineageParent(pin,logical.visibility_ceiling,logical.outcome_access)
                for pin in (value.record,value.prior_execution.receipt))
        writer.require_verification_snapshot()
    for value in development:
        access,custody,facts=_development_metadata(artifact_writer,value,read_access)
        scopes.append(access);development_custodies.append(custody);original_members.update(facts)
        logical=value.publication.logical
        parents.extend(ArtifactLineageParent(pin,logical.visibility_ceiling,logical.outcome_access)
            for pin in (value.record,value.receipt))
    if read_access is not None:
        allowed={value.record for value in originals}
        pending=list(scopes)
        while pending:
            scope=pending.pop()
            allowed.update(value.record for value in scope.originals)
            pending.extend(getattr(scope,"development_scopes",()))
        if any(value.record not in allowed for value in read_access.originals):
            raise PermissionError("prepared current access adds a foreign unused original producer")
    parents=tuple(sorted(set(parents),key=lineage_parent_sort_key));validate_produced_input_parents(parents)
    result=SelectedPreparedOriginalInputAccess(artifact_writer,originals,selected,development,parents,
        tuple(entries.values()),tuple(scopes),read_access,original_members=frozenset(original_members),development_custodies=tuple(development_custodies))
    result.require_current();return result


def _locator_rows(bindings,read):
    rows=[];types={(kind.SCHEMA,kind.VERSION):kind for kind in domain.locator_record_types()}
    for key,reference in bindings:
        if not key.startswith(('original.','development.')):continue
        kind=types.get((reference.object_schema,reference.object_version))
        if kind is None:raise PermissionError('prepared bootstrap refuses a fitted body as a locator')
        rows.append((key,read(key,reference,kind)))
    original=tuple(key for key,_ in rows if key.startswith('original.'))
    development=tuple(key for key,_ in rows if key.startswith('development.'))
    if (original not in (('original.0','original.1'),('original.0','original.1','original.2','original.3'))
            or len(development)>3
            or development!=tuple('development.'+str(index) for index in range(len(development)))):
        raise PermissionError('prepared bootstrap changes its complete canonical locator roster')
    return tuple(rows)


def bootstrap_selected_input_access(*,specification,selection,read_locator,artifact_writer,read_access=None,selection_path=None):
    from empirical_lawhood.api.experiment_preparation import _input_member
    _require_specification(specification,development=None)
    from empirical_lawhood.planning.experiment_inputs import ExperimentInputSelection,ExperimentFileInputSelection
    if type(selection) not in (ExperimentInputSelection,ExperimentFileInputSelection):
        raise TypeError('prepared selected bootstrap requires its exact canonical selector')
    selection.__post_init__()
    expected=domain.DEVELOPMENT_PROTOCOL_ID if specification.phase=='E5_OPPORTUNITY' else domain.PROTECTED_PROTOCOL_ID
    if selection.protocol_id!=expected:raise PermissionError('prepared selector changes its exact protocol')
    rows=_locator_rows(tuple((row.key,row.identity) for row in selection.bindings),read_locator)
    _require_account(specification,rows)
    access=original_input_access(artifact_writer=artifact_writer,locators=rows,read_access=read_access)
    primary=tuple(row for row in selection.bindings if row.key in ('request','selection'))
    if len(primary)!=1:raise PermissionError('prepared selected input requires one exact current request/selection')
    if type(selection_path) is not Path and not isinstance(selection_path,Path):
        raise TypeError('prepared copied inputs require their actual canonical selector path')
    if selection_path!=selection_path.resolve(strict=True):
        raise PermissionError('prepared selector changes its actual canonical path')
    directory=selection_path.parent
    # Requests/selections contain models; exact selected publication metadata
    # and current original grants precede their first body hash. Locators remain
    # intrinsic metadata. Every publication sibling must be selected explicitly.
    manifests=[]
    for row in (*selection.bindings,*getattr(selection,'files',())):
        path=_input_member(directory,row.relative_path)
        relative=path.relative_to(artifact_writer.root.contract.canonical_path).as_posix()
        manifest=artifact_writer.read_manifest(relative)
        is_file=hasattr(row.identity,'size_bytes')
        expected=(row.identity.payload_schema,row.identity.sha256) if is_file else (
            row.identity.object_schema,row.identity.object_fingerprint)
        if ((manifest.logical.payload_schema,manifest.logical.content_sha256)!=expected
                or (manifest.materialization.size_bytes!=row.identity.size_bytes if is_file else
                    manifest.materialization.size_bytes>row.maximum_bytes)
                or manifest.materialization.relative_path!=relative
                or manifest.materialization.storage_root_id!=artifact_writer.root.contract.storage_root_id
                or manifest.logical.media_type!=(row.identity.media_type if is_file else 'application/json')):
            raise PermissionError('prepared input substitutes its exact selected manifest bytes')
        logical=manifest.logical
        selected=tuple(value for value in logical.lineage_parents if value.identity in {parent.identity for parent in access.parents})
        if row in primary:
            if selected!=access.parents:
                raise PermissionError('model-bearing prepared input omits its exact authenticated original parents')
            expected_pair=produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY,parents=logical.lineage_parents)
            if (logical.outcome_access,logical.visibility_ceiling)!=expected_pair:
                raise PermissionError('prepared selected model changes its exact inherited input custody')
        elif selected or (logical.outcome_access,logical.visibility_ceiling)!=(OutcomeAccess.OUTCOME_BLIND,VisibilityCeiling.PROSPECTIVE):
            raise PermissionError('prepared intrinsic locator/initial FILE changes its exact blind input role')
        manifests.append(manifest)
    facts=frozenset((row.logical,row.materialization) for row in manifests)
    def before_member(member):
        if (member.logical,member.materialization) not in facts:
            raise PermissionError('prepared selected publication includes an unselected sibling')
        access.require_current()
    for manifest in manifests:
        artifact_writer.verify_manifest(manifest,before_member=before_member)
    access.require_current()
    return access.require_current


def bootstrap_development_input_access(*,directory,artifact_writer,specification,instance,packet,read_member,read_access=None):
    _require_specification(specification,development=True)
    if instance.specification!=specification.identity:raise PermissionError('prepared bootstrap changes its exact scientific instance')
    rows=_locator_rows(tuple((row.object_id,row) for row in instance.sources),lambda key,pin,kind:read_member(pin,kind))
    _require_account(specification,rows)
    return original_input_access(artifact_writer=artifact_writer,locators=rows,read_access=read_access)


def bootstrap_prospective_input_access(*,directory,artifact_writer,specification,instance,association,read_member,read_access=None):
    """Read only exact current locator companions before prospective bodies."""
    _require_specification(specification,development=False)
    if instance.specification!=specification.identity:
        raise PermissionError('prepared prospective bootstrap changes its scientific instance')
    rows=_locator_rows(tuple((row.object_id,row) for row in instance.sources),lambda key,pin,kind:read_member(pin,kind))
    _require_account(specification,rows)
    access=original_input_access(artifact_writer=artifact_writer,locators=rows,read_access=read_access)
    return replace(access,issued_specification=specification,issued_directory=Path(directory).resolve(strict=True))


def bootstrap_authoring_input_access(*,preparation,artifact_writer,read_access=None):
    selections=tuple(record for _,record in preparation.design_records if type(record) in domain.derived_selection_types())
    if len(selections)!=1:raise PermissionError('prepared authoring lacks its exact current derived selection')
    _require_specification(preparation.specification_record,development=None)
    request=selections[0].request
    locators=tuple((name,value) for name,value in preparation.design_records if name.startswith(('original.','development.')))
    domain.validate_locator_records(request,locators)
    _require_account(preparation.specification_record,locators)
    access=original_input_access(artifact_writer=artifact_writer,locators=locators,read_access=read_access)
    if access.parents!=request.produced_input_parents:
        raise PermissionError('prepared authoring changes the exact actual original parent census')
    if preparation.specification_record.phase!='E5_OPPORTUNITY':
        access=replace(access,issued_specification=preparation.specification_record)
    return access


def validate_development_read_access(*,payloads,read_access=None,**_):
    access=getattr(payloads,'original_input_access',None)
    if type(access) is not SelectedPreparedOriginalInputAccess or access.current_access!=read_access:
        raise PermissionError('prepared read lacks its exact current original access bootstrap')
    access.require_current()


def guarded_output_payload(writer,receipt,logical,maximum,access):
    """Reopen an already plan/receipt-joined result under fresh original access.

    The caller owns the complete scientific task/receipt census. This helper
    independently joins its exact physical publication and guards every batch
    sibling; it does not create own-issued outcome access or a receipt verdict.
    """
    from hashlib import sha256
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    if logical not in receipt.output_logical_artifacts:
        raise PermissionError('prepared output is foreign to its actual producing receipt')
    materials=tuple(row for row in receipt.output_materializations if row.logical_artifact_id==logical.logical_artifact_id)
    if len(materials)!=1:raise PermissionError('prepared result omits its exact output materialization')
    physical=materials[0]
    if (physical.size_bytes>maximum or physical.compression!='none' or physical.partition_selector is not None
            or physical.storage_root_id!=writer.root.contract.storage_root_id):
        raise PermissionError('prepared result changes its bounded physical output')
    manifest=writer.read_manifest(physical.relative_path)
    if manifest.logical!=logical or manifest.materialization!=physical or manifest.publication is None:
        raise PermissionError('prepared result differs from its actual completion publication')
    logicals={row.logical_artifact_id:row for row in receipt.output_logical_artifacts}
    facts={(logicals[row.logical_artifact_id],row) for row in receipt.output_materializations
        if row.logical_artifact_id in logicals}
    def before_member(member):
        if (member.logical,member.materialization) not in facts:
            raise PermissionError("prepared result publication includes a sibling outside its exact receipt facts")
        access.require_current()
    access.require_current()
    writer.verify_manifest(manifest,before_member=before_member)
    access.require_current()
    raw=read_bounded_bytes(writer.root.resolve(physical.relative_path,for_write=False),maximum_bytes=maximum)
    if (len(raw)!=physical.size_bytes or sha256(raw).hexdigest()!=physical.physical_sha256
            or sha256(raw).hexdigest()!=logical.content_sha256):
        raise PermissionError('prepared output changes exact receipted bytes')
    access.require_current()
    return raw
