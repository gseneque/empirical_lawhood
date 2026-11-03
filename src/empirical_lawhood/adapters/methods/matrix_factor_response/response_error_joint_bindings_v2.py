# SPDX-License-Identifier: MPL-2.0
"""Typed E3 FREEZE provider and receipt-bound gate for a new native graph.

No old response root validator is relaxed. The selected new native owner must
declare the joint-forecast port and call validate_native_forecast_gate before
BEGIN, with its actual origin/source. Generic scheduling/custody/authority stays
with the existing owners. Exposed conformance is never source qualification.
"""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from decimal import Decimal
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from .eligibility import MatrixAllocationReservation
from .records import identity as response_identity
from .response_error_prediction import MatrixResponseErrorModel, MatrixResponseErrorPredictionSpec
from .response_frontier import MatrixResponseFrontierProtocol
from .response_error_joint_v2 import (
    MatrixResponseCausalErrorInputV2, MatrixResponseErrorRolesV2, MatrixResponseJointCalibrationV2,
    MatrixResponseJointDesignV2, MatrixResponseJointForecastV2, forecast, identity, validate_calibration,
)

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

NAMESPACE = 'matrix-response-error-development-v2'
BUDGET = ResourceBudget(1,None,0,None,None,None)
INPUTS = (('calibration',MatrixResponseJointCalibrationV2),('criterion',MatrixResponseFrontierProtocol),
          ('design',MatrixResponseJointDesignV2),('feature',MatrixResponseCausalErrorInputV2),
          ('model',MatrixResponseErrorModel),('reservation',MatrixAllocationReservation),
          ('roles',MatrixResponseErrorRolesV2),('training-spec',MatrixResponseErrorPredictionSpec))


def namespace(protected):
    return 'matrix-response-error-v2' if protected else NAMESPACE


def node_id(root_id,protected=False):
    return namespace(protected)+'.'+root_id+'.forecast'


@dataclass(frozen=True,slots=True)
class MatrixResponseJointForecastConfigV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/forecast-config-v2'
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    design: ObjectIdentity
    root_id: str
    independent_group_id: str
    family_id: str
    source: ObjectIdentity
    input_producers: tuple[tuple[str,str],...]
    protected: bool = False

    def __post_init__(self):
        for name in ('config_id','root_id','independent_group_id','family_id'):
            validate_stable_id(getattr(self,name))
        if (self.design.object_schema != MatrixResponseJointDesignV2.SCHEMA
                or type(self.protected) is not bool
                or self.config_id != 'config.'+node_id(self.root_id,self.protected)
                or tuple(name for name,_ in self.input_producers) != tuple(name for name,_ in INPUTS)):
            raise ValueError('joint forecast config changes exact root/design/causal input census')
        for _,producer in self.input_producers:
            validate_stable_id(producer)


def operation_declaration(protected=False):
    return RecursiveOperationDeclaration(
        capability_key=namespace(protected) + "." + "forecast",
        capability_version="1.0.0",
        implementation_id="matrix-response-error.joint4family-max15-fixed-model-forecast-v2",
        kind=CapabilityKind.EXPERIMENT_DESIGNER
        if protected
        else CapabilityKind.ANALYSIS,
        config_record_type=MatrixResponseJointForecastConfigV2,
        stage=ScientificStage.FREEZE,
        input_ports=tuple(
            (
                RecursivePortContract(name, t.SCHEMA, "application/json", None)
                for name, t in INPUTS
            )
        ),
        outputs=(
            OutputTemplate(
                "forecast",
                MatrixResponseJointForecastV2.SCHEMA,
                ArtifactProfile.CANONICAL_JSON,
                "application/json",
                ".json",
            ),
        ),
        permissions=tuple(
            sorted(
                (
                    CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                    CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
                    CapabilityPermission.READ_FROZEN_MODELS
                    if protected
                    else CapabilityPermission.READ_DEVELOPMENT,
                )
            )
        ),
        evidence_ceiling=EvidenceCeiling.RESPONSE
        if protected
        else EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.OUTCOME_BLIND
        if protected
        else OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE
        if protected
        else VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=BUDGET,
        conformance_check_ids=(
            "actual-source-origin-receipt-gate",
            "complete-reserved-calibration-roots",
            "exact-prior-model-criterion-roles-reservation",
            "source-and-future-free-forecast-ports",
        ),
        runner_factory=lambda: MatrixResponseJointForecastRunnerV2(protected),
        record_codecs={
            t.SCHEMA: t
            for t in (
                MatrixResponseJointForecastConfigV2,
                MatrixResponseJointForecastV2,
                *(t for _, t in INPUTS),
            )
        },
        scientific_hooks=RecursiveScientificHooks(
            scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids,
            scientific_root_validator=scientific_root_validator,
        ),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
    )


