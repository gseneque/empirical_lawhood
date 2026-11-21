# SPDX-License-Identifier: MPL-2.0
"""Measure and reread complete non-force analysis/export work in guarded custody."""

from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
import resource
import sys
import time

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_allocation import PilotAllocationRule, PilotCostMeasurement, allocate_pilot
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_allocation_read import RetainedPilotCalibration, read_pilot_allocation, validate_pilot_sources
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_analysis_cost import PilotAnalysisCostObservation, PilotAnalysisCostScope
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs
from empirical_lawhood.storage.bounded_io import bounded_file_sha256
from empirical_lawhood.storage.canonical_record_read import read_verified_canonical_record
from empirical_lawhood.science.records.decoding import decode_canonical_record
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.serialization import validate_relative_locator
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import MEMBERS, MAXIMUM_BYTES


def analysis_owners(kind):
    """Closed code-owned routes; input documents cannot select Python imports."""
    from empirical_lawhood.api.domain_composition.rubisco_response import electronic_ensembles, paired_forecast, physical_suppliers, reactive_flux
    owners = {
        'ELECTRONIC_ENSEMBLES': (electronic_ensembles.ElectronicEnsembleRule,
            electronic_ensembles.export_electronic_ensembles, electronic_ensembles.read_electronic_ensembles_export),
        'PAIRED_FORECAST': (paired_forecast.PairedForecastSelection,
            paired_forecast.export_paired_forecast, paired_forecast.read_paired_forecast_export),
        'PHYSICAL_SUPPLIERS': (physical_suppliers.PhysicalSupplierSelection,
            physical_suppliers.export_physical_suppliers, physical_suppliers.read_physical_supplier_export),
        'REACTIVE_FLUX': (reactive_flux.ReactiveFluxRule,
            reactive_flux.export_reactive_flux, reactive_flux.read_reactive_flux_export),
    }
    if kind not in owners:
        raise ValueError('unsupported pilot analysis/export operation')
    return owners[kind]


def _members(writer, directory):
    rows = []
    for name in sorted(MEMBERS):
        path = writer.root.resolve(directory+'/'+name, for_write=False)
        if path.exists():
            size, digest = bounded_file_sha256(path, maximum_bytes=MAXIMUM_BYTES)
            rows.append(FileEvidence(name, size, digest))
    return tuple(rows)


def _parent(pin):
    return ArtifactLineageParent(pin, VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)


def measure_pilot_analysis_export(*, analysis_kind, selection, sources, project_root, artifact_writer,
        output_relative_path, observation_relative_path):
    """Run only the existing read/export owner and retain the whole invocation.

    RSS is the conservative lifetime high-water of this controller process.
    A failed export remains a failed calibration with its observed costs and
    exact partial members. No native result is reacquired to fill a failure.
    """
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    kind, export, read = analysis_owners(analysis_kind)
    exact(selection, kind)
    for relative in (output_relative_path, observation_relative_path):
        validate_relative_locator(relative)
    destination = artifact_writer.root.resolve(observation_relative_path, for_write=True)
    output = artifact_writer.root.resolve(output_relative_path, for_write=True)
    if destination.exists() or output.exists() or destination == output or destination.is_relative_to(output):
        raise ValueError('analysis measurement requires fresh disjoint observation and export destinations')
    if sys.platform not in {'linux', 'darwin'}:
        raise ValueError('analysis cost measurement has no declared native RSS unit on this platform')
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256, expected_lock_sha256=implementation.dependency_lock_sha256)
    scope = PilotAnalysisCostScope(analysis_kind, selection.identity, provenance.identity)
    cpu, wall = time.process_time(), time.perf_counter()
    evidence, failure, exported = None, None, None
    try:
        exported = export(selection=selection, sources=sources, project_root=project_root,
            artifact_writer=artifact_writer, output_relative_path=output_relative_path)
        original = read(directory_relative_path=output_relative_path, sources=sources, artifact_writer=artifact_writer)
        if original['selection'] != selection or original['evidence'] != exported['evidence']:
            raise ValueError('measured analysis changes its exact independent reconstruction')
        evidence = original['evidence'].identity
    except Exception as error:
        failure = type(error).__name__+': '+str(error)
    cpu = Decimal.from_float(time.process_time()-cpu)
    wall = Decimal.from_float(time.perf_counter()-wall)
    rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*(1024 if sys.platform == 'linux' else 1)
    members = _members(artifact_writer, output_relative_path)
    cost = InquiryCost(cpu, wall, Decimal(sum(m.byte_count for m in members)))
    record = PilotAnalysisCostObservation('cost.pending', scope, provenance, output_relative_path, evidence, members,
        'COMPLETE' if failure is None else 'FAILED', cost, rss, failure)
    record = replace(record, observation_id='cost.pilot-analysis.'+record.fingerprint())
    relative = Path(observation_relative_path).parent.as_posix()
    parents = (_parent(evidence),) if evidence is not None else ()
    artifact_writer.write(ArtifactWriteRequest(record.observation_id, observation_relative_path, record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', record.observation_id, relative,
        record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, tuple(p.visibility_ceiling for p in parents),
        OutcomeAccess.DEVELOPMENT_VISIBLE, lineage_parents=parents))
    return dict(observation=record, observation_path=str(destination), exported=exported, new_native_calls=0)


