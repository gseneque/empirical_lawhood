# SPDX-License-Identifier: MPL-2.0
"""Current exposed programme scaffolding from public mathematical declarations.

No record here is an actual source publication, entry, issue or capacity proof.
The public derivers independently authenticate every actual selected operand.
"""
from dataclasses import fields, replace
from decimal import Decimal as D
import json
from pathlib import Path
from matrix_example_handles import example_input_bytes

from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import AvailabilitySpec


def _read(root, relative, kind):
    """Build from editable public examples; typed owners validate every field."""
    raw = example_input_bytes(root / relative)
    return decode_canonical_record(json.loads(raw), kind)


def _context(coordinates, choices, namespace):
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_bindings
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.e1_assembly import MatrixProgrammeE1ScientificContext
    from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
    from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, EvidenceRung, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.experiments import AssignmentKind, AssignmentSpec, ControlKind, ControlSpec, PrecisionGoal
    from empirical_lawhood.kernel.obligations import (
        ClosureSpec, ComputabilityEvidence, FalsifierKind, FalsifierSpec, ObligationStatus,
        ScientificObligations, StructuralConvergenceSpec, SupportSpec, UncertaintySpec, ValiditySpec)
    from empirical_lawhood.kernel.quantities import QuantityKind, QuantitySpec, ResponseDirection
    from empirical_lawhood.kernel.status import LifecycleStatus, ReadinessStatus
    from empirical_lawhood.kernel.systems import IndependentUnitSpec, RelationalIdentity, SystemBoundaryKind, SystemSpec
    from empirical_lawhood.kernel.time import CausalPhase, ClockLabelSemantics, ClockSpec, HoldSemantics, HorizonSpec, SamplingSemantics
    from empirical_lawhood.kernel.worlds import (
        ComputabilityEnvelope, NumericalCoordinateKind, NumericalCoordinateSpec, NumericalViewSpec,
        RandomnessSemantics, WorldKind, WorldSpec)
    from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight

    prefix = 'example.current-e1'
    coordinate = coordinates[0]
    dt = coordinate.primary_view.timestep
    world = WorldSpec(prefix + '.world', 'Declared E1 numerical example', WorldKind.NUMERICAL_SIMULATOR,
        ('six-matrix-native-dynamics',), ('physical-material-realization',), (), EvidenceCeiling.RESPONSE, frozenset(OutcomeAccess))
    policy = AuthorityPolicy(prefix + '.policy', 'human.replace-with-operator', 'service.replace-with-delegate', (namespace,),
        frozenset((WorldKind.NUMERICAL_SIMULATOR,)), frozenset((AuthorityAction.SIMULATION_EXECUTION,
            AuthorityAction.NONACTUATING_PROSPECTIVE_FREEZE, AuthorityAction.EVALUATOR_REVEAL)),
        frozenset((SourceAccessClass.NONE,)), ('actual-current-entry-required',), frozenset(),
        ResourceBudget(4, 16 * 1024**3, 0, None, None, None), OutcomeAccess.EVALUATOR_REVEAL)
    quantities = tuple(sorted((QuantitySpec(prefix + '.' + name, name, kind, unit, unit, 'matrix-frame',
        coordinate.clock_id, AvailabilitySpec(coordinate.clock_id, phase, access, lag), direction)
        for name, kind, unit, phase, access, lag, direction in (
            ('bath', QuantityKind.BOUNDARY, 'temperature', CausalPhase.PRE_ACTION, OutcomeAccess.OUTCOME_BLIND, D(0), ResponseDirection.NOT_APPLICABLE),
            ('denominator', QuantityKind.DENOMINATOR, 'physical-root', CausalPhase.PRE_ACTION, OutcomeAccess.OUTCOME_BLIND, D(0), ResponseDirection.NOT_APPLICABLE),
            ('history', QuantityKind.HISTORY, 'native-history', CausalPhase.PRE_ACTION, OutcomeAccess.OUTCOME_BLIND, D(0), ResponseDirection.NOT_APPLICABLE),
            ('schedule', QuantityKind.ACTION, 'coupling', CausalPhase.ACTION_REQUESTED, OutcomeAccess.OUTCOME_BLIND, D(0), ResponseDirection.NOT_APPLICABLE),
            ('factor', QuantityKind.RECEIVER, 'event', CausalPhase.RECEIVER, OutcomeAccess.EVALUATION_SEALED,
                dt * choices.occurrence_end_tick, ResponseDirection.HIGHER_IS_BETTER))), key=lambda value: value.quantity_id))
    unit = IndependentUnitSpec(prefix + '.unit', 'One original root; paired views are nested', 'matrix-original-independent-group-id')
    relation = RelationalIdentity(prefix + '.relation', (prefix + '.denominator',), (prefix + '.history',), False,
        (prefix + '.schedule',), (prefix + '.factor',), HorizonSpec(prefix + '.horizon', coordinate.clock_id,
            dt * choices.survival_duration_ticks, coordinate.primary_view.time_unit))
    envelope = ComputabilityEnvelope(prefix + '.envelope', ('full-native-history',), (), ('whole-root-census',),
        ('whole-root-census',), 4, 16 * 1024**3, 0, 3600, 1024**3, D(3600))
    views = tuple(sorted((NumericalViewSpec(view.view_id, world.world_id, unit.unit_id, 'equations.six-matrix',
        ('closure.six-matrix',), ('boundary.six-matrix',), (NumericalCoordinateSpec(prefix + '.' + label + '.dt',
            NumericalCoordinateKind.TIMESTEP, view.timestep, view.time_unit, index),), 'solver.baoab', '1.0.0',
        view.precision.value, 'cpu', prefix + '.runtime', RandomnessSemantics.GENERATIVE_PREPARATION,
        prefix + '.observation', envelope.envelope_id)
        for index, (label, view) in enumerate((('primary', coordinate.primary_view), ('fine', coordinate.fine_view)))), key=lambda value: value.view_id))
    clocks = tuple(ClockSpec(name, 'Declared physical history clock', coordinate.primary_view.time_unit, 'matrix-frame',
        SamplingSemantics.REGULAR, HoldSemantics.NONE, ClockLabelSemantics.INSTANT, dt, D(0))
        for name in sorted({value.clock_id for value in coordinates}))
    system = SystemSpec(prefix + '.system', 'Current E1 mathematical context', SystemBoundaryKind.OPEN_DRIVEN_DISSIPATIVE,
        world, relation, clocks, quantities, unit, policy, (), computability_envelopes=(envelope,), numerical_views=views)
    required = ObligationStatus.REQUIRED
    obligations = ScientificObligations(prefix + '.obligations',
        SupportSpec(prefix + '.support', relation.relation_id, unit.unit_id, sum(value.requested_roots for value in choices.family_requirements),
            2, 'cutoff.replace-with-original', ('factor-chart',), ('all-assigned-roots',), (), required),
        ValiditySpec(prefix + '.validity', ('declared-numerical-world',), ('sampling-not-established',), ('NONUSE',), required),
        UncertaintySpec(prefix + '.uncertainty', 'exact-rational-whole-root-binomial', unit.unit_id,
            D('.99375'), (prefix + '.factor',), ('SAMPLING_NOT_ESTABLISHED',), required),
        (FalsifierSpec(prefix + '.falsifier', FalsifierKind.BASELINE_COMPARATOR, compact_bindings.KEY,
            'Whole-root occurrence and persistence', 'Retain all assigned roots and both views', required),),
        ClosureSpec(prefix + '.closure', ('complete-eight-primary-y-cell-menu',), ('fixed-factor-rule',), (prefix + '.history',), required),
        StructuralConvergenceSpec(prefix + '.convergence', ('independent-full-native-and-factor-witness',),
            tuple(value.view_id for value in views), (), required),
        ComputabilityEvidence(prefix + '.computability', envelope.envelope_id, tuple(value.view_id for value in views),
            ReadinessStatus.AUTHORITY_REQUIRED, ('ACTUAL_CAPACITY_EVIDENCE_REQUIRED',), ()))
    claim = ClaimSpec(prefix + '.claim', world.world_id, relation.relation_id, 'Selected E1 occurrence and BOTH survival?',
        'Complete assigned root probabilities', unit.unit_id, EvidenceRung.RESPONSE, EvidenceCeiling.RESPONSE,
        OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE, 'Actual qualification remains required',
        ('complete-assigned-denominator',), numerical_view_ids=tuple(value.view_id for value in views))
    control = ControlSpec(prefix + '.control', ControlKind.BASELINE_COMPARATOR, compact_bindings.NAMESPACE + '.check',
        (prefix + '.factor',), 'Independent complete native/factor witnesses in both views')
    context = MatrixProgrammeE1ScientificContext(prefix + '.context', claim.proposition, ('selected-four-family-design',),
        system, (claim,), AssignmentSpec(prefix + '.assignment', AssignmentKind.SIMULATOR_INTERVENTION, unit.unit_id,
            relation.action_quantity_ids, 'Acquire every C-assigned history exactly once', ('all-assigned-roots',)),
        (prefix + '.factor',), (control,), (PrecisionGoal(prefix + '.precision', 'exact-cell-probability', D('.25'),
            'probability', 1, 'No outcome-dependent top-up'),), obligations, ObjectIdentity.from_record(control.control_id, control))
    node = CampaignNode(prefix + '.node', CampaignNodeKind.CLAIM, CampaignLane.PROSPECTIVE,
        ObjectIdentity.from_record(claim.claim_id, claim), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec(prefix + '.campaign', context.question, (system.system_id,), (world.world_id,), (claim.claim_id,),
        policy.budget_ceiling, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(prefix + '.right', AuthorityAction.SIMULATION_EXECUTION, policy.delegate_id, policy.policy_id, True),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    return context, campaign


def generated_programme_examples(root: Path, allocation_outputs):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_operational_resources import MatrixSelectedOperationalResources
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_assembly import ConfiguredProtectedE3AssemblyRequest
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import NativeTrainingAssemblyRequest
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_assembly import MatrixFiniteDtSourceAssemblyRequest
    from empirical_lawhood.adapters.methods.matrix_researcher_programme import e1_assembly, e2_assembly
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.e1_allocation import MatrixProgrammeE1AllocationRequest
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.e4_operations import MatrixProgrammeE4Operations
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.operations import MatrixProgrammeE3Operations, MatrixProgrammeOperations
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.prepared_operations import MatrixProgrammePreparedOperations
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import PROTOCOL_ID, MatrixResearchProgrammePlan, MatrixResearchProgrammeSpecification
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.product_export import MatrixProgrammeProductExportSelection
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.source_operations import MatrixProgrammeSourceOperations
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings, selected_e4_method_bindings, selected_e4_native_bindings
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import ScheduledFullFactorResources
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import SelectedE3E4OperationalSelection
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4NativeBudgets
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
    from empirical_lawhood.runtime.execution_envelope import NonTimeResourceBudget

    def read(name, kind):
        return _read(root, 'programmes/foundations/emergent-structure/workflows/matrix-response-experiment/' + name, kind)
    raw = allocation_outputs['programmes/foundations/emergent-structure/workflows/matrix-programme/e1-allocation.request.example.json']
    allocation = decode_canonical_bytes(raw, MatrixProgrammeE1AllocationRequest, maximum_bytes=len(raw))
    training = read('native-training-request.example.json', NativeTrainingAssemblyRequest)
    protected = read('configured-scientific-assembly.request.example.json', ConfiguredProtectedE3AssemblyRequest)
    source = read('finite-dt-source-request.example.json', MatrixFiniteDtSourceAssemblyRequest)
    context, campaign = _context(allocation.coordinates, allocation.criterion_choices, allocation.namespace)
    e1 = e1_assembly.MatrixProgrammeE1AssemblySelection('selection.example.current-e1',
        context, campaign, tuple((phase, NonTimeResourceBudget('budget.example.e1.' + phase, 1, 1024**3,
            64 * 1024**2, 100, 256 * 1024**2)) for phase in e1_assembly.RESOURCE_PHASES),
        protected.resources.resources, protected.resources.native_progress, None, None, ())
    e2 = e2_assembly.MatrixProgrammeE2AssemblyRequest('request.example.current-e2', training.resources, training.campaign)
    e3 = MatrixProgrammeE3Operations('operations.example.e3', protected.resources, protected.authority_policy,
        protected.computability_envelope, protected.computability_evidence, protected.operator_id)
    source_metadata = MatrixProgrammeSourceOperations(record_id='operations.example.source-metadata',
        **{field.name: getattr(source, field.name) for field in fields(MatrixProgrammeSourceOperations) if field.name != 'record_id'})
    budget = ResourceBudget(1, 1024**3, 0, None, 256 * 1024**2, 64 * 1024**2)
    native = _read(root, 'programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/native-budgets.example.json', SelectedE4NativeBudgets)
    phases = sorted({*selected_e4_native_bindings.PHASES, 'phase-collect', *selected_e4_method_bindings.OPERATIONS})
    e4 = MatrixProgrammeE4Operations('operations.example.e4', training.campaign,
        SelectedE3E4OperationalSelection('resources.example.e4-development',
            tuple((phase, budget) for phase in sorted(selected_e3_e4_bindings.PHASES))),
        selected_e4_method_bindings.SelectedE4MethodResources('resources.example.e4-methods',
            tuple((phase, budget) for phase in sorted(selected_e4_method_bindings.OPERATIONS))),
        ScheduledFullFactorResources('resources.example.e4-structure', tuple((phase, budget) for phase in ('assess', 'measure', 'reduce'))),
        native, replace(source.operational_resources, record_id='resources.example.e4-protected',
            source_request_limits=tuple((phase, 100) for phase in phases)))
    opportunity = _read(root, 'programmes/foundations/emergent-structure/workflows/matrix-selected-opportunity/resources.example.json', MatrixSelectedOperationalResources)
    confirmation = _read(root, 'programmes/foundations/emergent-structure/workflows/matrix-selected-e4-protected/resources.example.json', MatrixSelectedOperationalResources)
    prepared = MatrixProgrammePreparedOperations('operations.example.prepared', training.campaign, source.physical_cutoff,
        protected.operator_id, source.source_budget.source_scan_bytes,
        replace(opportunity, phase_budgets=tuple((phase, budget) for phase, _ in opportunity.phase_budgets)),
        replace(confirmation, phase_budgets=tuple((phase, budget) for phase, _ in confirmation.phase_budgets)))
    operations = MatrixProgrammeOperations('operations.example.whole-programme', allocation.metadata_budget,
        source_metadata, e1, e2, training, e3, e4, prepared)
    specification = MatrixResearchProgrammeSpecification('programme.example.replace-with-current-c',
        'programmes/replace-with-current-programme', source.input_commitments, operations)
    sources = ExperimentFileInputSelection('sources.example.whole-programme', PROTOCOL_ID, (), ())
    delivery = MatrixProgrammeProductExportSelection('export.disclosed-matrix-programme',
        ObjectIdentity('plan.disclosed-unwritten-programme', MatrixResearchProgrammePlan.SCHEMA,
            MatrixResearchProgrammePlan.VERSION, 'a' * 64), 'exports/disclosed-matrix-programme')
    from empirical_lawhood.adapters.methods.matrix_researcher_programme import source_continuation
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
    # Exposed, unwritten selection only. The real deriver requires the complete
    # original publication and cannot use these placeholders as custody.
    pin = ObjectIdentity('plan.replace-with-original-unwritten', MatrixResearchProgrammePlan.SCHEMA,
        MatrixResearchProgrammePlan.VERSION, '0' * 64)
    template = source.input_commitments.publication
    path = 'programmes/replace-with-original/matrix-programme.json'
    logical = replace(template.logical, logical_artifact_id=pin.object_id, payload_schema=pin.object_schema,
        content_sha256=pin.object_fingerprint,
        generic_validation=replace(template.logical.generic_validation, payload_schema=pin.object_schema))
    publication = replace(template, logical=logical,
        materialization=replace(template.materialization, logical_artifact_id=pin.object_id,
            materialization_id='materialization.original-programme-unwritten', relative_path=path),
        manifest_materialization=replace(template.manifest_materialization,
            materialization_id='materialization.original-programme-manifest-unwritten', relative_path=path + '.manifest.json'))
    continuation = source_continuation.MatrixProgrammeSourceContinuationSpecification(
        'continuation.replace-with-original-programme', MatrixProgrammePublishedInput(pin, publication),
        'programmes/replace-with-continued-programme')
    continuation_sources = ExperimentFileInputSelection('sources.example.source-continuation', source_continuation.PROTOCOL_ID, (), ())
    from empirical_lawhood.adapters.methods.matrix_researcher_programme import retained_training_continuation
    retained = retained_training_continuation.MatrixProgrammeRetainedTrainingContinuationSpecification(
        'continuation.replace-with-completed-training-programme', continuation.predecessor,
        'programmes/replace-with-retained-training-programme')
    retained_sources = ExperimentFileInputSelection('sources.example.retained-training-continuation',
        retained_training_continuation.PROTOCOL_ID, (), ())
    return {'programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json': specification.canonical_bytes(),
        'programmes/foundations/emergent-structure/workflows/matrix-programme/sources.example.json': sources.canonical_bytes(),
        'programmes/foundations/emergent-structure/workflows/matrix-programme/product-export.example.json': delivery.canonical_bytes(),
        'programmes/foundations/emergent-structure/workflows/matrix-programme/source-continuation.example.json': continuation.canonical_bytes(),
        'programmes/foundations/emergent-structure/workflows/matrix-programme/source-continuation.sources.example.json': continuation_sources.canonical_bytes(),
        'programmes/foundations/emergent-structure/workflows/matrix-programme/retained-training-continuation.example.json': retained.canonical_bytes(),
        'programmes/foundations/emergent-structure/workflows/matrix-programme/retained-training-continuation.sources.example.json': retained_sources.canonical_bytes()}


def generated_matched_design(root: Path, allocation_outputs, prepared_outputs):
    """Full amended mathematics with an actually constructed exposed allocation.

    These deterministic public streams are exposed software examples. They
    create no source publication, qualification, execution or freshness claim.
    A researcher must replace the E1 criterion with their public allocation
    result and bind their own complete exposure census before compiling C.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import e6_transport_records as transport
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import (
        SelectedPreparedDevelopmentSpecification, SelectedPreparedProtectedSpecification, SelectedPreparedRecipeFamily,
    )
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryTarget
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import CURVE_IMPROVEMENT_RULE, CURVE_RELATION_LOSS_RULE
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import (
        ConfiguredE3Assessment, ConfiguredE3Protocol, matched_e3_estimators, matched_e3_measurement,
    )
    from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_protocol import NativeTrainingScientificProtocol
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_records import NativeAmendedUtilityCriterion
    from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixIO48Construction, MatrixOriginResponseModel
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
    from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY
    from empirical_lawhood.adapters.methods.matrix_researcher_programme import scientific_design as owner
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.e1_allocation import MatrixProgrammeE1AllocationRequest, e1_allocation
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import e4_structural_prediction as relation
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeFactor
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import coordinate_identity, identity
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseAssay
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledCalibrationCriterion
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Design
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_choices import SelectedE4FactorialChoices
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4MatchedRelationRule
    from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
    from empirical_lawhood.runtime.experimental_factorial import PairInteractionScale

    def read(name, kind):
        return _read(root, 'programmes/foundations/emergent-structure/workflows/matrix-response-experiment/' + name, kind)

    def generated(outputs, name, kind):
        return decode_canonical_bytes(outputs[name], kind, maximum_bytes=None)

    prefix = 'example.amended'
    request = generated(allocation_outputs, 'programmes/foundations/emergent-structure/workflows/matrix-programme/e1-allocation.request.example.json',
        MatrixProgrammeE1AllocationRequest)
    census = generated(allocation_outputs, 'programmes/foundations/emergent-structure/workflows/matrix-programme/e1-allocation.census.example.json', MatrixFactorExposureCensus)
    allocation = e1_allocation(namespace=request.namespace, coordinates=request.coordinates,
        family_requirements=request.criterion_choices.family_requirements, census=census,
        root_material=request.root_seed_material_sha256)
    e1 = request.criterion_choices.bind_allocation(allocation, request.factor_rule)
    original_protocol = read('native-training-scientific-protocol.example.json', NativeTrainingScientificProtocol)
    math = replace(original_protocol.mathematical_protocol, protocol_id=prefix + '.dense-response', horizon_steps=DENSE_RESPONSE_HORIZONS)
    temperatures = {'e6-nearby.coordinate': D('1.125'), 'e6-shifted.coordinate': D('3.25')}
    coordinates = []
    for co in original_protocol.coordinates:
        selected = next(((suffix, value) for suffix, value in temperatures.items() if co.coordinate_id.endswith(suffix)), None)
        if selected is not None:
            suffix, value = selected
            co = replace(co, coordinate_id=prefix + '.' + suffix,
                primary_view=replace(co.primary_view, view_id=prefix + '.' + suffix + '.primary', bath_temperature=value),
                fine_view=replace(co.fine_view, view_id=prefix + '.' + suffix + '.fine', bath_temperature=value))
        coordinates.append(co)
    paired = tuple(sorted(((co, dict(original_protocol.coordinate_policies)[coordinate_identity(previous)])
        for previous, co in zip(original_protocol.coordinates, coordinates, strict=True)), key=lambda row: row[0].coordinate_id))
    protocol = replace(original_protocol, protocol_id=prefix + '.native-training', mathematical_protocol=math,
        coordinates=tuple(co for co, _ in paired), coordinate_policies=tuple((coordinate_identity(co), policy) for co, policy in paired))
    previous_assay = read('native-training-assay.example.json', ScheduledResponseAssay)
    assay = replace(previous_assay, assay_id=prefix + '.assay', criterion=math.identity, horizon_steps=DENSE_RESPONSE_HORIZONS,
        mechanical_model=MatrixOriginResponseModel(prefix + '.origin-model', previous_assay.mechanical_model.implementation,
            MatrixIO48Construction(prefix + '.io48')))
    nominal = next(co for co in protocol.coordinates if co.coordinate_id.endswith('nominal.coordinate'))
    policy = next(row for row in protocol.prefix_policies if identity(row) == dict(protocol.coordinate_policies)[coordinate_identity(nominal)])
    original = read('configured-protected-v2.json', ConfiguredProtectedE3Specification)
    sizes = {'TRAIN': 64, 'CALIBRATION': 64, 'EVALUATION': 80, 'TRANSFER_NEARBY': 64, 'TRANSFER_SHIFTED': 64}
    roles = tuple((role, coordinate_identity(next(co for co in protocol.coordinates if co.coordinate_id.endswith(
        'e6-nearby.coordinate' if role == 'TRANSFER_NEARBY' else
        'e6-shifted.coordinate' if role == 'TRANSFER_SHIFTED' else 'nominal.coordinate')))) for role, _ in original.role_coordinates)
    e3 = replace(original, specification_id=prefix + '.e3',
        protocol=ConfiguredE3Protocol(prefix + '.e3-protocol', matched_e3_measurement(), 'ORIGIN_ONLY_WHOLE_ROOT_MATCHED58'),
        methods=matched_e3_estimators(curve_primary=True), role_coordinates=roles,
        populations=tuple(replace(row, expected_units=sizes[row.role], unit_ids=None) for row in original.populations),
        assessment=ConfiguredE3Assessment(improvement_margin=D('.1'), minimum_usable_units=0,
            null_success_numerator=1, null_success_denominator=2, alpha_numerator=1, alpha_denominator=160,
            comparison_ids=AMENDED_PRIMARY_FAMILY, improvement_rule=CURVE_IMPROVEMENT_RULE,
            duration_margin_numerator=1, duration_margin_denominator=29),
        calibration_alpha=D('.05'), calibration_scope='MAX_POSITIVE_LOG1P_RESIDUAL_PAIRED58_FACTOR_OUTPUTS_PER_WHOLE_UNIT')
    e2 = owner.MatrixNativeUtilityDesign(prefix + '.e2', 96, math, protocol.scalar_definition, (nominal,),
        protocol.numerical_design, (policy,), ((coordinate_identity(nominal), identity(policy)),), assay,
        NativeAmendedUtilityCriterion(prefix + '.e2-criterion'))
    families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
    physical = nominal.primary_view.bath_temperature, nominal.primary_view.friction_gamma, nominal.member.cross_coupling_gamma
    factors = tuple(ScheduledProgrammeFactor(name, 'LOG', value / 2, value, value * 2)
        for name, value in zip(('temperature', 'friction', 'coupling'), physical, strict=True))
    designs = tuple(SelectedE3E4Design(prefix + '.e4-' + role, count, D('.95'), factors, 4,
        'BALANCED_FIXED_FOUR_FAMILY_GROUPS' if role == 'development' else 'IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW')
        for role, count in (('development', 16), ('calibration', 20), ('confirmation', 32)))
    selection = relation.E4MatchedRelationSelection(prefix + '.relation', *physical, loss=CURVE_RELATION_LOSS_RULE)
    target = relation.E4MatchedRelationTarget(prefix + '.relation-target', math.identity)
    factorial = SelectedE4FactorialChoices(prefix + '.factorial', target, 'MAX_PAIRED_LOG1P_CUMULATIVE_FACTOR_ERROR58',
        PairInteractionScale.SIGNED_MEAN_DIFFERENCE, (), None,
        'DESCRIPTIVE_MAIN_PAIR_AGGREGATE_CURVATURE_THREE_WAY_NO_SIGNIFICANCE_TESTS', None, (),
        'REQUIRE_COMPLETE_ASSIGNED_WHOLE_GROUPS', AMENDED_PRIMARY_FAMILY)
    revision = owner.MatrixE4RevisionChoices(prefix + '.revision', target, None,
        tuple((family, ordinal, ordinal % 2) for family in families for ordinal in range(4)),
        2, 5, (), (), (), (), selection.feature_rule, 'MINIMIZE', selection.missing_policy, selection)
    structure = owner.MatrixE4StructuralChoices(prefix + '.structure', protocol.full_factor_rule,
        policy.factor_numerical_design, ('PRIMARY', 'FINE'),
        'COMPLETE_ORIGINAL_LATTICE_ASSOCIATIVE_LIE_FACTOR_TRANSPORT_ORIGIN_FIXED_SCALAR_CONTRAST',
        'ORIGINAL_MATCHED_GROUPS_COORDINATES_VIEWS_SECTORS_AND_TICKS_ARE_NESTED',
        MatrixE4SecondaryTarget(prefix + '.secondary', math, D('.01'), (D('.005'), D('.02'), D('.05')),
            DENSE_RESPONSE_HORIZONS, D('.001')), selection)
    dev = generated(prepared_outputs, 'declarative-opportunity.example.json', SelectedPreparedDevelopmentSpecification)
    transfer = generated(prepared_outputs, 'declarative-transfer.example.json', SelectedPreparedProtectedSpecification)
    confirmation = owner.MatrixE5ConfirmationChoices(prefix + '.e5-confirmation', 80, dev.criterion,
        'baseline', ('delayed', 'early'), 'BASELINE_AND_AUTHENTICATED_DEV_WINNER_FROM_FROZEN_MENU_UNCHANGED_CRITERION',
        'NO_NOMINATION_NO_CONFIRMATION_ENTRY')
    panels = owner.MatrixPreparedPanelChoices(prefix + '.panels', math.panel_roles, owner.HISTORY_PURPOSES,
        'ORIGINAL_ROOT_PURPOSE_STREAMS', 'SEPARATE_DECLARED_WHOLE_GROUP_FUTURE_STREAMS', 'SAME_PANELS_ALL_MATCHED_ARMS',
        'EXACT_ORIGINAL_PRETRAIN_TRANSFER_SELECTORS', 'SUPPLIED_FUTURE_INNOVATIONS_NO_CHECKPOINT_AUTHORITY')
    e6_policy = owner.MatrixE6PolicyChoices(prefix + '.e6-policy', dev.criterion,
        tuple(('FACTOR', tick) for tick in DENSE_RESPONSE_HORIZONS), D('.05'), transport.MATCHED_CALIBRATION_METHOD,
        transport.POINT_TRANSFORM, transport.MATCHED_ADMISSION_RULE,
        'ALL_ASSIGNED_NONSUCCESS_AND_ADMITTED_UNRESOLVED_FALSE_ADMISSION_WORST_CASE', transport.MATCHED_METHODS, transport.MATCHED_STANDING)
    design = owner.MatrixProgrammeScientificDesign(record_id=prefix + '.whole-design', downstream_account='REVISION',
        e1_factor_rule=request.factor_rule, e1_criterion=e1, e1_numerical_design=protocol.numerical_design,
        e1_factor_numerical_design=policy.factor_numerical_design, e1_scalar_definition=protocol.scalar_definition,
        e1_coordinates=request.coordinates, e2=e2, training_protocol=protocol, training_assay=assay,
        e3_calibration_criterion=ScheduledCalibrationCriterion(prefix + '.e3-calibration', 'unit.whole-root', 64, D(1),
            (nominal.family_id,), 'WHOLE_ROOT_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_FACTOR58_NONUSE_INFINITY'), e3=e3,
        e4_development=designs[0], e4_calibration=designs[1], e4_confirmation=designs[2],
        e4_preparation_coordinates=tuple(replace(nominal, coordinate_id=prefix + '.e4-family-' + str(index), family_id=family)
            for index, family in enumerate(families)),
        e4_calibration_criterion=ScheduledCalibrationCriterion(prefix + '.e4-calibration', 'unit.whole-group',
            20, D(1), (), relation.RELATION_SCORE_RULE), e4_calibration_alpha=D('.05'), e4_factorial=factorial,
        e4_revision=revision, e4_nomination=SelectedE4MatchedRelationRule(prefix + '.relation-rule', 32,
            account_rule='FROZEN_SR_BR_CURVE_AFTER_ELIGIBLE_DEV_NO_CONFIRMATION_SELECTION', margin_denominator=10), e4_structure=structure,
        e5_development=dev, e5_confirmation=confirmation, prepared_assay=MatrixPreparedAssayMethod.from_assay(prefix + '.prepared-assay', assay),
        recipe_interpretations=tuple(SelectedPreparedRecipeFamily(arm, 'cc1.history.de-anneal', recipe.identity) for arm, recipe in dev.arms),
        panel_choices=panels, e6=transfer, e6_policy=e6_policy)
    return {'programmes/foundations/emergent-structure/workflows/matrix-programme/scientific-design.example.json': design.canonical_bytes()}