def selected_manifest(protected=False):
    return operation_declaration(protected).manifest()


def scientific_root_validator(config,context):
    if config.protected:
        if (type(context.root) is not StudyDraft or context.root.unresolved_decisions
                or context.root.system is None or context.root.experiment is None
                or config.independent_group_id not in context.root.evaluation_unit_ids
                or not {config.design,config.source} <= {i.object_identity for i in context.root.design_inputs}):
            raise ValueError('joint E3 protected caller lacks its actual prospective source/design/root')
    elif (type(context.root) is not DevelopmentStudySpec or config.design not in context.root.scientific_operands
            or config.source not in context.root.scientific_operands
            or config.independent_group_id not in context.root.assigned_unit_ids):
        raise ValueError('joint E3 caller changes its actual development source/design/root')
    if (context.node_id != node_id(config.root_id,config.protected) or context.stage is not ScientificStage.FREEZE
            or context.unit_ids != (config.independent_group_id,)
            or context.outcome_access is not (OutcomeAccess.OUTCOME_BLIND if config.protected else OutcomeAccess.DEVELOPMENT_VISIBLE)
            or context.visibility_ceiling is not (VisibilityCeiling.PROSPECTIVE if config.protected else VisibilityCeiling.DEVELOPMENT_ONLY)):
        raise ValueError('joint E3 caller changes its actual development root/unit/FREEZE boundary')
    links = tuple(l for l in context.links if l.consumer_node_id == context.node_id)
    producers = dict(config.input_producers)
    if len(links) != len(INPUTS) or {l.consumer_input_id for l in links} != set(producers):
        raise ValueError('joint E3 caller drops required prior/causal input dependencies')
    for link in links:
        name = link.consumer_input_id
        role = 'HISTORY' if name == 'feature' else 'MODEL' if name in ('model','calibration') else 'SOURCE'
        if (link.external_input_id is not None or link.producer_node_id != producers[name]
                or link.producer_output_id != name or link.scientific_role != role):
            raise ValueError('joint E3 caller changes exact genuine dependency producer/role')


def operation_registration(protected=False):
    return operation_declaration(protected).registration()


def scientific_operand_sha256s(config):
    return tuple(sorted((config.design.object_fingerprint,config.source.object_fingerprint)))


def scientific_unit_ids(config):
    return (config.independent_group_id,)


def _dependency(context,port,producer):
    receipts = tuple(r for r in context.dependency_receipts if port.materialization_id in r.output_materialization_ids)
    if port.kind is not WorkerInputKind.DEPENDENCY or len(receipts) != 1 or receipts[0].task_id != producer:
        raise ValueError('joint E3 operand lacks its exact actual producing receipt')
    return receipts[0]


