# SPDX-License-Identifier: MPL-2.0
"""Guarded joint-root calculation and a separately closed original-source export."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import time
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model import required_initial_sources
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import InitialModelEvidence, InitialModelSelection
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root import assess_initial_root, calculate_initial_root, prepare_initial_root, validate_initial_root_inputs
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs, InitialRootAssessment, InitialRootDomainLimit, InitialRootRequest, InitialRootResult, InitialRootReviewInputs
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_relative_locator
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.api.domain_composition.rubisco_response.initial_model import MAXIMUM_BYTES, _exposed, _parents, with_initial_model_sources


MEMBERS = ('request.json', 'selection.json', 'inputs.json', 'result.json', 'assessment.json', 'evidence.json', 'report.txt')


@dataclass(frozen=True, slots=True)
class InitialRootAnalysisEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-analysis-evidence'
    request: ObjectIdentity
    selection: ObjectIdentity
    inputs: ObjectIdentity
    result: ObjectIdentity
    assessment: ObjectIdentity
    provenance: NumericalProducingProvenance
    original_sources: tuple[ObjectIdentity, ...]
    report: FileEvidence
    cpu_seconds: Decimal
    wall_seconds: Decimal
    new_native_calls: int = 0

    def __post_init__(self):
        for pin, kind in ((self.request, InitialRootRequest), (self.selection, InitialModelSelection),
                (self.inputs, InitialModelEvidence), (self.result, InitialRootResult), (self.assessment, InitialRootAssessment)):
            exact(pin, ObjectIdentity)
            if (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError('initial root analysis changes its exact input or result revision')
        exact(self.provenance, NumericalProducingProvenance)
        identities(self.original_sources)
        exact(self.report, FileEvidence)
        if self.report.relative_path != 'report.txt':
            raise ValueError('initial root analysis changes its human readout member')
        for name in ('cpu_seconds', 'wall_seconds'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if type(self.new_native_calls) is not int or self.new_native_calls != 0:
            raise ValueError('initial root analysis cannot manufacture native acquisition')


def _calculate(request, selection, evidence, reviews, joint_reviews):
    arguments = dict(request=request, selection=selection, evidence=evidence, reviews=reviews, joint_reviews=joint_reviews)
    result = calculate_initial_root(**arguments)
    assessment = assess_initial_root(result=result, **arguments)
    return result, assessment


def read_initial_root_sources(*, request, selection, evidence, sources):
    validate_initial_root_inputs(request, selection, evidence)
    def read(reviews, joint_reviews):
        result, assessment = _calculate(request, selection, evidence, reviews, joint_reviews)
        return dict(request=request, selection=selection, inputs=evidence, result=result, assessment=assessment,
            new_native_calls=0, verification='ORIGINAL_SOURCE_PUBLICATIONS_AND_INDEPENDENT_JOINT_RECONSTRUCTION')
    return with_initial_model_sources(selection=selection, evidence=evidence, sources=sources, consumer=read)


def prepare_initial_root_analysis(*, request, selection, evidence, sources):
    """Capture exact exposed review inputs through the original guarded reader.

    The returned immutable data can enter the ordinary copied-input protocol.
    It retains original source pins and grants neither access nor qualification.
    """
    validate_initial_root_inputs(request, selection, evidence)
    def capture(reviews, joint_reviews):
        reviewed = InitialRootReviewInputs(selection.identity, evidence.identity,
            required_initial_sources(selection, evidence),
            tuple(sorted(reviews, key=lambda row: row.review_id)),
            tuple(sorted(joint_reviews, key=lambda row: row.review_id)))
        return InitialRootAnalysisInputs(request, selection, evidence, reviewed)
    return with_initial_model_sources(selection=selection, evidence=evidence, sources=sources, consumer=capture)


def _text(request, result, assessment):
    lines = ['Conditional paired Rubisco joint root', '',
        'Criteria: turnover ratio > 1; specificity ratio >= 1.',
        'Alternative policy: ' + request.alternative_policy + '.',
        'Processing policy: ' + request.processing_policy + '.',
        'Joint result: ' + result.joint_outcome + '.',
        'Independent numerical reconstruction: ' + assessment.numerical_disposition.value + '.',
        'Biological predictive validity: UNEVALUABLE. New native calls: 0.', '',
        'Original selection, joint dependence, closure requirements and evidence ceiling are retained.', '']
    for case in result.cases:
        lines.append(case.case_id + ' (' + case.processing_view + '): ' + case.joint_outcome)
        for alternative in case.alternatives:
            lines.append('  ' + alternative.alternative_id + ': ' + alternative.joint_outcome + ' [' + alternative.original_state + ']')
            for row in alternative.realizations:
                lines.append('    ' + row.realization_id + ': ' + row.joint_outcome)
                for endpoint in row.endpoints:
                    bounds = 'unavailable' if endpoint.ratio_bounds is None else ', '.join(str(v.fraction) for v in endpoint.ratio_bounds)
                    lines.append('      ' + endpoint.endpoint + ': ' + endpoint.conditional_criterion + '; bounds ' + bounds)
                for label, condition in (('sufficient turnover support', row.support_waiting_condition),
                        ('sufficient turnover contradiction', row.contradiction_waiting_condition)):
                    if condition is not None:
                        lines.append('      ' + label + ': w ' + condition.equivalent_relation +
                            ('' if condition.threshold is None else ' ' + str(condition.threshold.fraction)))
                if row.omitted_operands:
                    lines.append('      Decision-specific omitted operands: ' + ', '.join(row.omitted_operands))
    lines.extend(('', 'Remaining decision requirements:', *(result.decision_requirement_ids or ('None in the conditional scope.',)),
        '', 'All original remaining requirements (including any decision-specific omissions):',
        *(result.original_remaining_requirement_ids or ('None recorded.',)), ''))
    return '\n'.join(lines).encode('utf-8')


def export_initial_root(*, request, selection, evidence, sources, project_root, artifact_writer, output_relative_path):
    """Retain a new seven-member product without changing any initial-model package."""
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    validate_initial_root_inputs(request, selection, evidence)
    validate_relative_locator(output_relative_path)
    for name in MEMBERS:
        if artifact_writer.root.resolve(output_relative_path + '/' + name, for_write=True).exists():
            raise ValueError('initial root export requires a fresh complete destination')
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256, expected_lock_sha256=implementation.dependency_lock_sha256)
    cpu, wall = time.process_time(), time.perf_counter()
    def publish(reviews, joint_reviews):
        result, assessment = _calculate(request, selection, evidence, reviews, joint_reviews)
        report = _text(request, result, assessment)
        accepted = InitialRootAnalysisEvidence(request.identity, selection.identity, evidence.identity,
            result.identity, assessment.identity, provenance, required_initial_sources(selection, evidence),
            FileEvidence('report.txt', len(report), sha256(report).hexdigest()),
            Decimal.from_float(time.process_time() - cpu), Decimal.from_float(time.perf_counter() - wall))
        records = dict(zip(MEMBERS[:-1], (request, selection, evidence, result, assessment, accepted), strict=True))
        payloads = {name: record.canonical_bytes() for name, record in records.items()}
        payloads['report.txt'] = report
        if sum(map(len, payloads.values())) > selection.maximum_analysis_bytes:
            raise ValueError('initial root export exceeds its selected complete package allocation')
        package = 'initial-root-package.' + sha256(b''.join(sha256(payloads[n]).digest() for n in MEMBERS)).hexdigest()
        parents = _parents(sources)
        writes = tuple(ArtifactWriteRequest('initial-root-member.' + sha256(raw).hexdigest() + '.' + name.replace('.', '-'),
            output_relative_path + '/' + name, records[name].SCHEMA if name in records else 'empirical-lawhood/rubisco-response/initial-root-text',
            ArtifactProfile.CANONICAL_JSON if name in records else ArtifactProfile.TEXT_PARAMETERS,
            'application/json' if name.endswith('.json') else 'text/plain', package, output_relative_path, raw,
            VisibilityCeiling.DEVELOPMENT_ONLY, tuple(p.visibility_ceiling for p in parents), OutcomeAccess.DEVELOPMENT_VISIBLE,
            lineage_parents=parents) for name, raw in payloads.items())
        publications = artifact_writer.write_batch(writes)
        return dict(request=request, selection=selection, inputs=evidence, result=result, assessment=assessment,
            evidence=accepted, new_native_calls=0, package_id=package, publications=publications,
            paths={name: str(artifact_writer.root.resolve(output_relative_path + '/' + name, for_write=False)) for name in MEMBERS})
    return with_initial_model_sources(selection=selection, evidence=evidence, sources=sources, consumer=publish)


def read_initial_root_export(*, directory_relative_path, sources, artifact_writer):
    validate_relative_locator(directory_relative_path)
    manifest = artifact_writer.read_manifest(directory_relative_path + '/evidence.json')
    def consume(members):
        expected = {directory_relative_path + '/' + name: name for name in MEMBERS}
        if set(members) != set(expected):
            raise ValueError('initial root export changes its complete closed member census')
        raw = {name: read_bounded_bytes(artifact_writer.root.resolve(path, for_write=False), maximum_bytes=MAXIMUM_BYTES)
            for path, name in expected.items()}
        kinds = (InitialRootRequest, InitialModelSelection, InitialModelEvidence, InitialRootResult, InitialRootAssessment, InitialRootAnalysisEvidence)
        request, selection, inputs, result, assessment, accepted = tuple(decode_canonical_bytes(raw[name], kind, maximum_bytes=MAXIMUM_BYTES)
            for name, kind in zip(MEMBERS[:-1], kinds, strict=True))
        validate_initial_root_inputs(request, selection, inputs)
        if (sum(map(len, raw.values())) > selection.maximum_analysis_bytes
                or (accepted.request, accepted.selection, accepted.inputs, accepted.result, accepted.assessment) !=
                    (request.identity, selection.identity, inputs.identity, result.identity, assessment.identity)
                or accepted.original_sources != required_initial_sources(selection, inputs)
                or accepted.report != FileEvidence('report.txt', len(raw['report.txt']), sha256(raw['report.txt']).hexdigest())
                or any(m.logical.lineage_parents != _parents(sources) for m in members.values())):
            raise ValueError('initial root export substitutes its original input, result or source ancestry')
        def reconstruct(reviews, joint_reviews):
            checked_result, checked_assessment = _calculate(request, selection, inputs, reviews, joint_reviews)
            if (result, assessment) != (checked_result, checked_assessment) or raw['report.txt'] != _text(request, result, assessment):
                raise ValueError('initial root export differs from its independent source reconstruction')
            return dict(request=request, selection=selection, inputs=inputs, result=result, assessment=assessment,
                evidence=accepted, new_native_calls=0,
                verification='ORIGINAL_SOURCE_PUBLICATIONS_AND_INDEPENDENT_JOINT_RECONSTRUCTION')
        return with_initial_model_sources(selection=selection, evidence=inputs, sources=sources, consumer=reconstruct)
    return artifact_writer.verify_manifest_members(manifest, validate_members=consume, before_member=_exposed)


__all__ = ('InitialRootRequest', 'InitialRootDomainLimit', 'InitialRootResult', 'InitialRootAssessment',
    'InitialRootAnalysisEvidence', 'InitialRootAnalysisInputs', 'InitialRootReviewInputs',
    'prepare_initial_root', 'prepare_initial_root_analysis', 'read_initial_root_sources',
    'export_initial_root', 'read_initial_root_export')
