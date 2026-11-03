# SPDX-License-Identifier: MPL-2.0
"""Generate editable Matrix selections; no acquisition, assignment or authority."""

import argparse
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from decimal import Decimal
import json
from matrix_example_handles import example_input_bytes

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import (
    selected_deanneal_specification,
)


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "programmes/foundations/emergent-structure/workflows/matrix-response-experiment"
PROTOCOL = ROOT / "programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/candidate-design02.json"


def generated_configured_examples():
    """Canonical projections of editable selections, never frozen evidence.

    The previous example revisions lack the new explicit target discriminator
    and optional duration margin. Current constructors supply those defaults;
    all scientific parameter values and placeholder source references persist.
    This offline example generator is not a historical runtime decoder.
    """
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_specification as owner
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import PopulationSelection
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    kinds = (owner.ConfiguredMatrixResponseErrorSpecification, ConfiguredProtectedE3Specification,
        owner.ConfiguredE3Protocol, owner.ConfiguredE3Measurement, owner.ConfiguredE3Estimator,
        owner.ConfiguredE3Assessment, PopulationSelection, ObjectIdentity)
    by_schema = {kind.SCHEMA: kind for kind in kinds}
    previous = {kind.SCHEMA: '2.0.0' for kind in kinds[:2] + kinds[3:6]}
    previous[owner.ConfiguredE3Protocol.SCHEMA] = '1.0.0'
    def selection(value):
        if type(value) is list:
            return tuple(selection(item) for item in value)
        if type(value) is dict:
            if set(value) == {'decimal'}:
                return Decimal(value['decimal'])
            if set(value) != {'schema', 'version', 'value'} or value['schema'] not in by_schema:
                raise ValueError('editable configured example contains an unsupported canonical value')
            kind = by_schema[value['schema']]
            if value['version'] not in (kind.VERSION, previous.get(kind.SCHEMA)):
                raise ValueError('editable configured example is not a current or original selected revision')
            return kind(**{name: selection(item) for name, item in value['value'].items()})
        return value
    return {name: selection(json.loads((DESTINATION / name).read_bytes())).canonical_bytes()
        for name in ('configured-v2.json', 'configured-protected-v2.json')}


def generated_examples():
    selected = selected_deanneal_specification(protocol_sha256=sha256(PROTOCOL.read_bytes()).hexdigest())
    selected = replace(selected, calibration_target_view="MAX_PAIRED_VIEWS")
    sizes = {"TRAIN": 12, "CALIBRATION": 20, "EVALUATION": 8,
             "TRANSFER_NEARBY": 8, "TRANSFER_SHIFTED": 8}
    alternative = replace(selected, specification_id="matrix.e3.exposed.alternative",
        populations=tuple(replace(population, source_key="exposed-"+population.source_key,
                                  expected_units=sizes[population.role])
                          for population in selected.populations),
        assessment=replace(selected.assessment, minimum_usable_units=8),
        evidence_scope="EXPOSED_CONFORMANCE")
    return {"specification.json": selected.canonical_bytes(),
            "alternative.json": alternative.canonical_bytes()}



def generated_configured_assembly_examples():
    """Project the current editable request without historical study scaffolds."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_assembly import (
        PROTOCOL_ID, ConfiguredProtectedE3AssemblyRequest,
        ConfiguredProtectedE3AssemblySpecification,
    )
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding

    request_name = 'configured-scientific-assembly.request.example.json'
    raw = example_input_bytes(DESTINATION / request_name)
    request = decode_canonical_bytes(raw, ConfiguredProtectedE3AssemblyRequest, maximum_bytes=len(raw))
    specification = ConfiguredProtectedE3AssemblySpecification('assembly.disclosed-configured-scientific-inputs', request.identity)
    sources = ExperimentFileInputSelection('sources.disclosed-configured-scientific-inputs', PROTOCOL_ID,
        (ExperimentInputBinding('request', request.identity, request_name, len(request.canonical_bytes())),), ())
    return {
        'configured-scientific-assembly.example.json': specification.canonical_bytes(),
        request_name: request.canonical_bytes(),
        'configured-scientific-assembly.sources.example.json': sources.canonical_bytes(),
    }


def generated_native_assembly_examples():
    """Project the operational request and the existing unwritten C handle."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import (
        PROTOCOL_ID, NativeTrainingAssemblyRequest, NativeTrainingAssemblySpecification,
    )
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding

    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_assembly import MatrixFiniteDtSourceAssemblyRequest

    request_name = 'native-training-request.example.json'
    raw = example_input_bytes(DESTINATION / request_name)
    request = decode_canonical_bytes(raw, NativeTrainingAssemblyRequest, maximum_bytes=len(raw))
    source_raw = example_input_bytes(DESTINATION / 'finite-dt-source-request.example.json')
    source = decode_canonical_bytes(source_raw, MatrixFiniteDtSourceAssemblyRequest, maximum_bytes=len(source_raw))
    candidate = ObjectIdentity('candidate.replace-with-original', ConfiguredProtectedE3Specification.SCHEMA,
        ConfiguredProtectedE3Specification.VERSION, '0' * 64)
    specification = NativeTrainingAssemblySpecification('assembly.disclosed-copied-native-training',
        'disclosed-copied-native-training', candidate, request.identity, source.input_commitments)
    sources = ExperimentFileInputSelection('sources.disclosed-copied-native-training', PROTOCOL_ID,
        (ExperimentInputBinding('request', request.identity, request_name, len(request.canonical_bytes())),), ())
    return {'native-training-assembly.example.json': specification.canonical_bytes(),
        request_name: request.canonical_bytes(), 'native-training-sources.example.json': sources.canonical_bytes()}