class MatrixResponseJointForecastRunnerV2:
    def __init__(self,protected=False):
        self.protected = protected
        self.manifest = selected_manifest(protected)

    def execute(self,context):
        try:
            config_ports = tuple(p for p in context.input_ports if p.payload_schema == MatrixResponseJointForecastConfigV2.SCHEMA)
            if len(config_ports) != 1:
                raise ValueError('joint E3 worker lacks exactlyone configuration')
            config = decode_canonical_bytes(config_ports[0].read(),MatrixResponseJointForecastConfigV2,maximum_bytes=None)
            if (config.protected != self.protected or context.task_id != node_id(config.root_id,self.protected)
                    or context.config.content_sha256 != config.fingerprint()
                    or context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
                    or context.permissions != self.manifest.permissions or context.resource_budget != BUDGET
                    or context.outcome_access is not (OutcomeAccess.OUTCOME_BLIND if self.protected else OutcomeAccess.DEVELOPMENT_VISIBLE)):
                raise ValueError('joint E3 worker changes exact source/config/access/resources')
            expected = {t.SCHEMA:(name,t) for name,t in INPUTS};values = {}
            for port in context.input_ports:
                if port is config_ports[0]:
                    continue
                if port.payload_schema not in expected:
                    raise ValueError('joint E3 predictor receives future/array/undeclared input')
                name,kind = expected[port.payload_schema]
                if name in values:
                    raise ValueError('joint E3 predictor duplicates an actual causal operand')
                if (port.outcome_access is not context.outcome_access
                        or port.visibility_ceiling is not (VisibilityCeiling.PROSPECTIVE if self.protected else VisibilityCeiling.DEVELOPMENT_ONLY)):
                    raise ValueError('joint E3 predictor changes actual source/model visibility or outcome access')
                _dependency(context,port,dict(config.input_producers)[name])
                values[name] = decode_canonical_bytes(port.read(),kind,maximum_bytes=None)
            if set(values) != {name for name,_ in INPUTS}:
                raise ValueError('joint E3 worker omits actual model/criterion/calibration/role/reservation/causal feature')
            d,r,m,c,f = (values[n] for n in ('design','roles','model','calibration','feature'))
            r.validate_reservation(values['reservation']);d.validate_roles(r)
            training = values['training-spec']
            criterion = values['criterion']
            if (d.identity != config.design or d.training_spec != training.identity or d.criterion != criterion.identity
                    or training.population.policy.protocol != criterion or identity(m) != d.model):
                raise ValueError('joint E3 caller substitutes locked model/training criterion/design')
            if (f.source != config.source or (f.root_id,f.independent_group_id,f.family_id) !=
                    (config.root_id,config.independent_group_id,config.family_id)):
                raise ValueError('joint E3 caller substitutes actual source/root/group/family')
            validate_calibration(d,r,c)
            result = forecast(d,r,m,c,f,record_id='forecast.joint-v2.'+config.root_id)
            if len(context.output_ports) != 1 or context.output_ports[0].payload_schema != result.SCHEMA:
                raise ValueError('joint E3 worker changes exact frozen output census')
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id,result.canonical_bytes()),),
                (ReceiptCheck('joint-e3-exact-prior-causal-custody',True,()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_factory(protected=False):
    declaration = operation_declaration(protected)
    m = declaration.manifest()
    _, components = bundle(
        "forecast",
        ExtensionContributionKind.METHOD,
        m,
        (),
        None,
        namespace=namespace(protected),
        maximum_config_bytes=None,
    )
    return declaration.provider_factory(
        components=tuple(sorted(components, key=lambda c: c.registration_id))
    )


def validate_native_forecast_gate(context,port,*,design,criterion,source,origin,expected_forecast_task_id,protected=False):
    """Actual new native owner calls before BEGIN; no contact or I/O capability.

    A scheduler dependency to the installed FREEZE provider is required in the
    new domain graph. This port check authenticates that completed receipt and
    exact feature/source/origin/clock/frame joins again at native entry. A seal
    supplies neither entry authority nor scientific qualification.
    """
    if (port.payload_schema != MatrixResponseJointForecastV2.SCHEMA or port.media_type != 'application/json'
            or port.outcome_access is not (OutcomeAccess.OUTCOME_BLIND if protected else OutcomeAccess.DEVELOPMENT_VISIBLE)
            or port.visibility_ceiling is not (VisibilityCeiling.PROSPECTIVE if protected else VisibilityCeiling.DEVELOPMENT_ONLY)
            or protected and getattr(source,'eligible',None) is None):
        raise ValueError('new native graph lacks its typed E3 forecast seal')
    if type(criterion) is not MatrixResponseFrontierProtocol or criterion.identity != design.criterion:
        raise ValueError('new native graph substitutes actual frozen E3 criterion')
    criterion.validate_design(source.design)
    receipt = _dependency(context,port,expected_forecast_task_id)
    raw = port.read()
    result = decode_canonical_bytes(raw,MatrixResponseJointForecastV2,maximum_bytes=None)
    feature = result.feature
    if (result.design != design.identity or result.model != design.model or result.criterion != design.criterion
            or result.roles != design.roles or result.reservation != design.reservation
            or feature.source != response_identity(source) or feature.origin != response_identity(origin)
            or feature.root_id != source.root.root_id or feature.independent_group_id != source.root.independent_group_id
            or feature.clock_id != origin.clock_id or feature.cutoff != origin.design.cutoff
            or feature.frame_sha256 != origin.frame_sha256 or origin.source != response_identity(source)
            or expected_forecast_task_id != node_id(source.root.root_id,protected)):
        raise ValueError('new native graph substitutes E3 source/origin/frame/model/criterion/cutoff seal')
    return {'forecast':result.identity,'receipt_id':receipt.receipt_id,
            'materialization_id':port.materialization_id,'sha256':sha256(raw).hexdigest(),
            'scope':'ACTUAL_RECEIPT_BOUND_PRE_FUTURE_SEAL;NO_ENTRY_AUTHORITY_OR_QUALIFICATION'}


def forecast_operation(config):
    """Compose the real PURE operation/dependencies for the selected new graph.

    Upstream nodes must own the eight declared output IDs; the compiler refuses
    missing/foreign suppliers. The new native owner declares its forecast port
    and dependent link separately. No old graph/config is modified here.
    """
    from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec
    registration = operation_registration(config.protected)
    node = node_id(config.root_id,config.protected)
    operation = RecursiveOperationSpec.from_config(node_id=node,selection=registration.selection,
        config_id=config.config_id,config=config,obligation_ids=('obligation.'+node+'.exact-joint-seal',),resource_budget=BUDGET)
    links = tuple(RecursiveInputLink('edge.'+node+'.'+name,node,name,producer_node_id=producer,producer_output_id=name,
        scientific_role='HISTORY' if name == 'feature' else 'MODEL' if name in ('model','calibration') else 'SOURCE')
        for name,producer in config.input_producers)
    return operation,links


@dataclass(frozen=True,slots=True)
class MatrixResponseJointAdmissionConfigV2(CanonicalRecord):
    """Small concrete config for the new Source2 graph's PURE admission owner."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/admission-config-v2'
    VERSION: ClassVar[str] = '2.0.0'
    config_id: str
    design: ObjectIdentity
    criterion: ObjectIdentity
    source: ObjectIdentity
    root_id: str
    independent_group_id: str
    forecast_task_id: str
    origin_task_id: str
    protected: bool = False

    def __post_init__(self):
        for name in ('config_id','root_id','independent_group_id','forecast_task_id','origin_task_id'):
            validate_stable_id(getattr(self,name))
        if (self.design.object_schema != MatrixResponseJointDesignV2.SCHEMA
                or self.criterion.object_schema != MatrixResponseFrontierProtocol.SCHEMA
                or type(self.protected) is not bool or self.forecast_task_id != node_id(self.root_id,self.protected)):
            raise ValueError('E3 pure admission config changes actual design/criterion/root/forecast owner')


@dataclass(frozen=True,slots=True)
class MatrixResponseJointAdmissionV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-error/precontact-admission-v2'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    design: ObjectIdentity
    criterion: ObjectIdentity
    source: ObjectIdentity
    origin: ObjectIdentity
    forecast: ObjectIdentity
    forecast_receipt_id: str
    forecast_materialization_id: str
    root_id: str
    independent_group_id: str
    clock_id: str
    cutoff: Decimal
    frame_sha256: str
    standing: str = 'PURE_PRECONTACT_JOIN_ACCEPTED_NO_ENTRY_AUTHORITY_OR_QUALIFICATION'

    def __post_init__(self):
        for name in ('record_id','forecast_receipt_id','forecast_materialization_id','root_id','independent_group_id','clock_id'):
            validate_stable_id(getattr(self,name))
        validate_decimal(self.cutoff,field_name='precontact admitted causal cutoff',minimum=Decimal(0))
        validate_sha256(self.frame_sha256)
        if (self.design.object_schema != MatrixResponseJointDesignV2.SCHEMA or self.criterion.object_schema != MatrixResponseFrontierProtocol.SCHEMA
                or self.forecast.object_schema != MatrixResponseJointForecastV2.SCHEMA
                or self.standing != 'PURE_PRECONTACT_JOIN_ACCEPTED_NO_ENTRY_AUTHORITY_OR_QUALIFICATION'):
            raise ValueError('E3 pure admission changes actual scientific operands or claims authority')

    @property
    def identity(self):
        return identity(self)


def admit_joint_forecast(context,forecast_port,origin_port,*,config,design,criterion,source,origin,record_id):
    """PURE success/receipt precedes the scheduler's outer Native parent BEGIN.

    Concrete new Source2 registration owns five typed ports: joint-design,
    criterion, source, origin and joint-forecast. It validates its config/source
    fields and supplies these decoded values. Native futures depends on this
    exact admission output; no shared executor preflight hook is needed.
    """
    if (type(config) is not MatrixResponseJointAdmissionConfigV2 or config.design != design.identity
            or config.criterion != criterion.identity or config.source != response_identity(source)
            or (config.root_id,config.independent_group_id) != (source.root.root_id,source.root.independent_group_id)):
        raise ValueError('E3 PURE admission substitutes actual config/root/source/design/criterion')
    _dependency(context,origin_port,config.origin_task_id)
    proof=validate_native_forecast_gate(context,forecast_port,design=design,criterion=criterion,source=source,origin=origin,
        expected_forecast_task_id=config.forecast_task_id,protected=config.protected)
    return MatrixResponseJointAdmissionV2(record_id,design.identity,criterion.identity,response_identity(source),
        response_identity(origin),proof['forecast'],proof['receipt_id'],proof['materialization_id'],
        source.root.root_id,source.root.independent_group_id,origin.clock_id,origin.design.cutoff,origin.frame_sha256)


def validate_admission_gate(context,port,*,design,criterion,source,origin,expected_admission_task_id,protected=False):
    """Native owner rechecks genuine PURE admission before child BEGIN/RNG."""
    if (port.payload_schema != MatrixResponseJointAdmissionV2.SCHEMA or port.media_type != 'application/json'
            or port.outcome_access is not (OutcomeAccess.OUTCOME_BLIND if protected else OutcomeAccess.DEVELOPMENT_VISIBLE)
            or port.visibility_ceiling is not (VisibilityCeiling.PROSPECTIVE if protected else VisibilityCeiling.DEVELOPMENT_ONLY)):
        raise ValueError('native E3 consumer lacks its exact typed precontact admission')
    receipt=_dependency(context,port,expected_admission_task_id)
    admission=decode_canonical_bytes(port.read(),MatrixResponseJointAdmissionV2,maximum_bytes=None)
    if (admission.design != design.identity or admission.criterion != criterion.identity or criterion.identity != design.criterion
            or admission.source != response_identity(source) or admission.origin != response_identity(origin)
            or (admission.root_id,admission.independent_group_id,admission.clock_id,admission.cutoff,admission.frame_sha256) != (
                source.root.root_id,source.root.independent_group_id,origin.clock_id,origin.design.cutoff,origin.frame_sha256)):
        raise ValueError('native E3 consumer substitutes the PURE precontact admission join')
    criterion.validate_design(source.design)
    return admission,receipt
