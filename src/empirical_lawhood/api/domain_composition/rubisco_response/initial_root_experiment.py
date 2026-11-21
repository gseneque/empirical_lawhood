# SPDX-License-Identifier: MPL-2.0
"""Public copied-input creation and original-result presentation for the root."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_experiment import PROTOCOL_ID, InitialRootExperimentSpecification, bind_inputs, initial_root_experiment_specification
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_inquiry import actual_assessment
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import initial_root_requirement_graph
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.design.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection


def create_initial_root_experiment_inputs(*, request, selection, evidence, sources, project_root, output_directory):
    """Capture original guarded inputs; derive every scientific record through its owner."""
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.domain_composition.rubisco_response.initial_root import prepare_initial_root_analysis

    destination = Path(output_directory).absolute()
    if destination.exists():
        raise FileExistsError('initial root input preparation requires a fresh explicit destination')
    analysis = prepare_initial_root_analysis(request=request, selection=selection, evidence=evidence, sources=sources)
    specification = initial_root_experiment_specification(analysis)
    source = implementation_binding(project_root)
    inputs = ExperimentInputSelection('inputs.rubisco-initial-root.' + specification.fingerprint(), PROTOCOL_ID,
        (ExperimentInputBinding('analysis', analysis.identity, 'analysis.json', analysis.canonical_size_bytes()),))
    payloads = {'analysis.json': analysis.canonical_bytes(), 'specification.json': specification.canonical_bytes(),
        'sources.json': inputs.canonical_bytes(), 'source-snapshot.json': source.canonical_bytes()}
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in sorted(payloads.items()):
        with (destination / name).open('xb') as stream:
            stream.write(raw)
    return {'protocol': PROTOCOL_ID, 'paths': {name: str(destination / name) for name in sorted(payloads)},
        'analysis': analysis.identity.to_document(), 'new_native_calls': 0,
        'scope': 'FROZEN_EXPOSED_SOURCE_CONDITIONED_REVIEW_DATA_NOT_AUTHORITY'}


def read_development_result(*, directory, artifact_writer, specification, instance, payloads, report,
        products, draft, plan, allow_partial=False):
    if type(specification) is not InitialRootExperimentSpecification or instance.specification != specification.identity:
        raise PermissionError('initial root read substitutes its exact original specification')
    base = dict(namespace='rubisco-initial-root', question=specification.question,
        biological_predictive_validity='UNEVALUABLE', new_native_calls=0, independent_biological_units=0,
        evidence_scope='EXPOSED_CONDITIONAL')
    if allow_partial or report.get('typed_product_validation') == 'DEFERRED':
        return {**base, 'scientific_completion': 'DEFERRED'}
    name = 'experiment-source-' + sha256(specification.analysis.object_id.encode()).hexdigest() + '.json'
    analysis = decode_canonical_bytes(payloads[name], InitialRootAnalysisInputs, maximum_bytes=64 * 2**20)
    bind_inputs(specification, {'analysis': analysis})
    if (report.get('run_id') != plan.source_plan.object_id
            or {row.task_id for row in plan.tasks} != set(draft.selected_operation_ids)
            or any(row.run_id != plan.source_plan.object_id for row in products['receipts'].values())):
        raise PermissionError('initial root read changes the complete original operation/run census')
    config, result, _, assessed = actual_assessment(draft, products)
    if config.analysis != analysis:
        raise PermissionError('initial root read changes the frozen original inputs')
    if assessed is None:
        return {**base, 'scientific_completion': 'INCOMPLETE', 'joint_outcome': 'UNRESOLVED'}
    graph = initial_root_requirement_graph(analysis, result=result)
    return {**base, 'scientific_completion': 'COMPLETED', 'joint_outcome': result.joint_outcome,
        'numerical_disposition': assessed[0].numerical_disposition.value,
        'scientific_reconstruction_performed': True, 'result': result.to_document(),
        'assessment': assessed[0].to_document(), 'requirement_graph': graph.to_document(),
        'remaining_requirement_ids': result.decision_requirement_ids,
        'original_remaining_requirement_ids': result.original_remaining_requirement_ids}