def generated_finite_dt_source_assembly_examples():
    """Project only the current C-backed source request and exact copied pins."""
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_assembly import (
        PROTOCOL_ID, MatrixFiniteDtSourceAssemblyRequest, MatrixFiniteDtSourceAssemblySpecification,
    )
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding

    request_name = 'finite-dt-source-request.example.json'
    raw = example_input_bytes(DESTINATION / request_name)
    request = decode_canonical_bytes(raw, MatrixFiniteDtSourceAssemblyRequest, maximum_bytes=len(raw))
    specification = MatrixFiniteDtSourceAssemblySpecification('assembly.disclosed-copied-finite-dt-source', request.identity)
    sources = ExperimentFileInputSelection('sources.disclosed-copied-finite-dt-source', PROTOCOL_ID,
        (ExperimentInputBinding('request', request.identity, request_name, len(request.canonical_bytes())),), ())
    return {'finite-dt-source-assembly.example.json': specification.canonical_bytes(),
        request_name: request.canonical_bytes(), 'finite-dt-source-sources.example.json': sources.canonical_bytes()}


def generated_initialization_examples():
    """Missing-input scaffolding; no invented original draw or native receipt."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_initialization import example_inputs
    specification, sources = example_inputs()
    return {"initialization.example.json": specification.canonical_bytes(),
        "initialization.sources.example.json": sources.canonical_bytes()}


def generated_prepared_source_assembly_examples():
    """Project the current direct-C request and its exact copied input pins."""
    from empirical_lawhood.adapters.methods.matrix_prepared_source_assembly import (
        PROTOCOL_ID, MatrixPreparedSourceAssemblyRequest, MatrixPreparedSourceAssemblySpecification,
    )
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding

    request_name = 'prepared-source-assembly-request.example.json'
    raw = example_input_bytes(DESTINATION / request_name)
    request = decode_canonical_bytes(raw, MatrixPreparedSourceAssemblyRequest, maximum_bytes=len(raw))
    specification = MatrixPreparedSourceAssemblySpecification('assembly.disclosed-prepared-source', request.identity)
    sources = ExperimentFileInputSelection('sources.disclosed-prepared-source-assembly', PROTOCOL_ID,
        (ExperimentInputBinding('request', request.identity, request_name, len(request.canonical_bytes())),), ())
    return {'prepared-source-assembly.example.json': specification.canonical_bytes(),
        request_name: request.canonical_bytes(), 'prepared-source-assembly-sources.example.json': sources.canonical_bytes()}


def generated_e1_allocation_examples():
    """Exposed prospective mathematics without a placeholder allocation pin."""
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_records import E1CompactCriterionChoices, E1FamilySize
    from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_protocol import NativeTrainingScientificProtocol
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.e1_allocation import (
        PROTOCOL_ID, MatrixProgrammeE1AllocationRequest, MatrixProgrammeE1AllocationSpecification)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import coordinate_identity, identity
    from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding

    def read(name, kind):
        raw = (DESTINATION / name).read_bytes()
        return decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    protocol = read('native-training-scientific-protocol.example.json', NativeTrainingScientificProtocol)
    census = read('exposure-census.example.json', MatrixFactorExposureCensus)
    nominal = next(value for value in protocol.coordinates if value.coordinate_id.endswith('nominal.coordinate'))
    policy = next(value for value in protocol.prefix_policies
        if identity(value) == dict(protocol.coordinate_policies)[coordinate_identity(nominal)])
    families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
    rule = replace(policy.factor_rule, spec_id='rule.software.whole-design.e1', sectors=('X', 'Y'),
        lattice=tuple(range(0, 1153, 16)), risk_start_tick=0)
    coordinates = tuple(replace(nominal, coordinate_id='coordinate.software.e1.' + str(index),
        family_id=family, autonomous_ticks=896, observation_ticks=rule.lattice)
        for index, family in enumerate(families))
    choices = E1CompactCriterionChoices('criterion.software.e1', rule.identity,
        'system.software.e1', 'world.software.e1',
        ObjectIdentity('relation.software.e1', 'empirical-lawhood/kernel/relational-identity', '1.0.0', 'a' * 64),
        'unit.software.whole-root',
        tuple(E1FamilySize(family, 96) for family in families),
        ('PRIMARY', 'FINE'), ('MOVING', 'ORIGIN_FIXED', 'BOTH'), 'INITIAL_PRESENCE_OR_FIRST_CAUSAL_ADMISSION', 1024, 128, 1, 160, 1024,
        'TWO_SIDED_EXACT_BINOMIAL_FEASIBLE_COMPLETION_ENVELOPE', 'EIGHT_PRIMARY_Y_CELLS_DIAGNOSTIC_MARGINAL_95_PERCENT')
    from matrix_programme_example_records import _context
    context, _ = _context(coordinates, choices, 'programme.software.complete')
    choices = replace(choices, system_id=context.system.system_id, world_id=context.system.world.world_id,
        relation=ObjectIdentity.from_record(context.system.relation.relation_id, context.system.relation),
        independent_unit_id=context.system.independent_unit.unit_id)
    request = MatrixProgrammeE1AllocationRequest('request.disclosed.public-e1-allocation',
        'programme.software.complete', census.identity, sha256(b'disclosed.programme.material.0').hexdigest(),
        coordinates, rule, choices, ResourceBudget(1, 2 * 1024**3, 0, 60, 128 * 1024**2, 128 * 1024**2))
    specification = MatrixProgrammeE1AllocationSpecification('assembly.disclosed.public-e1-allocation', request.identity)
    sources = ExperimentFileInputSelection('sources.disclosed.public-e1-allocation', PROTOCOL_ID,
        (ExperimentInputBinding('exposure-census', census.identity, 'e1-allocation.census.example.json', len(census.canonical_bytes())),
            ExperimentInputBinding('request', request.identity, 'e1-allocation.request.example.json', len(request.canonical_bytes()))), ())
    prefix = 'programmes/foundations/emergent-structure/workflows/matrix-programme/'
    return {prefix + name: record.canonical_bytes() for name, record in (
        ('e1-allocation.example.json', specification), ('e1-allocation.request.example.json', request),
        ('e1-allocation.census.example.json', census), ('e1-allocation.sources.example.json', sources))}


def generated_e4_revision_example():
    """Current matched DEV16 scaffold; original acquisitions remain required."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import CURVE_RELATION_LOSS_RULE
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import (
        E4MatchedRelationSelection, E4MatchedRelationTarget,
    )
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_methods import SelectedE4RevisionExperimentSpecification
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4DevelopmentProgramme
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_revision_transition import SelectedE4RevisionAcquisitionSpecification
    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.experimental_selection import WholeUnitFold
    nominal = decode_canonical_bytes((ROOT / 'programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/matrix.e3.deanneal.nominal.canonical.json').read_bytes(),
        MatrixParameterCoordinate, maximum_bytes=None)
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
    criterion = ObjectIdentity('example.original-criterion', MatrixResponseFrontierProtocol.SCHEMA,
        MatrixResponseFrontierProtocol.VERSION, '0' * 64)
    selection = E4MatchedRelationSelection('example.selected-e4.relation', nominal.primary_view.bath_temperature,
        nominal.primary_view.friction_gamma, nominal.member.cross_coupling_gamma, loss=CURVE_RELATION_LOSS_RULE)
    programme = ObjectIdentity('example.original-dev-programme', SelectedE3E4DevelopmentProgramme.SCHEMA,
        SelectedE3E4DevelopmentProgramme.VERSION, '0' * 64)
    revision = SelectedE4RevisionExperimentSpecification('example.selected-e4.revision',
        programme, E4MatchedRelationTarget('example.selected-e4.target', criterion), None,
        tuple(WholeUnitFold('example.dev.' + str(index + 1).zfill(3), index % 2) for index in range(16)),
        2, 5, (), (), (), (), matched_selection=selection)
    record = SelectedE4RevisionAcquisitionSpecification('example.selected-e4.revision-acquisition', revision)
    return {'programmes/foundations/emergent-structure/workflows/matrix-selected-e4-revision/specification.json': record.canonical_bytes()}