@dataclass(frozen=True, slots=True)
class RetainedPilotAnalysisCalibration:
    calibration_id: str
    observation_relative_path: str | None
    observation: ObjectIdentity | None
    sources: tuple

    def __post_init__(self):
        if (self.observation_relative_path is None) != (self.observation is None):
            raise ValueError('non-force observation path and exact original identity must be supplied together')
        if self.observation_relative_path is not None:
            validate_relative_locator(self.observation_relative_path)
            exact(self.observation, ObjectIdentity)
        if type(self.sources) is not tuple:
            raise TypeError('non-force calibration requires its immutable original source census')


def read_pilot_analysis_calibration(*, case, profile, source, artifact_writer):
    exact(source, RetainedPilotAnalysisCalibration)
    if case.calibration_id != source.calibration_id or profile.unit != 'COMPLETE_ANALYSIS_EXPORT':
        raise ValueError('non-force calibration substitutes its cost class or calibration slot')
    if source.observation is None:
        return PilotCostMeasurement(case.calibration_id, case.configuration, None, 'MISSING_ORIGINAL',
            InquiryCost(None, None, None), 0, None, ('ORIGINAL_NOT_SUPPLIED_NOT_PROVEN_NONENTRY',))
    with artifact_writer.read_context() as reader:
        manifest = reader.read_manifest(source.observation_relative_path)
        record = read_verified_canonical_record(reader, manifest, PilotAnalysisCostObservation, maximum_bytes=2**20)
        if (record.identity != source.observation or record.scope.identity != profile.scope
                or record.scope.scientific_selection != case.configuration):
            raise ValueError('non-force calibration substitutes its original selection, implementation or observation')
        parents = (_parent(record.analysis_evidence),) if record.analysis_evidence is not None else ()
        if (manifest.logical.lineage_parents != parents
                or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError('non-force observation changes its original evidence lane or ancestry')
        if _members(reader, record.analysis_relative_path) != record.members:
            raise ValueError('non-force calibration original complete or partial export changed')
        if record.disposition == 'COMPLETE':
            _, _, read = analysis_owners(record.scope.analysis_kind)
            original = read(directory_relative_path=record.analysis_relative_path, sources=source.sources, artifact_writer=reader)
            if (original['selection'].identity != case.configuration or original['evidence'].identity != record.analysis_evidence
                    or original['evidence'].provenance.identity != record.scope.producing_provenance):
                raise ValueError('non-force calibration changes its authenticated original export')
        if _members(reader, record.analysis_relative_path) != record.members:
            raise ValueError('non-force calibration export changed during reconstruction')
        reader.verify_manifest(manifest)
    return PilotCostMeasurement(case.calibration_id, case.configuration, record.identity,
        record.disposition, record.cost, 1 if record.disposition == 'COMPLETE' else 0, record.process_peak_rss_bytes,
        () if record.disposition == 'COMPLETE' else ('ORIGINAL_ANALYSIS_EXPORT_FAILED',))


def read_complete_pilot_allocation(*, selection, native_sources, analysis_sources, artifact_writer, assessor_source):
    """Combine authenticated force and non-force costs in one complete rule."""
    exact(selection, PilotAllocationRule)
    if (type(native_sources) is not tuple or any(type(s) is not RetainedPilotCalibration for s in native_sources)
            or type(analysis_sources) is not tuple or any(type(s) is not RetainedPilotAnalysisCalibration for s in analysis_sources)):
        raise TypeError('complete cost read requires explicit immutable force and non-force carriers')
    all_sources = (*native_sources, *analysis_sources)
    by_id = {s.calibration_id:s for s in all_sources}
    if len(by_id) != len(all_sources) or set(by_id) != {c.calibration_id for c in selection.calibrations}:
        raise ValueError('complete cost read omits or repeats an original calibration')
    profiles = {p.class_id:p for p in selection.cost_classes}
    native_cases = tuple(c for c in selection.calibrations if type(by_id[c.calibration_id]) is RetainedPilotCalibration)
    native = tuple(by_id[c.calibration_id] for c in native_cases)
    # Reuse the accepted force reader. Its intermediate cost decision is not
    # used; the final allocation below includes every selected cost class.
    native_rule = replace(selection, calibrations=native_cases) if native_cases else None
    if native_rule is not None:
        validate_pilot_sources(native_rule, native)
    measurements = {}
    original_native = None
    if native_rule is not None:
        original_native, _ = read_pilot_allocation(selection=native_rule, sources=native, assessor_source=assessor_source)
        measurements.update((c.calibration_id, decode_canonical_record(document, PilotCostMeasurement))
            for c, document in zip(native_cases, original_native['original_calibrations'], strict=True))
    for case in selection.calibrations:
        source = by_id[case.calibration_id]
        if type(source) is RetainedPilotAnalysisCalibration:
            measurements[case.calibration_id] = read_pilot_analysis_calibration(case=case,
                profile=profiles[case.cost_class], source=source, artifact_writer=artifact_writer)
    report = allocate_pilot(selection, tuple(measurements[c.calibration_id] for c in selection.calibrations))
    recheck_original_native_outputs(native, description='complete pilot cost calibration')
    report['original_force_analysis'] = original_native
    report['non_force_scope'] = 'COMPLETE_ANALYSIS_EXPORT_AND_INDEPENDENT_RECONSTRUCTION_NO_NATIVE_ENTRY'
    report['new_native_calls'] = 0
    return report