def generated_matched_prepared_examples():
    """Current DEV16/transfer64 mathematical scaffolds; no authentic sources."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import CURVE_TRANSFER_PROCEDURE
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixCouplingRecipe, original_schedule_recipe
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.records import MatrixFunctionalCriterion
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import (
        SelectedPreparedDevelopmentSpecification, SelectedPreparedProtectedSpecification,
    )
    from empirical_lawhood.adapters.methods.matrix_primary_family import AMENDED_PRIMARY_FAMILY
    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    nominal = decode_canonical_bytes((ROOT / 'programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/matrix.e3.deanneal.nominal.canonical.json').read_bytes(),
        MatrixParameterCoordinate, maximum_bytes=None)
    baseline = original_schedule_recipe(nominal, 256, recipe_id='recipe.copied.original-ramp', effort_unit='effort.declared-coupling-integral')
    recipes = (('baseline', baseline), *tuple((arm, MatrixCouplingRecipe('recipe.copied.' + arm, 'FIXED_COUPLING', 256,
        tuple(baseline.half_tick_couplings[min(2*j, 512) if arm == 'early' else max(2*j-512, 0)] for j in range(513)),
        baseline.effort_rule, baseline.effort_unit)) for arm in ('delayed', 'early')))
    criterion = MatrixFunctionalCriterion('FACTOR', 64, Decimal('.01'), Decimal('.0001'), 0, 0, 0, 1, 2, 1, 160,
        AMENDED_PRIMARY_FAMILY, (), baseline.effort_unit, 1, 20, 'BONFERRONI_FIXED_FULL_PRIMARY_FAMILY',
        CURVE_TRANSFER_PROCEDURE, 'ALL_ASSIGNED_PAIRED_WORST_CASE_AND_TRANSFER_NONSUCCESS')
    dev = SelectedPreparedDevelopmentSpecification('specification.selected-declarative.copied.opportunity', 'REVISION',
        'E5_OPPORTUNITY', 16, recipes, criterion, 2, 'MINIMUM_TOTAL_EFFORT_THEN_LEXICAL', ())
    transfer = SelectedPreparedProtectedSpecification('specification.selected-declarative.copied.transfer', 'REVISION',
        'E6_TRANSFER', 64, (recipes[0],), criterion, 2, 'MINIMUM_TOTAL_EFFORT_THEN_LEXICAL',
        ('INTERPOLATION_WITHIN_ASSESSED_DOMAIN', 'EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN'))
    return {'declarative-opportunity.example.json': dev.canonical_bytes(), 'declarative-transfer.example.json': transfer.canonical_bytes()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    outputs = {DESTINATION/name:payload for name,payload in generated_examples().items()}
    configured = generated_configured_examples()
    outputs.update({DESTINATION/name:payload for name,payload in configured.items()})
    outputs.update({DESTINATION/name:payload for name,payload in generated_configured_assembly_examples().items()})
    outputs.update({DESTINATION/name:payload for name,payload in generated_native_assembly_examples().items()})
    outputs.update({DESTINATION/name:payload for name,payload in generated_finite_dt_source_assembly_examples().items()})
    outputs.update({DESTINATION/name:payload for name,payload in generated_prepared_source_assembly_examples().items()})
    outputs.update({ROOT / "programmes/foundations/emergent-structure/workflows/matrix-selected-revision" / name: payload for name, payload in generated_initialization_examples().items()})
    prepared_outputs = generated_matched_prepared_examples()
    outputs.update({ROOT / "programmes/foundations/emergent-structure/workflows/matrix-selected-revision" / name: payload for name, payload in prepared_outputs.items()})
    outputs.update({ROOT / name: payload for name, payload in generated_e4_revision_example().items()})
    allocation_outputs = generated_e1_allocation_examples()
    outputs.update({ROOT / name: payload for name, payload in allocation_outputs.items()})
    from matrix_programme_example_records import generated_programme_examples, generated_matched_design
    outputs.update({ROOT / name: payload for name, payload in generated_programme_examples(ROOT, allocation_outputs).items()})
    outputs.update({ROOT / name: payload for name, payload in generated_matched_design(ROOT, allocation_outputs, prepared_outputs).items()})
    for path,payload in outputs.items():
        if path.is_symlink() or path.parent.is_symlink():
            raise ValueError("example generator refuses symbolic output paths")
        if arguments.check:
            if not path.is_file() or path.read_bytes() != payload:
                raise SystemExit("generated Matrix experiment selection is missing or stale: " + path.relative_to(ROOT).as_posix())
        else:
            path.write_bytes(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
